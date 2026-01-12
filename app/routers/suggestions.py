from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.models.requests import SuggestionsRequest
from app.utils import get_cache

router = APIRouter(prefix="/suggest", tags=["suggest"])

# NOTE: No need for rate limiting here as it's invoked by the chat method only.
@router.get("/")
async def suggest(request: SuggestionsRequest = Depends()):
    """
    Get suggestions for a conversation session.
    If suggestions are not cached, trigger creation asynchronously.
    """
    cache_key = f"suggestions_{request.session_id}_{request.target_lang}"
    suggestions = await get_cache(cache_key) or []
    return JSONResponse(suggestions)