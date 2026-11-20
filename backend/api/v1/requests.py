"""
K-Drama Requests API Router (/api/v1/requests)
Community request submission, voting, and admin approval workflows.
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException, Depends
from backend.core.dependencies import get_current_user, require_moderator_or_admin
from backend.services.request_service import request_service
from backend.schemas.api_responses import (
    ApiResponse, PaginatedApiResponse, PaginationMetadata,
    CreateDramaRequestPayload, UpdateRequestStatusPayload
)

router = APIRouter(prefix="/requests", tags=["K-Drama Requests"])

@router.post("", response_model=ApiResponse[Dict[str, Any]])
async def create_request(
    payload: CreateDramaRequestPayload,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit a request for a new K-Drama"""
    result = await request_service.create_request(
        user_id=user["user_id"],
        title=payload.title,
        tmdb_id=payload.tmdb_id,
        notes=payload.notes
    )
    return ApiResponse(success=True, data=result["request"], message=result["message"])

@router.post("/{request_id}/vote", response_model=ApiResponse[Dict[str, Any]])
async def vote_for_request(
    request_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Upvote an existing drama request (prevents duplicate voting)"""
    result = await request_service.vote_request(request_id=request_id, user_id=user["user_id"])
    return ApiResponse(success=True, data=result, message="Vote recorded successfully")

@router.get("/my", response_model=PaginatedApiResponse[Dict[str, Any]])
async def get_my_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """List requests submitted by the authenticated user"""
    res = await request_service.get_my_requests(user_id=user["user_id"], page=page, page_size=page_size)
    pagination = PaginationMetadata(
        page=res.page,
        page_size=res.page_size,
        total_count=res.total,
        total_pages=res.total_pages,
        has_next=res.has_next,
        has_prev=res.has_prev
    )
    return PaginatedApiResponse(data=res.items, pagination=pagination)

@router.get("", response_model=PaginatedApiResponse[Dict[str, Any]])
async def list_community_requests(
    status: Optional[str] = Query(None, description="Status filter (pending, approved, rejected, available)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List all community requests sorted by votes count"""
    res = await request_service.list_requests(status=status, page=page, page_size=page_size)
    pagination = PaginationMetadata(
        page=res.page,
        page_size=res.page_size,
        total_count=res.total,
        total_pages=res.total_pages,
        has_next=res.has_next,
        has_prev=res.has_prev
    )
    return PaginatedApiResponse(data=res.items, pagination=pagination)

@router.put("/{request_id}/status", response_model=ApiResponse[Dict[str, Any]], dependencies=[Depends(require_moderator_or_admin)])
async def update_status(
    request_id: str,
    payload: UpdateRequestStatusPayload,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Update request status (Admin & Moderator Only)"""
    ok = await request_service.update_request_status(
        request_id=request_id,
        status=payload.status,
        admin_id=user["user_id"],
        notes=payload.admin_notes
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Request not found")
    return ApiResponse(success=True, data={"request_id": request_id, "status": payload.status})
