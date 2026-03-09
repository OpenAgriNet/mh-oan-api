"""
Data pools for synthetic conversation generation — Maharashtra-specific.
Indian names, Maharashtra locations, APMC mandi names, crop price ranges,
weather ranges, agristack profiles, MahaDBT statuses, agricultural services.
"""

import json
import random
from pathlib import Path
from typing import Tuple

from faker import Faker

fake = Faker("en_IN")


# ─── Failure Simulation ──────────────────────────────────────────────────────

MOCK_FAILURE_RATE = 0.05


def should_fail() -> bool:
    return random.random() < MOCK_FAILURE_RATE


# ─── Indian Names (via Faker en_IN) ──────────────────────────────────────────


def random_name() -> str:
    return fake.name()


# ─── Maharashtra Locations (district, taluka, village, lat, lon) ─────────────

LOCATIONS: list[dict] = [
    # Pune Division
    {"district": "Pune", "taluka": "Junnar", "village": "Otur", "lat": 19.27, "lon": 73.83},
    {"district": "Pune", "taluka": "Baramati", "village": "Morgaon", "lat": 18.27, "lon": 74.22},
    {"district": "Pune", "taluka": "Indapur", "village": "Nimgaon Ketki", "lat": 18.12, "lon": 75.02},
    {"district": "Pune", "taluka": "Shirur", "village": "Pabal", "lat": 18.85, "lon": 74.18},
    {"district": "Pune", "taluka": "Daund", "village": "Yavat", "lat": 18.52, "lon": 74.18},
    {"district": "Satara", "taluka": "Wai", "village": "Surur", "lat": 17.95, "lon": 73.89},
    {"district": "Satara", "taluka": "Karad", "village": "Umbraj", "lat": 17.28, "lon": 74.19},
    {"district": "Solapur", "taluka": "Pandharpur", "village": "Mangalvedhe", "lat": 17.67, "lon": 75.33},
    {"district": "Solapur", "taluka": "Barshi", "village": "Pangaon", "lat": 18.23, "lon": 75.69},
    {"district": "Kolhapur", "taluka": "Hatkanangle", "village": "Ichalkaranji", "lat": 16.69, "lon": 74.46},
    {"district": "Kolhapur", "taluka": "Karveer", "village": "Kagal", "lat": 16.58, "lon": 74.32},
    {"district": "Sangli", "taluka": "Miraj", "village": "Kupwad", "lat": 16.82, "lon": 74.66},
    {"district": "Sangli", "taluka": "Tasgaon", "village": "Kundal", "lat": 17.04, "lon": 74.61},
    # Nashik Division
    {"district": "Nashik", "taluka": "Sinnar", "village": "Shirdi", "lat": 19.77, "lon": 74.48},
    {"district": "Nashik", "taluka": "Niphad", "village": "Lasalgaon", "lat": 20.14, "lon": 74.23},
    {"district": "Nashik", "taluka": "Dindori", "village": "Vani", "lat": 20.35, "lon": 73.88},
    {"district": "Ahmednagar", "taluka": "Shrirampur", "village": "Belapur", "lat": 19.62, "lon": 74.65},
    {"district": "Ahmednagar", "taluka": "Rahuri", "village": "Loni Bk.", "lat": 19.39, "lon": 74.65},
    {"district": "Ahmednagar", "taluka": "Sangamner", "village": "Akole", "lat": 19.54, "lon": 73.89},
    {"district": "Jalgaon", "taluka": "Chopda", "village": "Adavad", "lat": 21.25, "lon": 75.29},
    {"district": "Jalgaon", "taluka": "Raver", "village": "Savda", "lat": 21.15, "lon": 76.07},
    {"district": "Dhule", "taluka": "Shirpur", "village": "Dondaicha", "lat": 21.33, "lon": 74.57},
    {"district": "Nandurbar", "taluka": "Shahada", "village": "Taloda", "lat": 21.56, "lon": 74.21},
    # Aurangabad / Marathwada Division
    {"district": "Aurangabad", "taluka": "Paithan", "village": "Lasur", "lat": 19.47, "lon": 75.38},
    {"district": "Aurangabad", "taluka": "Gangapur", "village": "Vaijapur", "lat": 19.93, "lon": 74.73},
    {"district": "Beed", "taluka": "Georai", "village": "Majalgaon", "lat": 19.15, "lon": 76.23},
    {"district": "Beed", "taluka": "Ashti", "village": "Patoda", "lat": 19.22, "lon": 75.43},
    {"district": "Latur", "taluka": "Udgir", "village": "Ahmedpur", "lat": 18.07, "lon": 76.93},
    {"district": "Latur", "taluka": "Nilanga", "village": "Deoni", "lat": 17.69, "lon": 76.75},
    {"district": "Osmanabad", "taluka": "Tuljapur", "village": "Omerga", "lat": 17.52, "lon": 76.04},
    {"district": "Parbhani", "taluka": "Jintur", "village": "Manwath", "lat": 19.10, "lon": 76.49},
    {"district": "Hingoli", "taluka": "Kalamnuri", "village": "Sengaon", "lat": 19.68, "lon": 76.96},
    {"district": "Jalna", "taluka": "Ambad", "village": "Ghansawangi", "lat": 19.79, "lon": 75.87},
    {"district": "Nanded", "taluka": "Deglur", "village": "Biloli", "lat": 18.77, "lon": 77.08},
    # Nagpur / Vidarbha Division
    {"district": "Nagpur", "taluka": "Kamptee", "village": "Saoner", "lat": 21.23, "lon": 78.92},
    {"district": "Nagpur", "taluka": "Hingna", "village": "Umred", "lat": 20.85, "lon": 79.33},
    {"district": "Amravati", "taluka": "Morshi", "village": "Chandur Railway", "lat": 21.33, "lon": 78.05},
    {"district": "Amravati", "taluka": "Achalpur", "village": "Paratwada", "lat": 21.26, "lon": 77.08},
    {"district": "Yavatmal", "taluka": "Pusad", "village": "Mahagaon", "lat": 19.91, "lon": 77.57},
    {"district": "Yavatmal", "taluka": "Arni", "village": "Digras", "lat": 20.10, "lon": 77.72},
    {"district": "Akola", "taluka": "Akot", "village": "Telhara", "lat": 21.09, "lon": 77.09},
    {"district": "Washim", "taluka": "Malegaon", "village": "Risod", "lat": 20.01, "lon": 76.78},
    {"district": "Buldhana", "taluka": "Chikhli", "village": "Deulgaon Raja", "lat": 20.02, "lon": 76.35},
    {"district": "Wardha", "taluka": "Arvi", "village": "Seloo", "lat": 20.75, "lon": 78.91},
    {"district": "Chandrapur", "taluka": "Warora", "village": "Bhadrawati", "lat": 20.10, "lon": 79.12},
    {"district": "Gadchiroli", "taluka": "Chamorshi", "village": "Aheri", "lat": 19.41, "lon": 80.00},
    {"district": "Gondia", "taluka": "Tirora", "village": "Goregaon", "lat": 21.38, "lon": 80.19},
    {"district": "Bhandara", "taluka": "Tumsar", "village": "Pauni", "lat": 20.79, "lon": 79.63},
    # Konkan Division
    {"district": "Raigad", "taluka": "Panvel", "village": "Pen", "lat": 18.74, "lon": 73.10},
    {"district": "Ratnagiri", "taluka": "Chiplun", "village": "Khed", "lat": 17.33, "lon": 73.52},
    {"district": "Sindhudurg", "taluka": "Kudal", "village": "Malvan", "lat": 16.06, "lon": 73.46},
    {"district": "Thane", "taluka": "Bhiwandi", "village": "Shahapur", "lat": 19.45, "lon": 73.33},
    {"district": "Palghar", "taluka": "Dahanu", "village": "Jawhar", "lat": 19.92, "lon": 73.23},
]


