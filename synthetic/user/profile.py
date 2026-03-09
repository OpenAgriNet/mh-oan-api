"""
FarmerProfile model and random profile generator for synthetic user agent.
Maharashtra-specific: Marathi/English only, Maharashtra locations, MahaDBT schemes.
"""

import random
from pydantic import BaseModel

from synthetic.mock_data import (
    get_random_location,
    FARMER_CROPS,
    MOOD_WEIGHTS,
    LANGUAGE_WEIGHTS,
    LATIN_SCRIPT_PROBABILITY,
    SCENARIOS,
    ADVERSARIAL_SCENARIO_IDS,
    GENDERS,
    GENDER_WEIGHTS,
    CASTE_CATEGORIES,
    CASTE_WEIGHTS,
    fake,
    random_name,
)


class FarmerProfile(BaseModel):
    """Profile of a simulated Maharashtra farmer for synthetic conversation generation."""

    # Identity
    name: str
    phone: str
    farmer_id: str  # Agristack farmer ID

    # Location
    state: str = "Maharashtra"
    district: str
    taluka: str
    village: str
    village_code: str
    latitude: float
    longitude: float

    # Demographics
    gender: str
    caste_category: str

    # Farming
    crops: list[str]
    land_acres: float
    is_pocra: bool

    # Language & behavior
    language: str
    use_latin_script: bool = False
    mood: str
    verbosity: str

    # Scenario
    scenario: dict

    # Extra context
    has_agristack: bool = True  # Whether farmer is registered in Agristack
    mahadbt_scheme_codes: list[str] = []  # Active MahaDBT scheme applications


def _render_scenario(scenario: dict, profile_data: dict) -> dict:
    """Render template variables in scenario descriptions."""
    rendered = dict(scenario)
    rendered["description"] = rendered["description"].format(**profile_data)
    return rendered


def generate_random_profile(
    language: str | None = None,
    scenario_id: str | None = None,
    mood: str | None = None,
) -> FarmerProfile:
    """Generate a random FarmerProfile for synthetic conversation generation."""

    # Location (from Maharashtra locations)
    loc = get_random_location()

    # Crops: 1-3 random crops
    num_crops = random.randint(1, 3)
    crops = random.sample(FARMER_CROPS, num_crops)

    # Phone: Indian mobile number
    phone = str(random.choice([6, 7, 8, 9])) + "".join(
        str(random.randint(0, 9)) for _ in range(9)
    )

    # Farmer ID: 11-digit number (Agristack format)
    farmer_id = "".join(str(random.randint(0, 9)) for _ in range(11))

    # Village code: 6-digit LGD code
    village_code = "".join(str(random.randint(0, 9)) for _ in range(6))

    # Demographics
    gender = random.choices(GENDERS, weights=GENDER_WEIGHTS, k=1)[0]
    caste_category = random.choices(CASTE_CATEGORIES, weights=CASTE_WEIGHTS, k=1)[0]

    # PoCRA village: ~40% of Maharashtra villages
    is_pocra = random.random() < 0.40

    # Language (weighted random)
    if language is None:
        langs, weights = zip(*LANGUAGE_WEIGHTS.items())
        language = random.choices(langs, weights=weights, k=1)[0]

    # Latin script transliteration (~10% for MH — many farmers type in Roman Marathi)
    use_latin_script = language != "en" and random.random() < LATIN_SCRIPT_PROBABILITY

    # Mood
    if mood is None:
        moods, weights = zip(*MOOD_WEIGHTS.items())
        mood = random.choices(moods, weights=weights, k=1)[0]

    # Land acres: 0.5 to 10.0 (Maharashtra farms tend to be smaller)
    land_acres = round(random.uniform(0.5, 10.0), 1)

    # Verbosity
    verbosity = random.choices(
        ["low", "medium", "high"],
        weights=[0.7, 0.2, 0.1],
        k=1,
    )[0]

    # Scenario
    if scenario_id is not None:
        scenario = next(s for s in SCENARIOS if s["id"] == scenario_id)
    elif mood == "adversarial":
        adversarial_scenarios = [
            s for s in SCENARIOS if s["id"] in ADVERSARIAL_SCENARIO_IDS
        ]
        scenario = random.choice(adversarial_scenarios)
    else:
        normal_scenarios = [
            s for s in SCENARIOS if s["id"] not in ADVERSARIAL_SCENARIO_IDS
        ]
        scenario = random.choice(normal_scenarios)

    scenario = _render_scenario(
        scenario,
        {
            "crop": random.choice(crops),
            "district": loc["district"],
            "taluka": loc["taluka"],
            "village": loc["village"],
            "land_acres": land_acres,
        },
    )

    # Agristack availability: 85% of farmers have it
    has_agristack = random.random() < 0.85

    # MahaDBT schemes: 0-3 active applications
    from synthetic.mock_data import SAMPLE_STATE_SCHEMES, SAMPLE_CENTRAL_SCHEMES
    num_schemes = random.choices([0, 1, 2, 3], weights=[0.3, 0.35, 0.25, 0.10], k=1)[0]
    all_schemes = SAMPLE_STATE_SCHEMES + SAMPLE_CENTRAL_SCHEMES
    mahadbt_scheme_codes = random.sample(all_schemes, min(num_schemes, len(all_schemes)))

    return FarmerProfile(
        name=random_name(),
        phone=phone,
        farmer_id=farmer_id,
        state="Maharashtra",
        district=loc["district"],
        taluka=loc["taluka"],
        village=loc["village"],
        village_code=village_code,
        latitude=loc["lat"],
        longitude=loc["lon"],
        gender=gender,
        caste_category=caste_category,
        crops=crops,
        land_acres=land_acres,
        is_pocra=is_pocra,
        language=language,
        use_latin_script=use_latin_script,
        mood=mood,
        verbosity=verbosity,
        scenario=scenario,
        has_agristack=has_agristack,
        mahadbt_scheme_codes=mahadbt_scheme_codes,
    )
