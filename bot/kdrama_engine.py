"""
My K-Drama 2.0 - Advanced Auto-Filter & Parsing Engine
Provides:
  1. Regex-based Season and Episode recognition (S01, E01, Ep 1, 1x01, Season 1).
  2. Resolution & Quality tag parsing (4k, 2160p, 1080p, 720p, 480p).
  3. Language tag extraction (Korean, English Sub, Hindi, Tamil, Telugu).
  4. Alternative & Korean title resolution via shared dramas_repo.
  5. Fuzzy title matching fallback.
  6. Duplicate file detection & deduplication.
  7. High-speed Redis search caching.
  8. Smart Episode Navigation Keyboards.
"""
import re
import difflib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shared.cache.redis_client import cache
from shared.database.repositories.dramas_repo import dramas_repo
from logging_helper import LOGGER

try:
    from fuzzywuzzy import process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# Regex patterns for season, episode, quality, language
COMBINED_PATTERNS = [
    re.compile(r'\b(?:s|season)\s*(\d{1,2})[\s\.\-_]*(?:e|ep|episode)\s*(\d{1,3})\b', re.IGNORECASE),
    re.compile(r'\b(\d{1,2})x(\d{1,3})\b', re.IGNORECASE),
]

SEASON_PATTERNS = [
    re.compile(r'\b(?:s|season)\s*(\d{1,2})\b', re.IGNORECASE),
    re.compile(r'\b(\d{1,2})x\d{1,2}\b', re.IGNORECASE),
]

EPISODE_PATTERNS = [
    re.compile(r'\b(?:e|ep|episode)\s*(\d{1,3})\b', re.IGNORECASE),
    re.compile(r'\b\d{1,2}x(\d{1,2})\b', re.IGNORECASE),
    re.compile(r'\[(\d{1,3})\]', re.IGNORECASE),
]

QUALITY_KEYWORDS = ["2160p", "4k", "1080p", "720p", "480p", "360p", "hdrip", "web-dl", "bluray"]
LANGUAGE_KEYWORDS = {
    "korean": ["korean", "kor"],
    "english": ["english", "eng", "esub"],
    "hindi": ["hindi", "hin"],
    "tamil": ["tamil", "tam"],
    "telugu": ["telugu", "tel"],
    "malayalam": ["malayalam", "mal"],
}

# In-memory per-user rate limit tracker for bot commands
_USER_COMMAND_TIMESTAMPS: Dict[int, List[float]] = {}

def check_user_rate_limit(user_id: int, max_per_minute: int = 15) -> bool:
    """Returns True if within rate limit, False if flood detected"""
    import time
    now = time.time()
    timestamps = _USER_COMMAND_TIMESTAMPS.get(user_id, [])
    timestamps = [ts for ts in timestamps if now - ts < 60]
    if len(timestamps) >= max_per_minute:
        return False
    timestamps.append(now)
    _USER_COMMAND_TIMESTAMPS[user_id] = timestamps
    return True

@dataclass
class ParsedQuery:
    raw_query: str
    clean_title: str
    season: Optional[int] = None
    episode: Optional[int] = None
    quality: Optional[str] = None
    language: Optional[str] = None


