"""
Personalized Drama Recommendations API Router (/api/v1/recommendations)
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, Depends
from backend.core.dependencies import get_optional_user
from backend.services.recommendation_service import recommendation_service
from backend.schemas.api_responses import ApiResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_recommendations(
    limit: int = Query(10, ge=1, le=30),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Get personalized recommendations based on user favorites and viewing history,
    powered by Gemini AI and catalog metrics.
    """
    user_id = user.get("user_id") if user else None
    results = await recommendation_service.get_recommendations(user_id=user_id, limit=limit)
    return ApiResponse(success=True, data=results)
