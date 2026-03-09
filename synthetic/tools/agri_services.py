"""Mock agricultural services tool for Maharashtra."""

import random
from typing import Literal
from synthetic.mock_data import (
    KVK_NAMES, CHC_NAMES, SOIL_LAB_NAMES, WAREHOUSE_NAMES,
    LOCATIONS, should_fail,
)


async def agri_services(latitude: float, longitude: float, category_code: Literal["kvk", "chc", "soil_lab", "warehouse"]) -> str:
    """Fetch agricultural services (KVK, CHC, soil labs, warehouse) for a given location via BAP.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        category_code: Service category to fetch - 'kvk' for Krishi Vigyan Kendra, 'chc' for Custom Hiring Center, 'soil_lab' for soil testing laboratories, 'warehouse' for warehouses

    Returns:
        str: Formatted agricultural services response
    """
    if should_fail():
        return "Agricultural services unavailable. Retrying"

    # Select appropriate names list
    name_map = {
        "kvk": KVK_NAMES,
        "chc": CHC_NAMES,
        "soil_lab": SOIL_LAB_NAMES,
        "warehouse": WAREHOUSE_NAMES,
    }
    names = name_map.get(category_code, KVK_NAMES)

    # 10% chance no results
    if random.random() < 0.10:
        return "> Agricultural Services\nNo agricultural services found for the requested location."

    # Pick 1-3 services
    num = random.randint(1, min(3, len(names)))
    selected = random.sample(names, num)

    lines = ["> Agricultural Services", "Responses:"]
    lines.append("    Providers:")

    for service_name in selected:
        loc = random.choice(LOCATIONS)
        distance = round(random.uniform(2.0, 45.0), 1)
        phone = str(random.choice([6, 7, 8, 9])) + "".join(str(random.randint(0, 9)) for _ in range(9))

        lines.append(f"    **{service_name}**")
        lines.append(f"      Location: {loc['village']}, {loc['taluka']}, {loc['district']}")
        lines.append(f"      Phone: {phone}")
        lines.append(f"      Distance: {distance} km")

    return "\n".join(lines)
