"""Mock scheme info tools for Maharashtra."""

import json
import random
from typing import List
from pathlib import Path
from synthetic.mock_data import SCHEME_LIST, should_fail

# Load scheme list for validation
_scheme_codes_set = {s["scheme_code"] for s in SCHEME_LIST}

# Categorization from the real tool
STATE_SCHEMES = {
    'mahadbt-bmkky', 'mahadbt-gmsassay', 'mahadbt-cmsaisfp', 'mahadbt-baksy', 'mahadbt-bfhps',
    'ndksp-sericulture-unit', 'ndksp-agroforestry-tree', 'ndksp-agroforestry-bamboo',
    'ndksp-horticulture-plantation', 'ndksp-flower-crop-planting-material-polyhouse',
    'ndksp-drip-irrigation', 'ndksp-inland-fishery', 'ndksp-goat-rearing',
    'ndksp-sprinkler-irrigation', 'ndksp-organic-production-unit', 'ndksp-pump-set',
    'ndksp-pipes', 'ndksp-well-recharge', 'ndksp-individual-farm-ponds',
    'ndksp-farm-pond-lining', 'ndksp-vegetable-planting-material-in-shednet-and-polyhouse',
    'ndksp-seed-production', 'sdda-farm-machinery-and-equipments', 'sdda-chc',
    'state-agri-award', 'state-crop-competition', 'state-farmer-international-tour',
    'mahadbt-rkvy-plastic-cover-for-grape', 'mahadbt-rkvy-anti-hectareil-net-with-ms-angle-structure',
    'mahadbt-midh-green-house-poly-house', 'pmrkvy-rad',
    'mahadbt-nmeo-oilseeds', 'mahadbt-nfsnm-cotton-development', 'mahadbt-nfsnm-sugarcane-development',
    'nfsnm-crop-demonstration', 'nfsnm-seed-production', 'nfsnm-seed-distribution', 'nfsnm-inm-ipm',
}

CENTRAL_SCHEMES = {
    'mahadbt-rwbcis', 'mahadbt-nsmnyy', 'mahadbt-pmfby', 'mahadbt-aif', 'mahadbt-kymidh',
    'mahadbt-pmkisan', 'mahadbt-pmkmy', 'mahadbt-pmrkvysmam', 'mahadbt-pmkrvypdmc', 'mahadbt-mgnregs',
    'cdda-farm-machinery-and-equipments', 'cdda-chc', 'cdda-namo-drone-didi',
}


async def get_scheme_codes() -> str:
    """Returns a prioritized list of scheme names and codes with state schemes first.

    Returns:
        str: A markdown-formatted table with scheme names and codes.
    """
    scheme_lookup = {s['scheme_code']: s for s in SCHEME_LIST}

    state_schemes = [scheme_lookup[c] for c in STATE_SCHEMES if c in scheme_lookup]
    central_schemes = [scheme_lookup[c] for c in CENTRAL_SCHEMES if c in scheme_lookup]

    markdown_table = "## State Schemes (Maharashtra)\n\n"
    markdown_table += "| Scheme Name | Scheme Code |\n|-------------|-------------|\n"
    for scheme in state_schemes:
        markdown_table += f"| {scheme['scheme_name']} | {scheme['scheme_code']} |\n"

    markdown_table += "\n## Central Schemes\n\n"
    markdown_table += "| Scheme Name | Scheme Code |\n|-------------|-------------|\n"
    for scheme in central_schemes:
        markdown_table += f"| {scheme['scheme_name']} | {scheme['scheme_code']} |\n"

    return markdown_table


async def get_scheme_info(scheme_code: str) -> str:
    """Retrieve detailed information about government agricultural schemes.

    Args:
        scheme_code (str): Code of the scheme to retrieve.

    Returns:
        str: Formatted scheme data.
    """
    if should_fail():
        return "Scheme service unavailable. Retrying"

    if scheme_code not in _scheme_codes_set:
        return f"Invalid scheme code: {scheme_code}. Use get_scheme_codes() to find valid codes."

    # Find scheme name
    scheme_name = next(
        (s["scheme_name"] for s in SCHEME_LIST if s["scheme_code"] == scheme_code),
        scheme_code,
    )

    sponsor = "State" if scheme_code in STATE_SCHEMES else "Central"

    # Generate realistic mock scheme info
    lines = [
        f"*Scheme Name*:\n{scheme_name}",
        "",
        f"*Sponsor*:\n{sponsor}",
        "",
        f"*Introduction*:\n{scheme_name} is a {'Maharashtra state' if sponsor == 'State' else 'Central Government'} initiative "
        f"to support farmers in Maharashtra. The scheme provides financial assistance and subsidies "
        f"to eligible farmers for agricultural development.",
        "",
        "*Eligibility*:\n- Must be a resident of Maharashtra\n- Must have valid land records\n"
        "- Must be registered on MahaDBT portal\n- Aadhaar linked bank account required",
        "",
        "*Benefits*:\n- Financial assistance for farming activities\n"
        "- Subsidy on equipment and inputs\n- Support for crop production",
        "",
        "*Application Process*:\n1. Register on MahaDBT portal (mahadbt.maharashtra.gov.in)\n"
        "2. Select the scheme and fill application\n3. Upload required documents\n"
        "4. Submit application and track status",
        "",
        "*Required Documents*:\n- 7/12 Extract (Saat-Baara Utara)\n- 8-A Extract\n"
        "- Aadhaar Card\n- Bank Passbook\n- Caste Certificate (if applicable)",
    ]

    return "\n\n".join(lines)


async def get_multiple_schemes_info(scheme_codes: List[str]) -> str:
    """Retrieve detailed information about multiple government agricultural schemes with automatic prioritization.

    Args:
        scheme_codes (List[str]): List of scheme codes to retrieve.

    Returns:
        str: Formatted scheme data with state schemes first.
    """
    if not scheme_codes:
        return "No scheme codes provided."

    # Categorize
    state = [c for c in scheme_codes if c in STATE_SCHEMES]
    central = [c for c in scheme_codes if c in CENTRAL_SCHEMES]
    ordered = state + central

    results = []
    for idx, code in enumerate(ordered, start=1):
        info = await get_scheme_info(code)
        results.append(f"## {idx}. Scheme Information\n\n{info}")

    summary = f"**Total schemes: {len(ordered)}** (State schemes: {len(state)}, Central schemes: {len(central)})\n\n"
    return summary + "\n\n---\n\n".join(results)
