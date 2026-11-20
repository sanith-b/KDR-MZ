"""
Groups, Bot Settings, Web Settings, Payments, and Audit Logs Repositories
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from shared.database.repositories.base import BaseRepository
from shared.database.schemas import (
    GroupSchema, BotSettingsSchema, WebSettingsSchema,
    PaymentSchema, AuditLogSchema
)
from shared.database.pagination import PaginationParams, PaginatedResult

class GroupRepository(BaseRepository[GroupSchema]):
    def __init__(self):
        super().__init__("groups", GroupSchema)

    async def get_by_group_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        return await self.find_one({"group_id": int(group_id)})

    async def upsert_group(
        self,
        group_id: int,
        title: str,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        existing = await self.get_by_group_id(group_id)
        if existing:
            update_data = {
                "title": title or existing.get("title", ""),
                "username": username if username is not None else existing.get("username"),
                "updated_at": datetime.utcnow()
            }
            await self.update_one({"group_id": int(group_id)}, update_data)
            existing.update(update_data)
            return existing

        grp = GroupSchema(
            group_id=int(group_id),
            title=title,
            username=username
        )
        return await self.create(grp)

    async def get_group_settings(self, group_id: int, default_settings: Optional[dict] = None) -> Dict[str, Any]:
        grp = await self.get_by_group_id(group_id)
        if grp and "settings" in grp:
            return grp["settings"]
        return (default_settings or {}).copy()

    async def update_group_setting(self, group_id: int, key: str, value: Any) -> bool:
        result = await self.collection.update_one(
            {"group_id": int(group_id)},
            {
                "$set": {
                    f"settings.{key}": value,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None


class BotSettingsRepository(BaseRepository[BotSettingsSchema]):
    def __init__(self):
        super().__init__("bot_settings", BotSettingsSchema)

    async def get_bot_settings(self, bot_id: int) -> Dict[str, Any]:
        doc = await self.find_one({"bot_id": int(bot_id)})
        if not doc:
            new_settings = BotSettingsSchema(bot_id=int(bot_id))
            return await self.create(new_settings)
        return doc

    async def set_toggle(self, bot_id: int, key: str, value: Any) -> bool:
        return await self.update_one(
            {"bot_id": int(bot_id)},
            {key: value, "updated_at": datetime.utcnow()},
            upsert=True
        )


class WebSettingsRepository(BaseRepository[WebSettingsSchema]):
    def __init__(self):
        super().__init__("web_settings", WebSettingsSchema)

    async def get_web_settings(self) -> Dict[str, Any]:
        doc = await self.find_one({"_id": "global_web_settings"})
        if not doc:
            new_settings = WebSettingsSchema()
            return await self.create(new_settings)
        return doc

    async def update_web_settings(self, settings_dict: Dict[str, Any]) -> bool:
        return await self.update_one(
            {"_id": "global_web_settings"},
            settings_dict,
            upsert=True
        )


class PaymentRepository(BaseRepository[PaymentSchema]):
    def __init__(self):
        super().__init__("payments", PaymentSchema)

    async def record_payment(
        self,
        user_id: str,
        amount: float,
        currency: str = "XTR",
        method: str = "telegram_stars",
        plan_id: str = "1month",
        telegram_id: Optional[int] = None,
        tx_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        pay = PaymentSchema(
            user_id=user_id,
            telegram_id=telegram_id,
            amount=amount,
            currency=currency,
            method=method,
            plan_id=plan_id,
            status="pending",
            telegram_payment_charge_id=tx_reference if method == "telegram_stars" else None,
            crypto_tx_hash=tx_reference if method.startswith("crypto_") else None
        )
        return await self.create(pay)

    async def mark_payment_completed(self, payment_id: str) -> bool:
        return await self.update_one(
            {"payment_id": payment_id},
            {"status": "completed", "updated_at": datetime.utcnow()}
        )


class AuditLogRepository(BaseRepository[AuditLogSchema]):
    def __init__(self):
        super().__init__("audit_logs", AuditLogSchema)

    async def log_action(
        self,
        actor_id: str,
        actor_role: str,
        action: str,
        target_type: str = "user",
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        log = AuditLogSchema(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
            ip_address=ip_address
        )
        return await self.create(log)


groups_repo = GroupRepository()
bot_settings_repo = BotSettingsRepository()
web_settings_repo = WebSettingsRepository()
payments_repo = PaymentRepository()
audit_logs_repo = AuditLogRepository()
