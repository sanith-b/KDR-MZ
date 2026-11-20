"""
User Search History API Router (/api/v1/history)
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Query, Depends
from backend.core.dependencies import get_current_user
from backend.services.user_interaction_service import user_interaction_service
from backend.schemas.api_responses import ApiResponse

router = APIRouter(prefix="/history", tags=["Search History"])

@router.get("", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_my_history(
    limit: int = Query(30, ge=1, le=100),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieve authenticated user's recent search queries"""
    items = await user_interaction_service.get_user_history(user_id=user["user_id"], limit=limit)
    return ApiResponse(success=True, data=items)

@router.delete("", response_model=ApiResponse[Dict[str, Any]])
async def clear_my_history(user: Dict[str, Any] = Depends(get_current_user)):
    """Clear personal search query history"""
    cleared = await user_interaction_service.clear_user_history(user_id=user["user_id"])
    return ApiResponse(success=True, data={"cleared": cleared}, message="Search history cleared")
