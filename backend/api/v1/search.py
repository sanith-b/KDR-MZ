"""
Unified Search API Router (/api/v1/search)
Integrates local drama catalog, telegram files, Gemini AI auto-correction & TMDb metadata.
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Query, Depends
from backend.services.drama_service import drama_service
from backend.core.dependencies import get_optional_user
from backend.core.rate_limiter import RateLimiter
from backend.schemas.api_responses import ApiResponse

router = APIRouter(prefix="/search", tags=["Search"])
search_limiter = RateLimiter(requests_per_minute=40, key_prefix="rate_search")

@router.get("", response_model=ApiResponse[Dict[str, Any]], dependencies=[Depends(search_limiter)])
async def search(
    q: str = Query(..., min_length=1, description="Drama name, romanized title or keyword"),
    limit: int = Query(20, ge=1, le=50),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Search across K-Dramas and Telegram files.
    Employs Gemini AI spell-correction if no local results match, and enriches with TMDb.
    Automatically logs search query and records user history if authenticated.
    """
    user_id = user.get("user_id") if user else None
    results = await drama_service.search_dramas_and_files(query=q, user_id=user_id, limit=limit)
    return ApiResponse(success=True, data=results)
