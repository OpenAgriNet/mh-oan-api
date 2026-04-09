"""
Middleware to extract JWT token and store user info in request state.

LOCAL TESTING: JWT decode is disabled (see `if False` block). Rate limiting
falls back to IP via get_rate_limit_key when request.state.user_info is unset.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from helpers.utils import get_logger

logger = get_logger(__name__)

if False:
    import jwt
    from cryptography.hazmat.primitives import serialization
    from app.config import settings

    public_key_path = settings.base_dir / settings.jwt_public_key_path
    with open(public_key_path, 'rb') as key_file:
        public_key = serialization.load_pem_public_key(key_file.read())


class JWTStateMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts JWT token from Authorization header
    and stores decoded user info in request.state for rate limiting.
    """

    async def dispatch(self, request: Request, call_next):
        if False:
            auth_header = request.headers.get("Authorization", "")

            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")

                try:
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

                    request.state.user_info = decoded_token
                    logger.debug(f"JWT user info stored in request.state: {list(decoded_token.keys())}")

                except jwt.ExpiredSignatureError:
                    logger.debug("JWT token expired - rate limiting will use IP")
                except jwt.InvalidTokenError as e:
                    logger.debug(f"Invalid JWT token: {e} - rate limiting will use IP")
                except Exception as e:
                    logger.debug(f"Error decoding JWT: {e} - rate limiting will use IP")

        response = await call_next(request)
        return response
