"""Tools for the MH-OAN synthetic conversation generation.

Uses real implementations for: search_documents, search_videos, geocoding, search_terms, scheme_codes.
Uses mock implementations for: weather, mandi, agri_services, agristack, mahadbt, scheme_info, staff_contact.
"""
from pydantic_ai import Tool
from synthetic.tools.common import reasoning_tool, planning_tool
from synthetic.tools.search import search_documents, search_videos       # Real (Marqo)
from synthetic.tools.maps import reverse_geocode, forward_geocode        # Real (Mapbox)
from synthetic.tools.weather import weather_forecast, weather_historical  # Mock
from synthetic.tools.mandi import mandi_prices                           # Mock
from synthetic.tools.agri_services import agri_services                  # Mock
from synthetic.tools.agristack import fetch_agristack_data               # Mock
from synthetic.tools.mahadbt import get_scheme_status                    # Mock
from synthetic.tools.terms import search_terms                           # Real (glossary)
from synthetic.tools.scheme_info import get_scheme_codes, get_scheme_info # Real codes, fixture info
from synthetic.tools.staff_contact import contact_agricultural_staff     # Mock

TOOLS = [
    # Search Terms (real glossary)
    Tool(search_terms, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Search Documents (real — Marqo)
    Tool(search_documents, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Search Videos (real — Marqo)
    Tool(search_videos, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Reverse Geocode (real — Mapbox)
    Tool(reverse_geocode, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Weather Forecast (mock)
    Tool(weather_forecast, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Weather Historical (mock)
    Tool(weather_historical, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Mandi Prices (mock)
    Tool(mandi_prices, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Agricultural Services (mock)
    Tool(agri_services, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Forward Geocode (real — Mapbox)
    Tool(forward_geocode, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Agristack (mock, uses context)
    Tool(fetch_agristack_data, takes_ctx=True, docstring_format='auto', require_parameter_descriptions=False),

    # Scheme Codes (real scheme_list.json)
    Tool(get_scheme_codes, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=False),

    # Scheme Info (fixture data)
    Tool(get_scheme_info, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # MahaDBT (mock, uses context)
    Tool(get_scheme_status, takes_ctx=True, docstring_format='auto', require_parameter_descriptions=False),

    # Agricultural Staff Contact (mock)
    Tool(contact_agricultural_staff, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),
]
