import os
import uuid
import json
from datetime import datetime, timezone
from helpers.utils import get_logger
import httpx
from pydantic import BaseModel, AnyHttpUrl, Field
from typing import List, Optional, Dict, Any
from pydantic_ai import ModelRetry, UnexpectedModelBehavior

logger = get_logger(__name__)

# -----------------------
# Basic Models
# -----------------------
class Image(BaseModel):
    url: AnyHttpUrl

class Descriptor(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    short_desc: Optional[str] = None
    long_desc: Optional[str] = None
    images: Optional[List[Image]] = None

    def __str__(self) -> str:
        return self.long_desc or self.short_desc or self.name or self.code or ""

class Country(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None

class Location(BaseModel):
    country: Optional[Country] = None
    
    class Config:
        extra = "allow"  # Allow extra fields in the response

# -----------------------
# Request Models
# -----------------------
class IntentDescriptor(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None

class IntentCategory(BaseModel):
    descriptor: IntentDescriptor

class IntentItem(BaseModel):
    descriptor: IntentDescriptor

class Intent(BaseModel):
    category: IntentCategory
    item: IntentItem

class RequestMessage(BaseModel):
    intent: Intent

# -----------------------
# Tag Models
# -----------------------
class TagItem(BaseModel):
    descriptor: Descriptor
    value: str
    display: bool = True

    def __str__(self) -> str:
        desc_name = self.descriptor.name or self.descriptor.code or "Tag"
        return f"{desc_name}: {self.value}"

    class Config:
        extra = "allow"  # Allow extra fields in the response

class Tag(BaseModel):
    display: bool = True
    descriptor: Descriptor
    list: List[TagItem]

    def __str__(self) -> str:
        items_str = "\n      ".join(str(tag_item) for tag_item in self.list)
        return items_str

    class Config:
        extra = "allow"  # Allow extra fields in the response

# -----------------------
# Item & Provider Models
# -----------------------
class Item(BaseModel):
    id: str
    descriptor: Descriptor
    tags: Optional[List[Tag]] = None

    def __str__(self) -> str:
        lines = []
        # Ignore tags that have no meaningful content
        if self.tags:
            for tag in self.tags:
                for tag_item in tag.list:
                    # Show all tag items that have meaningful content
                    if tag_item.value and tag_item.value.strip() and tag_item.descriptor.name and tag_item.value.strip().lower() != "null":
                        lines.append(f"*{tag_item.descriptor.name}*:\n{tag_item.value.strip()}")

        return "\n\n".join(lines).strip()

    class Config:
        extra = "allow"  # Allow extra fields in the response

class Provider(BaseModel):
    id: Optional[str] = None
    descriptor: Descriptor
    items: Optional[List[Item]] = None

    def __str__(self) -> str:
        lines = []
        if self.items:
            for item in self.items:
                lines.append(str(item))
        return "\n\n---\n\n".join(lines)

    class Config:
        extra = "allow"  # Allow extra fields in the response

# -----------------------
# Catalog & Message Models
# -----------------------
class Catalog(BaseModel):
    descriptor: Optional[Descriptor] = None
    providers: List[Provider]

    def __str__(self) -> str:
        lines = []
        if self.providers:
            for provider in self.providers:
                lines.append(str(provider))
        return "\n".join(lines)

    class Config:
        extra = "allow"  # Allow extra fields in the response

class Message(BaseModel):
    catalog: Catalog

    def __str__(self) -> str:
        return str(self.catalog)

    class Config:
        extra = "allow"  # Allow extra fields in the response

# -----------------------
# Context & Response Models
# -----------------------
class Context(BaseModel):
    ttl: Optional[str] = None
    action: str
    timestamp: str
    message_id: str
    transaction_id: str
    domain: str
    version: str
    bap_id: Optional[str] = None
    bap_uri: Optional[AnyHttpUrl] = None
    bpp_id: Optional[str] = None
    bpp_uri: Optional[AnyHttpUrl] = None
    country: Optional[str] = None
    city: Optional[str] = None
    location: Optional[Location] = None

    class Config:
        extra = "allow"  # Allow extra fields in the response

class ResponseItem(BaseModel):
    context: Context
    message: Message

    def __str__(self) -> str:
        return str(self.message)

class SchemeResponse(BaseModel):
    context: Context
    responses: List[ResponseItem]

    def _has_scheme_data(self) -> bool:
        """Check if there are any responses with providers that have items."""
        for response in self.responses:
            for provider in response.message.catalog.providers:
                if provider.items and len(provider.items) > 0:
                    return True
        return False
    
    def __str__(self) -> str:
        lines = []
        
        has_scheme_data = self._has_scheme_data()
        if not self.responses or not has_scheme_data:
            lines.append("No scheme data found.")
            return "\n".join(lines)
            
        for idx, rsp in enumerate(self.responses, start=1):
            lines.append(str(rsp))
        return "\n".join(lines)

    class Config:
        extra = "allow"  # Allow extra fields in the response

# -----------------------
# Request Model
# -----------------------
class SchemeRequest(BaseModel):
    """SchemeRequest model for the scheme API.
    
    Args:
        scheme_code (str): Code of the scheme to retrieve. Available scheme codes can be found by calling get_scheme_code().
    """
    context: Optional[Context] = None
    message: Optional[RequestMessage] = None
    scheme_code: str
    
    def get_payload(self) -> Dict[str, Any]:
        """
        Convert the SchemeRequest object to a dictionary.
        
        Returns:
            Dict[str, Any]: The dictionary representation of the SchemeRequest object
        """
        now = datetime.today()
        
        return {
            "context": {
                "domain": "advisory:mh-vistaar",
                "location": {
                    "country": {
                        "name": "IND"
                    }
                },
                "action": "search",
                "version": "1.1.0",
                "bap_id": os.getenv("BAP_ID"),
                "bap_uri": os.getenv("BAP_URI"),
                "bpp_id": os.getenv("POCRA_BPP_ID"),
                "bpp_uri": os.getenv("POCRA_BPP_URI"),
                "message_id": str(uuid.uuid4()),
                "transaction_id": str(uuid.uuid4()),
                "timestamp": now.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            },
            "message": {
                "intent": {
                    "category": {
                        "descriptor": {
                            "code": "schemes-agri"
                        }
                    },
                    "item": {
                        "descriptor": {
                            "code": self.scheme_code
                        }
                    }
                }
            }
        }


# Scheme categorization constants
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
    'nfsnm-crop-demonstration', 'nfsnm-seed-production', 'nfsnm-seed-distribution', 'nfsnm-inm-ipm'
}

CENTRAL_SCHEMES = {
    'mahadbt-rwbcis', 'mahadbt-nsmnyy', 'mahadbt-pmfby', 'mahadbt-aif', 'mahadbt-kymidh', 'mahadbt-pmkisan', 'mahadbt-pmkmy',
    'mahadbt-pmrkvysmam', 'mahadbt-pmkrvypdmc', 'mahadbt-mgnregs',
    'pmfmfpe-individual-new', 'pmfmfpe-individual-old-more-than-1cr', 'pmfmfpe-individual-old-less-than-1cr',
    'pmfmfpe-group-fpo-fpc', 'pmfmfpe-group-shg', 'pmfmfpe-group-cs',
    'pmfmfpe-common-infra-fpo-fpc', 'pmfmfpe-common-infra-shg', 'pmfmfpe-common-infra-cs',
    'pmfmfpe-common-infra-govt', 'pmfmfpe-seed-capital', 'pmfmfpe-marketing-branding', 'pmfmfpe-training',
    'cdda-farm-machinery-and-equipments', 'cdda-chc', 'cdda-namo-drone-didi',
    'mahadbt-midh-water-resources', 'mahadbt-midh-pc-shadenet-house',
    'mahadbt-midh-pc-plastic-mulching', 'mahadbt-midh-pc-weed-mat', 'mahadbt-midh-pc-fruit-cover-skirting-bag',
    'mahadbt-midh-pc-hydroponics-technology', 'mahadbt-midh-area-expansion-fruit-flower',
    'mahadbt-midh-rejuvenation', 'mahadbt-midh-area-expansion-mushroom-cultivation',
    'mahadbt-midh-pollinatation', 'mahadbt-midh-planting-material', 'mahadbt-midh-pack-house',
    'mahadbt-midh-collection-centre', 'mahadbt-midh-cold-room-solar-power-room',
    'mahadbt-midh-cs-1', 'mahadbt-midh-cs-1-onion', 'mahadbt-midh-cs-2', 'mahadbt-midh-cs-2-ca',
    'mahadbt-midh-cs-4', 'mahadbt-midh-refrigerated-transport-vehicles', 'mahadbt-midh-cs-3',
    'mahadbt-midh-integrated-cold-chectarein-project', 'mahadbt-post-harvest-management-farm-gate-packhouse',
    'mahadbt-post-harvest-management-low-cost-onion-garlic-storage', 'mahadbt-midh-tractor-2-wd',
    'mahadbt-midh-tractor-4-wd', 'mahadbt-midh-power-tiller-below-8-bhp',
    'mahadbt-midh-power-tiller-above-8-bhp', 'mahadbt-midh-manual-prated-machinery',
    'mahadbt-midh-manual-prated-machinery-above-8-12-lts', 'mahadbt-midh-manual-prated-machinery-above-12-16-lts',
    'mahadbt-midh-manual-prated-machinery-above-16-lts', 'mahadbt-midh-tractor-operated-sprayer-boom-type',
    'mahadbt-midh-operated-sprayer-air-carrier-assisted', 'mahadbt-midh-Tractor-oprated-electrostatics-sprayer',
    'mahadbt-midh-medicinal-plant', 'mahadbt-midh-cost-intensive-aromatic-plants',
    'mahadbt-midh-other-aromatic-plants', 'mahadbt-midh-creation-of-water-resources'
}

def _validate_scheme_code(scheme_code: str) -> bool:
    """Validate the scheme code.
    
    Args:
        scheme_code (str): The scheme code to validate.
        
    Returns:
        bool: True if the scheme code is valid, False otherwise.
    """
    with open('assets/scheme_list.json', 'r') as f:
        scheme_list = json.load(f)
    return any(scheme['scheme_code'] == scheme_code for scheme in scheme_list)


async def get_scheme_type(scheme_code: str) -> str:
    """Get the type of a scheme (state or central).
    
    Args:
        scheme_code (str): The scheme code to check.
        
    Returns:
        str: "state" if it's a Maharashtra state scheme, "central" if it's a central scheme, "unknown" if invalid.
    """
    if scheme_code in STATE_SCHEMES:
        return "state"
    elif scheme_code in CENTRAL_SCHEMES:
        return "central"
    else:
        return "unknown"

async def get_scheme_codes() -> str:
    """Returns a prioritized list of scheme names and codes with state schemes first.
    
    Returns:
        str: A markdown-formatted table with scheme names and codes, prioritizing state schemes.
    """
    with open('assets/scheme_list.json', 'r') as f:
        scheme_list = json.load(f)
    
    # Create a lookup dictionary for scheme data
    scheme_lookup = {scheme['scheme_code']: scheme for scheme in scheme_list}
    
    # Build prioritized lists
    state_schemes = []
    central_schemes = []
    
    for scheme_code in STATE_SCHEMES:
        if scheme_code in scheme_lookup:
            state_schemes.append(scheme_lookup[scheme_code])
    
    for scheme_code in CENTRAL_SCHEMES:
        if scheme_code in scheme_lookup:
            central_schemes.append(scheme_lookup[scheme_code])
    
    # Build markdown table with state schemes first
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
    
    This tool fetches comprehensive scheme data including benefits, eligibility criteria, application process, and other relevant details for agricultural schemes. 

    Available scheme codes can be found by calling `get_scheme_codes()` which returns a markdown table with scheme names and codes.

    Args:
        scheme_code (str): Code of the scheme to retrieve (e.g., 'mahadbt-pmkisan', 'mahadbt-pmfby').

    Returns:
        str: Formatted scheme data including introduction, benefits, eligibility, application process, and other relevant information.
    """
    try:
        # Check if the scheme code is valid
        if not _validate_scheme_code(scheme_code):
            raise ModelRetry(f"Invalid scheme code: {scheme_code}. Available scheme codes can be found by calling `get_scheme_codes()` which returns a markdown table with scheme names and codes.")
        
        payload = SchemeRequest(scheme_code=scheme_code).get_payload()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                os.getenv("BAP_ENDPOINT"),
                json=payload,
                timeout=15.0
            )
        
        if response.status_code != 200:
            logger.error(f"Scheme API returned status code {response.status_code}")
            return "Scheme service unavailable. Retrying"
            
        scheme_response = SchemeResponse.model_validate(response.json())
        # Sponsor field is already in the response text (e.g., "Sponsor: State" or "Sponsor: Central")
        # Agent can read this directly from the response to determine prioritization
        return str(scheme_response)
                
    except httpx.TimeoutException as e:
        logger.error(f"Scheme API request timed out: {str(e)}")
        return "Scheme request timed out. Please try again later."
    
    except httpx.RequestError as e:
        logger.error(f"Scheme API request failed: {e}")
        return f"Scheme request failed: {str(e)}"
    
    except UnexpectedModelBehavior as e:
        logger.warning("Scheme request exceeded retry limit")
        return "Scheme data is temporarily unavailable. Please try again later."
    except Exception as e:
        logger.error(f"Error getting scheme data: {e}")
        raise ModelRetry(f"Unexpected error in scheme request. {str(e)}") 


async def get_multiple_schemes_info(scheme_codes: List[str]) -> str:
    """Retrieve detailed information about multiple government agricultural schemes with automatic prioritization.
    
    This tool fetches comprehensive scheme data for multiple schemes at once and automatically returns them 
    in the correct order: Maharashtra state schemes FIRST, then central schemes SECOND.
    
    Args:
        scheme_codes (List[str]): List of scheme codes to retrieve (e.g., ['state scheme code', 'central scheme code', 'central scheme code']).

    Returns:
        str: Formatted scheme data with state schemes first, then central schemes, including benefits, 
             eligibility, application process, and other relevant information for each scheme.
    """
    try:
        if not scheme_codes or len(scheme_codes) == 0:
            return "No scheme codes provided. Please provide at least one scheme code."
        
        # Validate all scheme codes first
        invalid_codes = [code for code in scheme_codes if not _validate_scheme_code(code)]
        if invalid_codes:
            raise ModelRetry(f"Invalid scheme codes: {', '.join(invalid_codes)}. Available scheme codes can be found by calling `get_scheme_codes()`.")
        
        # Categorize schemes into state and central
        state_schemes = []
        central_schemes = []
        
        for code in scheme_codes:
            scheme_type = await get_scheme_type(code)
            if scheme_type == "state":
                state_schemes.append(code)
            elif scheme_type == "central":
                central_schemes.append(code)
        
        # Build ordered list: state schemes first, then central schemes
        ordered_schemes = state_schemes + central_schemes
        
        # Fetch information for each scheme in order
        results = []
        for idx, code in enumerate(ordered_schemes, start=1):
            scheme_info = await get_scheme_info(code)
            # Add a numbered header for each scheme
            results.append(f"## {idx}. Scheme Information\n\n{scheme_info}")
        
        if not results:
            return "No valid schemes found."
        
        # Combine all results with clear separators
        combined_results = "\n\n---\n\n".join(results)
        
        # Add a summary header
        summary = f"**Total schemes: {len(ordered_schemes)}** (State schemes: {len(state_schemes)}, Central schemes: {len(central_schemes)})\n\n"
        
        return summary + combined_results
                
    except Exception as e:
        logger.error(f"Error getting multiple schemes data: {e}")
        raise ModelRetry(f"Unexpected error in multiple schemes request. {str(e)}")

