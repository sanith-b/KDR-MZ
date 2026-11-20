import datetime
import pytz
from typing import Optional, Dict, Any, List
from shared.database.connection import DatabaseConnection
from logging_helper import LOGGER

class UserRepository:
    @property
    def users(self):
        db = DatabaseConnection.get_db()
        return db.users if db is not None else None

    @property
    def premium_users(self):
        db = DatabaseConnection.get_db()
        return db.uersz if db is not None else None

    @property
    def groups(self):
        db = DatabaseConnection.get_db()
        return db.groups if db is not None else None

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        if self.users is None:
            return None
        return await self.users.find_one({"id": int(user_id)})

    async def is_premium(self, user_id: int) -> bool:
        if self.premium_users is None:
            return False
        user = await self.premium_users.find_one({"id": int(user_id)})
        if not user:
            return False
        expiry = user.get("expiry_time")
        if not expiry:
            return False
        if isinstance(expiry, datetime.datetime):
            return datetime.datetime.now() <= expiry
        return False

    async def add_premium(self, user_id: int, duration_seconds: int) -> bool:
        if self.premium_users is None:
            return False
        now = datetime.datetime.now()
        existing = await self.premium_users.find_one({"id": int(user_id)})
        current_expiry = existing.get("expiry_time") if existing else None
        
        start_time = current_expiry if (current_expiry and current_expiry > now) else now
        new_expiry = start_time + datetime.timedelta(seconds=duration_seconds)
        
        await self.premium_users.update_one(
            {"id": int(user_id)},
            {"$set": {"expiry_time": new_expiry}},
            upsert=True
        )
        return True

    async def get_group_settings(self, group_id: int, default_settings: dict) -> Dict[str, Any]:
        if self.groups is None:
            return default_settings.copy()
        chat = await self.groups.find_one({"id": int(group_id)})
        if chat and "settings" in chat:
            return chat["settings"]
        return default_settings.copy()

user_repo = UserRepository()
