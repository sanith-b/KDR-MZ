"""
Administration, System Settings, Audit Logging & Analytics Service
Protected service layer for administrative operations.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from shared.database.repositories.users_repo import users_repo, subscriptions_repo
from shared.database.repositories.dramas_repo import dramas_repo, telegram_files_repo
from shared.database.repositories.requests_repo import drama_requests_repo
from shared.database.repositories.interactions_repo import search_logs_repo
from shared.database.repositories.operations_repo import (
    bot_settings_repo, web_settings_repo, audit_logs_repo, groups_repo
)
from shared.database.pagination import PaginationParams, PaginatedResult

class AdminService:
    async def get_system_overview(self) -> Dict[str, Any]:
        """Aggregate high-level system statistics for admin dashboard"""
        total_users = await users_repo.count({})
        total_dramas = await dramas_repo.count({})
        total_files = await telegram_files_repo.count({})
        total_requests = await drama_requests_repo.count({})
        pending_requests = await drama_requests_repo.count({"status": "pending"})
        total_groups = await groups_repo.count({})

        return {
            "users_count": total_users,
            "dramas_count": total_dramas,
            "files_count": total_files,
            "groups_count": total_groups,
            "requests_count": total_requests,
            "pending_requests_count": pending_requests,
            "server_timestamp": datetime.now(timezone.utc)
        }

    async def log_admin_action(
        self,
        actor_id: Any,
        actor_role: str,
        action: str,
        target_type: str,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Append an immutable audit log entry"""
        await audit_logs_repo.create({
            "actor_id": str(actor_id),
            "actor_role": actor_role,
            "action": action,
            "target_type": target_type,
            "target_id": str(target_id) if target_id else None,
            "details": details or {},
            "created_at": datetime.now(timezone.utc)
        })

    async def list_audit_logs(self, page: int = 1, page_size: int = 50) -> PaginatedResult[Dict[str, Any]]:
        params = PaginationParams(page=page, page_size=page_size, sort_by="created_at", sort_direction=-1)
        return await audit_logs_repo.find_many({}, pagination=params)

    async def update_bot_setting(self, key: str, value: Any, admin_id: Any) -> Dict[str, Any]:
        """Update a key-value setting for the Telegram Bot"""
        await bot_settings_repo.update_one(
            {"key": key},
            {"$set": {"key": key, "value": value, "updated_at": datetime.now(timezone.utc)}},
            upsert=True
        )
        await self.log_admin_action(
            actor_id=admin_id,
            actor_role="admin",
            action="update_bot_setting",
            target_type="setting",
            target_id=key,
            details={"value": value}
        )
        return {"key": key, "value": value}

    async def get_search_analytics(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Top queries by frequency from search logs"""
        cursor = search_logs_repo.collection.find({}).sort("hit_count", -1).limit(limit)
        return await cursor.to_list(length=limit)

admin_service = AdminService()
