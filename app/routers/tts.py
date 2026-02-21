from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import JSONResponse
from app.models.requests import TTSRequest
from helpers.tts import text_to_speech_bhashini, text_to_speech_bhili
import uuid
import base64
from helpers.utils import get_logger
from app.auth.jwt_auth import get_current_user  # auth disabled
from app.core.limiter import limiter
logger = get_logger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])

@router.post("/")
@limiter.limit("1000/hour")
async def tts(
    request: Request,
    tts_request: TTSRequest = Body(...),
    user_info: dict = Depends(get_current_user)
):
    """
    Convert text to speech using the specified service.
    """
    session_id = tts_request.session_id or str(uuid.uuid4())

    if tts_request.service_type == 'bhashini':

        # 🔹 If Bhili (bhb), use voice cloning endpoint
        if tts_request.source_lang == "bhb":
            logger.info(f"Using Bhili voice cloning endpoint for source language: {tts_request.source_lang}")
            audio_data = text_to_speech_bhili(
                text=tts_request.text,
                target_lang=tts_request.target_lang,
                gender='female',
                sampling_rate=8000
            )

        # All other languages use normal pipeline TTS
        else:
            audio_data = text_to_speech_bhashini(
                tts_request.text,
                tts_request.target_lang,
                gender='female',
                sampling_rate=8000
            )

    else:
        return JSONResponse({
            'status': 'error',
            'message': 'Service type not implemented yet'
        }, status_code=400)

    if isinstance(audio_data, bytes):
        audio_data = base64.b64encode(audio_data).decode('utf-8')

    return JSONResponse({
        'status': 'success',
        'audio_data': audio_data,
        'session_id': session_id
    }, status_code=200)