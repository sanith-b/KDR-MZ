"""
Pydantic Schemas for all 21 Entities in My K-Drama 2.0
Provides strong typing, default values, timestamps, and schema validation.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, EmailStr, HttpUrl
import uuid

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.utcnow()

# ==========================================
# 1. USER SCHEMA
# ==========================================
class UserBanStatus(BaseModel):
    is_banned: bool = False
    ban_reason: str = ""
    banned_at: Optional[datetime] = None
    banned_by: Optional[int] = None

class UserPreferences(BaseModel):
    preferred_language: str = "korean"
    subtitle_language: str = "english"
    preferred_quality: str = "1080p"
    notifications_enabled: bool = True

class UserSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    telegram_id: Optional[int] = Field(default=None, description="Telegram User ID")
    web_id: Optional[str] = Field(default=None, description="Web Client UUID / Identifier")
    email: Optional[str] = None
    username: Optional[str] = None
    first_name: str = ""
    last_name: Optional[str] = None
    role: Literal["user", "premium", "moderator", "admin", "superadmin"] = "user"
    is_active: bool = True
    auth_provider: Literal["telegram", "email", "google"] = "telegram"
    ban_status: UserBanStatus = Field(default_factory=UserBanStatus)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    referral_points: int = 0
    referred_by: Optional[int] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

# ==========================================
# 2. ADMIN SCHEMA
# ==========================================
class AdminSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    user_id: str = Field(description="Reference to User ID")
    telegram_id: Optional[int] = None
    role: Literal["moderator", "admin", "superadmin"] = "moderator"
    permissions: List[str] = Field(default_factory=lambda: [
        "manage_requests", "view_analytics"
    ])
    added_by: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 3. GROUP SCHEMA
# ==========================================
class GroupSettings(BaseModel):
    button: bool = True
    file_secure: bool = True
    imdb: bool = True
    spell_check: bool = True
    welcome: bool = False
    auto_delete: bool = True
    auto_ffilter: bool = True
    max_btn: bool = True
    template: str = ""
    caption: str = ""
    fsub_id: List[int] = Field(default_factory=list)
    shortner: str = ""
    api: str = ""
    shortner_two: str = ""
    api_two: str = ""
    shortner_three: str = ""
    api_three: str = ""
    is_verify: bool = False
    verify_time: int = 1200
    third_verify_time: int = 54000
    log: str = ""
    tutorial: str = ""
    tutorial_2: str = ""
    tutorial_3: str = ""

class GroupSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    group_id: int = Field(description="Telegram Group / Channel ID (e.g. -100...)")
    title: str = ""
    username: Optional[str] = None
    is_disabled: bool = False
    disable_reason: str = ""
    members_count: int = 0
    connected_admin_ids: List[int] = Field(default_factory=list)
    settings: GroupSettings = Field(default_factory=GroupSettings)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 4. DRAMA SCHEMA
# ==========================================
class CastMember(BaseModel):
    name: str
    character: Optional[str] = None
    profile_url: Optional[str] = None

class DramaSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    drama_id: str = Field(description="URL friendly slug or identifier", default_factory=generate_uuid)
    slug: Optional[str] = None
    tmdb_id: Optional[int] = None
    title: str
    korean_title: Optional[str] = None
    romanized_title: Optional[str] = None
    alt_titles: List[str] = Field(default_factory=list)
    synopsis: Optional[str] = None
    status: Literal["ongoing", "completed", "upcoming"] = "completed"
    release_year: Optional[int] = None
    air_date: Optional[str] = None
    end_date: Optional[str] = None
    genres: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    network: Optional[str] = None
    rating_average: float = 0.0
    rating_count: int = 0
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    total_seasons: int = 1
    total_episodes: int = 16
    cast: List[CastMember] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 5. SEASON SCHEMA
# ==========================================
class SeasonSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    season_id: str = Field(description="Compound key like drama_id:s1")
    drama_id: str
    season_number: int = 1
    title: str = "Season 1"
    synopsis: Optional[str] = None
    poster_url: Optional[str] = None
    air_date: Optional[str] = None
    episode_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 6. EPISODE SCHEMA
# ==========================================
class EpisodeSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    episode_id: str = Field(description="Compound key like drama_id:s1:e1")
    drama_id: str
    season_id: str
    season_number: int = 1
    episode_number: int
    title: str = ""
    synopsis: Optional[str] = None
    duration_minutes: Optional[int] = None
    air_date: Optional[str] = None
    still_url: Optional[str] = None
    telegram_file_ids: List[str] = Field(default_factory=list, description="IDs of matching TelegramFile documents")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 7. TELEGRAM FILE SCHEMA
# ==========================================
class TelegramFileSchema(BaseModel):
    id: str = Field(alias="_id", description="Telegram file_id string")
    file_unique_id: str
    file_ref: Optional[str] = None
    file_name: str
    clean_name: str
    file_size: int
    file_type: str = "video"
    mime_type: Optional[str] = None
    caption: Optional[str] = None
    channel_id: Optional[int] = None
    message_id: Optional[int] = None
    drama_id: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    quality: str = "720p"
    audio_languages: List[str] = Field(default_factory=list)
    subtitle_languages: List[str] = Field(default_factory=list)
    is_bad_file: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 8. WATCHLIST SCHEMA
# ==========================================
class WatchlistSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    user_id: str
    drama_id: str
    status: Literal["plan_to_watch", "watching", "completed", "dropped"] = "plan_to_watch"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 9. FAVORITES SCHEMA
# ==========================================
class FavoriteSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    user_id: str
    drama_id: str
    created_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 10. WATCH PROGRESS SCHEMA
# ==========================================
class WatchProgressSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    user_id: str
    drama_id: str
    episode_id: str
    progress_seconds: int = 0
    total_seconds: int = 0
    percentage: float = 0.0
    completed: bool = False
    device_info: Optional[str] = None
    last_watched_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 11. SEARCH HISTORY SCHEMA
# ==========================================
class SearchHistorySchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    user_id: Optional[str] = None
    telegram_id: Optional[int] = None
    query: str
    platform: Literal["telegram", "web"] = "telegram"
    result_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 12. SEARCH LOGS SCHEMA
# ==========================================
class SearchLogSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    query: str
    normalized_query: str
    hit_count: int = 1
    successful: bool = True
    last_searched_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 13. DRAMA REQUEST SCHEMA
# ==========================================
class DramaRequestSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    user_id: str
    telegram_id: Optional[int] = None
    user_name: str
    platform: Literal["telegram", "web"] = "telegram"
    drama_name: str
    tmdb_id: Optional[int] = None
    details: Optional[str] = None
    status: Literal["pending", "approved", "rejected", "fulfilled"] = "pending"
    vote_count: int = 1
    admin_notes: Optional[str] = None
    processed_by: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 14. REQUEST VOTE SCHEMA
# ==========================================
class RequestVoteSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    request_id: str
    user_id: str
    created_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 15. NOTIFICATION SCHEMA
# ==========================================
class NotificationSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    notification_id: str = Field(default_factory=generate_uuid)
    user_id: str
    telegram_id: Optional[int] = None
    title: str
    message: str
    type: Literal["request_update", "premium_expiring", "new_episode", "system_alert"] = "system_alert"
    status: Literal["unread", "read", "sent_tg"] = "unread"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    read_at: Optional[datetime] = None

    class Config:
        populate_by_name = True

# ==========================================
# 16. SUBSCRIPTION SCHEMA
# ==========================================
class SubscriptionSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    user_id: str
    telegram_id: Optional[int] = None
    plan_id: str = "1month"
    tier: Literal["free", "premium", "vip"] = "premium"
    status: Literal["active", "expired", "cancelled"] = "active"
    start_date: datetime = Field(default_factory=utc_now)
    expiry_date: datetime
    is_trial: bool = False
    auto_renew: bool = False
    reminders_sent: Dict[str, bool] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 17. PAYMENT SCHEMA
# ==========================================
class PaymentSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    payment_id: str = Field(default_factory=lambda: f"pay_{uuid.uuid4().hex[:12]}")
    user_id: str
    telegram_id: Optional[int] = None
    method: Literal["telegram_stars", "crypto_usdt", "crypto_ton", "crypto_btc", "redeem_code", "manual"] = "telegram_stars"
    amount: float
    currency: str = "XTR"
    status: Literal["pending", "completed", "failed", "refunded"] = "pending"
    plan_id: str = "1month"
    telegram_payment_charge_id: Optional[str] = None
    crypto_tx_hash: Optional[str] = None
    redeem_code: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 18. BOT SETTINGS SCHEMA
# ==========================================
class BotSettingsSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    bot_id: int = Field(description="Telegram Bot ID")
    maintenance_mode: bool = False
    pm_search: bool = True
    movie_update_notification: bool = False
    stream_mode: bool = False
    paid_stream: bool = False
    auto_delete_time: int = 43200
    custom_caption_template: str = ""
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 19. WEB SETTINGS SCHEMA
# ==========================================
class AnnouncementBanner(BaseModel):
    enabled: bool = False
    text: str = ""
    banner_type: Literal["info", "warning", "success"] = "info"

class WebSettingsSchema(BaseModel):
    id: str = Field(default="global_web_settings", alias="_id")
    site_name: str = "My K-Drama 2.0"
    maintenance_mode: bool = False
    registration_enabled: bool = True
    guest_streaming_enabled: bool = False
    ads_enabled: bool = False
    featured_drama_ids: List[str] = Field(default_factory=list)
    announcement: AnnouncementBanner = Field(default_factory=AnnouncementBanner)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 20. AI CONVERSATION SCHEMA
# ==========================================
class AIMessage(BaseModel):
    role: Literal["user", "model", "system"]
    content: str
    timestamp: datetime = Field(default_factory=utc_now)
    suggested_drama_ids: List[str] = Field(default_factory=list)

class AIConversationSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    conversation_id: str = Field(default_factory=generate_uuid)
    user_id: Optional[str] = None
    telegram_id: Optional[int] = None
    platform: Literal["telegram", "web"] = "telegram"
    messages: List[AIMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# ==========================================
# 21. AUDIT LOG SCHEMA
# ==========================================
class AuditLogSchema(BaseModel):
    id: str = Field(default_factory=generate_uuid, alias="_id")
    log_id: str = Field(default_factory=generate_uuid)
    actor_id: str
    actor_role: str
    action: str
    target_type: Literal["user", "drama", "file", "request", "setting", "payment"] = "user"
    target_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True

# Schema / Model Name Aliases
UserModel = UserSchema
AdminModel = AdminSchema
GroupModel = GroupSchema
DramaModel = DramaSchema
SeasonModel = SeasonSchema
EpisodeModel = EpisodeSchema
TelegramFileModel = TelegramFileSchema
WatchlistModel = WatchlistSchema
FavoriteModel = FavoriteSchema
WatchProgressModel = WatchProgressSchema
SearchHistoryModel = SearchHistorySchema
SearchLogModel = SearchLogSchema
DramaRequestModel = DramaRequestSchema
RequestVoteModel = RequestVoteSchema
NotificationModel = NotificationSchema
SubscriptionModel = SubscriptionSchema
PaymentModel = PaymentSchema
BotSettingsModel = BotSettingsSchema
WebSettingsModel = WebSettingsSchema
AIConversationModel = AIConversationSchema
AuditLogModel = AuditLogSchema
