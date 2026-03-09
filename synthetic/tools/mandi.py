"""Mock mandi price tool for Maharashtra."""

import random
from datetime import datetime, timedelta

from synthetic.mock_data import (
    MANDI_NAMES, MANDI_DISTRICTS,
    CROP_PRICE_RANGES, DEFAULT_PRICE_RANGE,
    COMMODITY_VARIETIES, DEFAULT_VARIETIES,
    GRADES, should_fail,
)


async def mandi_prices(latitude: float, longitude: float) -> str:
    """Get Market/Mandi prices for a specific location.

    Args:
        latitude (float): Latitude of the location
        longitude (float): Longitude of the location

    Returns:
        str: The mandi prices for the specific location
    """
    if should_fail():
        return "Mandi service unavailable. Retrying"

    # 15% chance no data
    if random.random() < 0.15:
        return "> Mandi Price Data\nNo mandi price data found for the requested location."

    # Pick 2-6 nearby mandis
    num_mandis = random.choices([1, 2, 3, 4, 5, 6], weights=[0.05, 0.15, 0.30, 0.25, 0.15, 0.10], k=1)[0]
    selected_mandis = random.sample(MANDI_NAMES, min(num_mandis, len(MANDI_NAMES)))

    lines = ["> Mandi Price Data", "Responses:"]

    for mandi_name in selected_mandis:
        district = MANDI_DISTRICTS.get(mandi_name, "Unknown")
        lines.append(f"  Provider: {mandi_name}")
        lines.append("  Locations:")
        lines.append(f"    - {district}")
        lines.append("  Items:")

        # 1-4 commodities per mandi
        num_commodities = random.randint(1, 4)
        commodity_names = random.sample(list(CROP_PRICE_RANGES.keys()), min(num_commodities, len(CROP_PRICE_RANGES)))

        for commodity in commodity_names:
            lo, hi = CROP_PRICE_RANGES.get(commodity, DEFAULT_PRICE_RANGE)
            est = random.randint(lo, hi)
            min_price = max(lo, est - random.randint(100, 500))
            max_price = min(hi + 500, est + random.randint(100, 500))

            varieties = COMMODITY_VARIETIES.get(commodity, DEFAULT_VARIETIES)
            variety = random.choice(varieties)

            days_ago = random.randint(0, 10)
            date = datetime.now() - timedelta(days=days_ago)
            relative = f"{days_ago} days ago" if days_ago > 0 else "today"

            lines.append(f"    - {commodity} ({variety}): Min: ₹{min_price}, Max: ₹{max_price}, Est: ₹{est} ({relative})")

    return "\n".join(lines)
