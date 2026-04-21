import os
from typing import AsyncGenerator

from fastapi import BackgroundTasks
from langfuse import get_client, observe, propagate_attributes

from agents.agrinet import agrinet_agent
from agents.moderation import moderation_agent
from helpers.langfuse_trace_schema import (
    AGENT_MODERATION,
    AGENT_VISTAAR,
    chat_trace_metadata_strings,
)
from helpers.langfuse_tracing import lf_set_trace_io, lf_update_current_observation
from helpers.utils import get_logger
from helpers.translation import (
    translation_service,
    BhashiniTranslator,
    markdown_to_chunks,
    chunks_to_markdown,
)
from helpers import langfuse_helper  # noqa: F401 — initialises Langfuse env vars
from app.utils import (
    update_message_history,
    trim_history,
    format_message_pairs,
    filter_thinking_from_history,
)
from app.tasks.suggestions import create_suggestions
from agents.deps import FarmerContext

logger = get_logger(__name__)

MODEL_NAME = (
    os.getenv("LLM_AGRINET_MODEL_NAME")
    or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    or os.getenv("LLM_MODEL_NAME")
)

CHAT_TRACE_NAME = (
    os.getenv("LANGFUSE_TRACE_NAME")
    or os.getenv("LANGFUSE_TRACE_ROOT_NAME")
    or "mh-vistaar-chat"
)
CHAT_CHAIN_SPAN_NAME = "chain.chat"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _translate_paragraph(text: str, source_lang: str, target_lang: str) -> str:
    """Translate a paragraph, preserving markdown structure."""
    chunks = markdown_to_chunks(text)
    translator = BhashiniTranslator(source_lang=source_lang, target_lang=target_lang)
    translated_chunks = await translator.translate(chunks, exclude_keys={"start", "end"})
    return chunks_to_markdown(translated_chunks)


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

async def stream_chat_messages(
    query: str,
    session_id: str,
    source_lang: str,
    target_lang: str,
    user_id: str,
    history: list,
    user_info: dict,
    background_tasks: BackgroundTasks,
) -> AsyncGenerator[str, None]:
    """Async generator for streaming chat messages with full Langfuse tracing.

    Uses start_as_current_observation (not @observe) so an OpenTelemetry current
    span exists across StreamingResponse/async-generator yields.
    """
    logger.info(f"User info: {user_info}")

    lf_env = os.getenv("LANGFUSE_TRACING_ENVIRONMENT", "development")
    trace_tags = [f"env:{lf_env}", *([f"model:{MODEL_NAME}"] if MODEL_NAME else [])]

    lf_client = get_client()

    # propagate_attributes sets TRACE-level metadata (user_id, session_id,
    # trace_name, tags) inherited by all child spans.
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        metadata=chat_trace_metadata_strings(
            source_lang=source_lang,
            target_lang=target_lang,
            environment=lf_env,
            query=query,
        ),
        tags=trace_tags,
        trace_name=CHAT_TRACE_NAME,
    ):
        with lf_client.start_as_current_observation(
            as_type="chain",
            name=CHAT_CHAIN_SPAN_NAME,
        ):
            lf_set_trace_io(input=query)

            # ------------------------------------------------------------------
            # Bhili: translate query → English before processing
            # ------------------------------------------------------------------
            is_bhili = source_lang == "bhb"
            if is_bhili:
                query = await translation_service.translate_text(query, source_lang, "en")
                logger.info(f"Bhili query translated to English: {query}")
                target_lang = "en"

            deps = FarmerContext(
                query=query,
                lang_code=target_lang,
                farmer_id=user_info.get("farmer_id"),
            )

            message_pairs = "\n\n".join(format_message_pairs(history, 3))
            logger.info(f"Message pairs: {message_pairs}")
            last_response = (
                f"**Conversation**\n\n{message_pairs}\n\n---\n\n" if message_pairs else ""
            )

            # ------------------------------------------------------------------
            # Moderation — child span via @observe (regular coroutine, safe)
            # ------------------------------------------------------------------
            moderation_data = await _run_moderation(
                user_message=f"{last_response}{deps.get_user_message()}",
                session_id=session_id,
            )
            logger.info(f"Moderation data: {moderation_data}")
            deps.update_moderation_str(str(moderation_data))

            if moderation_data.category == "valid_agricultural":
                logger.info(f"Triggering suggestions generation for session {session_id}")
                try:
                    background_tasks.add_task(create_suggestions, session_id, target_lang)
                except Exception as e:
                    logger.error(f"Error adding suggestions task: {str(e)}")

            # ------------------------------------------------------------------
            # History prep
            # ------------------------------------------------------------------
            trimmed_history = trim_history(
                history,
                max_tokens=80_000,
                include_system_prompts=True,
                include_tool_calls=True,
            )
            logger.info(f"Trimmed history: {len(trimmed_history)} messages")
            trimmed_history = filter_thinking_from_history(trimmed_history)

            # ------------------------------------------------------------------
            # Main agent — true streaming, child span via manual observation
            # ------------------------------------------------------------------
            with propagate_attributes(tags=[moderation_data.category]):
                async for chunk in _run_agrinet_stream(
                    user_message=deps.get_user_message(),
                    trimmed_history=trimmed_history,
                    history=history,
                    deps=deps,
                    session_id=session_id,
                    user_id=user_id,
                    moderation_category=moderation_data.category,
                    is_bhili=is_bhili,
                ):
                    yield chunk

            lf_client.flush()


