"""Prototype alert rule engine.

Every alert produced here is 
explicitly non-official guidance.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.utils.dateparse import parse_datetime
from django.utils import timezone

from weather.services import weather_service

from .models import Alert

HEAT_MAX_TEMP_C = 45.0
RAIN_PROBABILITY_PCT = 80
RAIN_PRECIPITATION_MM = 20.0
WIND_MAX_KMH = 50.0


class AlertEngine:
    """Evaluates the daily forecast against prototype thresholds."""

    def evaluate_forecast(
        self,
        latitude: float,
        longitude: float,
        location_name: str,
        forecast_daily: List[Dict[str, Any]],
    ) -> List[Alert]:
        alerts: List[Alert] = []
        for day in forecast_daily:
            alerts.extend(
                [
                    alert
                    for alert in (
                        self._heat_rule(latitude, longitude, location_name, day),
                        self._rain_rule(latitude, longitude, location_name, day),
                        self._wind_rule(latitude, longitude, location_name, day),
                    )
                    if alert is not None
                ]
            )
        return alerts

    def evaluate_and_save(
        self,
        latitude: float,
        longitude: float,
        location_name: str = "",
        days: int = 7,
    ) -> List[Alert]:
        """Fetch the forecast, evaluate rules, persist and return any new alerts."""
        forecast = weather_service.forecast(
            latitude=latitude,
            longitude=longitude,
            days=days,
            location_name=location_name or None,
        )
        candidates = self.evaluate_forecast(latitude, longitude, location_name, forecast["daily"])
        if not candidates:
            return []
        # Skip (type, day) pairs already stored so repeated GETs don't duplicate rows.
        existing = set(
            Alert.objects.filter(
                latitude=candidates[0].latitude, longitude=candidates[0].longitude
            ).values_list("alert_type", "starts_at")
        )
        fresh = [a for a in candidates if (a.alert_type, a.starts_at) not in existing]
        Alert.objects.bulk_create(fresh)
        return fresh

    def get_active_alerts(
        self, latitude: Optional[float] = None, longitude: Optional[float] = None
    ) -> List[Alert]:
        queryset = Alert.objects.filter(ends_at__gte=timezone.now())
        if latitude is not None and longitude is not None:
            queryset = queryset.filter(
                latitude=Decimal(str(latitude)), longitude=Decimal(str(longitude))
            )
        return list(queryset)

    # --- individual prototype rules -------------------------------------

    def _heat_rule(self, latitude, longitude, location_name, day) -> Optional[Alert]:
        max_temp = day.get("temperature_max_c")
        if max_temp is None or float(max_temp) < HEAT_MAX_TEMP_C:
            return None
        return self._build(
            latitude, longitude, location_name,
            alert_type=Alert.AlertType.HEAT,
            severity=Alert.Severity.HIGH,
            title=f"Extreme heat expected on {day['date']}",
            description=f"Maximum temperature of {max_temp}°C forecast.",
            advice="Stay hydrated, avoid outdoor activity during peak sun hours, and check on vulnerable people.",
            day=day,
        )

    def _rain_rule(self, latitude, longitude, location_name, day) -> Optional[Alert]:
        probability = day.get("precipitation_probability_pct")
        precipitation = day.get("precipitation_mm")
        if probability is None or precipitation is None:
            return None
        if float(probability) < RAIN_PROBABILITY_PCT or float(precipitation) < RAIN_PRECIPITATION_MM:
            return None
        return self._build(
            latitude, longitude, location_name,
            alert_type=Alert.AlertType.RAIN,
            severity=Alert.Severity.MEDIUM,
            title=f"Heavy rain likely on {day['date']}",
            description=f"{precipitation} mm of rain expected ({probability}% probability).",
            advice="Expect waterlogging, carry rain protection, and allow extra travel time.",
            day=day,
        )

    def _wind_rule(self, latitude, longitude, location_name, day) -> Optional[Alert]:
        wind = day.get("wind_max_kmh")
        if wind is None or float(wind) < WIND_MAX_KMH:
            return None
        return self._build(
            latitude, longitude, location_name,
            alert_type=Alert.AlertType.WIND,
            severity=Alert.Severity.MEDIUM,
            title=f"Strong winds expected on {day['date']}",
            description=f"Wind speeds up to {wind} km/h forecast.",
            advice="Secure loose outdoor objects and take care on exposed roads.",
            day=day,
        )

    def _build(self, latitude, longitude, location_name, *, alert_type, severity, title, description, advice, day) -> Alert:
        return Alert(
            location_name=location_name or "Unknown location",
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude)),
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            advice=advice,
            starts_at=parse_datetime(f"{day['date']}T00:00:00Z"),
            ends_at=parse_datetime(f"{day['date']}T23:59:59Z"),
        )