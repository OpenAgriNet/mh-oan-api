"""
Middleware to extract JWT token and store user info in request state.

This runs before rate limiting, so the rate limiter can access user info
from the JWT token for per-user rate limiting.
"""
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from cryptography.hazmat.primitives import serialization
from app.config import settings
from helpers.utils import get_logger

logger = get_logger(__name__)

# Load public key for JWT verification
public_key_path = settings.base_dir / settings.jwt_public_key_path
with open(public_key_path, 'rb') as key_file:
    public_key = serialization.load_pem_public_key(key_file.read())


class JWTStateMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts JWT token from Authorization header
    and stores decoded user info in request.state for rate limiting.
    
    This runs before the rate limiter, ensuring user identification
    is available for per-user rate limits.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extract JWT token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            
            try:
                # Decode JWT token
                decoded_token = jwt.decode(
                    token,
                    public_key,
                    algorithms=[settings.jwt_algorithm],
                    options={
                        "verify_signature": True,
                        "verify_aud": False,
                        "verify_iss": False
                    }
                )
                
                # Store user info in request state for rate limiting
                request.state.user_info = decoded_token
                logger.debug(f"JWT user info stored in request.state: {list(decoded_token.keys())}")
                
            except jwt.ExpiredSignatureError:
                logger.debug("JWT token expired - rate limiting will use IP")
            except jwt.InvalidTokenError as e:
                logger.debug(f"Invalid JWT token: {e} - rate limiting will use IP")
            except Exception as e:
                logger.debug(f"Error decoding JWT: {e} - rate limiting will use IP")
        
        # Continue processing the request
        response = await call_next(request)
        return response

