"""
Generic Async Base Repository for MongoDB operations in My K-Drama 2.0
"""
from typing import Generic, TypeVar, Optional, List, Dict, Any, Type
from datetime import datetime, timezone
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError as MongoDuplicateKeyError
from shared.database.connection import DatabaseConnection
from shared.database.pagination import PaginationParams, PaginatedResult
from shared.database.errors import DuplicateKeyError, DocumentNotFoundError, DatabaseError
from logging_helper import LOGGER

T = TypeVar("T", bound=BaseModel)

class BaseRepository(Generic[T]):
    def __init__(self, collection_name: str, schema_cls: Optional[Type[T]] = None):
        self.collection_name = collection_name
        self.schema_cls = schema_cls
        self._collection = None

    @property
    def collection(self):
        if self._collection is not None:
            return self._collection
        db = DatabaseConnection.get_db()
        if db is None:
            raise DatabaseError("Database connection is not initialized.")
        return db[self.collection_name]

    async def create(self, data: T | Dict[str, Any]) -> Dict[str, Any]:
        """Insert a validated document and return the stored dictionary"""
        if isinstance(data, BaseModel):
            doc = data.model_dump(by_alias=True)
        else:
            doc = data.copy()

        now = datetime.now(timezone.utc)
        if "created_at" not in doc or not doc["created_at"]:
            doc["created_at"] = now
        if "updated_at" not in doc or not doc["updated_at"]:
            doc["updated_at"] = now

        try:
            result = await self.collection.insert_one(doc)
            if "_id" not in doc and hasattr(result, "inserted_id"):
                doc["_id"] = result.inserted_id
            return doc
        except MongoDuplicateKeyError as e:
            raise DuplicateKeyError(
                f"Duplicate key violation in [{self.collection_name}]: {str(e)}",
                details={"collection": self.collection_name, "error": str(e)}
            )
        except Exception as e:
            raise DatabaseError(f"Insert error in [{self.collection_name}]: {str(e)}")

    async def find_by_id(self, doc_id: str | int) -> Optional[Dict[str, Any]]:
        """Find a document by its _id"""
        return await self.collection.find_one({"_id": doc_id})

    # Convenient alias
    get_by_id = find_by_id

    async def find_one(self, filter_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the filter"""
        return await self.collection.find_one(filter_query)

    async def find_many(
        self,
        filter_query: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
        sort: Optional[List[tuple]] = None
    ) -> PaginatedResult[Dict[str, Any]]:
        """Find paginated documents with total count"""
        filter_query = filter_query or {}
        params = pagination or PaginationParams()
        sort_spec = sort or [(params.sort_by, params.sort_direction)]

        total = await self.collection.count_documents(filter_query)
        cursor = self.collection.find(filter_query).sort(sort_spec).skip(params.skip).limit(params.limit)
        items = await cursor.to_list(length=params.limit)

        return PaginatedResult.create(items=items, total=total, params=params)

    async def update_by_id(self, doc_id: str | int, update_data: Dict[str, Any]) -> bool:
        """Update an existing document by _id"""
        update_data = update_data.copy()
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = await self.collection.update_one(
            {"_id": doc_id},
            {"$set": update_data}
        )
        return result.matched_count > 0

    async def update_one(self, filter_query: Dict[str, Any], update_data: Dict[str, Any], upsert: bool = False) -> bool:
        """Update a document matching filter query"""
        update_data = update_data.copy()
        update_data["updated_at"] = datetime.now(timezone.utc)
        try:
            result = await self.collection.update_one(
                filter_query,
                {"$set": update_data},
                upsert=upsert
            )
            return (result.matched_count > 0) or (result.upserted_id is not None)
        except MongoDuplicateKeyError as e:
            raise DuplicateKeyError(f"Duplicate key on update in [{self.collection_name}]: {str(e)}")

    async def delete_by_id(self, doc_id: str | int) -> bool:
        """Delete document by _id"""
        result = await self.collection.delete_one({"_id": doc_id})
        return result.deleted_count > 0

    async def delete_many(self, filter_query: Dict[str, Any]) -> int:
        """Delete documents matching filter query"""
        result = await self.collection.delete_many(filter_query)
        return result.deleted_count

    async def count(self, filter_query: Optional[Dict[str, Any]] = None) -> int:
        """Count total matching documents"""
        return await self.collection.count_documents(filter_query or {})
