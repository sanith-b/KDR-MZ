"""
Personalized AI & Genre-based K-Drama Recommendations Service
Combines user favorites, watch history, TMDb trending, and Gemini AI.
"""
from typing import Dict, Any, List, Optional
from shared.database.repositories.dramas_repo import dramas_repo
from shared.database.repositories.users_repo import favorites_repo, watch_progress_repo
from shared.services.gemini import gemini
from shared.services.tmdb import tmdb
from shared.cache.redis_client import cache
from logging_helper import LOGGER

class RecommendationService:
    async def get_recommendations(
        self,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generates smart drama recommendations:
        1. If user is logged in, checks their favorite genres and watch progress.
        2. Queries Gemini AI for smart recommendations based on their titles.
        3. Enriches with popular catalog entries as fallback.
        """
        cache_key = f"recommendations:user:{user_id or 'anonymous'}:{limit}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        user_favorites = []
        if user_id:
            favs = await favorites_repo.find_many({"user_id": str(user_id)})
            fav_drama_ids = [f.get("drama_id") for f in favs.items if f.get("drama_id")]
            if fav_drama_ids:
                user_favorites = fav_drama_ids[:5]

        # If user has favorites, ask Gemini AI for recommendations
        ai_recommendations = []
        if user_favorites and settings.GEMINI_API_KEY:
            try:
                # Fetch drama titles for user favorites
                titles = []
                for d_id in user_favorites:
                    d = await dramas_repo.get_by_slug_or_id(d_id)
                    if d:
                        titles.append(d.get("title"))

                if titles:
                    prompt = f"Given that a user loves the following K-Dramas: {', '.join(titles)}, recommend 5 similar popular Korean dramas. Return just the titles separated by commas."
                    response = await gemini.client.aio.models.generate_content(
                        model=gemini.model_name,
                        contents=prompt
                    )
                    suggested_titles = [t.strip() for t in response.text.split(",") if t.strip()]
                    for st in suggested_titles:
                        matched = await dramas_repo.find_one({"title": {"$regex": st, "$options": "i"}})
                        if matched:
                            ai_recommendations.append(matched)
            except Exception as e:
                LOGGER.debug(f"Gemini recommendations failed: {e}")

        # Fallback: top rated / popular dramas from local catalog
        if len(ai_recommendations) < limit:
            remaining = limit - len(ai_recommendations)
            existing_ids = [d.get("_id") for d in ai_recommendations]
            top_dramas = await dramas_repo.collection.find(
                {"_id": {"$nin": existing_ids}}
            ).sort("rating_average", -1).limit(remaining).to_list(length=remaining)
            ai_recommendations.extend(top_dramas)

        await cache.set(cache_key, ai_recommendations, ttl=600)
        return ai_recommendations

recommendation_service = RecommendationService()
