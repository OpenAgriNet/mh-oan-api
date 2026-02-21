from fastapi import APIRouter, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from app.auth.jwt_auth import get_current_user
from app.services.chat import stream_chat_messages
from app.services.bhili_translate import translation_service
from app.utils import _get_message_history
from app.tasks.suggestions import create_suggestions
from app.models.requests import ChatRequest
from fastapi.responses import JSONResponse
from app.core.limiter import limiter
from helpers.utils import get_logger
from app.services.chat import run_agent_full
import uuid

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Bhili (bhb): query translated to English, agent runs in English (no stream), response translated to bhb
BHILI_TARGET_LANG = "bhb"
EN_LANG = "en"

@router.get("/")
@limiter.limit("1000/hour")
async def chat_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    chat_request: ChatRequest = Depends(),
    user_info: dict = {"sub": "anonymous", "preferred_username": "anonymous"}  # Authentication required
):
    """
    Chat endpoint that streams responses back to the client.
    Requires JWT authentication.
    """
    session_id = chat_request.session_id or str(uuid.uuid4())
    
    logger.info(
        f"Chat request received - session_id: {session_id}, user_id: {chat_request.user_id}, "
        f"authenticated_user: {user_info}, source_lang: {chat_request.source_lang}, "
        f"target_lang: {chat_request.target_lang}, query: {chat_request.query}"
    )
    
    history = await _get_message_history(session_id)
    logger.debug(f"Retrieved message history for session {session_id} - length: {len(history)}")
    
    if chat_request.source_lang == "bhb":
        # logger.info(f"chat request query: {chat_request.query}")
        # 1️ Translate user query to English
        query_en = await translation_service.translate_text(
            chat_request.query,
            chat_request.source_lang,
            EN_LANG
        )
        logger.info(f"query_en: {query_en}")
        # logger.info(f"Chat-bhili: translated query to English (len={len(query_en)})")

        #2
        response_en = await run_agent_full(
            query=query_en,
            session_id=session_id,
            target_lang=EN_LANG,
            user_id=chat_request.user_id,
            history=history,
            user_info=user_info,
            background_tasks=background_tasks,
        )
        # logger.info(f"Chat-bhili: agent response in English (len={len(response_en)})")
        # logger.info(f"response_en: {response_en}")
        #3
        response_bhb = await translation_service.translate_text(
            response_en,
            EN_LANG,
            BHILI_TARGET_LANG
        )
        # logger.info(f"Chat-bhili: translated response to bhb (len={len(response_bhb)})")
        # logger.info(f"response_bhb: {response_bhb}")

        return JSONResponse(content={"response": response_bhb})

    #  DEFAULT FLOW (Streaming)
    return StreamingResponse(
        stream_chat_messages(
            query=chat_request.query,
            session_id=session_id,
            source_lang=chat_request.source_lang,
            target_lang=chat_request.target_lang,
            user_id=chat_request.user_id,
            history=history,
            user_info=user_info,
            background_tasks=background_tasks
        ),
        media_type="text/event-stream"
    )