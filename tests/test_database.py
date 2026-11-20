"""
My K-Drama 2.0 - Database Architecture Test Suite
===================================================
Tests for MongoDB 2.0 async database layer:
  1. CRUD Operations on BaseRepository and domain repositories.
  2. Index definitions across all 21 domain entities.
  3. Duplicate record prevention and DuplicateKeyError mapping.
  4. Pagination parameters and paginated result calculations.
  5. Schema integrity and default field behavior.
"""

import sys
import os
import unittest
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import asyncio

# Setup path and environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ---------------------------------------------------------------------------
# Dependency Shims (Enables running in environments without pre-installed packages)
# ---------------------------------------------------------------------------
try:
    import pymongo
    import pymongo.errors
    import motor
    import motor.motor_asyncio
    import pydantic
    import pydantic_settings
except ImportError:
    import types
    pymongo_mod = types.ModuleType('pymongo')
    pymongo_mod.ASCENDING = 1
    pymongo_mod.DESCENDING = -1
    pymongo_mod.TEXT = 'text'

    class IndexModel:
        def __init__(self, keys, **kwargs):
            self.keys = keys
            self.kwargs = kwargs
    pymongo_mod.IndexModel = IndexModel

    pymongo_errors = types.ModuleType('pymongo.errors')
    class PyMongoError(Exception): pass
    class DuplicateKeyError(PyMongoError): pass
    class ConnectionFailure(PyMongoError): pass
    class ServerSelectionTimeoutError(PyMongoError): pass
    pymongo_errors.PyMongoError = PyMongoError
    pymongo_errors.DuplicateKeyError = DuplicateKeyError
    pymongo_errors.ConnectionFailure = ConnectionFailure
    pymongo_errors.ServerSelectionTimeoutError = ServerSelectionTimeoutError
    pymongo_mod.errors = pymongo_errors
    sys.modules['pymongo'] = pymongo_mod
    sys.modules['pymongo.errors'] = pymongo_errors

    motor_mod = types.ModuleType('motor')
    motor_asyncio = types.ModuleType('motor.motor_asyncio')
    class MockAsyncIOMotorClient: pass
    class MockAsyncIOMotorDatabase: pass
    class MockAsyncIOMotorCollection: pass
    motor_asyncio.AsyncIOMotorClient = MockAsyncIOMotorClient
    motor_asyncio.AsyncIOMotorDatabase = MockAsyncIOMotorDatabase
    motor_asyncio.AsyncIOMotorCollection = MockAsyncIOMotorCollection
    motor_mod.motor_asyncio = motor_asyncio
    sys.modules['motor'] = motor_mod
    sys.modules['motor.motor_asyncio'] = motor_asyncio

    def _mock_field(default=..., default_factory=None, **kwargs):
        if default_factory is not None:
            try:
                return default_factory()
            except Exception:
                return None
        if default is not ...:
            return default
        return None

    class MockBaseModel:
        def __init__(self, **data):
            for k in dir(self.__class__):
                if not k.startswith('_'):
                    try:
                        v = getattr(self.__class__, k)
                        if not callable(v) and not isinstance(v, property):
                            setattr(self, k, v)
                    except Exception:
                        pass
            for k, v in data.items():
                setattr(self, k, v)
        def model_dump(self, **kwargs):
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        def dict(self, **kwargs):
            return self.model_dump(**kwargs)

    pydantic_mod = types.ModuleType('pydantic')
    pydantic_mod.BaseModel = MockBaseModel
    pydantic_mod.Field = _mock_field
    pydantic_mod.EmailStr = str
    pydantic_mod.HttpUrl = str
    pydantic_mod.field_validator = lambda *args, **kwargs: (lambda f: f)
    sys.modules['pydantic'] = pydantic_mod

    pydantic_settings = types.ModuleType('pydantic_settings')
    class BaseSettings(MockBaseModel):
        model_config = {}
    pydantic_settings.BaseSettings = BaseSettings
    sys.modules['pydantic_settings'] = pydantic_settings

# Import database module components
import shared.database as db
from shared.database.errors import (
    DatabaseError,
    DuplicateKeyError as CustomDuplicateKeyError,
    DocumentNotFoundError,
)
from shared.database.pagination import PaginationParams, PaginatedResult
from shared.database.indexes import INDEX_DEFINITIONS