class KDramaSearchEngine:
    """Core intelligence engine for queries, recognition, and filtering"""

    @classmethod
    def parse_query(cls, raw_query: str) -> ParsedQuery:
        """Extracts title, season, episode, quality, and language tokens from user query"""
        text = raw_query.strip()
        season = None
        episode = None
        quality = None
        language = None

        # 1. Combined Season & Episode extraction
        for pat in COMBINED_PATTERNS:
            match = pat.search(text)
            if match:
                try:
                    season = int(match.group(1))
                    episode = int(match.group(2))
                    text = pat.sub(" ", text)
                    break
                except (ValueError, IndexError):
                    pass

        # 2. Individual Season extraction
        if season is None:
            for pat in SEASON_PATTERNS:
                match = pat.search(text)
                if match:
                    try:
                        season = int(match.group(1))
                        text = pat.sub(" ", text)
                        break
                    except (ValueError, IndexError):
                        pass

        # 3. Individual Episode extraction
        if episode is None:
            for pat in EPISODE_PATTERNS:
                match = pat.search(text)
                if match:
                    try:
                        episode = int(match.group(1))
                        text = pat.sub(" ", text)
                        break
                    except (ValueError, IndexError):
                        pass

        # 4. Quality extraction (strip all occurrences from title text)
        for q in QUALITY_KEYWORDS:
            if re.search(r'\b' + re.escape(q) + r'\b', text, flags=re.IGNORECASE):
                if quality is None:
                    quality = q.lower()
                text = re.sub(r'\b' + re.escape(q) + r'\b', ' ', text, flags=re.IGNORECASE)

        # 5. Language extraction (strip all occurrences from title text)
        for lang, aliases in LANGUAGE_KEYWORDS.items():
            matched_lang = False
            for alias in aliases:
                if re.search(r'\b' + re.escape(alias) + r'\b', text, flags=re.IGNORECASE):
                    matched_lang = True
                    text = re.sub(r'\b' + re.escape(alias) + r'\b', ' ', text, flags=re.IGNORECASE)
            if matched_lang and language is None:
                language = lang

        # 6. Strip auxiliary release tags
        text = re.sub(r'\b(?:dub|sub|esub|raw|multi|audio|complete|batch|all|episodes|ep)\b', ' ', text, flags=re.IGNORECASE)

        # 7. Clean remaining title
        clean_title = re.sub(r'[\.\+\-_:()\[\]]', ' ', text)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()

        return ParsedQuery(
            raw_query=raw_query,
            clean_title=clean_title or raw_query,
            season=season,
            episode=episode,
            quality=quality,
            language=language
        )

    @classmethod
    async def resolve_alternative_titles(cls, title: str) -> Optional[Dict[str, Any]]:
        """
        Looks up Korean, Romanized, and Alternative drama titles in shared MongoDB.
        Returns the canonical drama metadata if an alias matches.
        """
        title_clean = title.strip()
        cache_key = f"kdrama:alias:{title_clean.lower()}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # Check title, korean_title, romanized_title, alt_titles
        match = await dramas_repo.find_one({
            "$or": [
                {"title": {"$regex": f"^{title_clean}$", "$options": "i"}},
                {"korean_title": {"$regex": f"^{title_clean}$", "$options": "i"}},
                {"romanized_title": {"$regex": f"^{title_clean}$", "$options": "i"}},
                {"alt_titles": {"$regex": f"^{title_clean}$", "$options": "i"}}
            ]
        })

        if match:
            await cache.set(cache_key, match, ttl=1800)
        return match

    @classmethod
    def fuzzy_match(cls, query: str, candidate_titles: List[str], cutoff: float = 0.6) -> List[str]:
        """Performs fuzzy matching on candidate titles to handle user misspellings"""
        if not candidate_titles:
            return []

        if FUZZY_AVAILABLE:
            matches = process.extractBests(query, candidate_titles, score_cutoff=int(cutoff * 100), limit=5)
            return [m[0] for m in matches]
        else:
            return difflib.get_close_matches(query, candidate_titles, n=5, cutoff=cutoff)

    @classmethod
    def deduplicate_files(cls, files: List[Any]) -> List[Any]:
        """
        Filters out redundant files with identical episode number, quality, and size
        to keep search keyboards neat and non-repetitive.
        """
        seen_keys = set()
        deduped = []
        for file in files:
            # Handle both PyMongo / Pyrofork dicts and Objects
            file_name = getattr(file, "file_name", None) or (file.get("file_name") if isinstance(file, dict) else "")
            file_size = getattr(file, "file_size", None) or (file.get("file_size") if isinstance(file, dict) else 0)
            
            # Key based on normalized filename base & size
            normalized_name = re.sub(r'[^a-zA-Z0-9]', '', file_name.lower())[:35]
            dedup_key = f"{normalized_name}_{file_size}"
            
            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                deduped.append(file)
        return deduped

    @classmethod
    def build_episode_grid(
        cls,
        drama_title: str,
        total_episodes: int,
        season: int = 1,
        session_key: str = ""
    ) -> InlineKeyboardMarkup:
        """
        Builds a compact grid of episode buttons for easy 1-tap navigation:
        [ Ep 1 ] [ Ep 2 ] [ Ep 3 ] [ Ep 4 ]
        [ Ep 5 ] [ Ep 6 ] [ Ep 7 ] [ Ep 8 ]
        """
        buttons = []
        row = []
        max_episodes = min(total_episodes, 32)
        for ep in range(1, max_episodes + 1):
            ep_str = f"E{ep:02d}"
            # Callback query for specific episode
            cb_data = f"kd_ep#{session_key}#{season}#{ep}"
            row.append(InlineKeyboardButton(ep_str, callback_data=cb_data))
            if len(row) == 4:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        # Navigation footer
        buttons.append([
            InlineKeyboardButton("🔙 Back to Files", callback_data=f"kd_back#{session_key}"),
            InlineKeyboardButton("⭐ Add to Favs", callback_data=f"fav_add#{session_key}")
        ])
        return InlineKeyboardMarkup(buttons)

kdrama_engine = KDramaSearchEngine()
