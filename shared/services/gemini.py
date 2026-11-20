import os
import json
from typing import Optional, Dict, Any
from shared.config.settings import settings
from shared.cache.redis_client import cache
from logging_helper import LOGGER

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        self._client = None
        if GENAI_AVAILABLE and self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                LOGGER.warning(f"Gemini client initialization failed: {e}")

    async def correct_kdrama_query(self, query: str) -> Optional[str]:
        """Normalize misspelled or phonetic Korean drama search queries into canon English titles"""
        if not self._client:
            return None

        cache_key = f"gemini:spell:{query.strip().lower()}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        prompt = f"""
You are a Korean Drama database expert. The user provided a potentially misspelled, incomplete, or phonetic romanized Korean drama title: "{query}".
Return ONLY a valid JSON object with:
{{
  "canonical_title": "Standard English Title of the Drama",
  "year": 2024,
  "confidence": 0.95
}}
If you cannot identify any plausible Korean drama, return {{"canonical_title": null}}. Do not include any explanations or markdown.
"""
        try:
            response = self._client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            data = json.loads(response.text)
            title = data.get("canonical_title")
            if title and data.get("confidence", 0) >= 0.7:
                await cache.set(cache_key, title, ttl=86400)
                return title
        except Exception as e:
            LOGGER.error(f"Gemini query correction error: {e}")
        return None

    async def parse_media_filename(self, filename: str) -> Dict[str, Any]:
        """Extract drama title, season, episode, and resolution from messy torrent/channel filenames"""
        default_res = {"title": filename, "season": 1, "episode": None, "quality": "HD"}
        if not self._client:
            return default_res

        cache_key = f"gemini:parse:{filename}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        prompt = f"""
Parse the following Korean drama media filename into structured metadata:
Filename: "{filename}"

Respond ONLY with JSON:
{{
  "title": "Clean Drama Title (without season, episode or group tags)",
  "season": 1,
  "episode": 1,
  "quality": "720p",
  "year": null
}}
"""
        try:
            response = self._client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            data = json.loads(response.text)
            await cache.set(cache_key, data, ttl=604800)
            return data
        except Exception as e:
            LOGGER.error(f"Gemini filename parse error: {e}")
        return default_res

gemini = GeminiService()
