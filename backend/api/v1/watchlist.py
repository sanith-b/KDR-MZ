"""
User Watchlist API Router (/api/v1/watchlist)
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Query, Depends, status
from backend.core.dependencies import get_current_user
from backend.services.user_interaction_service import user_interaction_service
from backend.schemas.api_responses import (
    ApiResponse, PaginatedApiResponse, PaginationMetadata,
    WatchlistAddRequest
)

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.get("", response_model=PaginatedApiResponse[Dict[str, Any]])
async def get_my_watchlist(
    status: Optional[str] = Query(None, description="Filter: plan_to_watch, watching, completed, dropped"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get authenticated user's personal watchlist"""
    res = await user_interaction_service.get_user_watchlist(
        user_id=user["user_id"], status_filter=status, page=page, page_size=page_size
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
async def add_to_watchlist(
    payload: WatchlistAddRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Add or update drama in personal watchlist"""
    item = await user_interaction_service.add_to_watchlist(
        user_id=user["user_id"], drama_id=payload.drama_id, status=payload.status
    )
    return ApiResponse(success=True, data=item, message="Watchlist updated")

@router.delete("/{drama_id}", response_model=ApiResponse[Dict[str, Any]])
async def remove_from_watchlist(
    drama_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove drama from personal watchlist"""
    removed = await user_interaction_service.remove_from_watchlist(
        user_id=user["user_id"], drama_id=drama_id
    )
    return ApiResponse(success=True, data={"removed": removed})
