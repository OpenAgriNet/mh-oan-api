"""Mock weather tools for Maharashtra."""

from datetime import datetime, timedelta

from synthetic.mock_data import (
    random_temp, random_weather, should_fail,
)


def _get_season_from_month(month: int) -> str:
    if month in (3, 4, 5):
        return "summer"
    elif month in (6, 7, 8, 9):
        return "monsoon"
    elif month in (10, 11):
        return "spring"
    else:
        return "winter"


def _generate_weather_days(num_days: int, start_date: datetime, response_type: str = "forecast") -> str:
    """Generate mock weather data for a number of days."""
    season = _get_season_from_month(start_date.month)
    lines = []

    if response_type == "historical":
        lines.append(f"**Weather Historical Data** [Today's Date: {datetime.now().strftime('%A, %d %B %Y')}]")
    else:
        lines.append(f"**Weather Forecast Data** [Today's Date: {datetime.now().strftime('%A, %d %B %Y')}]")

    lines.append("Responses:")
    lines.append("    Catalog: Weather Data")
    lines.append("    Providers:")
    lines.append("      Provider: IMD/Skymet")
    lines.append("      Items:")

    for i in range(num_days):
        if response_type == "historical":
            day = start_date - timedelta(days=num_days - i)
        else:
            day = start_date + timedelta(days=i)

        min_t, max_t = random_temp(season)
        w = random_weather(season)

        lines.append(f"        {day.strftime('%Y-%m-%d')}:")
        lines.append(f"          Condition: {w['condition']}")
        lines.append(f"          Min Temp: {min_t}°C")
        lines.append(f"          Max Temp: {max_t}°C")
        lines.append(f"          Humidity: {w['humidity']}%")
        lines.append(f"          Rainfall: {w['rainfall']} mm")
        lines.append(f"          Wind: {w['wind_speed']} km/h {w['wind_dir']}")

    return "\n".join(lines)


async def weather_forecast(latitude: float, longitude: float, days: int = 5) -> str:
    """Get Weather forecast for a specific location.

    Args:
        latitude (float): Latitude of the location
        longitude (float): Longitude of the location
        days (int): Number of days for weather forecast (defaults to 5)

    Returns:
        str: The weather forecast for the specific location
    """
    if should_fail():
        return "Weather service unavailable. Retrying"

    days = min(days, 7)
    return _generate_weather_days(days, datetime.now(), "forecast")


async def weather_historical(latitude: float, longitude: float, days: int = 5) -> str:
    """Get historical weather data for a specific location.

    Args:
        latitude (float): Latitude of the location
        longitude (float): Longitude of the location
        days (int): Number of days for weather history (defaults to 5)

    Returns:
        str: The historical weather data for the specific location
    """
    if should_fail():
        return "Weather service unavailable. Retrying"

    days = min(days, 7)
    return _generate_weather_days(days, datetime.now(), "historical")
