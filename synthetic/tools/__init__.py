"""Mock tools for the MH-OAN synthetic conversation generation."""
from pydantic_ai import Tool
from agents.tools.common import reasoning_tool, planning_tool
from synthetic.tools.search import search_documents, search_videos
from synthetic.tools.weather import weather_forecast, weather_historical
from synthetic.tools.mandi import mandi_prices
from synthetic.tools.agri_services import agri_services
from synthetic.tools.maps import reverse_geocode, forward_geocode
from synthetic.tools.agristack import fetch_agristack_data
from synthetic.tools.mahadbt import get_scheme_status
from synthetic.tools.terms import search_terms
from synthetic.tools.scheme_info import get_scheme_codes, get_scheme_info, get_multiple_schemes_info
from synthetic.tools.staff_contact import contact_agricultural_staff

TOOLS = [
    # Search Terms (uses real glossary)
    Tool(search_terms, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Search Documents (mock)
    Tool(search_documents, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Search Videos (mock)
    Tool(search_videos, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Reverse Geocode (mock)
    Tool(reverse_geocode, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Weather Forecast (mock)
    Tool(weather_forecast, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Weather Historical (mock)
    Tool(weather_historical, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Mandi Prices (mock)
    Tool(mandi_prices, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Agricultural Services (mock)
    Tool(agri_services, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Forward Geocode (mock)
    Tool(forward_geocode, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Agristack (mock, uses context)
    Tool(fetch_agristack_data, takes_ctx=True, docstring_format='auto', require_parameter_descriptions=False),

    # Scheme Codes (uses real scheme_list.json)
    Tool(get_scheme_codes, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=False),

    # Scheme Info (mock)
    Tool(get_scheme_info, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # Multiple Schemes Info (mock)
    Tool(get_multiple_schemes_info, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),

    # MahaDBT (mock, uses context)
    Tool(get_scheme_status, takes_ctx=True, docstring_format='auto', require_parameter_descriptions=False),

    # Agricultural Staff Contact (mock)
    Tool(contact_agricultural_staff, takes_ctx=False, docstring_format='auto', require_parameter_descriptions=True),
]
