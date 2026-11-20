"""
Drama Catalog, Seasons, Episodes & Metadata Service
Integrates shared MongoDB, Redis caching, TMDb metadata, and Gemini AI.
"""
from typing import Optional, Dict, Any, List, Tuple
from fastapi import HTTPException
from shared.database.repositories.dramas_repo import (
    dramas_repo, seasons_repo, episodes_repo, telegram_files_repo
)
from shared.database.repositories.interactions_repo import search_logs_repo, search_history_repo
from shared.database.pagination import PaginationParams, PaginatedResult
from shared.cache.redis_client import cache
from shared.services.tmdb import tmdb
from shared.services.gemini import gemini
from logging_helper import LOGGER

class DramaService:
    async def list_dramas(
        self,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResult[Dict[str, Any]]:
        """List and filter dramas with optional keyword and genre search"""
        params = PaginationParams(page=page, page_size=page_size)
        cache_key = f"dramas:list:{query}:{genre}:{year}:{status}:{page}:{page_size}"

        cached = await cache.get(cache_key)
        if cached:
            return PaginatedResult(**cached)

        filter_query: Dict[str, Any] = {}
        if query:
            filter_query["$text"] = {"$search": query}
        if genre:
            filter_query["genres"] = {"$regex": f"^{genre}$", "$options": "i"}
        if year:
            filter_query["release_year"] = year
        if status:
            filter_query["status"] = status

        result = await dramas_repo.find_many(filter_query, pagination=params)
        await cache.set(cache_key, result.model_dump(), ttl=300)
        return result

    async def get_drama_by_id_or_slug(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Fetch drama document by drama_id, slug, or MongoDB _id with Redis cache"""
        cache_key = f"drama:detail:{identifier}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        drama = await dramas_repo.get_by_slug_or_id(identifier)
        if not drama:
            drama = await dramas_repo.find_one({"_id": identifier})

        if drama:
            await cache.set(cache_key, drama, ttl=600)
        return drama

    async def get_drama_seasons(self, drama_id: str) -> List[Dict[str, Any]]:
        """Fetch all seasons for a drama"""
        res = await seasons_repo.find_many({"drama_id": drama_id}, PaginationParams(page_size=50))
        return res.items

    async def get_drama_episodes(
        self,
        drama_id: str,
        season_number: int = 1
    ) -> List[Dict[str, Any]]:
        """Fetch episodes for a specific drama season"""
        res = await episodes_repo.find_many(
            {"drama_id": drama_id, "season_number": season_number},
            PaginationParams(page_size=100)
        )
        return res.items

    async def search_dramas_and_files(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Unified search:
          1. Searches local drama catalog and telegram files.
          2. If 0 results found, queries Gemini AI for query correction / romanized variants.
          3. Enriches matches with TMDb metadata.
          4. Logs search metrics and user history.
        """
        query_clean = query.strip()
        # 1. Local catalog search
        dramas_res = await dramas_repo.search_by_title(query_clean, limit=limit)
        files_res = await telegram_files_repo.search_files(query_clean, limit=limit)

        corrected_query = None
        # 2. Consult Gemini AI if no local dramas found
        if not dramas_res and not files_res:
            corrected_query = await gemini.correct_kdrama_query(query_clean)
            if corrected_query and corrected_query.lower() != query_clean.lower():
                dramas_res = await dramas_repo.search_by_title(corrected_query, limit=limit)
                files_res = await telegram_files_repo.search_files(corrected_query, limit=limit)

        # 3. Enrich with TMDb metadata
        effective_query = corrected_query or query_clean
        tmdb_matches = await tmdb.search_kdrama(effective_query)

        # 4. Asynchronously log query stats and user history
        try:
            await search_logs_repo.log_search(query_clean, results_count=len(dramas_res) + len(files_res))
            if user_id:
                await search_history_repo.add_entry(user_id=str(user_id), query=query_clean)
        except Exception as e:
            LOGGER.debug(f"Search log error: {e}")

        return {
            "query": query,
            "corrected_query": corrected_query,
            "dramas": dramas_res,
            "files": files_res,
            "tmdb_matches": tmdb_matches,
            "total_matches": len(dramas_res) + len(files_res)
        }

drama_service = DramaService()
