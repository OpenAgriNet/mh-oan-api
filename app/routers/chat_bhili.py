import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse

from app.core.limiter import limiter
from app.models.requests import ChatRequest
from app.services.bhili_translate import translation_service
from app.services.chat import run_agent_full
from app.utils import _get_message_history
from helpers.utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat-bhili", tags=["chat-bhili"])

# Bhili (bhb): query translated to English, agent runs in English (no stream), response translated to bhb
BHILI_TARGET_LANG = "bhb"
EN_LANG = "en"


@router.get("/")
@limiter.limit("20/day")
async def chat_bhili_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    chat_request: ChatRequest = Depends(),
    user_info: dict = {"sub": "anonymous", "preferred_username": "anonymous"},
):
    """
    Chat-bhili: translate query to English, run agent (no stream), translate response to bhb, return JSON.
    Same query params: query, session_id, source_lang, target_lang, user_id.
    """
    session_id = chat_request.session_id or str(uuid.uuid4())

    logger.info(
        f"Chat-bhili request - session_id: {session_id}, user_id: {chat_request.user_id}, "
        f"source_lang: {chat_request.source_lang}, target_lang: {chat_request.target_lang}, query: {chat_request.query}"
    )

    history = await _get_message_history(session_id)
    logger.debug(f"Retrieved message history for session {session_id} - length: {len(history)}")

    # 1. Translate query to English
    query_en = await translation_service.translate_text(
        chat_request.query, chat_request.source_lang, EN_LANG
    )
    logger.info(f"Chat-bhili: translated query to English (len={len(query_en)})")

    # 2. Run agent in English (no streaming)
    response_en = await run_agent_full(
        query=query_en,
        session_id=session_id,
        target_lang=EN_LANG,
        user_id=chat_request.user_id,
        history=history,
        user_info=user_info,
        background_tasks=background_tasks,
    )
    logger.info(f"Chat-bhili: agent response in English (len={len(response_en)})")

    # 3. Translate agent response to bhb (Bhili)
    response_bhb = await translation_service.translate_text(
        response_en, EN_LANG, BHILI_TARGET_LANG
    )
    logger.info(f"Chat-bhili: translated response to bhb (len={len(response_bhb)})")

    return JSONResponse(content={"response": response_bhb})
