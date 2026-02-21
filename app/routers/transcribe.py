import uuid
import time
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import JSONResponse
from app.models.requests import TranscribeRequest
from helpers.transcription import transcribe_bhashini, detect_audio_language_bhashini, transcribe_whisper
from helpers.utils import get_logger
from app.auth.jwt_auth import get_current_user
from app.core.limiter import limiter
logger = get_logger(__name__)

router = APIRouter(prefix="/transcribe", tags=["transcribe"])

@router.post("/")
@limiter.limit("1000/hour")
async def transcribe(request: Request, transcribe_request: TranscribeRequest = Body(...), user_info: dict = Depends(get_current_user)):
    """
    Transcribe audio content using the specified service.
    """
    session_id = transcribe_request.session_id or str(uuid.uuid4())
    
#    current_timestamp = int(time.time() * 1000)
    
    if transcribe_request.service_type == 'bhashini':
        lang_code = detect_audio_language_bhashini(transcribe_request.audio_content)
        logger.info(f"Detected language code: {lang_code}")
        transcription = transcribe_bhashini(transcribe_request.audio_content, lang_code)
        logger.info(f"Transcription: {transcription}")
    elif transcribe_request.service_type == 'whisper':
        lang_code, transcription = transcribe_whisper(transcribe_request.audio_content)
    else:
        return JSONResponse({
            'status': 'error',
            'message': 'Invalid service type'
        }, status_code=400)
        
    return JSONResponse({
        'status': 'success',
        'text': transcription,
        'lang_code': lang_code,
        'session_id': session_id
    }, status_code=200)