# ---------------------------------------------------------------------------
# In-Memory Async Mock Collection for Testing Repositories
# ---------------------------------------------------------------------------
class MockAsyncCursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self.docs = docs
        self._skip = 0
        self._limit = None

    def sort(self, key_or_list, direction=1):
        return self

    def skip(self, count: int):
        self._skip = count
        return self

    def limit(self, count: int):
        self._limit = count
        return self

    async def to_list(self, length: Optional[int] = None):
        res = self.docs[self._skip:]
        if self._limit is not None:
            res = res[:self._limit]
        return [dict(d) for d in res]

    def __aiter__(self):
        self._iter = iter(self.docs[self._skip:None if self._limit is None else self._skip + self._limit])
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class MockInsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class MockUpdateResult:
    def __init__(self, matched_count, modified_count, upserted_id=None):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.upserted_id = upserted_id


class MockDeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class MockAsyncCollection:
    """Simulates Motor's AsyncIOMotorCollection in-memory with unique key enforcement."""

    def __init__(self, name: str, unique_keys: Optional[List[str]] = None):
        self.name = name
        self.docs: List[Dict[str, Any]] = []
        self.unique_keys = unique_keys or []
        self._id_counter = 1

    def _matches(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        for k, v in query.items():
            if k == "_id":
                if str(doc.get("_id")) != str(v):
                    return False
            elif doc.get(k) != v:
                return False
        return True

    async def insert_one(self, doc: Dict[str, Any]):
        # Check unique constraint violations
        for key in self.unique_keys:
            if key in doc and doc[key] is not None:
                for existing in self.docs:
                    if existing.get(key) == doc[key]:
                        # Simulate PyMongo's DuplicateKeyError
                        import pymongo.errors
                        raise pymongo.errors.DuplicateKeyError(f"E11000 duplicate key error collection: {self.name} index: {key}_1 dup key: {doc[key]}")

        doc_copy = dict(doc)
        if "_id" not in doc_copy:
            doc_copy["_id"] = str(self._id_counter)
            self._id_counter += 1

        self.docs.append(doc_copy)
        return MockInsertOneResult(doc_copy["_id"])

    async def find_one(self, query: Dict[str, Any]):
        for doc in self.docs:
            if self._matches(doc, query):
                return dict(doc)
        return None

    def find(self, query: Dict[str, Any]):
        matched = [doc for doc in self.docs if self._matches(doc, query)]
        return MockAsyncCursor(matched)

    async def count_documents(self, query: Dict[str, Any]):
        matched = [doc for doc in self.docs if self._matches(doc, query)]
        return len(matched)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        for doc in self.docs:
            if self._matches(doc, query):
                if "$set" in update:
                    doc.update(update["$set"])
                if "$inc" in update:
                    for ik, iv in update["$inc"].items():
                        doc[ik] = doc.get(ik, 0) + iv
                return MockUpdateResult(matched_count=1, modified_count=1)

        if upsert:
            new_doc = dict(query)
            if "$set" in update:
                new_doc.update(update["$set"])
            if "$setOnInsert" in update:
                new_doc.update(update["$setOnInsert"])
            await self.insert_one(new_doc)
            return MockUpdateResult(matched_count=0, modified_count=1, upserted_id=new_doc.get("_id"))

        return MockUpdateResult(matched_count=0, modified_count=0)

    async def delete_one(self, query: Dict[str, Any]):
        for i, doc in enumerate(self.docs):
            if self._matches(doc, query):
                self.docs.pop(i)
                return MockDeleteResult(deleted_count=1)
        return MockDeleteResult(deleted_count=0)

    async def delete_many(self, query: Dict[str, Any]):
        initial_len = len(self.docs)
        self.docs = [doc for doc in self.docs if not self._matches(doc, query)]
        return MockDeleteResult(deleted_count=initial_len - len(self.docs))

    async def create_indexes(self, indexes):
        return [f"idx_{i}" for i in range(len(indexes))]


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestPagination(unittest.TestCase):
    """Tests pagination parameters and paginated result helper."""

    def test_pagination_params_defaults(self):
        p = PaginationParams()
        self.assertEqual(p.page, 1)
        self.assertEqual(p.page_size, 20)
        self.assertEqual(p.skip, 0)
        self.assertEqual(p.limit, 20)

    def test_pagination_params_custom(self):
        p = PaginationParams(page=3, page_size=15)
        self.assertEqual(p.skip, 30)
        self.assertEqual(p.limit, 15)

    def test_paginated_result_calculation(self):
        items = [{"id": 1}, {"id": 2}]
        params = PaginationParams(page=1, page_size=20)
        res = PaginatedResult.create(items=items, total=45, params=params)
        self.assertEqual(res.page, 1)
        self.assertEqual(res.page_size, 20)
        self.assertEqual(res.total, 45)
        self.assertEqual(res.total_pages, 3)
        self.assertTrue(res.has_next)
        self.assertFalse(res.has_prev)

        # Last page
        params_last = PaginationParams(page=3, page_size=20)
        res_last = PaginatedResult.create(items=items, total=45, params=params_last)
        self.assertFalse(res_last.has_next)
        self.assertTrue(res_last.has_prev)


class TestIndexDefinitions(unittest.TestCase):
    """Tests automated index definitions for all 21 collections."""

    def test_all_21_collections_have_index_definitions(self):
        expected_collections = [
            "users", "admins", "groups", "dramas", "seasons", "episodes",
            "telegram_files", "watchlists", "favorites", "watch_progress",
            "search_history", "search_logs", "drama_requests", "request_votes",
            "notifications", "subscriptions", "payments", "bot_settings",
            "web_settings", "ai_conversations", "audit_logs"
        ]
        self.assertEqual(len(INDEX_DEFINITIONS), 21)
        for col_name in expected_collections:
            self.assertIn(col_name, INDEX_DEFINITIONS, f"Missing index definitions for '{col_name}'")
            indexes = INDEX_DEFINITIONS[col_name]
            self.assertTrue(len(indexes) > 0, f"Collection '{col_name}' has 0 index definitions")

    def test_unique_indexes_configured(self):
        # Users should have unique index on telegram_id
        user_indexes = INDEX_DEFINITIONS["users"]
        has_unique_telegram_id = any(
            idx.get("unique") is True and any(k[0] == "telegram_id" for k in idx.get("keys", []))
            for idx in user_indexes
        )
        self.assertTrue(has_unique_telegram_id, "Users collection must have a unique index on telegram_id")

        # Dramas should have unique index on slug
        drama_indexes = INDEX_DEFINITIONS["dramas"]
        has_unique_slug = any(
            idx.get("unique") is True and any(k[0] == "slug" for k in idx.get("keys", []))
            for idx in drama_indexes
        )
        self.assertTrue(has_unique_slug, "Dramas collection must have a unique index on slug")

        # Telegram files should have unique index on file_id
        file_indexes = INDEX_DEFINITIONS["telegram_files"]
        has_unique_file_id = any(
            idx.get("unique") is True and any(k[0] == "file_id" for k in idx.get("keys", []))
            for idx in file_indexes
        )
        self.assertTrue(has_unique_file_id, "Telegram files must have a unique index on file_id")

    def test_ttl_indexes_configured(self):
        # Search logs or search history should have expireAfterSeconds
        search_log_indexes = INDEX_DEFINITIONS["search_logs"]
        has_ttl = any("expireAfterSeconds" in idx for idx in search_log_indexes)
        self.assertTrue(has_ttl, "Search logs must have a TTL index configured")


class TestRepositoryCRUDAndDuplicates(unittest.TestCase):
    """Tests BaseRepository and domain repositories: CRUD, duplicate detection, and queries."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_crud_operations_base_repo(self):
        async def _test():
            mock_col = MockAsyncCollection("test_items")
            repo = db.BaseRepository(collection_name="test_items")
            repo._collection = mock_col

            # 1. CREATE
            item_data = {"name": "Item 1", "category": "drama", "active": True}
            created = await repo.create(item_data)
            self.assertIn("_id", created)
            self.assertEqual(created["name"], "Item 1")
            self.assertIn("created_at", created)
            self.assertIn("updated_at", created)

            # 2. READ (get_by_id)
            fetched = await repo.get_by_id(created["_id"])
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched["name"], "Item 1")

            # 3. READ (find_one)
            found = await repo.find_one({"category": "drama"})
            self.assertIsNotNone(found)
            self.assertEqual(found["_id"], created["_id"])

            # 4. UPDATE
            updated = await repo.update_by_id(created["_id"], {"name": "Item 1 Renamed"})
            self.assertTrue(updated)
            fetched_after_update = await repo.get_by_id(created["_id"])
            self.assertEqual(fetched_after_update["name"], "Item 1 Renamed")

            # 5. COUNT
            count = await repo.count({})
            self.assertEqual(count, 1)

            # 6. DELETE
            deleted = await repo.delete_by_id(created["_id"])
            self.assertTrue(deleted)
            fetched_after_delete = await repo.get_by_id(created["_id"])
            self.assertIsNone(fetched_after_delete)

        self.loop.run_until_complete(_test())

    def test_duplicate_key_error_prevention(self):
        async def _test():
            # Mock collection enforcing uniqueness on 'slug'
            mock_col = MockAsyncCollection("dramas", unique_keys=["slug"])
            repo = db.BaseRepository(collection_name="dramas")
            repo._collection = mock_col

            # Insert first drama
            drama_1 = {"title": "Crash Landing on You", "slug": "crash-landing-on-you"}
            await repo.create(drama_1)

            # Attempt duplicate insert with same slug
            drama_duplicate = {"title": "Another CLOY", "slug": "crash-landing-on-you"}
            with self.assertRaises(CustomDuplicateKeyError) as ctx:
                await repo.create(drama_duplicate)

            self.assertIn("crash-landing-on-you", str(ctx.exception))

        self.loop.run_until_complete(_test())

    def test_users_repository_specialized_methods(self):
        async def _test():
            mock_col = MockAsyncCollection("users", unique_keys=["telegram_id"])
            repo = db.users_repo
            repo._collection = mock_col

            # Create user
            user_doc = {
                "telegram_id": 99887766,
                "first_name": "Min-ho",
                "role": "user",
                "points": 50,
                "is_banned": False
            }
            created = await repo.create(user_doc)
            self.assertEqual(created["telegram_id"], 99887766)

            # Find by telegram_id
            user = await repo.get_by_telegram_id(99887766)
            self.assertIsNotNone(user)
            self.assertEqual(user["first_name"], "Min-ho")

            # Update points
            updated_user = await repo.update_points(99887766, delta=25)
            self.assertEqual(updated_user["points"], 75)

            # Ban user
            ban_success = await repo.ban_user(99887766, reason="Spamming")
            self.assertTrue(ban_success)
            banned_user = await repo.get_by_telegram_id(99887766)
            self.assertTrue(banned_user["is_banned"])
            self.assertEqual(banned_user["ban_reason"], "Spamming")

            # Unban user
            unban_success = await repo.unban_user(99887766)
            self.assertTrue(unban_success)
            unbanned_user = await repo.get_by_telegram_id(99887766)
            self.assertFalse(unbanned_user["is_banned"])

        self.loop.run_until_complete(_test())

    def test_drama_requests_repository_voting(self):
        async def _test():
            mock_col = MockAsyncCollection("drama_requests")
            repo = db.drama_requests_repo
            repo._collection = mock_col

            # Create request
            req = await repo.create({
                "title": "Hospital Playlist Season 3",
                "requested_by": 123456,
                "status": "pending",
                "votes_count": 1
            })
            self.assertEqual(req["votes_count"], 1)

            # Upvote request
            upvoted = await repo.upvote(req["_id"])
            self.assertEqual(upvoted["votes_count"], 2)

            # Change status
            await repo.update_status(req["_id"], "approved")
            updated = await repo.get_by_id(req["_id"])
            self.assertEqual(updated["status"], "approved")

        self.loop.run_until_complete(_test())


class TestSchemas(unittest.TestCase):
    """Tests Pydantic domain models for default values and structure."""

    def test_user_schema_defaults(self):
        user = db.UserModel(telegram_id=1234567, first_name="Kim")
        self.assertEqual(user.telegram_id, 1234567)
        self.assertEqual(user.first_name, "Kim")
        self.assertEqual(user.role, "user")
        self.assertTrue(user.is_active)
        self.assertFalse(user.ban_status.is_banned)
        self.assertEqual(user.referral_points, 0)
        self.assertIsNotNone(user.created_at)

    def test_drama_schema_defaults(self):
        drama = db.DramaModel(
            title="Goblin: The Lonely and Great God",
            drama_id="goblin",
            korean_title="쓸쓸하고 찬란하神 - 도깨비"
        )
        self.assertEqual(drama.title, "Goblin: The Lonely and Great God")
        self.assertEqual(drama.drama_id, "goblin")
        self.assertEqual(drama.status, "completed")
        self.assertEqual(drama.total_seasons, 1)

    def test_telegram_file_schema_defaults(self):
        tf = db.TelegramFileModel(
            file_id="BAACAgIAAxkBAAE...",
            file_unique_id="AQAD...",
            file_name="Goblin.S01E01.720p.mkv",
            file_size=524288000
        )
        self.assertEqual(tf.file_name, "Goblin.S01E01.720p.mkv")
        self.assertEqual(tf.file_size, 524288000)
        self.assertEqual(tf.quality, "720p")
        self.assertFalse(tf.is_bad_file)


if __name__ == "__main__":
    unittest.main(verbosity=2)
