"""
User Favorites API Router (/api/v1/favorites)
"""
from typing import Dict, Any
from fastapi import APIRouter, Query, Depends
from backend.core.dependencies import get_current_user
from backend.services.user_interaction_service import user_interaction_service
from backend.schemas.api_responses import (
    ApiResponse, PaginatedApiResponse, PaginationMetadata, FavoriteAddRequest
)

router = APIRouter(prefix="/favorites", tags=["Favorites"])

@router.get("", response_model=PaginatedApiResponse[Dict[str, Any]])
async def get_my_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """List authenticated user's favorite dramas"""
    res = await user_interaction_service.get_user_favorites(
        user_id=user["user_id"], page=page, page_size=page_size
    )
    pagination = PaginationMetadata(
        page=res.page,
        page_size=res.page_size,
        total_count=res.total,
        total_pages=res.total_pages,
        has_next=res.has_next,
        has_prev=res.has_prev
    )
    return PaginatedApiResponse(data=res.items, pagination=pagination)

@router.post("", response_model=ApiResponse[Dict[str, Any]])
async def toggle_favorite(
    payload: FavoriteAddRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Toggle a drama in personal favorites (add if absent, remove if present)"""
    result = await user_interaction_service.toggle_favorite(
        user_id=user["user_id"], drama_id=payload.drama_id
    )
    return ApiResponse(success=True, data=result)
