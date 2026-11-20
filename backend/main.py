"""
My K-Drama 2.0 - FastAPI Backend Server
Unified High-Performance REST API for Web Portal and External Clients.
Operates fully independently from the Telegram Bot.
"""
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.api.router import api_router
from backend.core.error_handlers import register_exception_handlers
from backend.core.logging_middleware import StructuredLoggingMiddleware
from shared.database.indexes import ensure_all_indexes
from shared.database.connection import DatabaseConnectionManager
from shared.cache.redis_client import cache
from shared.config.settings import settings
from logging_helper import LOGGER

@asynccontextmanager
async def lifespan(app: FastAPI):
    LOGGER.info("🚀 Starting My K-Drama 2.0 FastAPI Backend...")
    # Initialize Redis cache with in-memory fallback
    await cache.connect()
    # Verify and create MongoDB indexes across all 21 collections
    try:
        await ensure_all_indexes()
    except Exception as e:
        LOGGER.warning(f"Index verification warning: {e}")
    LOGGER.info("✅ FastAPI Backend initialized and ready for requests.")
    yield
    LOGGER.info("🛑 Shutting down My K-Drama 2.0 FastAPI Backend...")

app = FastAPI(
    title="My K-Drama 2.0 API",
    description="Comprehensive Backend API for My K-Drama Platform. Provides drama catalog, streaming, user library, and admin operations.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 1. Structured Logging Middleware
app.add_middleware(StructuredLoggingMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Standardized Exception Handlers
register_exception_handlers(app)

# 4. Include All 17 API Routers
app.include_router(api_router)

# 5. Root & Health Endpoints
@app.get("/", tags=["Health"])
async def root():
    return {
        "app": "My K-Drama 2.0 API",
        "status": "online",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness probe"""
    return {
        "status": "healthy",
        "version": "2.0.0"
    }

@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe checking MongoDB and Redis connectivity"""
    db_health = await DatabaseConnectionManager.health_check()
    cache_status = "connected" if cache._connected else "in-memory-fallback"
    
    is_ready = db_health.get("status") == "healthy"
    return {
        "status": "ready" if is_ready else "degraded",
        "database": db_health,
        "cache": cache_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.BIND_ADDRESS, port=settings.WEB_PORT, reload=True)
