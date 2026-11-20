"""
Drama Episodes API Router (/api/v1/episodes)
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException, Depends
from backend.core.dependencies import require_admin
from backend.schemas.api_responses import ApiResponse, EpisodeCreateRequest
from shared.database.repositories.dramas_repo import episodes_repo

router = APIRouter(prefix="/episodes", tags=["Episodes"])

@router.get("", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_episodes(
    drama_id: str = Query(..., description="Drama identifier"),
    season_number: int = Query(1, ge=1, description="Season number")
):
    """List all episodes for a specific drama season"""
    res = await episodes_repo.find_many(
        {"drama_id": drama_id, "season_number": season_number}
    )
    return ApiResponse(success=True, data=res.items)

@router.get("/{episode_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_episode_details(episode_id: str):
    """Get details for a specific episode"""
    ep = await episodes_repo.find_one({"$or": [{"episode_id": episode_id}, {"_id": episode_id}]})
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    return ApiResponse(success=True, data=ep)

@router.post("", response_model=ApiResponse[Dict[str, Any]], dependencies=[Depends(require_admin)])
async def create_episode(payload: EpisodeCreateRequest):
    """Create a new episode record (Admin Only)"""
    created = await episodes_repo.create(payload.model_dump())
    return ApiResponse(success=True, data=created, message="Episode created successfully")