def get_random_location() -> dict:
    return random.choice(LOCATIONS)


# ─── Maharashtra APMC Mandi Names ────────────────────────────────────────────

MANDI_NAMES = [
    "Lasalgaon APMC", "Pune Market Yard", "Nashik APMC", "Solapur APMC",
    "Sangli APMC", "Kolhapur APMC", "Aurangabad APMC", "Nagpur APMC",
    "Latur APMC", "Jalgaon APMC", "Ahmednagar APMC", "Satara APMC",
    "Amravati APMC", "Akola APMC", "Beed APMC", "Parbhani APMC",
    "Nanded APMC", "Osmanabad APMC", "Yavatmal APMC", "Chandrapur APMC",
    "Baramati APMC", "Niphad APMC", "Rahuri APMC", "Pandharpur APMC",
    "Indapur APMC", "Kopargaon APMC", "Shrirampur APMC", "Karad APMC",
]

MANDI_DISTRICTS = {
    "Lasalgaon APMC": "Nashik", "Pune Market Yard": "Pune", "Nashik APMC": "Nashik",
    "Solapur APMC": "Solapur", "Sangli APMC": "Sangli", "Kolhapur APMC": "Kolhapur",
    "Aurangabad APMC": "Aurangabad", "Nagpur APMC": "Nagpur", "Latur APMC": "Latur",
    "Jalgaon APMC": "Jalgaon", "Ahmednagar APMC": "Ahmednagar", "Satara APMC": "Satara",
    "Amravati APMC": "Amravati", "Akola APMC": "Akola", "Beed APMC": "Beed",
    "Parbhani APMC": "Parbhani", "Nanded APMC": "Nanded", "Osmanabad APMC": "Osmanabad",
    "Yavatmal APMC": "Yavatmal", "Chandrapur APMC": "Chandrapur",
}


