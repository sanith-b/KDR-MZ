"""
Drama Seasons API Router (/api/v1/seasons)
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException, Depends
from backend.core.dependencies import require_admin
from backend.schemas.api_responses import ApiResponse, SeasonCreateRequest
from shared.database.repositories.dramas_repo import seasons_repo

router = APIRouter(prefix="/seasons", tags=["Seasons"])

@router.get("", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_seasons(drama_id: str = Query(..., description="Drama identifier")):
    """List all seasons for a specified drama"""
    res = await seasons_repo.find_many({"drama_id": drama_id})
    return ApiResponse(success=True, data=res.items)

@router.post("", response_model=ApiResponse[Dict[str, Any]], dependencies=[Depends(require_admin)])
async def create_season(payload: SeasonCreateRequest):
    """Create a new season for a drama (Admin Only)"""
    created = await seasons_repo.create(payload.model_dump())
    return ApiResponse(success=True, data=created, message="Season created successfully")
