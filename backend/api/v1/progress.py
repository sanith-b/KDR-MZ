"""
User Watch Progress API Router (/api/v1/progress)
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, Depends
from backend.core.dependencies import get_current_user
from backend.services.user_interaction_service import user_interaction_service
from backend.schemas.api_responses import ApiResponse, ProgressUpdateRequest

router = APIRouter(prefix="/progress", tags=["Watch Progress"])

@router.get("", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_my_progress(
    drama_id: Optional[str] = Query(None, description="Optional drama identifier"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieve personal episode playback progress"""
    items = await user_interaction_service.get_progress(user_id=user["user_id"], drama_id=drama_id)
    return ApiResponse(success=True, data=items)

@router.post("", response_model=ApiResponse[Dict[str, Any]])
async def update_progress(
    payload: ProgressUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Record playback position and completion status for an episode"""
    result = await user_interaction_service.update_progress(
        user_id=user["user_id"],
        drama_id=payload.drama_id,
        episode_id=payload.episode_id,
        season_number=payload.season_number,
        episode_number=payload.episode_number,
        playback_position_seconds=payload.playback_position_seconds,
        duration_seconds=payload.duration_seconds,
        is_completed=payload.is_completed
    )
    return ApiResponse(success=True, data=result, message="Playback progress recorded")
