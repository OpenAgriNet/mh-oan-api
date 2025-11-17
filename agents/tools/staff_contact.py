import os
import uuid
import json
from datetime import datetime, timezone
from helpers.utils import get_logger
import requests
from pydantic import BaseModel, AnyHttpUrl, Field
from typing import List, Optional, Dict, Any
from pydantic_ai import ModelRetry, UnexpectedModelBehavior
from dotenv import load_dotenv

load_dotenv()

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
        if self.name:
            return self.name
        elif self.code:
            return self.code
        return ""


class Country(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None


class Location(BaseModel):
    country: Optional[Country] = None


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


class TagItem(BaseModel):
    descriptor: Descriptor
    value: str


class Tag(BaseModel):
    descriptor: Optional[Descriptor] = None
    list: Optional[List[TagItem]] = None


class Address(BaseModel):
    address: Optional[str] = None
    district: Optional[str] = None
    region: Optional[str] = None
    taluka: Optional[str] = None
    vilage: Optional[str] = None
    pinCode: Optional[str] = None


class Contact(BaseModel):
    person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    webUrl: Optional[str] = None


class Creator(BaseModel):
    descriptor: Optional[Descriptor] = None


class Fulfillment(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = None
    status: Optional[List[Dict[str, str]]] = None
    locations: Optional[Dict[str, str]] = None
    categories: Optional[List[Dict[str, Any]]] = None


class Item(BaseModel):
    id: Optional[str] = None
    descriptor: Descriptor
    address: Optional[Address] = None
    contact: Optional[Contact] = None
    creator: Optional[Creator] = None
    fulfillment_ids: Optional[List[str]] = None
    status: Optional[List[str]] = None
    category_ids: Optional[List[str]] = None
    tags: Optional[List[Tag]] = None

    def __str__(self) -> str:
        lines = []
        title = self.descriptor.name or self.descriptor.code or (self.id or "Officer")
        lines.append(f"**{title}**")
        
        if self.descriptor.short_desc:
            lines.append(f"  {self.descriptor.short_desc}")
        if self.descriptor.long_desc:
            lines.append(f"  {self.descriptor.long_desc}")
            
        if self.address:
            addr_parts = []
            if self.address.vilage:
                addr_parts.append(self.address.vilage)
            if self.address.taluka:
                addr_parts.append(self.address.taluka)
            if self.address.district:
                addr_parts.append(self.address.district)
            if self.address.region:
                addr_parts.append(self.address.region)
            if addr_parts:
                lines.append(f"  Location: {', '.join(addr_parts)}")
                
        if self.contact:
            if self.contact.person:
                lines.append(f"  Contact: {self.contact.person}")
            if self.contact.phone:
                lines.append(f"  Phone: {self.contact.phone}")
            if self.contact.email and self.contact.email != "N/A":
                lines.append(f"  Email: {self.contact.email}")
                
        if self.tags:
            for tag in self.tags:
                if tag.list:
                    for ti in tag.list:
                        label = (ti.descriptor.name or ti.descriptor.code) if ti.descriptor else "value"
                        if label == "role_name":
                            lines.append(f"  Role: {ti.value}")
                        elif label == "division":
                            lines.append(f"  Division: {ti.value}")
                        elif label == "circle":
                            lines.append(f"  Circle: {ti.value}")
        return "\n".join(lines)


class Provider(BaseModel):
    id: Optional[str] = None
    descriptor: Descriptor
    fulfillments: Optional[List[Fulfillment]] = None
    items: Optional[List[Item]] = None

    def __str__(self) -> str:
        lines = []
        lines.append(f"Provider: {self.descriptor.name or self.descriptor.code or self.id}")
        
        if self.descriptor.short_desc:
            lines.append(f"  {self.descriptor.short_desc}")
            
        if self.items:
            lines.append("  Officers:")
            for item in self.items:
                item_str = str(item).replace("\n", "\n    ")
                lines.append(f"    {item_str}")
        
        return "\n".join(lines)


class Catalog(BaseModel):
    descriptor: Optional[Descriptor] = None
    providers: List[Provider] = Field(default_factory=list)

    def __str__(self) -> str:
        lines = []
        if self.descriptor and (self.descriptor.name or self.descriptor.code):
            lines.append(f"Catalog: {self.descriptor.name or self.descriptor.code}")
        if self.providers:
            lines.append("Providers:")
            for p in self.providers:
                p_str = str(p).replace("\n", "\n  ")
                lines.append(f"  {p_str}")
        return "\n".join(lines)


class Message(BaseModel):
    catalog: Catalog

    def __str__(self) -> str:
        return str(self.catalog)


class ResponseItem(BaseModel):
    context: Context
    message: Message

    def __str__(self) -> str:
        return str(self.message)

    class Config:
        extra = "allow"  # Allow extra fields in the response


class ContactResponse(BaseModel):
    context: Context
    responses: List[ResponseItem]

    def _has_officers(self) -> bool:
        for response in self.responses:
            for provider in response.message.catalog.providers:
                if provider.items and len(provider.items) > 0:
                    return True
        return False

    def __str__(self) -> str:
        lines = []
        lines.append("> Officer Details")
        
        has_officers = self._has_officers()
        if len(self.responses) == 0 or not has_officers:
            lines.append("No officer details found for the requested location.")
            return "\n".join(lines)
        else:
            lines.append("Responses:")
            for idx, rsp in enumerate(self.responses, start=1):
                rsp_str = str(rsp).replace("\n", "\n  ")
                lines.append(f"    {rsp_str}")
            return "\n".join(lines)

    class Config:
        extra = "allow"  # Allow extra fields in the response


# -----------------------
# Administrative Info Models (for village code lookup)
# -----------------------
class AdminAddress(BaseModel):
    district: Optional[str] = None
    taluka: Optional[str] = None
    vilage: Optional[str] = None
    districtCode: Optional[str] = None
    talukaCode: Optional[str] = None
    villageCode: Optional[str] = None


class AdminItem(BaseModel):
    id: Optional[str] = None
    descriptor: Descriptor
    address: Optional[AdminAddress] = None
    tags: Optional[List[Tag]] = None


class AdminProvider(BaseModel):
    id: Optional[str] = None
    descriptor: Descriptor
    items: Optional[List[AdminItem]] = None


class AdminCatalog(BaseModel):
    descriptor: Optional[Descriptor] = None
    providers: List[AdminProvider] = Field(default_factory=list)


class AdminMessage(BaseModel):
    catalog: AdminCatalog


class AdminResponseItem(BaseModel):
    context: Context
    message: AdminMessage

    class Config:
        extra = "allow"


class AdminResponse(BaseModel):
    context: Context
    responses: List[AdminResponseItem]

    class Config:
        extra = "allow"


# -----------------------
# Request Models
# -----------------------
class AdministrativeRequest(BaseModel):
    """Request model for administrative information API."""
    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location")

    def get_payload(self) -> Dict[str, Any]:
        """Create the payload for the administrative information API request."""
        now = datetime.today()
        
        return {
            "context": {
                "domain": "advisory:mh-vistaar",
                "location": {"country": {"name": "IND"}},
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
                    "category": {"descriptor": {"code": "village-information"}},
                    "fulfillment": {
                        "stops": [
                            {
                                "location": {"gps": f"{self.latitude},{self.longitude}"}
                            }
                        ]
                    }
                }
            }
        }


class ContactRequest(BaseModel):
    """Request model for officer details API."""
    village_code: str = Field(..., description="Village code for the location")
    data_category: str = Field(default="aa", description="Data category for officer type")

    def get_payload(self) -> Dict[str, Any]:
        """Create the payload for the officer details API request."""
        now = datetime.today()
        
        return {
            "context": {
                "domain": "advisory:mh-vistaar",
                "location": {"country": {"name": "IND"}},
                "action": "search",
                "version": "1.1.0",
                "bap_id": os.getenv("BAP_ID"),
                "bap_uri": os.getenv("BAP_URI"),
                "bpp_id": os.getenv("POCRA_BPP_ID"),
                "bpp_uri": os.getenv("POCRA_BPP_URI"),
                "message_id": str(uuid.uuid4()),
                "transaction_id": str(uuid.uuid4()),
                "timestamp": now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            },
            "message": {
                "intent": {
                    "category": {"descriptor": {"code": "officer"}},
                    "item": {
                        "descriptor": {
                            "code": self.village_code,
                            "name": self.data_category
                        }
                    },
                    "fulfillment": {
                        "stops": [
                            {
                                "location": {"id": self.village_code}
                            }
                        ]
                    }
                }
            }
        }


# -----------------------
# Helper Functions
# -----------------------
def _get_village_code_from_admin_api(latitude: float, longitude: float) -> Optional[str]:
    """Get village code from administrative information API.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        
    Returns:
        Optional[str]: Village code if found, None otherwise
    """
    try:
        payload = AdministrativeRequest(latitude=latitude, longitude=longitude).get_payload()
        bap_endpoint = os.getenv("BAP_ENDPOINT")
        if not bap_endpoint:
            logger.error("BAP_ENDPOINT environment variable not set")
            return None

        response = requests.post(
            bap_endpoint,
            json=payload,
            timeout=(10, 15)
        )

        if response.status_code != 200:
            logger.error(f"Administrative API returned status code {response.status_code}")
            return None

        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None

        parsed = AdminResponse.model_validate(response_data)
        
        # Extract village code from the response
        for response_item in parsed.responses:
            for provider in response_item.message.catalog.providers:
                if provider.items:
                    for item in provider.items:
                        if item.address and item.address.villageCode:
                            return item.address.villageCode
        
        logger.warning("No village code found in administrative response")
        return None

    except requests.Timeout:
        logger.error("Administrative API request timed out")
        return None
    except requests.RequestException as e:
        logger.error(f"Administrative API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting village code: {e}")
        return None


# -----------------------
# Contact information for - aa (Agricultural Assistant), ga (Government Agricultural Staff)
# -----------------------
async def contact_agricultural_staff(latitude: float, longitude: float) -> str:
    """Get the contact information for the agricultural staff for a specific location.

    Args:
        latitude (float): Latitude of the location
        longitude (float): Longitude of the location

    Returns:
        str: The contact information for the agricultural staff for the specific location
    """
    try:
        # First, get the village code from administrative information
        village_code = _get_village_code_from_admin_api(latitude, longitude)
        
        if not village_code:
            logger.warning("Could not retrieve village code for the given coordinates")
            return "Agricultural staff details unavailable: Could not determine village information for the given location."
        
        # Now get officer details using the village code.
        
        # Data category is `aa` (Agricultural Assistant) by default for now.
        payload = ContactRequest(village_code=village_code, data_category="aa").get_payload()
        bap_endpoint = os.getenv("BAP_ENDPOINT")
        if not bap_endpoint:
            logger.error("BAP_ENDPOINT environment variable not set")
            return "Agricultural staff details configuration error."

        response = requests.post(
            bap_endpoint,
            json=payload,
            timeout=(10, 15)
        )

        if response.status_code != 200:
            logger.error(f"Officer Details API returned status code {response.status_code}")
            return "Agricultural staff details unavailable."

        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return "Agricultural staff details returned invalid response."

        parsed = ContactResponse.model_validate(response_data)
        return str(parsed)

    except requests.Timeout:
        logger.error("Agricultural staff Details API request timed out")
        return "Agricultural staff details request timed out."
    except requests.RequestException as e:
        logger.error(f"Agricultural staff Details API request failed: {e}")
        return f"Agricultural staff details request failed: {str(e)}"
    except UnexpectedModelBehavior as e:
        logger.warning("Agricultural staff details request exceeded retry limit")
        return "Agricultural staff details are temporarily unavailable. Please try again later."
    except Exception as e:
        logger.error(f"Error getting agricultural staff details: {e}")
        raise ModelRetry(f"Unexpected error in officer details request. {str(e)}")
