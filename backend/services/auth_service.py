"""
Authentication & Authorization Business Logic Service
"""
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from backend.core.security import (
    verify_telegram_auth, create_access_token, hash_password, verify_password
)
from shared.database.repositories.users_repo import users_repo, admins_repo
from shared.database.schemas import UserSchema
from shared.config.settings import settings
from logging_helper import LOGGER

class AuthService:
    async def authenticate_telegram(self, payload_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Validates Telegram widget hash and returns user + JWT token"""
        user_id = payload_dict.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing Telegram user id")

        # Verify signature
        if not verify_telegram_auth(payload_dict):
            # Development fallback for configured admins when bot token not set
            if not settings.BOT_TOKEN and user_id in settings.ADMINS:
                LOGGER.warning(f"Telegram signature bypassed for admin {user_id} in dev mode.")
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Telegram authentication cryptographic signature"
                )

        # Upsert user record in shared MongoDB
        first_name = payload_dict.get("first_name", "")
        last_name = payload_dict.get("last_name")
        username = payload_dict.get("username")

        user_doc = await users_repo.upsert_telegram_user(
            telegram_id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username
        )

        is_admin = user_id in settings.ADMINS or user_doc.get("role") in ["admin", "superadmin"]
        role = "admin" if is_admin else user_doc.get("role", "user")

        token_payload = {
            "sub": str(user_id),
            "user_id": user_id,
            "telegram_id": user_id,
            "name": first_name,
            "username": username,
            "role": role
        }
        token = create_access_token(token_payload)

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "user": {
                "id": user_id,
                "telegram_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "role": role,
                "points": user_doc.get("points") or user_doc.get("referral_points", 0)
            }
        }

    async def register_web_user(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Registers a web user with email/username and hashed password"""
        username = payload.get("username", "").strip()
        email = payload.get("email", "").strip().lower()
        password = payload.get("password", "")

        # Check existing username or email
        existing_username = await users_repo.find_one({"username": username})
        if existing_username:
            raise HTTPException(status_code=409, detail="Username is already taken")

        existing_email = await users_repo.get_by_email(email)
        if existing_email:
            raise HTTPException(status_code=409, detail="Email is already registered")

        web_id = str(uuid.uuid4())
        hashed_pw = hash_password(password)

        new_user = UserSchema(
            web_id=web_id,
            email=email,
            username=username,
            first_name=payload.get("first_name") or username,
            last_name=payload.get("last_name"),
            auth_provider="email"
        )
        user_dict = new_user.model_dump(by_alias=True)
        user_dict["password_hash"] = hashed_pw

        created = await users_repo.create(user_dict)

        token_payload = {
            "sub": web_id,
            "user_id": web_id,
            "email": email,
            "username": username,
            "role": "user"
        }
        token = create_access_token(token_payload)

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "user": {
                "id": web_id,
                "email": email,
                "username": username,
                "role": "user"
            }
        }

    async def login_web_user(self, identifier: str, password: str) -> Dict[str, Any]:
        """Authenticates web user by email or username"""
        user = await users_repo.find_one({"$or": [{"email": identifier.lower()}, {"username": identifier}]})
        if not user or not user.get("password_hash"):
            raise HTTPException(status_code=401, detail="Invalid username/email or password")

        if not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid username/email or password")

        user_id = user.get("web_id") or user.get("telegram_id") or str(user.get("_id"))
        role = user.get("role", "user")

        token_payload = {
            "sub": str(user_id),
            "user_id": user_id,
            "username": user.get("username"),
            "role": role
        }
        token = create_access_token(token_payload)

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "user": {
                "id": user_id,
                "email": user.get("email"),
                "username": user.get("username"),
                "role": role
            }
        }

auth_service = AuthService()
