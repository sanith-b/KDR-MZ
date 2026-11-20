"""
Drama Catalog API Router (/api/v1/dramas)
Browse, filter, and view detailed K-Drama records.
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException, Depends, status
from backend.services.drama_service import drama_service
from backend.services.media_service import media_service
from backend.core.dependencies import require_admin
from backend.schemas.api_responses import (
    ApiResponse, PaginatedApiResponse, PaginationMetadata,
    DramaCreateRequest, DramaUpdateRequest
)
from shared.database.repositories.dramas_repo import dramas_repo

router = APIRouter(prefix="/dramas", tags=["Dramas & Catalog"])

@router.get("", response_model=PaginatedApiResponse[Dict[str, Any]])
async def list_dramas(
    query: Optional[str] = Query(None, description="Search keyword"),
    genre: Optional[str] = Query(None, description="Genre filter (e.g. Romance, Thriller)"),
    year: Optional[int] = Query(None, description="Release year filter"),
    status: Optional[str] = Query(None, description="Status filter (ongoing, completed, upcoming)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List and filter drama catalog with pagination"""
    res = await drama_service.list_dramas(
        query=query, genre=genre, year=year, status=status, page=page, page_size=page_size
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

@router.get("/{drama_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_drama_details(drama_id: str):
    """Retrieve detailed information about a drama including its seasons and available files"""
    drama = await drama_service.get_drama_by_id_or_slug(drama_id)
    if not drama:
        raise HTTPException(status_code=404, detail="Drama not found")

    # Fetch associated seasons
    actual_id = drama.get("drama_id") or str(drama.get("_id"))
    seasons = await drama_service.get_drama_seasons(actual_id)
    files = await media_service.list_files(drama_id=actual_id, page_size=50)

    result = {
        **drama,
        "seasons": seasons,
        "available_files_count": files.total
    }
    return ApiResponse(success=True, data=result)

@router.post("", response_model=ApiResponse[Dict[str, Any]], dependencies=[Depends(require_admin)])
async def create_drama(payload: DramaCreateRequest):
    """Add a new drama to the catalog (Admin Only)"""
    data = payload.model_dump()
    if not data.get("slug"):
        data["slug"] = payload.title.lower().replace(" ", "-").replace(":", "")
    created = await dramas_repo.create(data)
    return ApiResponse(success=True, data=created, message="Drama created successfully")

@router.put("/{drama_id}", response_model=ApiResponse[Dict[str, Any]], dependencies=[Depends(require_admin)])
async def update_drama(drama_id: str, payload: DramaUpdateRequest):
    """Update drama metadata (Admin Only)"""
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    drama = await drama_service.get_drama_by_id_or_slug(drama_id)
    if not drama:
        raise HTTPException(status_code=404, detail="Drama not found")

    await dramas_repo.update_by_id(drama["_id"], update_data)
    updated = await drama_service.get_drama_by_id_or_slug(drama_id)
    return ApiResponse(success=True, data=updated, message="Drama updated successfully")
