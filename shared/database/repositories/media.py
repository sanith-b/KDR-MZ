import re
from typing import List, Tuple, Optional, Dict, Any
from shared.database.connection import DatabaseConnection
from shared.config.settings import settings
from logging_helper import LOGGER

class MediaRepository:
    def __init__(self):
        pass

    @property
    def collection(self):
        db = DatabaseConnection.get_db()
        return db[settings.COLLECTION_NAME] if db is not None else None

    @property
    def secondary_collection(self):
        db2 = DatabaseConnection.get_secondary_db()
        return db2[settings.COLLECTION_NAME] if db2 is not None else None

    async def get_search_results(
        self,
        query: str,
        max_results: int = 10,
        offset: int = 0,
        file_type: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], str, int]:
        """Search media files with regex on file_name and caption with pagination"""
        if self.collection is None:
            return [], "", 0

        query = query.strip()
        if not query:
            raw_pattern = '.'
        elif ' ' not in query:
            raw_pattern = r"(\b|[\.\+\-_])" + re.escape(query) + r"(\b|[\.\+\-_])"
        else:
            raw_pattern = query.replace(" ", r".*[\s\.\+\-_()\[\]]")

        try:
            regex = re.compile(raw_pattern, flags=re.IGNORECASE)
        except Exception:
            return [], "", 0

        filter_query = {
            '$or': [{'file_name': regex}, {'caption': regex}]
        }
        if file_type:
            filter_query['file_type'] = file_type

        total_results = await self.collection.count_documents(filter_query)
        if self.secondary_collection is not None:
            total_results += await self.secondary_collection.count_documents(filter_query)

        cursor = self.collection.find(filter_query).sort("_id", -1).skip(offset).limit(max_results)
        files = await cursor.to_list(length=max_results)

        if self.secondary_collection is not None and len(files) < max_results:
            remaining = max_results - len(files)
            cursor2 = self.secondary_collection.find(filter_query).sort("_id", -1).skip(offset).limit(remaining)
            files2 = await cursor2.to_list(length=remaining)
            files.extend(files2)

        next_offset = str(offset + len(files)) if (offset + len(files)) < total_results else ""
        return files, next_offset, total_results

    async def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        if self.collection is None:
            return None
        file_doc = await self.collection.find_one({"_id": file_id})
        if not file_doc and self.secondary_collection is not None:
            file_doc = await self.secondary_collection.find_one({"_id": file_id})
        return file_doc

    async def get_recent_movies(self, limit: int = 20) -> List[Dict[str, Any]]:
        if self.collection is None:
            return []
        cursor = self.collection.find().sort("_id", -1).limit(limit)
        return await cursor.to_list(length=limit)

media_repo = MediaRepository()
