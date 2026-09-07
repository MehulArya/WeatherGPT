from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from common.errors import WeatherProviderError
from weather.services import weather_service

from .models import Alert
from .services import AlertEngine


def _day(date="2026-09-08", **overrides):
    day = {
        "date": date,
        "temperature_max_c": 30.0,
        "temperature_min_c": 20.0,
        "precipitation_probability_pct": 10,
        "precipitation_mm": 0.0,
        "wind_max_kmh": 12.0,
        "condition": "Sunny",
    }
    day.update(overrides)
    return day


class AlertEngineTests(TestCase):
    def setUp(self):
        self.engine = AlertEngine()
        self.coords = {"latitude": 26.91962, "longitude": 75.78781, "location_name": "Jaipur"}

    def test_no_alerts_for_mild_forecast(self):
        alerts = self.engine.evaluate_forecast(forecast_daily=[_day()], **self.coords)
        self.assertEqual(alerts, [])

    def test_heat_alert_when_max_temp_reaches_threshold(self):
        alerts = self.engine.evaluate_forecast(
            forecast_daily=[_day(temperature_max_c=45.0)], **self.coords
        )
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_type, Alert.AlertType.HEAT)
        self.assertEqual(alerts[0].severity, Alert.Severity.HIGH)

    def test_rain_alert_requires_probability_and_amount(self):
        at_threshold = self.engine.evaluate_forecast(
            forecast_daily=[_day(precipitation_probability_pct=80, precipitation_mm=20.0)],
            **self.coords,
        )
        self.assertEqual(len(at_threshold), 1)
        self.assertEqual(at_threshold[0].alert_type, Alert.AlertType.RAIN)

        below = self.engine.evaluate_forecast(
            forecast_daily=[_day(precipitation_probability_pct=79, precipitation_mm=25.0)],
            **self.coords,
        )
        self.assertEqual(below, [])

    def test_wind_alert_when_speed_reaches_threshold(self):
        alerts = self.engine.evaluate_forecast(
            forecast_daily=[_day(wind_max_kmh=50.0)], **self.coords
        )
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_type, Alert.AlertType.WIND)

    def test_alerts_are_always_prototype_not_official(self):
        alerts = self.engine.evaluate_forecast(
            forecast_daily=[_day(temperature_max_c=47.0)], **self.coords
        )
        self.assertFalse(alerts[0].is_official)
        self.assertEqual(alerts[0].source, "prototype-rule-engine")

    def test_evaluate_and_save_persists_and_dedupes(self):
        forecast = {"daily": [_day(temperature_max_c=46.0)]}
        with mock.patch.object(weather_service, "forecast", return_value=forecast):
            first = self.engine.evaluate_and_save(days=7, **self.coords)
            second = self.engine.evaluate_and_save(days=7, **self.coords)
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertEqual(Alert.objects.count(), 1)

    def test_evaluate_and_save_propagates_provider_error(self):
        with mock.patch.object(weather_service, "forecast", side_effect=WeatherProviderError()):
            with self.assertRaises(WeatherProviderError):
                self.engine.evaluate_and_save(days=7, **self.coords)


class AlertEndpointTests(TestCase):
    def setUp(self):
        self.url = reverse("alert-list")
        self.coords = {"latitude": "26.91962", "longitude": "75.78781"}

    def _create_alert(self, **overrides):
        defaults = dict(
            location_name="Jaipur",
            latitude=Decimal("26.91962"),
            longitude=Decimal("75.78781"),
            alert_type=Alert.AlertType.RAIN,
            severity=Alert.Severity.MEDIUM,
            title="Heavy rain likely",
            description="20 mm of rain expected.",
            advice="Carry rain protection.",
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=2),
        )
        defaults.update(overrides)
        return Alert.objects.create(**defaults)

    def test_list_without_params_returns_active_alerts_only(self):
        self._create_alert()
        self._create_alert(title="Expired", ends_at=timezone.now() - timedelta(hours=1))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Heavy rain likely")

    def test_query_params_trigger_engine_evaluation(self):
        with mock.patch.object(AlertEngine, "evaluate_and_save", return_value=[]) as evaluate:
            response = self.client.get(self.url, self.coords)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        evaluate.assert_called_once()

    def test_single_coordinate_is_rejected(self):
        response = self.client.get(self.url, {"latitude": "26.91962"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "INVALID_QUERY")

    def test_days_out_of_range_is_rejected(self):
        response = self.client.get(self.url, {**self.coords, "days": "20"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "INVALID_QUERY")

    def test_create_alert_via_post(self):
        payload = {
            "location_name": "Jaipur",
            "latitude": "26.91962",
            "longitude": "75.78781",
            "alert_type": "rain",
            "severity": "medium",
            "title": "Heavy rain likely",
            "description": "20 mm of rain expected.",
            "advice": "Carry rain protection.",
            "starts_at": "2026-09-08T00:00:00Z",
            "ends_at": "2026-09-08T23:59:59Z",
        }
        response = self.client.post(self.url, payload, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data["is_official"])
        self.assertEqual(response.data["source"], "prototype-rule-engine")