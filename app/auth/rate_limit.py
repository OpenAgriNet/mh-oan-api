"""
Rate limiting utilities for API endpoints using SlowAPI.

Provides custom key generation functions based on JWT payload fields
for user identification in rate limiting.
"""
import hashlib
import simplejson as json
from typing import Dict, Any, Optional
from fastapi import Request
from helpers.utils import get_logger
from datetime import datetime
from zoneinfo import ZoneInfo
from app.config import settings

logger = get_logger(__name__)


def current_date_str() -> str:
    """Get current date as a string in the format YYYY-MM-DD in the timezone specified in the settings"""
    return datetime.now(tz=ZoneInfo(settings.timezone)).strftime("%Y-%m-%d")


def md5_sha_from_str(val: str) -> str:
    """Generate md5 hash from string"""
    return hashlib.md5(val.encode("utf-8")).hexdigest()


def md5_sha_from_dict(obj: Dict[str, Any], ignore_nan: bool = False, default: Optional[Any] = None) -> str:
    """Generate md5 hash from dictionary"""
    json_data = json.dumps(obj, sort_keys=True, ignore_nan=ignore_nan, default=default)
    return md5_sha_from_str(json_data)


def get_rate_limit_key(request: Request) -> str:
    """
    SlowAPI-compatible key function.
    Extract user identification fields from JWT token and generate unique hash.
    
    Uses the following fields from JWT payload (if available):
    - mobile
    - name
    - farmer_id
    - unique_id

    NOTE: Adding today's date so that the rate limit is different for each day.
    
    Returns MD5 hash of the sorted dictionary containing these fields.
    Note: This is a synchronous function as required by SlowAPI.
    """
    # Get user_info from request state (set by get_current_user dependency)
    user_info = getattr(request.state, 'user_info', None)
    
    today_date = current_date_str()
    if not user_info:
        # Fallback to IP address if no user info available
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"No user_info found in request state, using IP: {client_host}")
        return md5_sha_from_str(f"{client_host}:{today_date}")
    
    # Extract relevant fields for rate limiting
    rate_limit_fields = {}
    
    for field in ['mobile', 'name', 'farmer_id', 'unique_id']:
        value = user_info.get(field)
        # Only include non-null and non-empty values
        if value is not None and value != "":
            rate_limit_fields[field] = value
    
    # Generate hash from the fields
    if rate_limit_fields:
        rate_limit_fields['date'] = today_date
        hash_key = md5_sha_from_dict(rate_limit_fields)
        logger.debug(f"Generated rate limit key: {hash_key} from fields: {list(rate_limit_fields.keys())}")
        return hash_key
    else:
        # If no fields are available, fallback to IP
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"No JWT fields available for rate limiting, using IP: {client_host}")
        return md5_sha_from_str(f"{client_host}:{today_date}")

