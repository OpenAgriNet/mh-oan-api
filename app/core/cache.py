"""
Core cache instance configuration using Redis and aiocache.

This module provides the cache instance that other parts of the application can use.
Uses enhanced Redis configuration with connection pooling and timeouts.
"""
from aiocache import Cache
from aiocache.serializers import JsonSerializer
from app.config import settings
from helpers.utils import get_logger
import redis.asyncio as redis

logger = get_logger(__name__)

# Configure the cache instance with enhanced settings and connection pooling
cache = Cache(
    Cache.REDIS,
    endpoint=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    serializer=JsonSerializer(),
    ttl=settings.default_cache_ttl,
    # Connection pool settings to prevent exhaustion
    timeout=settings.redis_socket_timeout,
    pool_max_size=settings.redis_max_connections,
    create_connection_timeout=settings.redis_socket_connect_timeout,
    # Pass additional connection pool kwargs for better connection management
    connection_pool_kwargs={
        "socket_keepalive": True,
        "retry_on_timeout": settings.redis_retry_on_timeout,
        "health_check_interval": 30,  # Check connection health every 30 seconds
    },
    # Add key prefix support
    key_builder=lambda key, namespace: f"{settings.redis_key_prefix}{namespace}:{key}" if namespace else f"{settings.redis_key_prefix}{key}",
)

logger.info(
    f"Cache configured with Redis at {settings.redis_host}:{settings.redis_port} "
    f"(DB: {settings.redis_db}, Prefix: {settings.redis_key_prefix}, "
    f"Max Connections: {settings.redis_max_connections}, Auto-cleanup: Enabled)"
) 