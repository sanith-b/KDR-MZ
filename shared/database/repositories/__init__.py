"""
Repository Exports for My K-Drama 2.0
Provides unified access to all 21 database repositories.
"""
from .base import BaseRepository
from .users_repo import (
    users_repo, admins_repo, subscriptions_repo,
    watchlists_repo, favorites_repo, watch_progress_repo
)
from .dramas_repo import (
    dramas_repo, seasons_repo, episodes_repo, telegram_files_repo
)
from .requests_repo import (
    drama_requests_repo, request_votes_repo
)
from .interactions_repo import (
    search_history_repo, search_logs_repo,
    notifications_repo, ai_conversations_repo
)
from .operations_repo import (
    groups_repo, bot_settings_repo, web_settings_repo,
    payments_repo, audit_logs_repo
)

__all__ = [
    "BaseRepository",
    "users_repo",
    "admins_repo",
    "subscriptions_repo",
    "watchlists_repo",
    "favorites_repo",
    "watch_progress_repo",
    "dramas_repo",
    "seasons_repo",
    "episodes_repo",
    "telegram_files_repo",
    "drama_requests_repo",
    "request_votes_repo",
    "search_history_repo",
    "search_logs_repo",
    "notifications_repo",
    "ai_conversations_repo",
    "groups_repo",
    "bot_settings_repo",
    "web_settings_repo",
    "payments_repo",
    "audit_logs_repo",
]
