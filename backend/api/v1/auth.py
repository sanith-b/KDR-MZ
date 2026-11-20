"""
Authentication API Router (/api/v1/auth)
Supports Telegram Login Widget & Web Email/Password registration and login.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from backend.core.security import decode_access_token
from backend.core.dependencies import get_current_user
from backend.core.rate_limiter import RateLimiter
from backend.services.auth_service import auth_service
from backend.schemas.api_responses import (
    TelegramAuthPayload, WebLoginPayload, WebRegisterPayload, TokenResponse, ApiResponse
)
from shared.database.repositories.users_repo import users_repo

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_limiter = RateLimiter(requests_per_minute=20, key_prefix="rate_auth")

@router.post("/telegram", response_model=ApiResponse[Dict[str, Any]], dependencies=[Depends(auth_limiter)])
async def telegram_login(payload: TelegramAuthPayload):
    """Authenticate via Telegram Login Widget hash verification"""
    result = await auth_service.authenticate_telegram(payload.model_dump(exclude_none=True))
    return ApiResponse(success=True, data=result, message="Telegram login successful")

@router.post("/register", response_model=ApiResponse[Dict[str, Any]], dependencies=[Depends(auth_limiter)])
async def register(payload: WebRegisterPayload):
    """Register a new web user with email, username and password"""
    result = await auth_service.register_web_user(payload.model_dump())
    return ApiResponse(success=True, data=result, message="Registration successful")

@router.post("/login", response_model=ApiResponse[Dict[str, Any]], dependencies=[Depends(auth_limiter)])
async def login(payload: WebLoginPayload):
    """Log in using web credentials (email/username + password)"""
    result = await auth_service.login_web_user(payload.email_or_username, payload.password)
    return ApiResponse(success=True, data=result, message="Login successful")

@router.get("/me", response_model=ApiResponse[Dict[str, Any]])
async def get_my_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve profile and preferences of the authenticated user"""
    uid = current_user.get("user_id")
    # Fetch latest profile from DB
    user_doc = None
    try:
        tg_id = int(uid)
        user_doc = await users_repo.get_by_telegram_id(tg_id)
    except (ValueError, TypeError):
        user_doc = await users_repo.get_by_web_id(str(uid))

    if not user_doc:
        user_doc = current_user

    # Strip sensitive fields
    user_clean = {k: v for k, v in user_doc.items() if k not in ["password_hash", "_legacy_id"]}
    return ApiResponse(success=True, data=user_clean)
