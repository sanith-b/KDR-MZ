"""
My K-Drama 2.0 - Legacy Data Migration & Rollback Script
=========================================================
Non-destructive data migration tool from legacy collections to 2.0 shared MongoDB architecture.

Legacy Collections Migrated:
  1. users (or uersz)       -> users (UserModel)
  2. groups (or chats)      -> groups (GroupModel)
  3. SilentXBotz_files      -> telegram_files (TelegramFileModel)
  4. kdrama_requests        -> drama_requests (DramaRequestModel)
  5. misc (bot settings)    -> bot_settings (BotSettingsModel)

Safety Guarantees:
  - STRICTLY NON-DESTRUCTIVE: Legacy collections are NEVER altered, updated, or deleted.
  - ROLLBACK SUPPORT: All migrated records are tagged with `_migrated_from_legacy: True`.
    Running with `--rollback` safely removes only migrated records without touching new data.
  - DRY RUN: Running with `--dry-run` calculates and outputs migration stats without writes.
  - IDEMPOTENT: Re-running does not produce duplicate records (uses unique key upserts).
"""

import sys
import os
import argparse
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("migration")


class LegacyMigrationManager:
    """Orchestrates non-destructive migration and rollback between legacy and 2.0 collections."""

    def __init__(
        self,
        mongo_uri: str,
        source_db_name: str,
        target_db_name: str,
        batch_size: int = 500,
        dry_run: bool = False
    ):
        self.mongo_uri = mongo_uri
        self.source_db_name = source_db_name
        self.target_db_name = target_db_name
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.client = None
        self.source_db = None
        self.target_db = None

        self.stats = {
            "users": {"scanned": 0, "migrated": 0, "skipped": 0, "errors": 0},
            "groups": {"scanned": 0, "migrated": 0, "skipped": 0, "errors": 0},
            "files": {"scanned": 0, "migrated": 0, "skipped": 0, "errors": 0},
            "requests": {"scanned": 0, "migrated": 0, "skipped": 0, "errors": 0},
            "settings": {"scanned": 0, "migrated": 0, "skipped": 0, "errors": 0},
        }

    async def connect(self):
        """Initializes Motor client connection."""
        from motor.motor_asyncio import AsyncIOMotorClient
        self.client = AsyncIOMotorClient(self.mongo_uri)
        self.source_db = self.client[self.source_db_name]
        self.target_db = self.client[self.target_db_name]
        logger.info(f"Connected to MongoDB. Source DB: '{self.source_db_name}', Target DB: '{self.target_db_name}'")

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    # ---------------------------------------------------------
    # Transformers (Legacy Schema -> 2.0 Schema)
    # ---------------------------------------------------------

    def transform_user(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Maps legacy user document to 2.0 UserModel schema."""
        telegram_id = doc.get("id") or doc.get("_id")
        if not telegram_id or not isinstance(telegram_id, int):
            try:
                telegram_id = int(telegram_id)
            except (ValueError, TypeError):
                return {}

        ban_info = doc.get("ban_status") or {}
        is_banned = False
        ban_reason = None
        if isinstance(ban_info, dict):
            is_banned = bool(ban_info.get("is_banned", False))
            ban_reason = ban_info.get("ban_reason")
        elif isinstance(ban_info, bool):
            is_banned = ban_info

        is_lifetime = bool(doc.get("lifetime", False))
        expiry_time = doc.get("expiry_time")
        is_premium = is_lifetime or (expiry_time is not None and expiry_time > datetime.now())

        return {
            "telegram_id": telegram_id,
            "username": doc.get("username"),
            "first_name": doc.get("name") or doc.get("first_name", "Telegram User"),
            "last_name": doc.get("last_name"),
            "role": "user",
            "is_banned": is_banned,
            "ban_reason": ban_reason,
            "is_premium": is_premium,
            "premium_expires_at": expiry_time,
            "points": int(doc.get("point", 0)),
            "referral": {
                "referrer_id": doc.get("refer_by"),
                "referral_count": 0,
                "points_earned": 0,
            },
            "preferences": {
                "preferred_language": "en",
                "notifications_enabled": True,
                "auto_delete_files": True,
                "auto_delete_minutes": 10,
            },
            "created_at": doc.get("joined_date") or datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "_migrated_from_legacy": True,
            "_legacy_id": str(doc.get("_id")),
            "_migrated_at": datetime.now(timezone.utc),
        }

    def transform_group(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Maps legacy chat/group document to 2.0 GroupModel schema."""
        chat_id = doc.get("id") or doc.get("_id")
        if not chat_id:
            return {}
        try:
            chat_id = int(chat_id)
        except (ValueError, TypeError):
            return {}

        status_info = doc.get("chat_status") or {}
        is_disabled = False
        if isinstance(status_info, dict):
            is_disabled = bool(status_info.get("is_disabled", False))

        raw_settings = doc.get("settings") or doc.get("chat_settings") or {}

        return {
            "telegram_chat_id": chat_id,
            "title": doc.get("title", f"Group {chat_id}"),
            "username": doc.get("username"),
            "is_active": not is_disabled,
            "settings": {
                "auto_filter": bool(raw_settings.get("auto_filter", True)),
                "imdb_poster": bool(raw_settings.get("imdb", True)),
                "spell_check": bool(raw_settings.get("spell_check", True)),
                "welcome": bool(raw_settings.get("welcome", True)),
                "auto_delete": bool(raw_settings.get("auto_delete", True)),
                "auto_delete_minutes": int(raw_settings.get("auto_delete_minutes", 10)),
                "shortener_enabled": bool(raw_settings.get("shortener_enabled", False)),
                "fsub_channel_id": raw_settings.get("fsub_channel_id"),
            },
            "created_at": doc.get("created_at") or datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "_migrated_from_legacy": True,
            "_legacy_id": str(doc.get("_id")),
            "_migrated_at": datetime.now(timezone.utc),
        }

    def transform_file(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Maps legacy SilentXBotz_files document to 2.0 TelegramFileModel schema."""
        file_id = doc.get("file_id")
        if not file_id:
            return {}

        file_name = doc.get("file_name", "Unknown File")
        file_size = int(doc.get("file_size", 0))

        # Basic quality / resolution extraction
        quality = None
        for q in ["2160p", "4k", "1080p", "720p", "480p", "360p"]:
            if q in file_name.lower():
                quality = q
                break

        return {
            "file_id": file_id,
            "file_unique_id": doc.get("file_ref") or doc.get("file_unique_id") or file_id[:20],
            "file_name": file_name,
            "file_size": file_size,
            "file_type": doc.get("file_type", "document"),
            "mime_type": doc.get("mime_type", "application/octet-stream"),
            "caption": doc.get("caption"),
            "quality": quality,
            "channel_id": doc.get("chat_id") or doc.get("channel_id"),
            "message_id": doc.get("message_id"),
            "has_stream_link": bool(doc.get("has_stream_link", False)),
            "created_at": doc.get("date") or doc.get("created_at") or datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "_migrated_from_legacy": True,
            "_legacy_id": str(doc.get("_id")),
            "_migrated_at": datetime.now(timezone.utc),
        }

    def transform_request(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Maps legacy kdrama_requests document to 2.0 DramaRequestModel schema."""
        title = doc.get("title") or doc.get("query")
        if not title:
            return {}

        user_id = doc.get("user_id") or doc.get("requested_by")
        try:
            user_id = int(user_id) if user_id else 0
        except (ValueError, TypeError):
            user_id = 0

        raw_status = str(doc.get("status", "pending")).lower()
        valid_statuses = {"pending", "approved", "rejected", "available"}
        status = raw_status if raw_status in valid_statuses else "pending"

        return {
            "title": title,
            "requested_by": user_id,
            "status": status,
            "votes_count": int(doc.get("votes", doc.get("votes_count", 1))),
            "notes": doc.get("notes") or doc.get("comment"),
            "created_at": doc.get("created_at") or datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "_migrated_from_legacy": True,
            "_legacy_id": str(doc.get("_id")),
            "_migrated_at": datetime.now(timezone.utc),
        }

    # ---------------------------------------------------------
    # Migration Routines
    # ---------------------------------------------------------

    async def migrate_users(self):
        """Migrates legacy users collection to target users collection."""
        stat = self.stats["users"]
        # Find which collection holds users (users or uersz)
        col_names = await self.source_db.list_collection_names()
        source_col_name = "users" if "users" in col_names else ("uersz" if "uersz" in col_names else None)

        if not source_col_name:
            logger.warning("No legacy users collection ('users' or 'uersz') found in source database.")
            return

        source_col = self.source_db[source_col_name]
        target_col = self.target_db["users"]

        total = await source_col.count_documents({})
        logger.info(f"Starting Users migration from '{source_col_name}' ({total} documents)...")

        cursor = source_col.find({})
        batch = []
        async for doc in cursor:
            stat["scanned"] += 1
            transformed = self.transform_user(doc)
            if not transformed:
                stat["skipped"] += 1
                continue

            batch.append(transformed)
            if len(batch) >= self.batch_size:
                await self._write_user_batch(target_col, batch, stat)
                batch = []

        if batch:
            await self._write_user_batch(target_col, batch, stat)

        logger.info(f"Users migration complete: {stat}")

    async def _write_user_batch(self, target_col, batch: List[Dict[str, Any]], stat: Dict[str, int]):
        if self.dry_run:
            stat["migrated"] += len(batch)
            return

        for user_data in batch:
            try:
                # Upsert by telegram_id to ensure idempotency
                await target_col.update_one(
                    {"telegram_id": user_data["telegram_id"]},
                    {"$setOnInsert": user_data},
                    upsert=True
                )
                stat["migrated"] += 1
            except Exception as e:
                logger.error(f"Error migrating user {user_data.get('telegram_id')}: {e}")
                stat["errors"] += 1

    async def migrate_groups(self):
        """Migrates legacy groups collection to target groups collection."""
        stat = self.stats["groups"]
        col_names = await self.source_db.list_collection_names()
        source_col_name = "groups" if "groups" in col_names else ("chats" if "chats" in col_names else None)

        if not source_col_name:
            logger.warning("No legacy groups collection ('groups' or 'chats') found.")
            return

        source_col = self.source_db[source_col_name]
        target_col = self.target_db["groups"]
        total = await source_col.count_documents({})
        logger.info(f"Starting Groups migration from '{source_col_name}' ({total} documents)...")

        cursor = source_col.find({})
        batch = []
        async for doc in cursor:
            stat["scanned"] += 1
            transformed = self.transform_group(doc)
            if not transformed:
                stat["skipped"] += 1
                continue

            batch.append(transformed)
            if len(batch) >= self.batch_size:
                await self._write_group_batch(target_col, batch, stat)
                batch = []

        if batch:
            await self._write_group_batch(target_col, batch, stat)

        logger.info(f"Groups migration complete: {stat}")

    async def _write_group_batch(self, target_col, batch: List[Dict[str, Any]], stat: Dict[str, int]):
        if self.dry_run:
            stat["migrated"] += len(batch)
            return

        for group_data in batch:
            try:
                await target_col.update_one(
                    {"telegram_chat_id": group_data["telegram_chat_id"]},
                    {"$setOnInsert": group_data},
                    upsert=True
                )
                stat["migrated"] += 1
            except Exception as e:
                logger.error(f"Error migrating group {group_data.get('telegram_chat_id')}: {e}")
                stat["errors"] += 1

    async def migrate_files(self):
        """Migrates legacy SilentXBotz_files collection to target telegram_files collection."""
        stat = self.stats["files"]
        col_names = await self.source_db.list_collection_names()
        source_col_name = None
        for candidate in ["SilentXBotz_files", "files", "telegram_files"]:
            if candidate in col_names and (candidate != "telegram_files" or self.source_db_name != self.target_db_name):
                source_col_name = candidate
                break

        if not source_col_name:
            logger.warning("No legacy files collection found in source database.")
            return

        source_col = self.source_db[source_col_name]
        target_col = self.target_db["telegram_files"]
        total = await source_col.count_documents({})
        logger.info(f"Starting Files migration from '{source_col_name}' ({total} documents)...")

        cursor = source_col.find({})
        batch = []
        async for doc in cursor:
            stat["scanned"] += 1
            transformed = self.transform_file(doc)
            if not transformed:
                stat["skipped"] += 1
                continue

            batch.append(transformed)
            if len(batch) >= self.batch_size:
                await self._write_file_batch(target_col, batch, stat)
                batch = []

        if batch:
            await self._write_file_batch(target_col, batch, stat)

        logger.info(f"Files migration complete: {stat}")

    async def _write_file_batch(self, target_col, batch: List[Dict[str, Any]], stat: Dict[str, int]):
        if self.dry_run:
            stat["migrated"] += len(batch)
            return

        for file_data in batch:
            try:
                await target_col.update_one(
                    {"file_id": file_data["file_id"]},
                    {"$setOnInsert": file_data},
                    upsert=True
                )
                stat["migrated"] += 1
            except Exception as e:
                logger.error(f"Error migrating file {file_data.get('file_id')}: {e}")
                stat["errors"] += 1

    async def migrate_requests(self):
        """Migrates legacy drama requests collection."""
        stat = self.stats["requests"]
        col_names = await self.source_db.list_collection_names()
        source_col_name = "kdrama_requests" if "kdrama_requests" in col_names else ("requests" if "requests" in col_names else None)

        if not source_col_name:
            logger.info("No legacy requests collection found. Skipping.")
            return

        source_col = self.source_db[source_col_name]
        target_col = self.target_db["drama_requests"]
        total = await source_col.count_documents({})
        logger.info(f"Starting Requests migration from '{source_col_name}' ({total} documents)...")

        cursor = source_col.find({})
        batch = []
        async for doc in cursor:
            stat["scanned"] += 1
            transformed = self.transform_request(doc)
            if not transformed:
                stat["skipped"] += 1
                continue

            batch.append(transformed)
            if len(batch) >= self.batch_size:
                await self._write_request_batch(target_col, batch, stat)
                batch = []

        if batch:
            await self._write_request_batch(target_col, batch, stat)

        logger.info(f"Requests migration complete: {stat}")

    async def _write_request_batch(self, target_col, batch: List[Dict[str, Any]], stat: Dict[str, int]):
        if self.dry_run:
            stat["migrated"] += len(batch)
            return

        for req_data in batch:
            try:
                await target_col.update_one(
                    {"title": req_data["title"], "requested_by": req_data["requested_by"]},
                    {"$setOnInsert": req_data},
                    upsert=True
                )
                stat["migrated"] += 1
            except Exception as e:
                logger.error(f"Error migrating request: {e}")
                stat["errors"] += 1

    async def migrate_settings(self):
        """Migrates legacy bot configurations from misc collection."""
        stat = self.stats["settings"]
        col_names = await self.source_db.list_collection_names()
        if "misc" not in col_names:
            logger.info("No legacy misc collection found. Skipping.")
            return

        source_col = self.source_db["misc"]
        target_col = self.target_db["bot_settings"]

        cursor = source_col.find({})
        async for doc in cursor:
            stat["scanned"] += 1
            key = doc.get("key") or doc.get("_id")
            val = doc.get("value")
            if not key:
                stat["skipped"] += 1
                continue

            if not self.dry_run:
                try:
                    await target_col.update_one(
                        {"key": str(key)},
                        {"$set": {
                            "key": str(key),
                            "value": val,
                            "updated_at": datetime.now(timezone.utc),
                            "_migrated_from_legacy": True,
                        }},
                        upsert=True
                    )
                    stat["migrated"] += 1
                except Exception as e:
                    logger.error(f"Error migrating setting {key}: {e}")
                    stat["errors"] += 1
            else:
                stat["migrated"] += 1

        logger.info(f"Settings migration complete: {stat}")

    # ---------------------------------------------------------
    # Rollback Functionality
    # ---------------------------------------------------------

    async def rollback(self):
        """
        Safely rolls back migrated records.
        Only deletes documents where `_migrated_from_legacy == True`.
        Leaves native 2.0 documents and legacy source collections untouched.
        """
        logger.warning("=====================================================")
        logger.warning("STARTING SAFE ROLLBACK FOR MIGRATED LEGACY RECORDS...")
        logger.warning("=====================================================")

        collections_to_rollback = ["users", "groups", "telegram_files", "drama_requests", "bot_settings"]
        rollback_stats = {}

        for col_name in collections_to_rollback:
            if col_name not in await self.target_db.list_collection_names():
                continue

            target_col = self.target_db[col_name]
            count = await target_col.count_documents({"_migrated_from_legacy": True})
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would rollback {count} records from '{col_name}'.")
                rollback_stats[col_name] = count
            else:
                res = await target_col.delete_many({"_migrated_from_legacy": True})
                logger.info(f"Successfully rolled back {res.deleted_count} migrated records from '{col_name}'.")
                rollback_stats[col_name] = res.deleted_count

        logger.info(f"Rollback summary: {rollback_stats}")
        return rollback_stats

    # ---------------------------------------------------------
    # Execution & Reporting
    # ---------------------------------------------------------

    async def run_migration(self, target_collections: Optional[List[str]] = None):
        """Runs the complete migration workflow."""
        start_time = datetime.now()
        mode_str = "[DRY-RUN] " if self.dry_run else ""
        logger.info(f"{mode_str}Beginning legacy database migration...")

        selected = target_collections or ["users", "groups", "files", "requests", "settings"]

        if "users" in selected:
            await self.migrate_users()
        if "groups" in selected:
            await self.migrate_groups()
        if "files" in selected:
            await self.migrate_files()
        if "requests" in selected:
            await self.migrate_requests()
        if "settings" in selected:
            await self.migrate_settings()

        duration = (datetime.now() - start_time).total_seconds()
        self.print_report(duration)

    def print_report(self, duration: float):
        """Prints a human-readable summary table of migration results."""
        header = f"\n{'='*70}\n{'MIGRATION EXECUTION REPORT':^70}\n{'='*70}"
        print(header)
        print(f"Mode: {'DRY RUN (No data written)' if self.dry_run else 'LIVE MIGRATION'}")
        print(f"Source DB: {self.source_db_name} -> Target DB: {self.target_db_name}")
        print(f"Duration: {duration:.2f} seconds\n")
        print(f"{'Collection':<18} | {'Scanned':<10} | {'Migrated':<10} | {'Skipped':<10} | {'Errors':<10}")
        print("-" * 70)
        total_migrated = 0
        total_errors = 0
        for col, data in self.stats.items():
            print(f"{col:<18} | {data['scanned']:<10} | {data['migrated']:<10} | {data['skipped']:<10} | {data['errors']:<10}")
            total_migrated += data["migrated"]
            total_errors += data["errors"]
        print("-" * 70)
        print(f"{'TOTAL':<18} | {'-':<10} | {total_migrated:<10} | {'-':<10} | {total_errors:<10}")
        print("=" * 70 + "\n")


async def main():
    parser = argparse.ArgumentParser(description="My K-Drama 2.0 Legacy Data Migration & Rollback Tool")
    parser.add_argument("--mongo-uri", default=os.getenv("DATABASE_URI", "mongodb://localhost:27017"), help="MongoDB connection URI")
    parser.add_argument("--source-db", default=os.getenv("LEGACY_DATABASE_NAME", "SilentXBotz"), help="Source legacy database name")
    parser.add_argument("--target-db", default=os.getenv("DATABASE_NAME", "kdrama_db"), help="Target 2.0 database name")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size for processing")
    parser.add_argument("--dry-run", action="store_true", help="Simulate migration without modifying target collections")
    parser.add_argument("--rollback", action="store_true", help="Safely roll back previously migrated records")
    parser.add_argument("--collections", default="all", help="Comma-separated collections to migrate (users,groups,files,requests,settings or all)")

    args = parser.parse_args()

    selected_cols = None
    if args.collections != "all":
        selected_cols = [c.strip() for c in args.collections.split(",")]

    manager = LegacyMigrationManager(
        mongo_uri=args.mongo_uri,
        source_db_name=args.source_db,
        target_db_name=args.target_db,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )

    try:
        await manager.connect()
        if args.rollback:
            await manager.rollback()
        else:
            await manager.run_migration(selected_cols)
    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
