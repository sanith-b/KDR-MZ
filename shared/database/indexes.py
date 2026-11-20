"""
Comprehensive Automated Index Management for all 21 Entities in My K-Drama 2.0
Ensures high-performance queries, uniqueness enforcement, text search, and automatic TTL expiration.
"""
from typing import Dict, Any, List
from pymongo import ASCENDING, DESCENDING, TEXT
from shared.database.connection import DatabaseConnection
from shared.config.settings import settings
from logging_helper import LOGGER

INDEX_DEFINITIONS: Dict[str, List[Dict[str, Any]]] = {
    # 1. Users
    "users": [
        {"keys": [("telegram_id", ASCENDING)], "unique": True, "sparse": True},
        {"keys": [("web_id", ASCENDING)], "unique": True, "sparse": True},
        {"keys": [("email", ASCENDING)], "unique": True, "sparse": True},
        {"keys": [("role", ASCENDING)]},
        {"keys": [("created_at", DESCENDING)]},
    ],
    # 2. Admins
    "admins": [
        {"keys": [("user_id", ASCENDING)], "unique": True},
        {"keys": [("telegram_id", ASCENDING)], "sparse": True},
        {"keys": [("is_active", ASCENDING)]},
    ],
    # 3. Groups
    "groups": [
        {"keys": [("group_id", ASCENDING)], "unique": True},
        {"keys": [("is_disabled", ASCENDING)]},
        {"keys": [("created_at", DESCENDING)]},
    ],
    # 4. Dramas
    "dramas": [
        {"keys": [("drama_id", ASCENDING)], "unique": True},
        {"keys": [("slug", ASCENDING)], "unique": True, "sparse": True},
        {"keys": [("tmdb_id", ASCENDING)], "unique": True, "sparse": True},
        {"keys": [("title", TEXT), ("korean_title", TEXT), ("alt_titles", TEXT), ("synopsis", TEXT)]},
        {"keys": [("status", ASCENDING), ("release_year", DESCENDING)]},
        {"keys": [("rating_average", DESCENDING)]},
        {"keys": [("created_at", DESCENDING)]},
    ],
    # 5. Seasons
    "seasons": [
        {"keys": [("season_id", ASCENDING)], "unique": True},
        {"keys": [("drama_id", ASCENDING), ("season_number", ASCENDING)], "unique": True},
        {"keys": [("drama_id", ASCENDING)]},
    ],
    # 6. Episodes
    "episodes": [
        {"keys": [("episode_id", ASCENDING)], "unique": True},
        {"keys": [("drama_id", ASCENDING), ("season_number", ASCENDING), ("episode_number", ASCENDING)], "unique": True},
        {"keys": [("drama_id", ASCENDING), ("season_number", ASCENDING)]},
    ],
    # 7. Telegram Files (and legacy media collection)
    "telegram_files": [
        {"keys": [("file_id", ASCENDING)], "unique": True, "sparse": True},
        {"keys": [("file_unique_id", ASCENDING)], "unique": True, "sparse": True},
        {"keys": [("clean_name", TEXT), ("file_name", TEXT), ("caption", TEXT)]},
        {"keys": [("clean_name", ASCENDING)]},
        {"keys": [("drama_id", ASCENDING), ("season_number", ASCENDING), ("episode_number", ASCENDING)]},
        {"keys": [("quality", ASCENDING)]},
        {"keys": [("file_size", ASCENDING)]},
        {"keys": [("created_at", DESCENDING)]},
    ],
    # 8. Watchlists
    "watchlists": [
        {"keys": [("user_id", ASCENDING), ("drama_id", ASCENDING)], "unique": True},
        {"keys": [("user_id", ASCENDING), ("status", ASCENDING)]},
        {"keys": [("created_at", DESCENDING)]},
    ],
    # 9. Favorites
    "favorites": [
        {"keys": [("user_id", ASCENDING), ("drama_id", ASCENDING)], "unique": True},
        {"keys": [("user_id", ASCENDING), ("created_at", DESCENDING)]},
    ],
    # 10. Watch Progress
    "watch_progress": [
        {"keys": [("user_id", ASCENDING), ("episode_id", ASCENDING)], "unique": True},
        {"keys": [("user_id", ASCENDING), ("last_watched_at", DESCENDING)]},
        {"keys": [("user_id", ASCENDING), ("drama_id", ASCENDING)]},
    ],
    # 11. Search History (TTL 90 days)
    "search_history": [
        {"keys": [("user_id", ASCENDING), ("created_at", DESCENDING)]},
        {"keys": [("telegram_id", ASCENDING), ("created_at", DESCENDING)]},
        {"keys": [("created_at", ASCENDING)], "expireAfterSeconds": 7776000},
    ],
    # 12. Search Logs
    "search_logs": [
        {"keys": [("normalized_query", ASCENDING)], "unique": True},
        {"keys": [("hit_count", DESCENDING)]},
        {"keys": [("last_searched_at", DESCENDING)]},
        {"keys": [("last_searched_at", ASCENDING)], "expireAfterSeconds": 7776000},
    ],
    # 13. Drama Requests
    "drama_requests": [
        {"keys": [("request_id", ASCENDING)], "unique": True},
        {"keys": [("user_id", ASCENDING), ("status", ASCENDING)]},
        {"keys": [("status", ASCENDING), ("vote_count", DESCENDING)]},
        {"keys": [("created_at", DESCENDING)]},
    ],
    # 14. Request Votes
    "request_votes": [
        {"keys": [("request_id", ASCENDING), ("user_id", ASCENDING)], "unique": True},
        {"keys": [("request_id", ASCENDING)]},
    ],
    # 15. Notifications
    "notifications": [
        {"keys": [("notification_id", ASCENDING)], "unique": True},
        {"keys": [("user_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)]},
    ],
    # 16. Subscriptions
    "subscriptions": [
        {"keys": [("user_id", ASCENDING), ("status", ASCENDING)]},
        {"keys": [("expiry_date", ASCENDING)]},
        {"keys": [("status", ASCENDING), ("expiry_date", ASCENDING)]},
    ],
    # 17. Payments
    "payments": [
        {"keys": [("payment_id", ASCENDING)], "unique": True},
        {"keys": [("user_id", ASCENDING), ("created_at", DESCENDING)]},
        {"keys": [("status", ASCENDING)]},
    ],
    # 18. Bot Settings
    "bot_settings": [
        {"keys": [("bot_id", ASCENDING)], "unique": True},
    ],
    # 19. Web Settings
    "web_settings": [
        {"keys": [("_id", ASCENDING)]},
    ],
    # 20. AI Conversations (TTL 30 days)
    "ai_conversations": [
        {"keys": [("conversation_id", ASCENDING)], "unique": True},
        {"keys": [("user_id", ASCENDING), ("updated_at", DESCENDING)]},
        {"keys": [("updated_at", ASCENDING)], "expireAfterSeconds": 2592000},
    ],
    # 21. Audit Logs (TTL 365 days)
    "audit_logs": [
        {"keys": [("log_id", ASCENDING)], "unique": True},
        {"keys": [("actor_id", ASCENDING), ("created_at", DESCENDING)]},
        {"keys": [("action", ASCENDING), ("created_at", DESCENDING)]},
        {"keys": [("target_type", ASCENDING), ("target_id", ASCENDING)]},
        {"keys": [("created_at", ASCENDING)], "expireAfterSeconds": 31536000},
    ],
}

async def ensure_all_indexes(db=None) -> Dict[str, int]:
    """
    Ensure all unique, compound, text and TTL indexes exist across all 21 collections.
    Returns a dictionary of collection names and count of created/verified indexes.
    """
    if db is None:
        db = DatabaseConnection.get_db()

    if db is None:
        LOGGER.warning("Database not connected. Skipping index creation.")
        return {}

    summary = {}
    LOGGER.info("Starting automated database index verification across 21 collections...")

    for col_name, index_list in INDEX_DEFINITIONS.items():
        collection = db[col_name]
        created_count = 0
        for index_spec in index_list:
            keys = index_spec["keys"]
            kwargs = {k: v for k, v in index_spec.items() if k != "keys"}
            try:
                await collection.create_index(keys, **kwargs)
                created_count += 1
            except Exception as e:
                LOGGER.debug(f"Index creation note on [{col_name} -> {keys}]: {e}")
        summary[col_name] = created_count

    # Also ensure legacy collection name (e.g. SilentXBotz_files) has text & name index
    legacy_col = db[settings.COLLECTION_NAME]
    try:
        await legacy_col.create_index([("clean_name", TEXT), ("file_name", TEXT), ("caption", TEXT)])
        await legacy_col.create_index([("clean_name", ASCENDING)])
    except Exception:
        pass

    LOGGER.info(f"✅ Successfully ensured indexes for {len(summary)} collections.")
    return summary
