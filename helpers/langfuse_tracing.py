"""Langfuse SDK helpers aligned with OpenTelemetry-based client (langfuse ≥3.x)."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from helpers import langfuse_helper  # noqa: F401 — initializes Langfuse env before get_client()
from langfuse import get_client


def lf_set_trace_io(*, input: Any = None, output: Any = None) -> None:
    """Trace-level input/output for the Langfuse trace detail view."""
    get_client().set_current_trace_io(input=input, output=output)


def lf_update_current_observation(
    *,
    input: Any = None,
    output: Any = None,
    metadata: Optional[Mapping[str, Any]] = None,
    model: Optional[str] = None,
    request_tokens: Optional[int] = None,
    response_tokens: Optional[int] = None,
) -> None:
    """Update the active observation. Uses generation updates when model/usage are set so Langfuse can aggregate tokens and cost."""
    meta: dict[str, Any] = dict(metadata) if metadata else {}
    if model is not None:
        meta["model"] = model

    has_usage = request_tokens is not None or response_tokens is not None
    usage_details: Optional[dict[str, int]] = None
    if has_usage:
        pt = int(request_tokens or 0)
        ct = int(response_tokens or 0)
        usage_details = {
            "prompt_tokens": pt,
            "completion_tokens": ct,
            "total_tokens": pt + ct,
        }

    client = get_client()
    if model is not None or usage_details is not None:
        client.update_current_generation(
            input=input,
            output=output,
            metadata=meta or None,
            model=model,
            usage_details=usage_details,
        )
    else:
        client.update_current_span(
            input=input,
            output=output,
            metadata=meta or None,
        )
