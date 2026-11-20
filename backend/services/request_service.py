"""
K-Drama Requests & Upvoting Service
Manages user drama requests, community upvoting, and admin fulfillment workflows.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from shared.database.repositories.requests_repo import drama_requests_repo, request_votes_repo
from shared.database.pagination import PaginationParams, PaginatedResult
from shared.services.tmdb import tmdb

class RequestService:
    async def create_request(
        self,
        user_id: Any,
        title: str,
        tmdb_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit a new drama request, enriching with TMDb details if available"""
        drama_title = title.strip()
        poster_url = None
        if tmdb_id:
            details = await tmdb.get_drama_details(tmdb_id)
            if details:
                drama_title = details.get("name") or drama_title
                poster_url = details.get("poster_path")

        # Check existing request by title
        existing = await drama_requests_repo.find_one({"title": {"$regex": f"^{drama_title}$", "$options": "i"}})
        if existing:
            # If already requested, automatically vote for it instead
            await self.vote_request(existing["_id"], user_id)
            return {
                "message": "This drama was already requested. Your vote has been added!",
                "request": existing,
                "already_existed": True
            }

        doc = {
            "title": drama_title,
            "tmdb_id": tmdb_id,
            "requested_by": user_id,
            "user_id": str(user_id),
            "status": "pending",
            "votes_count": 1,
            "vote_count": 1,
            "notes": notes,
            "poster_url": poster_url,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        created = await drama_requests_repo.create(doc)
        # Register user vote
        await request_votes_repo.create({
            "request_id": str(created["_id"]),
            "user_id": str(user_id),
            "created_at": datetime.now(timezone.utc)
        })
        return {"message": "Drama request submitted successfully", "request": created, "already_existed": False}

    async def vote_request(self, request_id: str, user_id: Any) -> Dict[str, Any]:
        """Upvotes a drama request. Prevents duplicate votes per user"""
        has_voted = await request_votes_repo.find_one({
            "request_id": str(request_id),
            "user_id": str(user_id)
        })
        if has_voted:
            raise HTTPException(status_code=400, detail="You have already voted for this request")

        await request_votes_repo.create({
            "request_id": str(request_id),
            "user_id": str(user_id),
            "created_at": datetime.now(timezone.utc)
        })
        updated = await drama_requests_repo.upvote(request_id)
        return {"success": True, "request": updated}

    async def get_my_requests(self, user_id: Any, page: int = 1, page_size: int = 20) -> PaginatedResult[Dict[str, Any]]:
        params = PaginationParams(page=page, page_size=page_size)
        return await drama_requests_repo.find_many(
            {"$or": [{"user_id": str(user_id)}, {"requested_by": user_id}]},
            pagination=params
        )

    async def list_requests(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResult[Dict[str, Any]]:
        params = PaginationParams(page=page, page_size=page_size, sort_by="votes_count", sort_direction=-1)
        query = {"status": status} if status else {}
        return await drama_requests_repo.find_many(query, pagination=params)

    async def update_request_status(
        self,
        request_id: str,
        status: str,
        admin_id: Any,
        notes: Optional[str] = None
    ) -> bool:
        return await drama_requests_repo.update_status(
            request_id=request_id,
            status=status,
            admin_id=str(admin_id),
            notes=notes
        )

request_service = RequestService()
