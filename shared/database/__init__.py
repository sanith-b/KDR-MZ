"""
Shared Database Module for My K-Drama 2.0
"""
from .connection import DatabaseConnectionManager, db_manager, get_database
from .indexes import ensure_all_indexes, INDEX_DEFINITIONS
from .pagination import PaginationParams, PaginatedResult
from .errors import (
    DatabaseError, DuplicateKeyError, DocumentNotFoundError,
    ValidationError, ConnectionError
)
from .repositories.base import BaseRepository
from .schemas import (
    UserSchema, AdminSchema, GroupSchema, DramaSchema, SeasonSchema,
    EpisodeSchema, TelegramFileSchema, WatchlistSchema, FavoriteSchema,
    WatchProgressSchema, SearchHistorySchema, SearchLogSchema,
    DramaRequestSchema, RequestVoteSchema, NotificationSchema,
    SubscriptionSchema, PaymentSchema, BotSettingsSchema,
    WebSettingsSchema, AIConversationSchema, AuditLogSchema,
    UserModel, AdminModel, GroupModel, DramaModel, SeasonModel,
    EpisodeModel, TelegramFileModel, WatchlistModel, FavoriteModel,
    WatchProgressModel, SearchHistoryModel, SearchLogModel,
    DramaRequestModel, RequestVoteModel, NotificationModel,
    SubscriptionModel, PaymentModel, BotSettingsModel,
    WebSettingsModel, AIConversationModel, AuditLogModel
)
from .repositories import (
    users_repo, admins_repo, subscriptions_repo,
    watchlists_repo, favorites_repo, watch_progress_repo,
    dramas_repo, seasons_repo, episodes_repo, telegram_files_repo,
    drama_requests_repo, request_votes_repo,
    search_history_repo, search_logs_repo,
    notifications_repo, ai_conversations_repo,
    groups_repo, bot_settings_repo, web_settings_repo,
    payments_repo, audit_logs_repo
)

__all__ = [
    "DatabaseConnectionManager", "db_manager", "get_database",
    "ensure_all_indexes", "INDEX_DEFINITIONS",
    "PaginationParams", "PaginatedResult",
    "DatabaseError", "DuplicateKeyError", "DocumentNotFoundError", "ValidationError", "ConnectionError",
    "BaseRepository",
    "UserSchema", "AdminSchema", "GroupSchema", "DramaSchema", "SeasonSchema",
    "EpisodeSchema", "TelegramFileSchema", "WatchlistSchema", "FavoriteSchema",
    "WatchProgressSchema", "SearchHistorySchema", "SearchLogSchema",
    "DramaRequestSchema", "RequestVoteSchema", "NotificationSchema",
    "SubscriptionSchema", "PaymentSchema", "BotSettingsSchema",
    "WebSettingsSchema", "AIConversationSchema", "AuditLogSchema",
    "UserModel", "AdminModel", "GroupModel", "DramaModel", "SeasonModel",
    "EpisodeModel", "TelegramFileModel", "WatchlistModel", "FavoriteModel",
    "WatchProgressModel", "SearchHistoryModel", "SearchLogModel",
    "DramaRequestModel", "RequestVoteModel", "NotificationModel",
    "SubscriptionModel", "PaymentModel", "BotSettingsModel",
    "WebSettingsModel", "AIConversationModel", "AuditLogModel",
    "users_repo", "admins_repo", "subscriptions_repo",
    "watchlists_repo", "favorites_repo", "watch_progress_repo",
    "dramas_repo", "seasons_repo", "episodes_repo", "telegram_files_repo",
    "drama_requests_repo", "request_votes_repo",
    "search_history_repo", "search_logs_repo",
    "notifications_repo", "ai_conversations_repo",
    "groups_repo", "bot_settings_repo", "web_settings_repo",
    "payments_repo", "audit_logs_repo"
]