# ─── Crop Price Ranges (INR per quintal) — Maharashtra-focused ───────────────

CROP_PRICE_RANGES: dict[str, Tuple[int, int]] = {
    "Onion": (800, 3500),
    "Soybean": (3800, 5500),
    "Cotton": (5500, 8000),
    "Sugarcane": (280, 380),
    "Jowar": (2200, 3500),
    "Bajra": (1800, 2800),
    "Wheat": (2000, 2800),
    "Paddy": (1800, 2600),
    "Rice": (2800, 4200),
    "Maize": (1600, 2400),
    "Gram": (4500, 6500),
    "Tur Dal": (5500, 8000),
    "Green Gram": (6000, 8500),
    "Black Gram": (5000, 7500),
    "Groundnut": (4500, 6500),
    "Sunflower": (4500, 6500),
    "Turmeric": (6000, 12000),
    "Chili Red": (8000, 18000),
    "Ginger": (5000, 12000),
    "Garlic": (3000, 10000),
    "Potato": (600, 2000),
    "Tomato": (500, 3000),
    "Grapes": (3000, 8000),
    "Pomegranate": (4000, 12000),
    "Orange": (2000, 5000),
    "Banana": (1000, 3000),
    "Mango": (2000, 6000),
    "Custard Apple": (3000, 8000),
}

DEFAULT_PRICE_RANGE = (2000, 5000)

COMMODITY_VARIETIES: dict[str, list[str]] = {
    "Onion": ["Nasik Red", "Bellary", "White", "Poona", "Local"],
    "Soybean": ["Yellow", "JS 335", "JS 9560", "Local"],
    "Cotton": ["H-4", "Shankar-6", "MCU-5", "Medium Staple", "Long Staple"],
    "Sugarcane": ["Co 86032", "CoC 671", "Co 0238", "Local"],
    "Jowar": ["Maldandi", "Hybrid", "Yellow", "White", "Local"],
    "Bajra": ["Hybrid", "Desi", "Bold", "Local"],
    "Wheat": ["Sharbati", "Lokwan", "MP Wheat", "Local"],
    "Gram": ["Desi", "Kabuli", "Bold", "Medium", "Local"],
    "Tur Dal": ["Bold", "Medium", "Local"],
    "Grapes": ["Thompson Seedless", "Sharad Seedless", "Flame", "Local"],
    "Pomegranate": ["Bhagwa", "Ganesh", "Arakta", "Local"],
    "Orange": ["Nagpur", "Kinnow", "Mosambi", "Local"],
}