# ---------------------------------------------------------------------------
# Moderation agent span
# ---------------------------------------------------------------------------

@observe(name=AGENT_MODERATION, as_type="agent")
async def _run_moderation(user_message: str, session_id: str):
    """Run moderation agent — traced as a child span of chain.chat."""
    lf_update_current_observation(
        input=user_message,
        metadata={"session_id": session_id},
    )

    run = await moderation_agent.run(user_message)
    usage_data = run.usage()

    lf_update_current_observation(
        output=str(run.output),
        model=MODEL_NAME,
        request_tokens=usage_data.request_tokens or 0,
        response_tokens=usage_data.response_tokens or 0,
        metadata={},
    )
    return run.output


# ---------------------------------------------------------------------------
# Agrinet agent span — true streaming async generator
# ---------------------------------------------------------------------------

async def _run_agrinet_stream(
    user_message: str,
    trimmed_history: list,
    history: list,
    deps: FarmerContext,
    session_id: str,
    user_id: str,
    moderation_category: str,
    is_bhili: bool,
) -> AsyncGenerator[str, None]:
    """
    Run agrinet agent in true streaming mode — child span of chain.chat.

    Yields individual text chunks as they arrive from the model (no buffering).
    Langfuse span input is set before the first yield; output + usage are set
    inside a finally block so the span is always closed correctly even on early
    client disconnect.

    Uses start_as_current_observation (not @observe) so current span exists
    across async-generator yields.

    History is updated AFTER the generator fully exhausts.  On early disconnect
    (generator .aclose()'d) the history write is skipped — partial responses
    are not persisted.
    """
    lf_client = get_client()
    with lf_client.start_as_current_observation(
        as_type="agent",
        name=AGENT_VISTAAR,
    ):
        # Set span input before streaming starts.
        lf_update_current_observation(
            input=user_message,
            metadata={
                "session_id": session_id,
                "user_id": user_id,
                "moderation_category": moderation_category,
            },
        )

        full_output = ""
        new_messages = []
        request_tokens = 0
        response_tokens = 0

        try:
            async with agrinet_agent.run_stream(
                user_prompt=user_message,
                message_history=trimmed_history,
                deps=deps,
            ) as response_stream:

                if is_bhili:
                    # Buffer paragraph-by-paragraph so Bhashini receives complete
                    # sentences, then translate each paragraph before yielding.
                    buffer = ""
                    async for chunk in response_stream.stream_text(delta=True):
                        buffer += chunk
                        while "\n\n" in buffer:
                            paragraph, buffer = buffer.split("\n\n", 1)
                            translated = await _translate_paragraph(paragraph, "en", "bhb")
                            full_output += translated + "\n\n"
                            yield translated + "\n\n"
                    # Flush remaining tail (no trailing double-newline)
                    if buffer.strip():
                        translated_tail = await _translate_paragraph(buffer, "en", "bhb")
                        full_output += translated_tail
                        yield translated_tail
                else:
                    async for chunk in response_stream.stream_text(delta=True):
                        full_output += chunk
                        yield chunk

                logger.info(f"Streaming complete for session {session_id}")
                new_messages = response_stream.new_messages()

                # Usage is only available after the stream context exits.
                try:
                    usage = response_stream.usage()
                    request_tokens = usage.request_tokens or 0
                    response_tokens = usage.response_tokens or 0
                except Exception:
                    pass  # Usage unavailable — tokens reported as 0

        finally:
            # Synchronous-only block: safe inside async generators on Python 3.9+.
            # Runs on normal exhaustion AND on early .aclose() (client disconnect).
            lf_update_current_observation(
                output=full_output,
                model=MODEL_NAME,
                request_tokens=request_tokens,
                response_tokens=response_tokens,
                metadata={},
            )
            lf_set_trace_io(output=full_output)

    # Reached only on normal exhaustion (not on .aclose()).
    # Persist the confirmed full response to message history.
    clean_new_messages = filter_thinking_from_history(list(new_messages or []))
    logger.info(f"Updating message history for session {session_id}")
    await update_message_history(session_id, [*history, *clean_new_messages])