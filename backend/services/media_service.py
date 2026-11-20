"""
Media Files & Fast Streaming Link Generation Service
Handles Telegram file records, resolution filtering, and secure streaming/download URLs.
"""
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from shared.database.repositories.dramas_repo import telegram_files_repo
from shared.database.pagination import PaginationParams, PaginatedResult
from shared.config.settings import settings

class MediaService:
    async def list_files(
        self,
        drama_id: Optional[str] = None,
        season_number: Optional[int] = None,
        episode_number: Optional[int] = None,
        quality: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResult[Dict[str, Any]]:
        """Find media files by drama and episode coordinates"""
        params = PaginationParams(page=page, page_size=page_size)
        filter_query: Dict[str, Any] = {}
        if drama_id:
            filter_query["drama_id"] = drama_id
        if season_number is not None:
            filter_query["season_number"] = season_number
        if episode_number is not None:
            filter_query["episode_number"] = episode_number
        if quality:
            filter_query["quality"] = quality

        return await telegram_files_repo.find_many(filter_query, pagination=params)

    async def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Fetch media file by Telegram file_id or MongoDB _id"""
        doc = await telegram_files_repo.get_by_file_id(file_id)
        if not doc:
            doc = await telegram_files_repo.find_one({"_id": file_id})
        return doc

    def generate_streaming_urls(self, file_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates direct streamable URL and download URL.
        Preserves streaming engine compatibility with Lucia / web server.
        """
        file_id = file_doc.get("file_id")
        base_url = settings.URL.rstrip("/")
        stream_path = f"{base_url}/watch/{file_id}" if settings.STREAM_MODE else f"{base_url}/dl/{file_id}"
        dl_path = f"{base_url}/dl/{file_id}"

        return {
            "file_id": file_id,
            "file_name": file_doc.get("file_name", "video.mp4"),
            "file_size": file_doc.get("file_size", 0),
            "quality": file_doc.get("quality", "720p"),
            "stream_url": stream_path,
            "download_url": dl_path,
            "mime_type": file_doc.get("mime_type", "video/mp4")
        }

media_service = MediaService()
