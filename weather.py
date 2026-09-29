import requests

BASE = "https://api.open-meteo.com/v1/forecast"

def current_weather(lat, lon):
    params = {
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
        "timezone": "auto"
    }
    r = requests.get(BASE, params=params, timeout=10)
    r.raise_for_status()
    c = r.json().get("current", {})
    return {
        "temperature": c.get("temperature_2m"),
        "humidity": c.get("relative_humidity_2m"),
        "rainfall": c.get("precipitation"),
        "wind_speed": c.get("wind_speed_10m"),
        "weather_code": c.get("weather_code")
    }
