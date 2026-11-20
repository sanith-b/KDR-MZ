"""
Dramas, Seasons, Episodes, and Telegram Files Repositories for My K-Drama 2.0
"""
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from shared.database.repositories.base import BaseRepository
from shared.database.schemas import DramaSchema, SeasonSchema, EpisodeSchema, TelegramFileSchema
from shared.database.pagination import PaginationParams, PaginatedResult

class DramaRepository(BaseRepository[DramaSchema]):
    def __init__(self):
        super().__init__("dramas", DramaSchema)

    async def get_by_drama_id(self, drama_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"drama_id": drama_id})

    async def get_by_tmdb_id(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        return await self.find_one({"tmdb_id": int(tmdb_id)})

    async def search_dramas(
        self,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResult[Dict[str, Any]]:
        filter_query = {}
        if query and query.strip():
            # Use text index search with regex fallback
            escaped = re.escape(query.strip())
            filter_query["$or"] = [
                {"title": {"$regex": escaped, "$options": "i"}},
                {"korean_title": {"$regex": escaped, "$options": "i"}},
                {"romanized_title": {"$regex": escaped, "$options": "i"}},
                {"alt_titles": {"$regex": escaped, "$options": "i"}},
            ]
        if genre:
            filter_query["genres"] = {"$regex": re.escape(genre), "$options": "i"}
        if year:
            filter_query["release_year"] = int(year)
        if status:
            filter_query["status"] = status

        return await self.find_many(filter_query, pagination)

    async def upsert_drama(self, drama: DramaSchema | Dict[str, Any]) -> Dict[str, Any]:
        data = drama.model_dump(by_alias=True) if isinstance(drama, DramaSchema) else drama.copy()
        drama_id = data.get("drama_id")
        data["updated_at"] = datetime.utcnow()
        await self.update_one({"drama_id": drama_id}, data, upsert=True)
        return data


class SeasonRepository(BaseRepository[SeasonSchema]):
    def __init__(self):
        super().__init__("seasons", SeasonSchema)

    async def get_seasons_for_drama(self, drama_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"drama_id": drama_id}).sort("season_number", 1)
        return await cursor.to_list(length=50)

    async def upsert_season(self, season: SeasonSchema | Dict[str, Any]) -> Dict[str, Any]:
        data = season.model_dump(by_alias=True) if isinstance(season, SeasonSchema) else season.copy()
        season_id = data.get("season_id")
        data["updated_at"] = datetime.utcnow()
        await self.update_one({"season_id": season_id}, data, upsert=True)
        return data


class EpisodeRepository(BaseRepository[EpisodeSchema]):
    def __init__(self):
        super().__init__("episodes", EpisodeSchema)

    async def get_episodes_for_season(self, drama_id: str, season_number: int = 1) -> List[Dict[str, Any]]:
        cursor = self.collection.find({
            "drama_id": drama_id,
            "season_number": int(season_number)
        }).sort("episode_number", 1)
        return await cursor.to_list(length=100)

    async def upsert_episode(self, episode: EpisodeSchema | Dict[str, Any]) -> Dict[str, Any]:
        data = episode.model_dump(by_alias=True) if isinstance(episode, EpisodeSchema) else episode.copy()
        episode_id = data.get("episode_id")
        data["updated_at"] = datetime.utcnow()
        await self.update_one({"episode_id": episode_id}, data, upsert=True)
        return data

    async def link_telegram_file(self, drama_id: str, season_number: int, episode_number: int, file_id: str) -> bool:
        """Add a Telegram file ID to the episode's available streams"""
        result = await self.collection.update_one(
            {
                "drama_id": drama_id,
                "season_number": int(season_number),
                "episode_number": int(episode_number)
            },
            {
                "$addToSet": {"telegram_file_ids": file_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0


class TelegramFileRepository(BaseRepository[TelegramFileSchema]):
    def __init__(self):
        super().__init__("telegram_files", TelegramFileSchema)

    async def search_files(
        self,
        query: str,
        quality: Optional[str] = None,
        file_type: Optional[str] = None,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResult[Dict[str, Any]]:
        escaped = re.escape(query.strip()) if query else "."
        regex = {"$regex": escaped, "$options": "i"}
        filter_query = {
            "$or": [{"clean_name": regex}, {"file_name": regex}, {"caption": regex}]
        }
        if quality:
            filter_query["quality"] = quality
        if file_type:
            filter_query["file_type"] = file_type

        return await self.find_many(filter_query, pagination)

    async def delete_bad_files(self) -> int:
        """Purge CamRip / PreDVD files"""
        result = await self.collection.delete_many({"is_bad_file": True})
        return result.deleted_count


dramas_repo = DramaRepository()
seasons_repo = SeasonRepository()
episodes_repo = EpisodeRepository()
telegram_files_repo = TelegramFileRepository()
