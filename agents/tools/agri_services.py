import os
import uuid
import json
from datetime import datetime
from helpers.utils import get_logger
import requests
from pydantic import BaseModel, AnyHttpUrl, Field
from typing import List, Optional, Dict, Any, Literal
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
    village: Optional[str] = None
    pinCode: Optional[str] = None

class Contact(BaseModel):
    person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    webUrl: Optional[str] = None

class Creator(BaseModel):
    descriptor: Optional[Descriptor] = None

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
        title = self.descriptor.name or self.descriptor.code or (self.id or "Item")
        lines.append(f"**{title}**")
        
        if self.descriptor.short_desc:
            lines.append(f"  {self.descriptor.short_desc}")
        if self.descriptor.long_desc:
            lines.append(f"  {self.descriptor.long_desc}")
            
        if self.address:
            addr_parts = []
            if self.address.village:
                addr_parts.append(self.address.village)
            if self.address.taluka:
                addr_parts.append(self.address.taluka)
            if self.address.district:
                addr_parts.append(self.address.district)
            if addr_parts:
                lines.append(f"  Location: {', '.join(addr_parts)}")
                
        if self.contact:
            if self.contact.person:
                lines.append(f"  Contact: {self.contact.person}")
            if self.contact.phone:
                lines.append(f"  Phone: {self.contact.phone}")
                
        if self.tags:
            for tag in self.tags:
                if tag.list:
                    for ti in tag.list:
                        label = (ti.descriptor.name or ti.descriptor.code) if ti.descriptor else "value"
                        if label == "distance":
                            lines.append(f"  Distance: {ti.value}")
        return "\n".join(lines)


class Provider(BaseModel):
    id: Optional[str] = None
    descriptor: Descriptor
    items: Optional[List[Item]] = None

    def __str__(self) -> str:
        lines = []
        lines.append(f"Provider: {self.descriptor.name or self.descriptor.code or self.id}")
        
        if self.descriptor.short_desc:
            lines.append(f"  {self.descriptor.short_desc}")
            
        if self.items:
            lines.append("  Items:")
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


class AgriServicesResponse(BaseModel):
    context: Context
    responses: List[ResponseItem]

    def _has_items(self) -> bool:
        for response in self.responses:
            for provider in response.message.catalog.providers:
                if provider.items and len(provider.items) > 0:
                    return True
        return False

    def __str__(self) -> str:
        lines = []
        lines.append("> Agricultural Services")
        
        has_services = self._has_items()
        if len(self.responses) == 0 or not has_services:
            lines.append("No agricultural services found for the requested location.")
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
# Request model
# -----------------------
class AgriServicesRequest(BaseModel):
    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location")
    category_code: Literal["kvk", "chc", "soil_lab", "warehouse"] = Field(..., description="Service category code: 'kvk' for Krishi Vigyan Kendra, 'chc' for Custom Hiring Center, 'soil_lab' for soil testing laboratories, 'warehouse' for warehouses")

    def get_payload(self) -> Dict[str, Any]:
        """Create the payload for the agri services API request."""
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
                    "category": {"descriptor": {"code": self.category_code}},
                    "item": {"descriptor": {"name": "service-locations"}},
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


async def agri_services(latitude: float, longitude: float, category_code: Literal["kvk", "chc", "soil_lab", "warehouse"]) -> str:
    """Fetch agricultural services (KVK, CHC, soil labs, warehouse) for a given location via BAP.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        category_code: Service category to fetch - 'kvk' for Krishi Vigyan Kendra, 'chc' for Custom Hiring Center, 'soil_lab' for soil testing laboratories, 'warehouse' for warehouses

    Returns:
        str: Formatted agricultural services response
    """
    try:
        payload = AgriServicesRequest(
            latitude=latitude,
            longitude=longitude,
            category_code=category_code,
        ).get_payload()
        bap_endpoint = os.getenv("BAP_ENDPOINT")
        if not bap_endpoint:
            logger.error("BAP_ENDPOINT environment variable not set")
            return "Agricultural services configuration error."

        response = requests.post(
            bap_endpoint,
            json=payload,
            timeout=(10, 15)
        )

        if response.status_code != 200:
            logger.error(f"Agricultural Services API returned status code {response.status_code}")
            return "Agricultural services unavailable. Retrying"

        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return "Agricultural services returned invalid response."

        parsed = AgriServicesResponse.model_validate(response_data)
        return str(parsed)

    except requests.Timeout:
        logger.error("Agricultural Services API request timed out")
        return "Agricultural services request timed out."
    except requests.RequestException as e:
        logger.error(f"Agricultural Services API request failed: {e}")
        return f"Agricultural services request failed: {str(e)}"
    except UnexpectedModelBehavior as e:
        logger.warning("Agricultural services request exceeded retry limit")
        return "Agricultural services are temporarily unavailable. Please try again later."
    except Exception as e:
        logger.error(f"Error getting agricultural services: {e}")
        raise ModelRetry(f"Unexpected error in agricultural services request. {str(e)}")


