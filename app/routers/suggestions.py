from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.models.requests import SuggestionsRequest
from app.utils import get_cache
from app.auth.jwt_auth import get_current_user
from helpers.translation import translation_service

router = APIRouter(prefix="/suggest", tags=["suggest"],)

# NOTE: No need for rate limiting here as it's invoked by the chat method only.
@router.get("/")
async def suggest(request: SuggestionsRequest = Depends(), user_info: dict = Depends(get_current_user)):
    """
    Get suggestions for a conversation session.
    If suggestions are not cached, trigger creation asynchronously.
    """
    cache_lang = "en" if request.target_lang == "bhb" else request.target_lang
    cache_key = f"suggestions_{request.session_id}_{cache_lang}"
    suggestions = await get_cache(cache_key) or []
    if request.target_lang == "bhb" and suggestions:
        suggestions = [
            await translation_service.translate_text(s, "en", "bhb")
            for s in suggestions
        ]
    return JSONResponse(suggestions)