DEFAULT_VARIETIES = ["Local", "Desi", "Hybrid", "FAQ"]
GRADES = ["FAQ", "Non-FAQ", "Average", "Superior", "Ordinary"]


# ─── Weather Ranges ──────────────────────────────────────────────────────────

WEATHER_CONDITIONS = [
    "Clear Sky", "Partly Cloudy", "Mostly Cloudy", "Overcast",
    "Light Rain", "Moderate Rain", "Heavy Rain", "Thunderstorm",
    "Haze", "Fog", "Mist", "Sunny",
]

WIND_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def random_temp(season: str = "summer") -> Tuple[float, float]:
    ranges = {
        "summer": (30, 45),
        "winter": (10, 28),
        "monsoon": (22, 35),
        "spring": (20, 38),
    }
    lo, hi = ranges.get(season, (22, 38))
    min_t = round(random.uniform(lo, lo + (hi - lo) * 0.4), 1)
    max_t = round(random.uniform(min_t + 3, hi), 1)
    return min_t, max_t


def random_humidity() -> int:
    return random.randint(30, 95)


def random_rainfall() -> float:
    if random.random() < 0.6:
        return 0.0
    return round(random.uniform(0.5, 100.0), 1)


def random_wind_speed() -> float:
    return round(random.uniform(5, 40), 1)


# ─── Maharashtra Farmer Crops ────────────────────────────────────────────────

FARMER_CROPS = [
    # Cereals & millets
    "Wheat", "Paddy", "Rice", "Jowar", "Bajra", "Maize", "Ragi",
    # Pulses
    "Gram", "Tur", "Green Gram", "Black Gram", "Lentil",
    "Cowpea", "Horse Gram",
    # Oilseeds
    "Soybean", "Groundnut", "Sunflower", "Sesamum", "Safflower", "Linseed",
    # Cash crops
    "Cotton", "Sugarcane",
    # Spices
    "Chili", "Turmeric", "Ginger", "Garlic", "Coriander",
    # Vegetables
    "Onion", "Potato", "Tomato", "Brinjal", "Cauliflower",
    "Capsicum", "Bitter Gourd", "Ladies Finger", "Spinach",
    "Cucumber", "Cabbage", "Drumstick", "Fenugreek Leaves",
    # Fruits
    "Banana", "Mango", "Orange", "Pomegranate", "Grapes",
    "Guava", "Papaya", "Custard Apple", "Watermelon",
    "Chikoo", "Fig", "Lemon",
]


# ─── Mood & Language Weights ─────────────────────────────────────────────────

MOOD_WEIGHTS = {
    "normal": 0.75,
    "frustrated": 0.23,
    "adversarial": 0.02,
}

# MH-OAN only supports Marathi and English
LANGUAGE_WEIGHTS = {
    "mr": 0.80,
    "en": 0.20,
}

TARGET_LANGUAGE_WEIGHTS = {
    "mr": 0.80,
    "en": 0.20,
}

LATIN_SCRIPT_PROBABILITY = 0.10  # Higher for MH — many farmers type Marathi in Roman
SAME_LANGUAGE_PROBABILITY = 0.95
LANGUAGE_SWITCH_PROBABILITY = 0.02


# ─── Agristack / Farmer Profile Data ────────────────────────────────────────

GENDERS = ["Male", "Female"]
GENDER_WEIGHTS = [0.70, 0.30]

CASTE_CATEGORIES = ["General", "OBC", "SC", "ST", "NT", "SBC", "VJNT"]
CASTE_WEIGHTS = [0.15, 0.35, 0.15, 0.10, 0.10, 0.08, 0.07]


# ─── MahaDBT Status Data ────────────────────────────────────────────────────

