"""
User Profile, Preferences & Points API Router (/api/v1/users)
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from backend.core.dependencies import get_current_user
from backend.schemas.api_responses import (
    ApiResponse, UserUpdateRequest, UserPreferencesUpdate
)
from shared.database.repositories.users_repo import users_repo

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/profile", response_model=ApiResponse[Dict[str, Any]])
async def get_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """Fetch current user's profile and settings"""
    uid = user.get("user_id")
    user_doc = None
    try:
        user_doc = await users_repo.get_by_telegram_id(int(uid))
    except (ValueError, TypeError):
        user_doc = await users_repo.get_by_web_id(str(uid))

    if not user_doc:
        user_doc = user

    safe_doc = {k: v for k, v in user_doc.items() if k not in ["password_hash", "_legacy_id"]}
    return ApiResponse(success=True, data=safe_doc)

@router.put("/profile", response_model=ApiResponse[Dict[str, Any]])
async def update_profile(
    payload: UserUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user first name, last name, and preferences"""
    uid = user.get("user_id")
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)

    filter_q = {"telegram_id": int(uid)} if str(uid).isdigit() else {"web_id": str(uid)}
    await users_repo.update_one(filter_q, update_data)
    updated = await users_repo.find_one(filter_q)
    return ApiResponse(success=True, data=updated, message="Profile updated successfully")

@router.put("/preferences", response_model=ApiResponse[Dict[str, Any]])
async def update_preferences(
    payload: UserPreferencesUpdate,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user app preferences (language, auto-deletion, notifications)"""
    uid = user.get("user_id")
    prefs = payload.model_dump()
    filter_q = {"telegram_id": int(uid)} if str(uid).isdigit() else {"web_id": str(uid)}
    await users_repo.update_one(filter_q, {"preferences": prefs, "updated_at": datetime.now(timezone.utc)})
    return ApiResponse(success=True, data=prefs, message="Preferences updated")

@router.get("/points", response_model=ApiResponse[Dict[str, Any]])
async def get_points_and_referrals(user: Dict[str, Any] = Depends(get_current_user)):
    """Get activity points and referral balance"""
    uid = user.get("user_id")
    filter_q = {"telegram_id": int(uid)} if str(uid).isdigit() else {"web_id": str(uid)}
    doc = await users_repo.find_one(filter_q) or {}
    points = doc.get("points") or doc.get("referral_points", 0)
    referral = doc.get("referral", {})
    return ApiResponse(success=True, data={"points": points, "referral": referral})
