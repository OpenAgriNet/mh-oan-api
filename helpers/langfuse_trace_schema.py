"""Langfuse: chain.chat → agent.moderation → agent.vistaar → tool:*; trace title via propagate_attributes(trace_name)."""

AGENT_MODERATION = "agent.moderation"
AGENT_VISTAAR = "agent.vistaar"


def chat_trace_metadata_strings(
    *,
    source_lang: str,
    target_lang: str,
    environment: str,
    query: str = "",
) -> dict[str, str]:
    """Propagated trace metadata (strings ≤200 chars for Langfuse)."""
    out: dict[str, str] = {
        "source_lang": source_lang,
        "target_lang": target_lang,
        "environment": environment,
    }
    if query:
        out["query"] = query if len(query) <= 200 else f"{query[:197]}..."
    return out
