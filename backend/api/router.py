"""
Central API Router for My K-Drama 2.0 Backend
Aggregates all 17 domain route modules under /api/v1.
"""
from fastapi import APIRouter
from backend.api.v1.auth import router as auth_router
from backend.api.v1.users import router as users_router
from backend.api.v1.dramas import router as dramas_router
from backend.api.v1.seasons import router as seasons_router
from backend.api.v1.episodes import router as episodes_router
from backend.api.v1.files import router as files_router
from backend.api.v1.search import router as search_router
from backend.api.v1.watchlist import router as watchlist_router
from backend.api.v1.favorites import router as favorites_router
from backend.api.v1.progress import router as progress_router
from backend.api.v1.history import router as history_router
from backend.api.v1.recommendations import router as recommendations_router
from backend.api.v1.requests import router as requests_router
from backend.api.v1.notifications import router as notifications_router
from backend.api.v1.subscriptions import router as subscriptions_router
from backend.api.v1.admin import router as admin_router
from backend.api.v1.analytics import router as analytics_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(dramas_router)
api_router.include_router(seasons_router)
api_router.include_router(episodes_router)
api_router.include_router(files_router)
api_router.include_router(search_router)
api_router.include_router(watchlist_router)
api_router.include_router(favorites_router)
api_router.include_router(progress_router)
api_router.include_router(history_router)
api_router.include_router(recommendations_router)
api_router.include_router(requests_router)
api_router.include_router(notifications_router)
api_router.include_router(subscriptions_router)
api_router.include_router(admin_router)
api_router.include_router(analytics_router)
