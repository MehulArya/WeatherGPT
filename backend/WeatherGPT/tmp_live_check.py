import json

from weather.services import weather_service

print("=== CURRENT (Jaipur) ===")
print(json.dumps(weather_service.current(26.9124, 75.7873, "Jaipur"), indent=2))

print("\n=== FORECAST 3 days (Jaipur) ===")
print(json.dumps(weather_service.forecast(26.9124, 75.7873, 3, "Jaipur"), indent=2))