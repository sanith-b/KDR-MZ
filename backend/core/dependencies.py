"""
FastAPI Authentication, Authorization and Request Dependencies
Ensures client-supplied IDs are NEVER trusted; identities and roles are verified via JWT.
"""
from typing import Dict, Any, Optional, List, Callable
from fastapi import HTTPException, Header, Depends, status
from backend.core.security import decode_access_token
from shared.database.repositories.users_repo import users_repo
from shared.config.settings import settings

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Extracts and cryptographically validates JWT Bearer token.
    Returns user payload dictionary containing sub, user_id, role, etc.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Bearer authorization token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization.split(" ")[1].strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Standardize user identifiers
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user identifier",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload["user_id"] = user_id
    payload["sub"] = str(user_id)
    return payload

async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """Optional user dependency for public endpoints enriched for authenticated users"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1].strip()
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("user_id") or payload.get("sub")
            if user_id:
                payload["user_id"] = user_id
                payload["sub"] = str(user_id)
                return payload
        return None
    except Exception:
        return None

def require_role(allowed_roles: List[str]) -> Callable:
    """Dependency factory checking that user holds at least one of the specified roles"""
    async def _role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = user.get("role", "user")
        # Global superadmin or admin check
        is_admin_id = False
        try:
            tg_id = int(user.get("user_id", 0))
            if tg_id in settings.ADMINS:
                is_admin_id = True
        except (ValueError, TypeError):
            pass

        if is_admin_id or user_role in allowed_roles:
            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access forbidden: required role one of {allowed_roles}, your role is '{user_role}'"
        )
    return _role_checker

# Predefined role dependencies
require_admin = require_role(["admin", "superadmin"])
require_moderator_or_admin = require_role(["moderator", "admin", "superadmin"])
require_premium = require_role(["premium", "admin", "superadmin"])

def validate_ownership(resource_owner_id: Any, current_user: Dict[str, Any]) -> bool:
    """
    Validates that the authenticated user owns the resource or has administrative rights.
    Never trusts client-supplied user identifiers.
    """
    current_uid = str(current_user.get("user_id") or current_user.get("sub"))
    target_uid = str(resource_owner_id)

    # Admin bypass check
    is_admin = current_user.get("role") in ["admin", "superadmin"]
    try:
        if int(current_user.get("user_id", 0)) in settings.ADMINS:
            is_admin = True
    except (ValueError, TypeError):
        pass

    if is_admin or current_uid == target_uid:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access forbidden: you do not have permission to access or modify this resource"
    )
