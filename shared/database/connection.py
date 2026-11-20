"""
Database Connection Manager for My K-Drama 2.0
Handles AsyncIOMotorClient connections, pooling, health checks, and lifecycle events.
"""
import asyncio
from typing import Optional, Dict, Any
import motor.motor_asyncio
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from shared.config.settings import settings
from shared.database.errors import ConnectionError
from logging_helper import LOGGER

class DatabaseConnectionManager:
    _instance: Optional["DatabaseConnectionManager"] = None
    _client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
    _db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
    _client2: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
    _db2: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
    _is_connected: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    async def connect(cls) -> motor.motor_asyncio.AsyncIOMotorDatabase:
        """Initialize primary and optional secondary database connections"""
        if cls._client is not None and cls._is_connected:
            return cls._db

        uri = settings.DATABASE_URI
        if not uri:
            LOGGER.warning("DATABASE_URI not set. Running without database connection.")
            return None

        try:
            LOGGER.info(f"Connecting to MongoDB database: {settings.DATABASE_NAME}...")
            cls._client = motor.motor_asyncio.AsyncIOMotorClient(
                uri,
                maxPoolSize=50,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
                retryWrites=True
            )
            # Ping database to verify connection
            await cls._client.admin.command('ping')
            cls._db = cls._client[settings.DATABASE_NAME]
            cls._is_connected = True
            LOGGER.info(f"✅ Connected to Primary MongoDB [{settings.DATABASE_NAME}] successfully.")

            # Secondary DB connection (if MULTIPLE_DB configured)
            if settings.MULTIPLE_DB and settings.DATABASE_URI2:
                try:
                    cls._client2 = motor.motor_asyncio.AsyncIOMotorClient(
                        settings.DATABASE_URI2,
                        maxPoolSize=20,
                        minPoolSize=5,
                        serverSelectionTimeoutMS=5000
                    )
                    await cls._client2.admin.command('ping')
                    cls._db2 = cls._client2[settings.DATABASE_NAME]
                    LOGGER.info("✅ Connected to Secondary MongoDB successfully.")
                except Exception as e2:
                    LOGGER.error(f"⚠️ Failed connecting to Secondary MongoDB: {e2}")

            return cls._db
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            cls._is_connected = False
            LOGGER.error(f"❌ MongoDB connection failed: {e}")
            raise ConnectionError(f"Could not connect to MongoDB: {str(e)}")

    @classmethod
    async def disconnect(cls):
        """Gracefully close all MongoDB client sessions and pools"""
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            cls._db = None
            cls._is_connected = False
            LOGGER.info("Primary MongoDB connection closed.")

        if cls._client2 is not None:
            cls._client2.close()
            cls._client2 = None
            cls._db2 = None
            LOGGER.info("Secondary MongoDB connection closed.")

    @classmethod
    def get_client(cls) -> Optional[motor.motor_asyncio.AsyncIOMotorClient]:
        if cls._client is None and settings.DATABASE_URI:
            cls._client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.DATABASE_URI,
                maxPoolSize=50,
                minPoolSize=10
            )
        return cls._client

    @classmethod
    def get_db(cls) -> Optional[motor.motor_asyncio.AsyncIOMotorDatabase]:
        if cls._db is None:
            client = cls.get_client()
            if client is not None:
                cls._db = client[settings.DATABASE_NAME]
        return cls._db

    @classmethod
    def get_secondary_db(cls) -> Optional[motor.motor_asyncio.AsyncIOMotorDatabase]:
        if settings.MULTIPLE_DB and settings.DATABASE_URI2:
            if cls._client2 is None:
                cls._client2 = motor.motor_asyncio.AsyncIOMotorClient(
                    settings.DATABASE_URI2,
                    maxPoolSize=20
                )
                cls._db2 = cls._client2[settings.DATABASE_NAME]
            return cls._db2
        return None

    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """Perform live health ping against MongoDB cluster"""
        if cls._client is None:
            return {"status": "disconnected", "database": settings.DATABASE_NAME}
        try:
            start_time = asyncio.get_event_loop().time()
            await cls._client.admin.command('ping')
            latency_ms = round((asyncio.get_event_loop().time() - start_time) * 1000, 2)
            return {
                "status": "healthy",
                "database": settings.DATABASE_NAME,
                "latency_ms": latency_ms,
                "multiple_db": settings.MULTIPLE_DB
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database": settings.DATABASE_NAME
            }

# Global convenient helpers
DatabaseConnection = DatabaseConnectionManager
db_manager = DatabaseConnectionManager()

def get_database() -> Optional[motor.motor_asyncio.AsyncIOMotorDatabase]:
    return DatabaseConnectionManager.get_db()
