"""
User, Admin, Subscription, Watchlist, Favorite and Progress Repositories
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from shared.database.repositories.base import BaseRepository
from shared.database.schemas import (
    UserSchema, AdminSchema, SubscriptionSchema,
    WatchlistSchema, FavoriteSchema, WatchProgressSchema
)
from shared.database.pagination import PaginationParams, PaginatedResult

class UserRepository(BaseRepository[UserSchema]):
    def __init__(self):
        super().__init__("users", UserSchema)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        return await self.find_one({"telegram_id": int(telegram_id)})

    async def get_by_web_id(self, web_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"web_id": web_id})

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"email": email.lower().strip()})

    async def upsert_telegram_user(
        self,
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Atomic upsert for Telegram user registration without duplicates"""
        existing = await self.get_by_telegram_id(telegram_id)
        if existing:
            update_data = {
                "first_name": first_name or existing.get("first_name", ""),
                "last_name": last_name if last_name is not None else existing.get("last_name"),
                "username": username if username is not None else existing.get("username"),
                "updated_at": datetime.now(timezone.utc)
            }
            await self.update_one({"telegram_id": int(telegram_id)}, update_data)
            existing.update(update_data)
            return existing

        user = UserSchema(
            telegram_id=int(telegram_id),
            first_name=first_name or "",
            last_name=last_name,
            username=username,
            auth_provider="telegram"
        )
        return await self.create(user)

    async def update_points(self, telegram_id: int, delta: int) -> Optional[Dict[str, Any]]:
        """Atomically increments or decrements user referral/activity points"""
        await self.collection.update_one(
            {"telegram_id": int(telegram_id)},
            {"$inc": {"referral_points": delta, "points": delta}, "$set": {"updated_at": datetime.now(timezone.utc)}}
        )
        return await self.get_by_telegram_id(telegram_id)

    async def ban_user(self, telegram_id: int, reason: str = "No Reason", banned_by: Optional[int] = None) -> bool:
        update_data = {
            "is_banned": True,
            "ban_reason": reason,
            "ban_status": {
                "is_banned": True,
                "ban_reason": reason,
                "banned_at": datetime.now(timezone.utc),
                "banned_by": banned_by
            }
        }
        return await self.update_one({"telegram_id": int(telegram_id)}, update_data)

    async def unban_user(self, telegram_id: int) -> bool:
        update_data = {
            "is_banned": False,
            "ban_reason": "",
            "ban_status": {
                "is_banned": False,
                "ban_reason": "",
                "banned_at": None,
                "banned_by": None
            }
        }
        return await self.update_one({"telegram_id": int(telegram_id)}, update_data)


class AdminRepository(BaseRepository[AdminSchema]):
    def __init__(self):
        super().__init__("admins", AdminSchema)

    async def is_admin(self, telegram_id: int) -> bool:
        admin = await self.find_one({"telegram_id": int(telegram_id), "is_active": True})
        return bool(admin)

    async def add_admin(
        self,
        user_id: str,
        telegram_id: Optional[int] = None,
        role: str = "moderator",
        permissions: Optional[List[str]] = None,
        added_by: Optional[str] = None
    ) -> Dict[str, Any]:
        permissions = permissions or ["manage_requests", "view_analytics"]
        doc = {
            "user_id": user_id,
            "telegram_id": int(telegram_id) if telegram_id else None,
            "role": role,
            "permissions": permissions,
            "added_by": added_by,
            "is_active": True,
            "updated_at": datetime.utcnow()
        }
        await self.update_one({"user_id": user_id}, doc, upsert=True)
        return doc


class SubscriptionRepository(BaseRepository[SubscriptionSchema]):
    def __init__(self):
        super().__init__("subscriptions", SubscriptionSchema)

    async def get_active_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        now = datetime.utcnow()
        return await self.find_one({
            "user_id": user_id,
            "status": "active",
            "expiry_date": {"$gt": now}
        })

    async def grant_subscription(
        self,
        user_id: str,
        duration_seconds: int,
        plan_id: str = "1month",
        tier: str = "premium",
        telegram_id: Optional[int] = None,
        is_trial: bool = False
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        active = await self.get_active_subscription(user_id)
        start_date = active["expiry_date"] if active else now
        expiry_date = start_date + timedelta(seconds=duration_seconds)

        sub = SubscriptionSchema(
            user_id=user_id,
            telegram_id=telegram_id,
            plan_id=plan_id,
            tier=tier,
            status="active",
            start_date=start_date,
            expiry_date=expiry_date,
            is_trial=is_trial
        )
        return await self.create(sub)

    async def get_expired(self, current_time: datetime) -> List[Dict[str, Any]]:
        cursor = self.collection.find({
            "status": "active",
            "expiry_date": {"$lte": current_time}
        })
        return await cursor.to_list(length=100)


class WatchlistRepository(BaseRepository[WatchlistSchema]):
    def __init__(self):
        super().__init__("watchlists", WatchlistSchema)

    async def set_watchlist_item(self, user_id: str, drama_id: str, status: str = "plan_to_watch") -> Dict[str, Any]:
        doc = {
            "user_id": user_id,
            "drama_id": drama_id,
            "status": status,
            "updated_at": datetime.utcnow()
        }
        await self.update_one({"user_id": user_id, "drama_id": drama_id}, doc, upsert=True)
        return doc

    async def get_user_watchlist(
        self,
        user_id: str,
        status: Optional[str] = None,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResult[Dict[str, Any]]:
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        return await self.find_many(query, pagination)


class FavoriteRepository(BaseRepository[FavoriteSchema]):
    def __init__(self):
        super().__init__("favorites", FavoriteSchema)

    async def toggle_favorite(self, user_id: str, drama_id: str) -> bool:
        """Toggle favorite status. Returns True if favorited, False if removed."""
        existing = await self.find_one({"user_id": user_id, "drama_id": drama_id})
        if existing:
            await self.delete_by_id(existing["_id"])
            return False
        fav = FavoriteSchema(user_id=user_id, drama_id=drama_id)
        await self.create(fav)
        return True

    async def is_favorite(self, user_id: str, drama_id: str) -> bool:
        return bool(await self.find_one({"user_id": user_id, "drama_id": drama_id}))


class WatchProgressRepository(BaseRepository[WatchProgressSchema]):
    def __init__(self):
        super().__init__("watch_progress", WatchProgressSchema)

    async def save_progress(
        self,
        user_id: str,
        drama_id: str,
        episode_id: str,
        progress_seconds: int,
        total_seconds: int,
        device_info: Optional[str] = None
    ) -> Dict[str, Any]:
        percentage = round((progress_seconds / total_seconds) * 100, 2) if total_seconds > 0 else 0.0
        completed = percentage >= 90.0

        doc = {
            "user_id": user_id,
            "drama_id": drama_id,
            "episode_id": episode_id,
            "progress_seconds": progress_seconds,
            "total_seconds": total_seconds,
            "percentage": percentage,
            "completed": completed,
            "device_info": device_info,
            "last_watched_at": datetime.utcnow()
        }
        await self.update_one({"user_id": user_id, "episode_id": episode_id}, doc, upsert=True)
        return doc

    async def get_progress(self, user_id: str, episode_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"user_id": user_id, "episode_id": episode_id})


users_repo = UserRepository()
admins_repo = AdminRepository()
subscriptions_repo = SubscriptionRepository()
watchlists_repo = WatchlistRepository()
favorites_repo = FavoriteRepository()
watch_progress_repo = WatchProgressRepository()