MAHADBT_STATUSES = [
    "Fund Disbursed",
    "Winner",
    "Wait List",
    "Application cancelled by applicant",
    "Department Cancelled",
    "Approved",
    "Rejected",
    "Under Review",
    "Pending",
    "Upload Documents",
    "Document scrutiny before pre-sanction",
    "Application Approved and Sanction letter generated",
]

MAHADBT_FINANCIAL_YEARS = ["2324", "2425", "2526"]


# ─── Agricultural Services Data ──────────────────────────────────────────────

KVK_NAMES = [
    "Krishi Vigyan Kendra, Baramati", "Krishi Vigyan Kendra, Rahuri",
    "Krishi Vigyan Kendra, Niphad", "Krishi Vigyan Kendra, Latur",
    "Krishi Vigyan Kendra, Amravati", "Krishi Vigyan Kendra, Nagpur",
    "Krishi Vigyan Kendra, Kolhapur", "Krishi Vigyan Kendra, Aurangabad",
    "Krishi Vigyan Kendra, Parbhani", "Krishi Vigyan Kendra, Akola",
]

CHC_NAMES = [
    "Custom Hiring Centre, Baramati", "Custom Hiring Centre, Karad",
    "Custom Hiring Centre, Latur", "Custom Hiring Centre, Nashik",
    "Custom Hiring Centre, Nagpur", "Custom Hiring Centre, Jalgaon",
]

SOIL_LAB_NAMES = [
    "Soil Testing Laboratory, Pune", "Soil Testing Laboratory, Nashik",
    "Soil Testing Laboratory, Aurangabad", "Soil Testing Laboratory, Nagpur",
    "Soil Testing Laboratory, Kolhapur", "Soil Testing Laboratory, Amravati",
]

WAREHOUSE_NAMES = [
    "CWC Warehouse, Pune", "State Warehouse, Nashik",
    "State Warehouse, Solapur", "CWC Warehouse, Nagpur",
    "State Warehouse, Latur", "CWC Warehouse, Aurangabad",
]


# ─── Officer / Staff Contact Data ────────────────────────────────────────────

OFFICER_NAMES = [
    "Shri. Patil R.M.", "Shri. Jadhav S.B.", "Shri. Deshmukh P.K.",
    "Shri. More A.R.", "Smt. Kulkarni V.S.", "Shri. Gaikwad D.N.",
    "Shri. Pawar M.B.", "Smt. Shinde T.R.", "Shri. Chavan K.L.",
    "Shri. Nikam H.J.", "Smt. Bhosale S.M.", "Shri. Kale R.G.",
]

OFFICER_ROLES = [
    "Krushi Sahayak (Agricultural Assistant)",
    "Taluka Krushi Adhikari (Taluka Agriculture Officer)",
    "Mandal Krushi Adhikari (Circle Agriculture Officer)",
]


# ─── Scenario Definitions ───────────────────────────────────────────────────

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def load_scenarios(path: Path | None = None) -> list[dict]:
    path = path or _ASSETS_DIR / "scenarios.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


SCENARIOS: list[dict] = load_scenarios()

ADVERSARIAL_SCENARIO_IDS = {s["id"] for s in SCENARIOS if s["id"].startswith("adversarial_")}


# ─── Scheme Fixtures ─────────────────────────────────────────────────────────

def load_scheme_list() -> list[dict]:
    path = _ASSETS_DIR / "scheme_list.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


SCHEME_LIST: list[dict] = load_scheme_list()

# Sample schemes for mock tool responses
SAMPLE_STATE_SCHEMES = [
    "mahadbt-baksy", "ndksp-drip-irrigation", "ndksp-goat-rearing",
    "sdda-farm-machinery-and-equipments", "ndksp-sprinkler-irrigation",
    "ndksp-horticulture-plantation", "ndksp-individual-farm-ponds",
]

SAMPLE_CENTRAL_SCHEMES = [
    "mahadbt-pmkisan", "mahadbt-pmfby", "mahadbt-aif",
    "mahadbt-pmrkvysmam", "mahadbt-kymidh", "cdda-namo-drone-didi",
]
