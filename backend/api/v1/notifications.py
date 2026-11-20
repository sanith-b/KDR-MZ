"""
User Notifications API Router (/api/v1/notifications)
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, Depends
from backend.core.dependencies import get_current_user
from backend.services.user_interaction_service import user_interaction_service
from backend.schemas.api_responses import (
    ApiResponse, PaginatedApiResponse, PaginationMetadata, MarkNotificationReadRequest
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=PaginatedApiResponse[Dict[str, Any]])
async def get_my_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """List authenticated user's notifications"""
    res = await user_interaction_service.get_user_notifications(
        user_id=user["user_id"], unread_only=unread_only, page=page, page_size=page_size
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

@router.post("/read", response_model=ApiResponse[Dict[str, Any]])
async def mark_notifications_read(
    payload: MarkNotificationReadRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Mark one or all notifications as read"""
    count = await user_interaction_service.mark_notifications_read(
        user_id=user["user_id"],
        notification_ids=payload.notification_ids,
        mark_all=payload.mark_all
    )
    return ApiResponse(success=True, data={"modified_count": count})
