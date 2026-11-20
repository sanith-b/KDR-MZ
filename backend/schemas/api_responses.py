"""
Standardized Pydantic Request & Response Schemas for My K-Drama 2.0 API
Enforces strict input validation, typed outputs, and consistent envelopes.
"""
from datetime import datetime
from typing import Generic, TypeVar, Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Standard Envelopes
# ---------------------------------------------------------------------------

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    pagination: PaginationMetadata
    message: Optional[str] = None

# ---------------------------------------------------------------------------
# 1. Auth Schemas
# ---------------------------------------------------------------------------

class TelegramAuthPayload(BaseModel):
    id: int = Field(description="Telegram numeric user ID")
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str

class WebLoginPayload(BaseModel):
    email_or_username: str = Field(min_length=3)
    password: str = Field(min_length=6)

class WebRegisterPayload(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: str
    password: str = Field(min_length=6)
    first_name: str = Field(default="")
    last_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: Dict[str, Any]

# ---------------------------------------------------------------------------
# 2. User Schemas
# ---------------------------------------------------------------------------

class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_language: Optional[str] = None
    notifications_enabled: Optional[bool] = None

class UserPreferencesUpdate(BaseModel):
    preferred_language: Optional[str] = "en"
    notifications_enabled: Optional[bool] = True
    auto_delete_files: Optional[bool] = True
    auto_delete_minutes: Optional[int] = 10

# ---------------------------------------------------------------------------
# 3. Drama Schemas
# ---------------------------------------------------------------------------

class DramaCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    korean_title: Optional[str] = None
    romanized_title: Optional[str] = None
    slug: Optional[str] = None
    tmdb_id: Optional[int] = None
    synopsis: Optional[str] = None
    status: Literal["ongoing", "completed", "upcoming"] = "completed"
    release_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    network: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    total_seasons: int = 1
    total_episodes: int = 16

class DramaUpdateRequest(BaseModel):
    title: Optional[str] = None
    korean_title: Optional[str] = None
    synopsis: Optional[str] = None
    status: Optional[Literal["ongoing", "completed", "upcoming"]] = None
    release_year: Optional[int] = None
    genres: Optional[List[str]] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None

# ---------------------------------------------------------------------------
# 4. Season & Episode Schemas
# ---------------------------------------------------------------------------

class SeasonCreateRequest(BaseModel):
    drama_id: str
    season_number: int = Field(ge=1)
    title: Optional[str] = None
    total_episodes: int = 16
    poster_url: Optional[str] = None

class EpisodeCreateRequest(BaseModel):
    drama_id: str
    season_number: int = Field(ge=1)
    episode_number: int = Field(ge=1)
    title: Optional[str] = None
    overview: Optional[str] = None
    air_date: Optional[str] = None
    duration_minutes: Optional[int] = None
    thumbnail_url: Optional[str] = None

# ---------------------------------------------------------------------------
# 5. File & Streaming Schemas
# ---------------------------------------------------------------------------

class FileCreateRequest(BaseModel):
    file_id: str
    file_unique_id: str
    file_name: str
    file_size: int = Field(ge=0)
    mime_type: Optional[str] = "video/mp4"
    quality: Optional[str] = "720p"
    drama_id: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    caption: Optional[str] = None

class StreamLinkResponse(BaseModel):
    file_id: str
    file_name: str
    stream_url: str
    download_url: str
    expires_at: Optional[datetime] = None

# ---------------------------------------------------------------------------
# 6. Watchlist, Favorites & Progress
# ---------------------------------------------------------------------------

class WatchlistAddRequest(BaseModel):
    drama_id: str
    status: Literal["plan_to_watch", "watching", "completed", "dropped"] = "plan_to_watch"

class WatchlistUpdateRequest(BaseModel):
    status: Literal["plan_to_watch", "watching", "completed", "dropped"]

class FavoriteAddRequest(BaseModel):
    drama_id: str

class ProgressUpdateRequest(BaseModel):
    drama_id: str
    episode_id: str
    season_number: int = 1
    episode_number: int = 1
    playback_position_seconds: int = Field(ge=0)
    duration_seconds: int = Field(ge=0)
    is_completed: bool = False

# ---------------------------------------------------------------------------
# 7. Drama Requests & Votes
# ---------------------------------------------------------------------------

class CreateDramaRequestPayload(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    tmdb_id: Optional[int] = None
    notes: Optional[str] = None

class UpdateRequestStatusPayload(BaseModel):
    status: Literal["pending", "approved", "rejected", "available"]
    admin_notes: Optional[str] = None

# ---------------------------------------------------------------------------
# 8. Notifications & Subscriptions
# ---------------------------------------------------------------------------

class MarkNotificationReadRequest(BaseModel):
    notification_ids: Optional[List[str]] = None
    mark_all: bool = False

class SubscriptionCreateRequest(BaseModel):
    plan_id: str = "monthly_premium"
    duration_days: int = 30
    payment_method: str = "telegram_stars"

# ---------------------------------------------------------------------------
# 9. Admin & Settings
# ---------------------------------------------------------------------------

class BotSettingsUpdateRequest(BaseModel):
    key: str
    value: Any

class WebSettingsUpdateRequest(BaseModel):
    banner_text: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    featured_drama_ids: Optional[List[str]] = None

class AdminUserUpdatePayload(BaseModel):
    role: Optional[Literal["user", "premium", "moderator", "admin", "superadmin"]] = None
    points_delta: Optional[int] = None
    is_banned: Optional[bool] = None
    ban_reason: Optional[str] = None
