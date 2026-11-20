"""
Drama Requests and Request Votes Repositories for My K-Drama 2.0
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from shared.database.repositories.base import BaseRepository
from shared.database.schemas import DramaRequestSchema, RequestVoteSchema
from shared.database.pagination import PaginationParams, PaginatedResult
from shared.database.errors import DuplicateKeyError

class DramaRequestRepository(BaseRepository[DramaRequestSchema]):
    def __init__(self):
        super().__init__("drama_requests", DramaRequestSchema)

    async def get_by_request_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"request_id": request_id})

    async def get_user_requests(
        self,
        user_id: str,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResult[Dict[str, Any]]:
        return await self.find_many({"user_id": user_id}, pagination)

    async def get_pending_requests(
        self,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResult[Dict[str, Any]]:
        params = pagination or PaginationParams(sort_by="vote_count", sort_direction=-1)
        return await self.find_many({"status": "pending"}, params)

    async def update_status(
        self,
        request_id: str,
        status: str,
        admin_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        update_data = {
            "status": status,
            "processed_by": admin_id,
            "processed_at": datetime.now(timezone.utc),
            "admin_notes": notes
        }
        res = await self.update_by_id(request_id, update_data)
        if not res:
            res = await self.update_one({"request_id": request_id}, update_data)
        return res

    async def upvote(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Atomically increments request vote count and returns updated doc"""
        await self.collection.update_one(
            {"_id": request_id},
            {"$inc": {"vote_count": 1, "votes_count": 1}, "$set": {"updated_at": datetime.now(timezone.utc)}}
        )
        return await self.get_by_id(request_id)

    async def increment_votes(self, request_id: str) -> bool:
        result = await self.collection.update_one(
            {"request_id": request_id},
            {"$inc": {"vote_count": 1, "votes_count": 1}, "$set": {"updated_at": datetime.now(timezone.utc)}}
        )
        return result.modified_count > 0


class RequestVoteRepository(BaseRepository[RequestVoteSchema]):
    def __init__(self):
        super().__init__("request_votes", RequestVoteSchema)

    async def vote(self, request_id: str, user_id: str) -> bool:
        """Atomic upvote: prevents duplicate voting per user per request"""
        vote_doc = RequestVoteSchema(request_id=request_id, user_id=user_id)
        try:
            await self.create(vote_doc)
            return True
        except DuplicateKeyError:
            return False

    async def has_voted(self, request_id: str, user_id: str) -> bool:
        return bool(await self.find_one({"request_id": request_id, "user_id": user_id}))


drama_requests_repo = DramaRequestRepository()
request_votes_repo = RequestVoteRepository()
