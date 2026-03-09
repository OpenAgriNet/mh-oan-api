"""Mock geocoding tools for Maharashtra."""

import random
from typing import Optional
from synthetic.mock_data import LOCATIONS, should_fail


async def forward_geocode(place_name: str) -> Optional[str]:
    """Forward Geocoding to get latitude and longitude from place name.

    Args:
        place_name (str): The place name to geocode, in English.

    Returns:
        Location: The location of the place.
    """
    if should_fail():
        return None

    # Find a matching location or pick a random one
    place_lower = place_name.lower()
    matches = [
        loc for loc in LOCATIONS
        if place_lower in loc["district"].lower()
        or place_lower in loc["village"].lower()
        or place_lower in loc["taluka"].lower()
    ]

    loc = random.choice(matches) if matches else random.choice(LOCATIONS)
    place_str = f"{loc['village']}, {loc['taluka']}, {loc['district']}, Maharashtra, India"
    return f"{place_str} ({loc['lat']}, {loc['lon']})"


async def reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    """Reverse Geocoding to get place name from latitude and longitude.

    Args:
        latitude (float): The latitude of the location.
        longitude (float): The longitude of the location.

    Returns:
        Location: The location of the place.
    """
    if should_fail():
        return None

    # Find nearest location by distance
    best = min(
        LOCATIONS,
        key=lambda loc: abs(loc["lat"] - latitude) + abs(loc["lon"] - longitude),
    )
    return f"{best['village']}, {best['taluka']}, {best['district']}, Maharashtra, India ({round(latitude, 3)}, {round(longitude, 3)})"
