"""

MahaDBT Scheme status

"""

import os
import uuid
from datetime import datetime
from helpers.utils import get_logger
import httpx
from pydantic import BaseModel, AnyHttpUrl, Field
from typing import List, Optional, Dict, Any, ClassVar
from pydantic_ai import ModelRetry, UnexpectedModelBehavior, RunContext
from agents.deps import FarmerContext
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
        if self.name and self.name != "NA":
            return self.name
        elif self.code:
            return self.code
        return "Unknown Scheme"

# -----------------------
# Tag Models
# -----------------------
class Tag(BaseModel):
    code: Optional[str] = None
    descriptor: Optional[Descriptor] = None
    value: str

    def __str__(self) -> str:
        if self.code:
            return f"{self.code}: {self.value}"
        elif self.descriptor and self.descriptor.code:
            return f"{self.descriptor.code}: {self.value}"
        return self.value

# -----------------------
# Scheme Application Models
# -----------------------
class SchemeApplication(BaseModel):
    """Model representing a farmer's scheme application with status and details."""

    id: str
    descriptor: Descriptor
    tags: List[Tag]

    # Class-level PII codes that should be masked
    PII_CODES: ClassVar[set[str]] = {"application_id", "farmer_component_mapping_id"}
    
    # Status labels with emojis and Marathi translations
    STATUS_LABELS: ClassVar[Dict[str, str]] = {
        "Fund Disbursed": "✅ Fund Disbursed (पैसे दिले गेले)",
        "Winner": "🏆 Winner (निवड झाली)",
        "Wait List": "⏳ Wait List (प्रतीक्षा यादीत आहे)",
        "WaitList": "⏳ Wait List (प्रतीक्षा यादीत आहे)",
        "Application cancelled by applicant": "❌ Cancelled by Applicant (तुम्ही अर्ज रद्द केला)",
        "Department Cancelled": "🚫 Department Cancelled (विभागाने अर्ज रद्द केला)",
        "Approved": "✅ Approved (अर्ज मंजूर झाला)",
        "Rejected": "❌ Rejected (अर्ज नाकारला)",
        "Under Review": "📋 Under Review (अर्ज तपासणीमध्ये आहे)",
        "Pending": "⏳ Pending (अर्ज थांबलेला आहे)",
        "Upload Documents": "📄 Upload Documents (कागदपत्रे टाका)",
        "Document scrutiny before pre-sanction": "🔍 Document scrutiny before pre-sanction (पूर्वमंजुरीसाठी कागदपत्र पडताळणी)",
        "Document SLA Cancelled": "🚫 Document SLA Cancelled (वेळेत कागदपत्रे न दिल्यामुळे रद्द)",
        "Upload DPR": "📝 Upload DPR (डीपीआर टाका)",
        "Document Scrutiny and Upload Site Inspection": "🔍 Document Check & Site Inspection Upload (कागदपत्र तपासणी व जागेची पाहणी अपलोड)",
        "Application Approved and Sanction letter generated": "✅ Application Approved – Sanction Letter Ready (अर्ज मंजूर – मंजुरी पत्र तयार आहे)",
        "Document Scrutiny and Upload Site Inspection": "🔍 Document Check & Site Inspection Upload (कागदपत्र तपासणी व जागेची पाहणी अपलोड)",
        "Application Cancelled (Give Up Subsidy)": "🚫 Application Cancelled – Subsidy Given Up (अर्ज रद्द – अनुदानाचा त्याग केला)",        
        "Application rejected by department": "❌ Application Rejected by Department (विभागाने अर्ज नाकारला)",
        "Upload Invoice": "🧾 Upload Invoice (बिल अपलोड करा)",
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

    @classmethod
    def format_status_display(cls, status: str) -> str:
        """Format status with appropriate emoji indicators and Marathi translations.
        
        Args:
            status: The status string to format
            
        Returns:
            Formatted status string with emoji and translation
        """
        return cls.STATUS_LABELS.get(status, f"📄 {status}")

    def _get_tag_value(self, code: str) -> Optional[str]:
        """Get value for a specific tag code."""
        for tag in self.tags:
            if tag.code == code or (tag.descriptor and tag.descriptor.code == code):
                if tag.value in ["null", "NA"]:
                    return None
                return tag.value
        return None

    def _format_tag_code(self, code: str) -> str:
        """Convert tag code to human-readable label."""
        special_mappings = {
            "application_id": "Application ID",
            "farmer_component_mapping_id": "Component Mapping ID",
            "status": "Status",
            "status_details": "Status Details",
            "primary_scheme": "Primary Scheme",
            "top_scheme": "Top Scheme",
            "last_updated_date": "Last Updated",
            "component_updated_date": "Component Updated",
            "disbursement_date": "Disbursement Date",
            "instalment_number": "Instalment Number",
            "instalment_status": "Instalment Status",
            "financial_year": "Financial Year",
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

        return value

    def _mask_pii_value(self, value: str) -> str:
        """Apply PII masking to show only last 4 digits for application IDs."""
        if not value or value in ["null", "NA"]:
            return "***"

        # Remove whitespace for processing
        clean_value = value.strip()

        # For application IDs, show only last 4 characters
        if len(clean_value) <= 4:
            return "***"
        else:
            return f"***{clean_value[-4:]}"

    def _format_status_for_display(self, status: str) -> str:
        """Format status with appropriate emoji indicators."""
        return self.format_status_display(status)

    def __str__(self, mask_pii: bool = True) -> str:
        lines = []
        indent_1 = "  "  # First level indentation
        
        # Scheme name and status from descriptor
        scheme_name = str(self.descriptor)
        if self.descriptor.short_desc:
            status_text = self.descriptor.short_desc.replace("Status: ", "")
            status_formatted = self._format_status_for_display(status_text)
            lines.append(f"> **{scheme_name}**")
            lines.append(f"{indent_1}Status: {status_formatted}")
        else:
            lines.append(f"> **{scheme_name}**")

        # Priority information to display
        priority_info = [
            ("financial_year", "Financial Year"),
            ("application_id", "Application ID"),
            ("last_updated_date", "Last Updated"),
            ("component_updated_date", "Component Updated"),
            ("disbursement_date", "Disbursement Date"),
            ("instalment_status", "Instalment Status"),
        ]

        for code, label in priority_info:
            value = self._get_tag_value(code)
            if value and value != "NA":
                if code == "financial_year":
                    # Format financial year nicely
                    if len(value) == 4:
                        fy_start = f"20{value[:2]}"
                        fy_end = f"20{value[2:]}"
                        lines.append(f"{indent_1}{label}: {fy_start}-{fy_end}")
                    else:
                        lines.append(f"{indent_1}{label}: {value}")
                elif "date" in code and value != "NA":
                    # Format dates nicely
                    try:
                        date_obj = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                        formatted_date = date_obj.strftime("%d %b %Y")
                        lines.append(f"{indent_1}{label}: {formatted_date}")
                    except ValueError:
                        lines.append(f"{indent_1}{label}: {value}")
                else:
                    # Apply PII masking for sensitive codes
                    formatted_value = self._format_tag_value(code, value, mask_pii)
                    lines.append(f"{indent_1}{label}: {formatted_value}")

        return "\n".join(lines)

class Provider(BaseModel):
    id: str
    descriptor: Descriptor
    items: List[SchemeApplication]

    def __str__(self, mask_pii: bool = True) -> str:
        lines = []
        indent_1 = "  "  # First level indentation
        lines.append(f"Provider: {self.descriptor.name}")

        if self.items:
            lines.append("Applications:")
            for item in self.items:
                item_str = item.__str__(mask_pii=mask_pii).replace("\n", f"\n{indent_1}")
                lines.append(f"{indent_1}{item_str}")

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
                provider_str = provider.__str__(mask_pii=mask_pii).replace("\n", "\n")
                lines.append(provider_str)
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

class MahaDBTResponse(BaseModel):
    context: Context
    responses: List[ResponseItem]

    def _has_scheme_data(self) -> bool:
        """Check if there are any responses with scheme information."""
        for response in self.responses:
            for provider in response.message.catalog.providers:
                if provider.items and len(provider.items) > 0:
                    return True
        return False

    def _get_scheme_summary(self) -> Dict[str, int]:
        """Get a summary of scheme statuses."""
        status_counts = {}
        total_applications = 0

        for response in self.responses:
            for provider in response.message.catalog.providers:
                for item in provider.items:
                    total_applications += 1
                    if item.descriptor.short_desc:
                        status = item.descriptor.short_desc.replace("Status: ", "")
                        status_counts[status] = status_counts.get(status, 0) + 1

        return {"total": total_applications, "statuses": status_counts}

    def __str__(self, mask_pii: bool = True) -> str:
        lines = []
        lines.append("## MahaDBT Scheme Status Information")
        lines.append("")

        has_scheme_data = self._has_scheme_data()
        if not self.responses or not has_scheme_data:
            lines.append("❌ No scheme application information found for the requested farmer ID.")
            return "\n".join(lines)

        # Get summary
        summary = self._get_scheme_summary()
        indent_1 = "  "  # First level indentation
        if summary["total"] > 0:
            lines.append(f"📊 **Summary: {summary['total']} total applications**")
            for status, count in summary["statuses"].items():
                formatted_status = SchemeApplication.format_status_display(status)
                lines.append(f"{indent_1}• {count} {formatted_status}")
            lines.append("")

        # Show detailed information
        lines.append("### Detailed Information:")
        lines.append("")

        # Group applications by actual application ID (before the dash) and scheme
        applications = {}
        for response in self.responses:
            for provider in response.message.catalog.providers:
                for item in provider.items:
                    # Extract base application ID (before the dash)
                    base_app_id = item.id.split('-')[0] if '-' in item.id else item.id
                    scheme_name = str(item.descriptor)
                    status = item.descriptor.short_desc.replace("Status: ", "") if item.descriptor.short_desc else "Unknown"
                    
                    key = f"{base_app_id}_{scheme_name}"
                    
                    if key not in applications:
                        applications[key] = {
                            "base_item": item,
                            "scheme_name": scheme_name,
                            "base_app_id": base_app_id,
                            "components": []
                        }
                    
                    applications[key]["components"].append({
                        "component_id": item.id,
                        "status": status,
                        "item": item
                    })

        # Display applications with component status breakdown
        indent_1 = "  "  # First level indentation
        indent_2 = "    "  # Second level indentation
        
        for app_data in applications.values():
            base_item = app_data["base_item"]
            scheme_name = app_data["scheme_name"]
            components = app_data["components"]
            
            lines.append(f"> **{scheme_name}**")
            
            # Show base application ID (masked)
            app_id_value = app_data["base_app_id"]
            if mask_pii:
                masked_app_id = base_item._mask_pii_value(app_id_value)
                lines.append(f"{indent_1}Application ID: {masked_app_id}")
            else:
                lines.append(f"{indent_1}Application ID: {app_id_value}")
            
            # Count component statuses
            status_counts = {}
            for component in components:
                status = component["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Show component status breakdown
            if len(components) > 1:
                lines.append(f"{indent_1}Total {len(components)} Components")
                for status, count in status_counts.items():
                    status_formatted = base_item._format_status_for_display(status)
                    lines.append(f"{indent_2}• {count} {status_formatted}")
            else:
                # Single component, show status directly
                status_formatted = base_item._format_status_for_display(components[0]["status"])
                lines.append(f"{indent_1}Status: {status_formatted}")
            
            # Show other details from the first component (they should be similar across components)
            first_component = components[0]["item"]
            priority_info = [
                ("financial_year", "Financial Year"),
                ("last_updated_date", "Last Updated"),
                ("disbursement_date", "Disbursement Date")
            ]
            
            for code, label in priority_info:
                value = first_component._get_tag_value(code)
                if value and value != "NA":
                    if code == "financial_year":
                        # Format financial year nicely
                        if len(value) == 4:
                            fy_start = f"20{value[:2]}"
                            fy_end = f"20{value[2:]}"
                            lines.append(f"{indent_1}{label}: {fy_start}-{fy_end}")
                        else:
                            lines.append(f"{indent_1}{label}: {value}")
                    elif "date" in code and value != "NA":
                        # Format dates nicely
                        try:
                            from datetime import datetime
                            date_obj = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                            formatted_date = date_obj.strftime("%d %b %Y")
                            lines.append(f"{indent_1}{label}: {formatted_date}")
                        except ValueError:
                            lines.append(f"{indent_1}{label}: {value}")
                    else:
                        lines.append(f"{indent_1}{label}: {value}")
            
            lines.append("")

        return "\n".join(lines)

# -----------------------
# Request Model
# -----------------------
class MahaDBTRequest(BaseModel):
    """MahaDBT Request model for the MahaDBT API.

    Args:
        farmer_id (str): The farmer ID to fetch scheme status information for
    """

    farmer_id: str = Field(..., description="The farmer ID to fetch scheme status information for")

    def get_payload(self) -> Dict[str, Any]:
        """
        Convert the MahaDBTRequest object to a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the MahaDBTRequest object
        """
        now = datetime.now()

        return {
            "context": {
                "domain": "mahadbt:mh-vistaar",
                "ttl": "PT10S",
                "action": "search",
                "version": "1.1.0",
                "bap_id": os.getenv("BAP_ID"),
                "bap_uri": os.getenv("BAP_URI"),
                "bpp_id": os.getenv("MAHADBT_BPP_ID"),
                "bpp_uri": os.getenv("MAHADBT_BPP_URI"),
                "message_id": str(uuid.uuid4()),
                "transaction_id": str(uuid.uuid4()),
                "timestamp": str(int(now.timestamp())),
                "location": {"country": {"name": "India", "code": "IND"}},
            },
            "message": {"intent": {"category": {"descriptor": {"code": "farmer-details-info"}}, "item": {"id": self.farmer_id}}},
        }

async def get_scheme_status(ctx: RunContext[FarmerContext]) -> str:
    """Fetch a summary of the farmer's scheme applications and their status from MahaDBT API. Returns a summary of the farmer's scheme applications and their status from MahaDBT, including application status, disbursement information, and scheme details."""
    if ctx.deps.farmer_id:
        farmer_id = ctx.deps.farmer_id
    else:
        return "Farmer ID is not available in the context. Please register with your farmer ID."

    try:
        payload = MahaDBTRequest(farmer_id=farmer_id).get_payload()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(os.getenv("BAP_ENDPOINT"), json=payload, timeout=15.0)

        if response.status_code != 200:
            logger.error(f"MahaDBT API returned status code {response.status_code}")
            return "Scheme status information service is currently unavailable. Please try again later."

        scheme_response = MahaDBTResponse.model_validate(response.json())
        return str(scheme_response)

    except httpx.TimeoutException as e:
        logger.error(f"MahaDBT API request timed out: {str(e)}")
        return "MahaDBT Scheme status request timed out. Please try again later."

    except httpx.RequestError as e:
        logger.error(f"MahaDBT API request failed: {e}")
        return f"MahaDBT Scheme status request failed: {str(e)}"

    except UnexpectedModelBehavior as e:
        logger.warning("MahaDBT request exceeded retry limit")
        return "Sorry, the MahaDBT scheme status information is temporarily unavailable. Please try again later."

    except Exception as e:
        logger.error(f"Error getting MahaDBT scheme status: {e}")
        raise ModelRetry(f"Unexpected error in MahaDBT scheme status request. {str(e)}")
