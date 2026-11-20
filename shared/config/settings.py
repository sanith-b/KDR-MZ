import os
import re
from typing import List, Optional
from pydantic_settings import BaseSettings

id_pattern = re.compile(r'^.\d+$')

def parse_int_list(val: Optional[str]) -> List[int]:
    if not val:
        return []
    result = []
    for item in val.strip().split():
        if id_pattern.search(item):
            result.append(int(item))
        else:
            try:
                result.append(int(item))
            except ValueError:
                pass
    return result

class Settings(BaseSettings):
    # Telegram Bot Core
    SESSION: str = "media_search"
    API_ID: int = 0
    API_HASH: str = ""
    BOT_TOKEN: str = ""
    WORKERS: int = 50
    SLEEP_THRESHOLD: int = 5
    
    # Admins & Channels
    ADMINS: List[int] = []
    CHANNELS: List[int] = []
    LOG_CHANNEL: int = 0
    BIN_CHANNEL: int = 0
    MOVIE_UPDATE_CHANNEL: int = 0
    PREMIUM_LOGS: int = 0
    SUPPORT_CHAT_ID: Optional[int] = None
    REQST_CHANNEL: Optional[int] = None
    LOG_VR_CHANNEL: int = 0
    LOG_API_CHANNEL: int = 0
    AU_CHANNEL: Optional[int] = None
    
    # Force Subscription
    AUTH_CHANNEL: List[int] = []
    AUTH_REQ_CHANNEL: List[int] = []
    
    # MongoDB Configuration
    DATABASE_URI: str = ""
    DATABASE_NAME: str = "kdrama_db"
    COLLECTION_NAME: str = "SilentXBotz_files"
    MULTIPLE_DB: bool = False
    DATABASE_URI2: str = ""
    DB_CHANGE_LIMIT: int = 432
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 1800  # 30 minutes
    
    # AI & Metadata Integrations
    GEMINI_API_KEY: Optional[str] = None
    TMDB_API_KEY: str = "90dde61a7cf8339a2cff5d805d5597a9"
    
    # Web & Streaming
    PORT: int = 8089
    WEB_PORT: int = 8000
    BIND_ADDRESS: str = "0.0.0.0"
    URL: str = "http://localhost:8089/"
    STREAM_MODE: bool = False
    PAID_STREAM: bool = False
    
    # Security & JWT (FastAPI)
    JWT_SECRET_KEY: str = "my-kdrama-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    
    # K-Drama Limits
    KDRAMA_MAX_REQUESTS_PER_DAY: int = 5
    KDRAMA_REQUEST_COOLDOWN: int = 10
    DELETE_TIME: int = 43200
    
    # Verification & Shorteners
    IS_VERIFY: bool = False
    TWO_VERIFY_GAP: int = 1200
    THREE_VERIFY_GAP: int = 54000
    SHORTENER_API: str = ""
    SHORTENER_WEBSITE: str = ""
    SHORTENER_API2: str = ""
    SHORTENER_WEBSITE2: str = ""
    SHORTENER_API3: str = ""
    SHORTENER_WEBSITE3: str = ""
    
    # Feature Toggles
    PM_SEARCH: bool = True
    EMOJI_MODE: bool = False
    MAINTENANCE_MODE: bool = False
    MOVIE_UPDATE_NOTIFICATION: bool = False
    PROTECT_CONTENT: bool = True
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Post-load parse from env if lists were strings
if not settings.ADMINS and os.getenv("ADMINS"):
    settings.ADMINS = parse_int_list(os.getenv("ADMINS"))
if not settings.CHANNELS and os.getenv("CHANNELS"):
    settings.CHANNELS = parse_int_list(os.getenv("CHANNELS"))
if not settings.AUTH_CHANNEL and os.getenv("AUTH_CHANNEL"):
    settings.AUTH_CHANNEL = parse_int_list(os.getenv("AUTH_CHANNEL"))
if not settings.AUTH_REQ_CHANNEL and os.getenv("AUTH_REQ_CHANNEL"):
    settings.AUTH_REQ_CHANNEL = parse_int_list(os.getenv("AUTH_REQ_CHANNEL"))
