import datetime
import uuid
from typing import List, Dict, Any, Optional
from shared.database.connection import DatabaseConnection
from shared.config.settings import settings
from logging_helper import LOGGER

class KDramaRepository:
    @property
    def col(self):
        db = DatabaseConnection.get_db()
        return db.kdrama_requests if db is not None else None

    async def create_request(self, user_id: int, user_name: str, drama_name: str, details: Optional[str] = None) -> Dict[str, Any]:
        req_id = f"kd_{uuid.uuid4().hex[:8]}"
        doc = {
            "request_id": req_id,
            "user_id": user_id,
            "user_name": user_name,
            "drama_name": drama_name.strip(),
            "details": details,
            "status": "pending",
            "created_at": datetime.datetime.utcnow(),
            "admin_notes": None,
            "processed_by": None
        }
        if self.col is not None:
            await self.col.insert_one(doc)
        return doc

    async def get_user_requests(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        if self.col is None:
            return []
        cursor = self.col.find({"user_id": int(user_id)}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_pending_requests(self, limit: int = 50) -> List[Dict[str, Any]]:
        if self.col is None:
            return []
        cursor = self.col.find({"status": "pending"}).sort("created_at", 1).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_status(self, request_id: str, status: str, admin_id: int, notes: Optional[str] = None) -> bool:
        if self.col is None:
            return False
        result = await self.col.update_one(
            {"request_id": request_id},
            {
                "$set": {
                    "status": status,
                    "processed_by": admin_id,
                    "processed_at": datetime.datetime.utcnow(),
                    "admin_notes": notes
                }
            }
        )
        return result.modified_count > 0

kdrama_repo = KDramaRepository()
