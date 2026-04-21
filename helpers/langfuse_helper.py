"""Set Langfuse client env before get_client() / OpenTelemetry export."""

import os

from app.config import settings
from langfuse import Langfuse

os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key or ""
os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key or ""
os.environ["LANGFUSE_HOST"] = (
    settings.langfuse_host or os.getenv("LANGFUSE_BASE_URL") or ""
)
os.environ["LANGFUSE_TRACING_ENVIRONMENT"] = settings.langfuse_tracing_environment

langfuse = Langfuse()
