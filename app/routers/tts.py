from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from app.models.requests import TTSRequest
from helpers.tts import text_to_speech_bhashini
import uuid
import base64
from helpers.utils import get_logger
from app.core.limiter import limiter
logger = get_logger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])

@router.post("/")
@limiter.limit("10/minute")
async def tts(request: Request, tts_request: TTSRequest = Body(...)):
    """
    Convert text to speech using the specified service.
    """
    session_id = tts_request.session_id or str(uuid.uuid4())
    
    # For now, only bhashini is implemented, but the model supports eleven_labs too
    if tts_request.service_type == 'bhashini':
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
