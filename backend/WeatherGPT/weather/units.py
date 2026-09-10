"""Unit conversion utilities.

Canonical storage is always metric (C, km/h, mm).
Imperial conversions happen at the API boundary only.
"""

VALID_UNITS = ("metric", "imperial")


def celsius_to_fahrenheit(c: float) -> float:
    return round(c * 9.0 / 5.0 + 32.0, 1)


def kmh_to_mph(kmh: float) -> float:
    return round(kmh * 0.621371, 1)


def mm_to_inches(mm: float) -> float:
    return round(mm / 25.4, 2)


def convert_current(current: dict, units: str) -> dict:
    if units != "imperial":
        return current
    out = dict(current)
    if out.get("temperature_c") is not None:
        out["temperature_f"] = celsius_to_fahrenheit(out.pop("temperature_c"))
    if out.get("feels_like_c") is not None:
        out["feels_like_f"] = celsius_to_fahrenheit(out.pop("feels_like_c"))
    if out.get("wind_kmh") is not None:
        out["wind_mph"] = kmh_to_mph(out.pop("wind_kmh"))
    if out.get("precipitation_mm") is not None:
        out["precipitation_in"] = mm_to_inches(out.pop("precipitation_mm"))
    return out


def convert_daily(day: dict, units: str) -> dict:
    if units != "imperial":
        return day
    out = dict(day)
    if out.get("temperature_max_c") is not None:
        out["temperature_max_f"] = celsius_to_fahrenheit(out.pop("temperature_max_c"))
    if out.get("temperature_min_c") is not None:
        out["temperature_min_f"] = celsius_to_fahrenheit(out.pop("temperature_min_c"))
    if out.get("precipitation_mm") is not None:
        out["precipitation_in"] = mm_to_inches(out.pop("precipitation_mm"))
    if out.get("wind_max_kmh") is not None:
        out["wind_max_mph"] = kmh_to_mph(out.pop("wind_max_kmh"))
    return out


def convert_hourly(hour: dict, units: str) -> dict:
    if units != "imperial":
        return hour
    out = dict(hour)
    if out.get("temperature_c") is not None:
        out["temperature_f"] = celsius_to_fahrenheit(out.pop("temperature_c"))
    if out.get("wind_kmh") is not None:
        out["wind_mph"] = kmh_to_mph(out.pop("wind_kmh"))
    if out.get("precipitation_mm") is not None:
        out["precipitation_in"] = mm_to_inches(out.pop("precipitation_mm"))
    return out
