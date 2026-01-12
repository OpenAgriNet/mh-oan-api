"""
Shared rate limiter instance for the application.

This module provides a centralized limiter instance to avoid circular imports.
"""
from slowapi import Limiter
from app.auth.rate_limit import get_rate_limit_key
from app.config import settings

# Initialize SlowAPI limiter with Redis storage and custom key function
limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
    default_limits=[]  # We'll set limits per endpoint
)

