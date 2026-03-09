"""Mock agricultural staff contact tool for Maharashtra."""

import random
from synthetic.mock_data import (
    OFFICER_NAMES, OFFICER_ROLES, LOCATIONS, should_fail,
)


async def contact_agricultural_staff(latitude: float, longitude: float) -> str:
    """Get the contact information for the agricultural staff for a specific location.

    Args:
        latitude (float): Latitude of the location
        longitude (float): Longitude of the location

    Returns:
        str: The contact information for the agricultural staff for the specific location
    """
    if should_fail():
        return "Agricultural staff details unavailable."

    # 10% chance no officers found
    if random.random() < 0.10:
        return "> Officer Details\nNo officer details found for the requested location."

    # Pick 1-3 officers
    num = random.randint(1, 3)

    lines = ["> Officer Details", "Responses:"]
    lines.append("    Providers:")
    lines.append("      Provider: Maharashtra Agriculture Department")
    lines.append("      Officers:")

    for _ in range(num):
        name = random.choice(OFFICER_NAMES)
        role = random.choice(OFFICER_ROLES)
        loc = random.choice(LOCATIONS)
        phone = str(random.choice([6, 7, 8, 9])) + "".join(str(random.randint(0, 9)) for _ in range(9))

        lines.append(f"        **{name}**")
        lines.append(f"          Role: {role}")
        lines.append(f"          Location: {loc['village']}, {loc['taluka']}, {loc['district']}")
        lines.append(f"          Phone: {phone}")

    return "\n".join(lines)
