import aiohttp
from typing import Dict, Any, Optional, List
from shared.config.settings import settings
from shared.cache.redis_client import cache
from logging_helper import LOGGER

class TMDbService:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TMDB_API_KEY

    async def search_kdrama(self, query: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search TV series prioritized for Korean dramas"""
        cache_key = f"tmdb:search:{query.lower()}:{year or ''}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        params = {
            "api_key": self.api_key,
            "query": query,
            "include_adult": "false",
            "language": "en-US",
        }
        if year:
            params["first_air_date_year"] = str(year)

        url = f"{self.BASE_URL}/search/tv"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("results", [])
                        # Prioritize Korean origin country
                        sorted_results = sorted(
                            results,
                            key=lambda x: "KR" in x.get("origin_country", []),
                            reverse=True
                        )
                        formatted = [self._format_tv_result(item) for item in sorted_results]
                        await cache.set(cache_key, formatted, ttl=86400) # 24h
                        return formatted
        except Exception as e:
            LOGGER.error(f"TMDb TV search error: {e}")
        return []

    async def get_drama_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """Fetch full metadata for a TV drama including seasons and episode counts"""
        cache_key = f"tmdb:tv:{tmdb_id}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        url = f"{self.BASE_URL}/tv/{tmdb_id}"
        params = {
            "api_key": self.api_key,
            "language": "en-US",
            "append_to_response": "credits"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        details = self._format_tv_details(data)
                        await cache.set(cache_key, details, ttl=604800) # 7 days
                        return details
        except Exception as e:
            LOGGER.error(f"TMDb TV details error: {e}")
        return None

    def _format_tv_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        poster_path = item.get("poster_path")
        backdrop_path = item.get("backdrop_path")
        return {
            "id": item.get("id"),
            "name": item.get("name"),
            "original_name": item.get("original_name"),
            "overview": item.get("overview"),
            "first_air_date": item.get("first_air_date"),
            "year": item.get("first_air_date", "")[:4] if item.get("first_air_date") else None,
            "vote_average": item.get("vote_average"),
            "vote_count": item.get("vote_count"),
            "poster_url": f"{self.IMAGE_BASE_URL}/w500{poster_path}" if poster_path else None,
            "backdrop_url": f"{self.IMAGE_BASE_URL}/original{backdrop_path}" if backdrop_path else None,
            "origin_country": item.get("origin_country", [])
        }

    def _format_tv_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = self._format_tv_result(data)
        genres = [g.get("name") for g in data.get("genres", [])]
        seasons = [
            {
                "season_number": s.get("season_number"),
                "name": s.get("name"),
                "episode_count": s.get("episode_count"),
                "air_date": s.get("air_date"),
                "poster_url": f"{self.IMAGE_BASE_URL}/w500{s.get('poster_path')}" if s.get('poster_path') else None
            }
            for s in data.get("seasons", [])
            if s.get("season_number", 0) > 0  # Skip specials (Season 0)
        ]
        cast = [
            c.get("name") for c in data.get("credits", {}).get("cast", [])[:5]
        ]
        result.update({
            "genres": ", ".join(genres) if genres else "K-Drama",
            "seasons": seasons,
            "number_of_seasons": data.get("number_of_seasons"),
            "number_of_episodes": data.get("number_of_episodes"),
            "status": data.get("status"),
            "cast": ", ".join(cast) if cast else "N/A"
        })
        return result

tmdb = TMDbService()
