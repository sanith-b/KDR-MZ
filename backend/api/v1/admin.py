"""
Admin API Router (/api/v1/admin)
Comprehensive back-office management protected by role-based authorization.
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException, Depends
from backend.core.dependencies import require_admin, get_current_user
from backend.services.admin_service import admin_service
from backend.schemas.api_responses import (
    ApiResponse, PaginatedApiResponse, PaginationMetadata,
    BotSettingsUpdateRequest, WebSettingsUpdateRequest, AdminUserUpdatePayload
)
from shared.database.repositories.users_repo import users_repo
from shared.database.repositories.operations_repo import web_settings_repo
from shared.database.pagination import PaginationParams

router = APIRouter(prefix="/admin", tags=["Administration"], dependencies=[Depends(require_admin)])

@router.get("/overview", response_model=ApiResponse[Dict[str, Any]])
async def get_overview():
    """Retrieve global system metrics and entity counts"""
    data = await admin_service.get_system_overview()
    return ApiResponse(success=True, data=data)

@router.get("/users", response_model=PaginatedApiResponse[Dict[str, Any]])
async def list_users(
    query: Optional[str] = Query(None, description="Username or name search"),
    role: Optional[str] = Query(None, description="Role filter: user, premium, moderator, admin"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List and paginate platform users"""
    params = PaginationParams(page=page, page_size=page_size)
    filter_q: Dict[str, Any] = {}
    if role:
        filter_q["role"] = role
    if query:
        filter_q["$or"] = [
            {"username": {"$regex": query, "$options": "i"}},
            {"first_name": {"$regex": query, "$options": "i"}}
        ]
    res = await users_repo.find_many(filter_q, pagination=params)
    pagination = PaginationMetadata(
        page=res.page,
        page_size=res.page_size,
        total_count=res.total,
        total_pages=res.total_pages,
        has_next=res.has_next,
        has_prev=res.has_prev
    )
    return PaginatedApiResponse(data=res.items, pagination=pagination)

@router.put("/users/{user_id}", response_model=ApiResponse[Dict[str, Any]])
async def update_user(
    user_id: str,
    payload: AdminUserUpdatePayload,
    admin: Dict[str, Any] = Depends(get_current_user)
):
    """Modify user role, adjust points balance, or ban/unban user"""
    filter_q = {"telegram_id": int(user_id)} if user_id.isdigit() else {"$or": [{"web_id": user_id}, {"_id": user_id}]}
    target_user = await users_repo.find_one(filter_q)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_dict = {}
    if payload.role:
        update_dict["role"] = payload.role
    if payload.is_banned is not None:
        if payload.is_banned:
            if "telegram_id" in target_user and target_user["telegram_id"]:
                await users_repo.ban_user(target_user["telegram_id"], reason=payload.ban_reason or "Admin banned", banned_by=admin.get("user_id"))
            else:
                update_dict["ban_status"] = {"is_banned": True, "ban_reason": payload.ban_reason}
        else:
            if "telegram_id" in target_user and target_user["telegram_id"]:
                await users_repo.unban_user(target_user["telegram_id"])
            else:
                update_dict["ban_status"] = {"is_banned": False}

    if payload.points_delta is not None and "telegram_id" in target_user and target_user["telegram_id"]:
        await users_repo.update_points(target_user["telegram_id"], payload.points_delta)

    if update_dict:
        await users_repo.update_one(filter_q, update_dict)

    await admin_service.log_admin_action(
        actor_id=admin.get("user_id"),
        actor_role="admin",
        action="update_user",
        target_type="user",
        target_id=user_id,
        details=payload.model_dump(exclude_none=True)
    )

    updated = await users_repo.find_one(filter_q)
    return ApiResponse(success=True, data=updated, message="User updated successfully")

@router.get("/logs", response_model=PaginatedApiResponse[Dict[str, Any]])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """Retrieve immutable audit logs of administrative actions"""
    res = await admin_service.list_audit_logs(page=page, page_size=page_size)
    pagination = PaginationMetadata(
        page=res.page,
        page_size=res.page_size,
        total_count=res.total,
        total_pages=res.total_pages,
        has_next=res.has_next,
        has_prev=res.has_prev
    )
    return PaginatedApiResponse(data=res.items, pagination=pagination)

@router.post("/settings/bot", response_model=ApiResponse[Dict[str, Any]])
async def update_bot_setting(
    payload: BotSettingsUpdateRequest,
    admin: Dict[str, Any] = Depends(get_current_user)
):
    """Update a Telegram Bot operational setting"""
    result = await admin_service.update_bot_setting(
        key=payload.key, value=payload.value, admin_id=admin.get("user_id")
    )
    return ApiResponse(success=True, data=result, message="Bot setting updated")

@router.post("/settings/web", response_model=ApiResponse[Dict[str, Any]])
async def update_web_setting(
    payload: WebSettingsUpdateRequest,
    admin: Dict[str, Any] = Depends(get_current_user)
):
    """Update Web Portal configuration and announcement banner"""
    data = payload.model_dump(exclude_none=True)
    await web_settings_repo.update_one({}, data, upsert=True)
    await admin_service.log_admin_action(
        actor_id=admin.get("user_id"),
        actor_role="admin",
        action="update_web_settings",
        target_type="setting",
        target_id="web_settings",
        details=data
    )
    return ApiResponse(success=True, data=data, message="Web settings updated")
