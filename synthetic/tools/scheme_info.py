"""Scheme info tools for Maharashtra — reads from scheme_fixtures.json."""

import json
from synthetic.mock_data import SCHEME_LIST, should_fail

# Load scheme list for validation and categorization from JSON
_scheme_codes_set = {s["scheme_code"] for s in SCHEME_LIST}
STATE_SCHEMES = {s["scheme_code"] for s in SCHEME_LIST if s.get("type") == "state"}
CENTRAL_SCHEMES = {s["scheme_code"] for s in SCHEME_LIST if s.get("type") == "central"}

# Load real scheme fixture data (keyed by scheme_code -> formatted info string)
with open("assets/scheme_fixtures.json", "r", encoding="utf-8") as _f:
    SCHEME_FIXTURES: dict[str, str] = json.load(_f)


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

    if scheme_code in SCHEME_FIXTURES:
        return SCHEME_FIXTURES[scheme_code]

    # Fallback if fixture data missing for this code
    scheme_name = next(
        (s["scheme_name"] for s in SCHEME_LIST if s["scheme_code"] == scheme_code),
        scheme_code,
    )
    return f"*Scheme Name*:\n{scheme_name}\n\nDetailed scheme information is currently unavailable."


