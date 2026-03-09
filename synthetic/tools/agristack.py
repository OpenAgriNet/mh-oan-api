"""Mock Agristack tool for Maharashtra synthetic conversations."""

import random
from pydantic_ai import RunContext
from synthetic.deps import FarmerContext
from synthetic.mock_data import should_fail


async def fetch_agristack_data(ctx: RunContext[FarmerContext]) -> str:
    """If Agristack Information is available for the user, use this tool to fetch it. This tool returns details of the farmer from the Agristack API, for instance:
        - Profile information such as Gender, Caste Category
        - Location information such as Village, Taluka, District, LGD Codes, and GPS Coordinates
        - Farm details such as Total Plot Area.
        - Masked PII information such as Name, Mobile, Date of Birth.
    """
    if not ctx.deps.farmer_id:
        return "Farmer ID is not available in the context. Please register with your farmer ID."

    if should_fail():
        return "Farmer information service unavailable. Please try again later."

    deps = ctx.deps

    # Mask PII values like the real tool does
    name = deps.farmer_name or "Unknown"
    masked_name = f"{name[:2]}***{name[-1]}" if name and len(name) > 4 else "***"

    phone = deps.farmer_phone or "0000000000"
    masked_phone = f"{phone[:2]}***{phone[-1]}"

    # Generate a mock DOB
    year = random.randint(1965, 2000)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    dob = f"{year:04d}-{month:02d}-{day:02d}"
    masked_dob = f"{str(year)[:2]}***{str(day)}"

    village = deps.farmer_village or "Unknown"
    taluka = deps.farmer_taluka or "Unknown"
    district = deps.farmer_district or "Unknown"
    gender = deps.farmer_gender or "Male"
    caste = deps.farmer_caste_category or "General"
    land_acres = deps.farmer_land_acres or 2.0
    land_hectares = round(land_acres * 0.4047, 2)
    is_pocra = "Yes" if deps.farmer_is_pocra else "No"
    lat = deps.farmer_latitude or 19.0
    lon = deps.farmer_longitude or 75.0

    village_code = deps.farmer_village_code or "000000"
    district_code = str(random.randint(500, 540))
    sub_district_code = str(random.randint(5000, 5400))

    lines = [
        "> Farmer Information (Agristack)",
        "Responses:",
        "    Provider: Agristack",
        "      Farmer Details:",
        f"        Name: {masked_name}",
        f"        Mobile: {masked_phone}",
        f"        Date of Birth: {masked_dob}",
        f"        Gender: {gender}",
        f"        Caste Category: {caste}",
        f"        Village Name: {village}",
        f"        Is PoCRA village?: {is_pocra}",
        f"        Taluka Name: {taluka}",
        f"        District Name: {district}",
        f"        Sub-District LGD Code: {sub_district_code}",
        f"        District LGD Code: {district_code}",
        f"        Village LGD Code: {village_code}",
        f"        Total Plot Area: {land_hectares} hectares",
        "      Locations:",
        f"        {village}, {taluka}, {district}, Maharashtra, India ({round(lat, 3)}, {round(lon, 3)})",
    ]

    return "\n".join(lines)
