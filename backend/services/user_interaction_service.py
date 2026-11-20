"""
User Interactions Service
Manages Watchlist, Favorites, Watch Progress, Search History, and Notifications.
Strictly ensures user can only view and mutate their own personal records.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from shared.database.repositories.users_repo import (
    watchlists_repo, favorites_repo, watch_progress_repo
)
from shared.database.repositories.interactions_repo import (
    search_history_repo, notifications_repo
)
from shared.database.schemas import (
    WatchlistSchema, FavoriteSchema, WatchProgressSchema, NotificationSchema
)
from shared.database.pagination import PaginationParams, PaginatedResult

class UserInteractionService:
    # -------------------------------------------------------------
    # Watchlist
    # -------------------------------------------------------------
    async def get_user_watchlist(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResult[Dict[str, Any]]:
        params = PaginationParams(page=page, page_size=page_size)
        filter_query = {"user_id": str(user_id)}
        if status_filter:
            filter_query["status"] = status_filter
        return await watchlists_repo.find_many(filter_query, pagination=params)

    async def add_to_watchlist(self, user_id: str, drama_id: str, status: str = "plan_to_watch") -> Dict[str, Any]:
        doc = {
            "user_id": str(user_id),
            "drama_id": str(drama_id),
            "status": status,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await watchlists_repo.update_one(
            {"user_id": str(user_id), "drama_id": str(drama_id)},
            {"$set": doc},
            upsert=True
        )
        return await watchlists_repo.find_one({"user_id": str(user_id), "drama_id": str(drama_id)})

    async def remove_from_watchlist(self, user_id: str, drama_id: str) -> bool:
        res = await watchlists_repo.collection.delete_one({"user_id": str(user_id), "drama_id": str(drama_id)})
        return res.deleted_count > 0

    # -------------------------------------------------------------
    # Favorites
    # -------------------------------------------------------------
    async def get_user_favorites(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResult[Dict[str, Any]]:
        params = PaginationParams(page=page, page_size=page_size)
        return await favorites_repo.find_many({"user_id": str(user_id)}, pagination=params)

    async def toggle_favorite(self, user_id: str, drama_id: str) -> Dict[str, Any]:
        existing = await favorites_repo.find_one({"user_id": str(user_id), "drama_id": str(drama_id)})
        if existing:
            await favorites_repo.collection.delete_one({"_id": existing["_id"]})
            return {"drama_id": drama_id, "is_favorite": False}
        else:
            await favorites_repo.create({
                "user_id": str(user_id),
                "drama_id": str(drama_id),
                "created_at": datetime.now(timezone.utc)
            })
            return {"drama_id": drama_id, "is_favorite": True}

    # -------------------------------------------------------------
    # Watch Progress
    # -------------------------------------------------------------
    async def get_progress(self, user_id: str, drama_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {"user_id": str(user_id)}
        if drama_id:
            query["drama_id"] = str(drama_id)
        res = await watch_progress_repo.find_many(query, PaginationParams(page_size=50))
        return res.items

    async def update_progress(
        self,
        user_id: str,
        drama_id: str,
        episode_id: str,
        season_number: int,
        episode_number: int,
        playback_position_seconds: int,
        duration_seconds: int,
        is_completed: bool = False
    ) -> Dict[str, Any]:
        doc = {
            "user_id": str(user_id),
            "drama_id": str(drama_id),
            "episode_id": str(episode_id),
            "season_number": season_number,
            "episode_number": episode_number,
            "playback_position_seconds": playback_position_seconds,
            "duration_seconds": duration_seconds,
            "is_completed": is_completed,
            "last_watched_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await watch_progress_repo.update_one(
            {"user_id": str(user_id), "episode_id": str(episode_id)},
            {"$set": doc},
            upsert=True
        )
        return doc

    # -------------------------------------------------------------
    # History
    # -------------------------------------------------------------
    async def get_user_history(self, user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        return await search_history_repo.get_user_history(str(user_id), limit=limit)

    async def clear_user_history(self, user_id: str) -> bool:
        res = await search_history_repo.collection.delete_many({"user_id": str(user_id)})
        return res.deleted_count >= 0

    # -------------------------------------------------------------
    # Notifications
    # -------------------------------------------------------------
    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResult[Dict[str, Any]]:
        params = PaginationParams(page=page, page_size=page_size)
        query: Dict[str, Any] = {"user_id": str(user_id)}
        if unread_only:
            query["status"] = "unread"
        return await notifications_repo.find_many(query, pagination=params)

    async def mark_notifications_read(
        self,
        user_id: str,
        notification_ids: Optional[List[str]] = None,
        mark_all: bool = False
    ) -> int:
        if mark_all:
            res = await notifications_repo.collection.update_many(
                {"user_id": str(user_id), "status": "unread"},
                {"$set": {"status": "read", "read_at": datetime.now(timezone.utc)}}
            )
            return res.modified_count
        elif notification_ids:
            res = await notifications_repo.collection.update_many(
                {"user_id": str(user_id), "_id": {"$in": notification_ids}},
                {"$set": {"status": "read", "read_at": datetime.now(timezone.utc)}}
            )
            return res.modified_count
        return 0

user_interaction_service = UserInteractionService()
