# import jwt
import os
from dotenv import load_dotenv
# from cryptography.hazmat.primitives import serialization
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from helpers.utils import get_logger
from app.config import settings  # Import the application settings

load_dotenv()

logger = get_logger(__name__)


class OptionalOAuth2PasswordBearer(OAuth2PasswordBearer):
    """OAuth2 scheme that's optional in development"""

    async def __call__(self, request: Request) -> str | None:
        # --- LOCAL TESTING: optional Bearer (no token required). Restore strict mode below when JWT is on. ---
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        scheme, param = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            return None
        return param
        # if settings.environment == "development":
        #     authorization = request.headers.get("Authorization")
        #     if not authorization:
        #         return None
        #     scheme, param = get_authorization_scheme_param(authorization)
        #     if scheme.lower() != "bearer":
        #         return None
        #     return param
        # return await super().__call__(request)


# OAuth2 scheme for FastAPI - optional in development
oauth2_scheme = OptionalOAuth2PasswordBearer(tokenUrl="token")

# --- LOCAL TESTING: PEM load commented out. Uncomment when enabling JWT verification. ---
# public_key_path = settings.base_dir / settings.jwt_public_key_path
# with open(public_key_path, 'rb') as key_file:
#     public_key = serialization.load_pem_public_key(key_file.read())
# logger.info(f"Successfully loaded JWT Public Key from: {public_key_path}")


async def get_current_user(token: str | None = Depends(oauth2_scheme)):
    """
    FastAPI dependency to get current authenticated user from JWT token.
    This replaces the Django middleware approach.
    """
    # --- LOCAL TESTING: bypass JWT verification. Remove this block when enabling JWT below. ---
    logger.info("Local testing: JWT verification bypassed")
    return {"sub": "development_user", "farmer_id": None}

    # credentials_exception = HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Could not validate credentials",
    #     headers={"WWW-Authenticate": "Bearer"},
    # )
    #
    # if public_key is None:
    #     logger.error("JWT Public Key is not loaded, cannot verify tokens.")
    #     raise credentials_exception
    #
    # try:
    #     decoded_token = jwt.decode(
    #         token,
    #         public_key,
    #         algorithms=[settings.jwt_algorithm],
    #         options={
    #             "verify_signature": True,
    #             "verify_aud": False,
    #             "verify_iss": False,
    #         },
    #     )
    #     logger.info(f"Decoded token: {decoded_token}")
    #     return decoded_token
    #
    # except jwt.ExpiredSignatureError:
    #     logger.warning("Token has expired")
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Token has expired",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    #
    # except jwt.InvalidTokenError as e:
    #     logger.warning(f"Invalid token error: {str(e)}")
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail=f"Invalid token: {str(e)}",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    #
    # except Exception as e:
    #     logger.error(f"Unexpected error during token verification: {str(e)}")
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Token verification failed",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
