import asyncio
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from shared.database.connection import DatabaseConnection
from logging_helper import LOGGER

class BackgroundTaskManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._bot_client = None

    def set_bot_client(self, bot_client):
        self._bot_client = bot_client

    async def schedule_auto_delete(self, chat_id: int, message_id: int, delay_seconds: int = 43200):
        """Schedule persistent message deletion in MongoDB instead of sleeping in handlers"""
        db = DatabaseConnection.get_db()
        if db is not None:
            delete_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=delay_seconds)
            await db.ephemeral_messages.insert_one({
                "chat_id": chat_id,
                "message_id": message_id,
                "delete_at": delete_at
            })

    async def process_ephemeral_deletions(self):
        """Worker job: clean up expired messages"""
        if not self._bot_client:
            return
        db = DatabaseConnection.get_db()
        if db is None:
            return

        now = datetime.datetime.utcnow()
        cursor = db.ephemeral_messages.find({"delete_at": {"$lte": now}}).limit(100)
        async for doc in cursor:
            try:
                await self._bot_client.delete_messages(
                    chat_id=doc["chat_id"],
                    message_ids=doc["message_id"]
                )
            except Exception:
                pass
            finally:
                await db.ephemeral_messages.delete_one({"_id": doc["_id"]})

    def start(self, bot_client=None):
        if bot_client:
            self.set_bot_client(bot_client)
        # Check expired ephemeral messages every 30 seconds
        self.scheduler.add_job(self.process_ephemeral_deletions, 'interval', seconds=30)
        self.scheduler.start()
        LOGGER.info("✅ Background Scheduler started (Ephemeral Message & Expiry tasks).")

background_worker = BackgroundTaskManager()
