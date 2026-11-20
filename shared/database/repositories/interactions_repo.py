"""
Search History, Search Logs, Notifications, and AI Conversations Repositories
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from shared.database.repositories.base import BaseRepository
from shared.database.schemas import (
    SearchHistorySchema, SearchLogSchema,
    NotificationSchema, AIConversationSchema, AIMessage
)
from shared.database.pagination import PaginationParams, PaginatedResult

class SearchHistoryRepository(BaseRepository[SearchHistorySchema]):
    def __init__(self):
        super().__init__("search_history", SearchHistorySchema)

    async def record_search(
        self,
        query: str,
        user_id: Optional[str] = None,
        telegram_id: Optional[int] = None,
        platform: str = "telegram",
        result_count: int = 0
    ) -> Dict[str, Any]:
        doc = SearchHistorySchema(
            query=query.strip(),
            user_id=user_id,
            telegram_id=telegram_id,
            platform=platform,
            result_count=result_count
        )
        return await self.create(doc)

    async def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)


class SearchLogRepository(BaseRepository[SearchLogSchema]):
    def __init__(self):
        super().__init__("search_logs", SearchLogSchema)

    async def log_query(self, query: str, successful: bool = True) -> None:
        normalized = query.strip().lower()
        if not normalized:
            return
        await self.collection.update_one(
            {"normalized_query": normalized},
            {
                "$set": {"query": query.strip(), "successful": successful, "last_searched_at": datetime.utcnow()},
                "$inc": {"hit_count": 1}
            },
            upsert=True
        )

    async def get_trending_queries(self, limit: int = 30) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"successful": True}).sort("hit_count", -1).limit(limit)
        return await cursor.to_list(length=limit)


class NotificationRepository(BaseRepository[NotificationSchema]):
    def __init__(self):
        super().__init__("notifications", NotificationSchema)

    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notif_type: str = "system_alert",
        telegram_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        notif = NotificationSchema(
            user_id=user_id,
            telegram_id=telegram_id,
            title=title,
            message=message,
            type=notif_type,
            metadata=metadata or {}
        )
        return await self.create(notif)

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResult[Dict[str, Any]]:
        filter_query = {"user_id": user_id}
        if unread_only:
            filter_query["status"] = "unread"
        return await self.find_many(filter_query, pagination)

    async def mark_as_read(self, notification_id: str) -> bool:
        return await self.update_one(
            {"notification_id": notification_id},
            {"status": "read", "read_at": datetime.utcnow()}
        )


class AIConversationRepository(BaseRepository[AIConversationSchema]):
    def __init__(self):
        super().__init__("ai_conversations", AIConversationSchema)

    async def get_or_create(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        telegram_id: Optional[int] = None,
        platform: str = "telegram"
    ) -> Dict[str, Any]:
        existing = await self.find_one({"conversation_id": conversation_id})
        if existing:
            return existing
        convo = AIConversationSchema(
            conversation_id=conversation_id,
            user_id=user_id,
            telegram_id=telegram_id,
            platform=platform
        )
        return await self.create(convo)

    async def append_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        suggested_drama_ids: Optional[List[str]] = None
    ) -> bool:
        msg = AIMessage(
            role=role,
            content=content,
            suggested_drama_ids=suggested_drama_ids or []
        ).model_dump()
        result = await self.collection.update_one(
            {"conversation_id": conversation_id},
            {
                "$push": {"messages": msg},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0


search_history_repo = SearchHistoryRepository()
search_logs_repo = SearchLogRepository()
notifications_repo = NotificationRepository()
ai_conversations_repo = AIConversationRepository()
