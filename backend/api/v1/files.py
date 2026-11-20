"""
Media Files & Fast Streaming API Router (/api/v1/files)
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException, Depends
from backend.services.media_service import media_service
from backend.core.dependencies import require_admin
from backend.schemas.api_responses import (
    ApiResponse, PaginatedApiResponse, PaginationMetadata, FileCreateRequest
)
from shared.database.repositories.dramas_repo import telegram_files_repo

router = APIRouter(prefix="/files", tags=["Files & Streaming"])

@router.get("", response_model=PaginatedApiResponse[Dict[str, Any]])
async def list_files(
    drama_id: Optional[str] = Query(None, description="Drama identifier"),
    season_number: Optional[int] = Query(None, ge=1),
    episode_number: Optional[int] = Query(None, ge=1),
    quality: Optional[str] = Query(None, description="Quality filter: 1080p, 720p, etc."),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List telegram files matching coordinates with pagination"""
    res = await media_service.list_files(
        drama_id=drama_id,
        season_number=season_number,
        episode_number=episode_number,
        quality=quality,
        page=page,
        page_size=page_size
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

@router.get("/{file_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_file_metadata(file_id: str):
    """Retrieve metadata for a specific media file"""
    file_doc = await media_service.get_file_by_id(file_id)
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    return ApiResponse(success=True, data=file_doc)

@router.get("/{file_id}/stream", response_model=ApiResponse[Dict[str, Any]])
async def get_stream_urls(file_id: str):
    """Resolve direct streaming and download URLs for a media file"""
    file_doc = await media_service.get_file_by_id(file_id)
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    urls = media_service.generate_streaming_urls(file_doc)
    return ApiResponse(success=True, data=urls)

@router.post("", response_model=ApiResponse[Dict[str, Any]], dependencies=[Depends(require_admin)])
async def register_file(payload: FileCreateRequest):
    """Index or register a new Telegram media file (Admin Only)"""
    created = await telegram_files_repo.create(payload.model_dump())
    return ApiResponse(success=True, data=created, message="File registered successfully")
