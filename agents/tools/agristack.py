import os
import uuid
from datetime import datetime
from helpers.utils import get_logger
import requests
from pydantic import BaseModel, AnyHttpUrl, Field
from typing import List, Optional, Dict, Any, ClassVar
from pydantic_ai import ModelRetry, UnexpectedModelBehavior, RunContext
from agents.deps import FarmerContext
from agents.tools.maps import Location
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

# -----------------------
# Basic Models
# -----------------------
class Descriptor(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    short_desc: Optional[str] = None
    long_desc: Optional[str] = None

    def __str__(self) -> str:
        if self.name:
            return self.name
        elif self.code:
            return self.code
        return ""

# -----------------------
# Tag Models
# -----------------------
class Tag(BaseModel):
    code: str
    value: str

    def __str__(self) -> str:
        return f"{self.code}: {self.value}"

# -----------------------
# Item & Provider Models
# -----------------------
class Item(BaseModel):
    """Item model representing farmer information with PII masking capabilities.

    PII Masking Examples (Unified Pattern):
    - Short values (≤2 chars): "AB" → "***"
    - Medium values (3-4 chars): "Test" → "T***"
    - Longer values (5+ chars): "7350994908" → "73***8", "farmer@example.com" → "fa***m"

    Usage:
        # With PII masking (default)
        farmer_info = str(item)

        # Without PII masking
        farmer_info = item.__str__(mask_pii=False)

        # Manage PII codes
        Item.add_pii_code("new_sensitive_field")
        Item.remove_pii_code("dob")  # If DOB should not be masked
    """

    id: str
    descriptor: Descriptor
    tags: List[Tag]

    # Class-level PII codes that should be masked
    PII_CODES: ClassVar[set[str]] = {
        "mobile",
        "email",
        "farmer_name_mr",
        "identifier_name", 
        "dob",
        "phone",
        "contact_number",
        "aadhar",
        "aadhar_number",
        "pan",
        "pan_number",
        "voter_id",
        "driving_license",
    }

    @classmethod
    def add_pii_code(cls, code: str) -> None:
        """Add a new code to the PII codes list.

        Args:
            code: The tag code to be masked as PII
        """
        cls.PII_CODES.add(code)

    @classmethod
    def remove_pii_code(cls, code: str) -> None:
        """Remove a code from the PII codes list.

        Args:
            code: The tag code to remove from PII masking
        """
        cls.PII_CODES.discard(code)

    @classmethod
    def get_pii_codes(cls) -> set[str]:
        """Get a copy of the current PII codes.

        Returns:
            A set of PII codes that are currently being masked
        """
        return cls.PII_CODES.copy()

    def _get_tag_value(self, code: str) -> Optional[str]:
        """Get value for a specific tag code."""
        for tag in self.tags:
            if tag.code == code:
                if tag.value == "null":
                    return None
                elif tag.value in ["true", "1"]:
                    return "Yes"
                elif tag.value in ["false", "0"]:
                    return "No"
                else:
                    return tag.value
        return None

    def _format_tag_code(self, code: str) -> str:
        """Convert tag code to human-readable label."""
        # Special mappings for specific codes that need custom labels
        special_mappings = {
            "farmer_name_mr": "Name",
            "identifier_name": "Identifier Name",
            "dob": "Date of Birth",
            "caste_category": "Caste Category",
            "total_plot_area": "Total Plot Area",
            "village_lgd_code": "Village LGD Code",
            "district_lgd_code": "District LGD Code",
            "sub_district_lgd_code": "Sub-District LGD Code",
            "is_pocra": "Is PoCRA village?",
        }

        if code in special_mappings:
            return special_mappings[code]

        # Generic conversion: split by underscore, capitalize each word
        return " ".join(word.capitalize() for word in code.split("_"))

    def _format_tag_value(self, code: str, value: str, mask_pii: bool = True) -> str:
        """Format tag value based on the code."""

        # Mask PII values if masking is enabled
        if mask_pii and code in self.PII_CODES:
            return self._mask_pii_value(value)

        # Special formatting for non-PII codes
        if code == "total_plot_area":
            return f"{value} hectares"

        return value

    def _mask_pii_value(self, value: str) -> str:
        """Apply unified PII masking to any sensitive value."""
        if not value or value == "null":
            return "***"

        # Remove whitespace for processing
        clean_value = value.strip()

        # For very short values, completely mask
        if len(clean_value) <= 2:
            return "***"

        # For values with 3-4 characters, show first and mask rest
        elif len(clean_value) <= 4:
            return f"{clean_value[0]}***"

        # For longer values, show first 2 and last 1 characters
        else:
            return f"{clean_value[:2]}***{clean_value[-1]}"

    def __str__(self, mask_pii: bool = True) -> str:
        lines = []

        # Handle name specially - try farmer_name_mr first, then descriptor.name
        name = self._get_tag_value("farmer_name_mr") or self.descriptor.name
        if name:
            if mask_pii and "farmer_name_mr" in [tag.code for tag in self.tags]:
                # Apply masking to farmer_name_mr if it exists in tags
                name = self._format_tag_value("farmer_name_mr", name, mask_pii)
            lines.append(f"Name: {name}")

        # Priority order for displaying other information
        priority_codes = [
            "mobile",
            "email",
            "dob",
            "gender",
            "caste_category",
            "village_name",
            "is_pocra",
            "taluka_name",
            "district_name",
            "sub_district_lgd_code",
            "district_lgd_code",
            "village_lgd_code",
            "total_plot_area",
        ]

        # Process priority codes in order
        processed_codes = {"farmer_name_mr"}  # Already handled name
        for code in priority_codes:
            value = self._get_tag_value(code)
            if value:
                label = self._format_tag_code(code)
                formatted_value = self._format_tag_value(code, value, mask_pii)
                lines.append(f"{label}: {formatted_value}")
                processed_codes.add(code)

        # Then process any remaining tags that weren't in the priority list
        for tag in self.tags:
            if tag.code not in processed_codes and tag.value and tag.value != "null":
                label = self._format_tag_code(tag.code)
                formatted_value = self._format_tag_value(tag.code, tag.value, mask_pii)
                lines.append(f"{label}: {formatted_value}")

        return "\n".join(lines) if lines else "No farmer information available"

class Provider(BaseModel):
    id: str
    descriptor: Descriptor
    items: List[Item]
    locations: Optional[List[Dict[str, Any]]] = None

    def _parse_locations(self) -> List[Location]:
        """Parse raw location dictionaries into Location objects."""
        parsed_locations = []
        if self.locations:
            for loc_dict in self.locations:
                gps_str = loc_dict.get("gps")
                if gps_str:
                    try:
                        # GPS format: "latitude,longitude"
                        lat_str, lon_str = gps_str.split(",")
                        latitude = float(lat_str.strip())
                        longitude = float(lon_str.strip())

                        location = Location(latitude=latitude, longitude=longitude)
                        parsed_locations.append(location)
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Failed to parse GPS coordinates '{gps_str}': {e}")
                        continue
        return parsed_locations

    def __str__(self, mask_pii: bool = True) -> str:
        lines = []
        lines.append(f"Provider: {self.descriptor.name}")

        if self.items:
            lines.append("  Farmer Details:")
            for item in self.items:
                item_str = item.__str__(mask_pii=mask_pii).replace("\n", "\n    ")
                lines.append(f"    {item_str}")

        parsed_locations = self._parse_locations()
        if parsed_locations:
            lines.append("  Locations:")
            for location in parsed_locations:
                lines.append(f"    {location}")

        return "\n".join(lines)

# -----------------------
# Catalog & Message Models
# -----------------------
class Catalog(BaseModel):
    descriptor: Optional[Descriptor] = None
    providers: List[Provider]

    def __str__(self, mask_pii: bool = True) -> str:
        lines = []
        if self.providers:
            for provider in self.providers:
                provider_str = provider.__str__(mask_pii=mask_pii).replace("\n", "\n  ")
                lines.append(f"  {provider_str}")
        return "\n".join(lines)

class Message(BaseModel):
    catalog: Catalog

    def __str__(self, mask_pii: bool = True) -> str:
        return self.catalog.__str__(mask_pii=mask_pii)

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
    location: Optional[Dict[str, Any]] = None

class ResponseItem(BaseModel):
    context: Context
    message: Message

    def __str__(self, mask_pii: bool = True) -> str:
        return self.message.__str__(mask_pii=mask_pii)

class AgristackResponse(BaseModel):
    context: Context
    responses: List[ResponseItem]

    def _has_farmer_data(self) -> bool:
        """Check if there are any responses with farmer information."""
        for response in self.responses:
            for provider in response.message.catalog.providers:
                if provider.items and len(provider.items) > 0:
                    return True
        return False

    def __str__(self, mask_pii: bool = True) -> str:
        lines = []
        lines.append("> Farmer Information (Agristack)")

        has_farmer_data = self._has_farmer_data()
        if not self.responses or not has_farmer_data:
            lines.append("No farmer information found for the requested ID.")
            return "\n".join(lines)

        lines.append("Responses:")
        for idx, rsp in enumerate(self.responses, start=1):
            rsp_str = rsp.__str__(mask_pii=mask_pii).replace("\n", "\n  ")
            lines.append(f"    {rsp_str}")
        return "\n".join(lines)

# -----------------------
# Request Model
# -----------------------
class AgristackRequest(BaseModel):
    """Agristack Request model for the Agristack API.

    Args:
        farmer_id (str): The ID to fetch information for

    """

    farmer_id: str = Field(..., description="The ID to fetch information for")

    def get_payload(self) -> Dict[str, Any]:
        """
        Convert the AgristackRequest object to a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the AgristackRequest object
        """
        now = datetime.today()

        return {
            "context": {
                # TODO: This will be changed soon.
                "domain": "advisory:mh-vistaar",
                "action": "search",
                "version": "1.1.0",
                "bap_id": os.getenv("BAP_ID"),
                "bap_uri": os.getenv("BAP_URI"),
                "bpp_id": os.getenv("POCRA_BPP_ID"),
                "bpp_uri": os.getenv("POCRA_BPP_URI"),
                "location": {"country": {"name": "India", "code": "IND"}},
                "transaction_id": str(uuid.uuid4()),
                "message_id": str(uuid.uuid4()),
                "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            },
            "message": {"intent": {"category": {"descriptor": {"code": "agristack_farmer_info"}}, "item": {"id": self.farmer_id}}},
        }

async def fetch_agristack_data(ctx: RunContext[FarmerContext]) -> str:
    """If Agristack Information is available for the user, use this tool to fetch it. This tool returns details of the farmer from the Agristack API, for instance:
        - Profile information such as Gender, Caste Category
        - Location information such as Village, Taluka, District, LGD Codes, and GPS Coordinates
        - Farm details such as Total Plot Area.
        - Masked PII information such as Name, Mobile, Date of Birth.
    """
    if ctx.deps.farmer_id:
        farmer_id = ctx.deps.farmer_id
    else:
        return "Farmer ID is not available in the context. Please register with your farmer ID."

    try:
        payload = AgristackRequest(farmer_id=farmer_id).get_payload()
        response = requests.post(os.getenv("BAP_ENDPOINT"), json=payload, timeout=(10, 15))

        if response.status_code != 200:
            logger.error(f"Farmer Info API returned status code {response.status_code}")
            return "Farmer information service unavailable. Please try again later."

        farmer_response = AgristackResponse.model_validate(response.json())
        return str(farmer_response)

    except requests.Timeout as e:
        logger.error(f"Farmer Info API request timed out: {str(e)}")
        return "Farmer information request timed out. Please try again later."

    except requests.RequestException as e:
        logger.error(f"Farmer Info API request failed: {e}")
        return f"Farmer information request failed: {str(e)}"

    except UnexpectedModelBehavior as e:
        logger.warning("Farmer Info request exceeded retry limit")
        return "Sorry, the farmer information is temporarily unavailable. Please try again later."

    except Exception as e:
        logger.error(f"Error getting farmer information: {e}")
        raise ModelRetry(f"Unexpected error in farmer information request. {str(e)}")
