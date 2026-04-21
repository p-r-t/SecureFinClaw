---
name: weather
description: >
  Get current weather conditions, temperature, humidity, wind, and multi-day forecasts for any
  city, airport code, or coordinates. No API key required. Use when the user asks about weather,
  temperature, rain, forecast, conditions, or anything climate-related. Works globally.
homepage: https://wttr.in/:help
metadata: {"finclaw":{"emoji":"🌤️","requires":{"bins":["curl"]}}}
---

# Weather

Two free, no-auth services. Default to wttr.in; fall back to Open-Meteo when structured JSON is needed.

## wttr.in (primary)

```bash
# Quick one-liner (current conditions)
curl -s "wttr.in/London?format=3"
# → London: ⛅️ +8°C

# Compact with humidity and wind
curl -s "wttr.in/London?format=%l:+%c+%t+(feels+%f)+%h+%w"
# → London: ⛅️ +8°C (feels +5°C) 71% ↙5km/h

# 3-day forecast (plain text, no ANSI colours)
curl -s "wttr.in/London?T"

# Today only
curl -s "wttr.in/London?1&T"

# Save as PNG (useful for sharing)
curl -s "wttr.in/Tokyo.png" -o /tmp/weather.png
```

**Format codes:** `%c` icon · `%t` temp · `%f` feels-like · `%h` humidity · `%w` wind · `%l` location · `%m` moon phase · `%p` precipitation · `%P` pressure

**URL tips:**
- Spaces → `+`: `wttr.in/New+York`
- Airport codes: `wttr.in/JFK`
- Coordinates: `wttr.in/-33.87,151.21` (Sydney)
- Units: `?m` metric · `?u` USCS · `?M` m/s wind

## Open-Meteo (fallback — JSON, no curl needed)

Best when the user wants structured data (temperature array, hourly breakdown):

```bash
# Step 1: Look up coordinates (use exec + python or known coords)
# Step 2: Query forecast
curl -s "https://api.open-meteo.com/v1/forecast?\
latitude=51.51&longitude=-0.12&\
current_weather=true&\
hourly=temperature_2m,precipitation_probability,weathercode&\
daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum&\
timezone=auto&forecast_days=3"
```

**WMO weather codes** (for `weathercode`): 0=clear · 1-3=partly cloudy · 45,48=fog ·
51-55=drizzle · 61-65=rain · 71-75=snow · 80-82=showers · 95=thunderstorm

Docs: https://open-meteo.com/en/docs

## Workflow

1. If the user gives a city name, use wttr.in directly — no coordinates needed.
2. If they ask for hourly breakdown or JSON data, use Open-Meteo.
3. Always mention the unit system in your response (°C / °F).
4. For forecasts beyond 3 days, note that wttr.in shows 3 days; Open-Meteo supports up to 16.
