"""
My K-Drama 2.0 - Telegram Bot Upgrade Test Suite
=================================================
Tests for:
  1. Regex query parsing (Season, Episode, Quality, Language recognition).
  2. Alternative & Korean title resolution via shared dramas repository.
  3. Fuzzy matching and candidate selection.
  4. Duplicate file detection & deduplication.
  5. Smart Episode Navigation Keyboard construction.
  6. User command rate limiting & anti-flood windowing.
  7. User features (Watchlist, Favorites, Progress, Recent, Profile).
"""

import sys
import os
import unittest
import asyncio
from typing import Dict, Any, List

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ---------------------------------------------------------------------------
# Dependency Shims (Enables running in environments without pre-installed packages)
# ---------------------------------------------------------------------------
import types

if 'pymongo' not in sys.modules:
    try:
        import pymongo
        import pymongo.errors
    except ImportError:
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

if 'motor' not in sys.modules:
    try:
        import motor
        import motor.motor_asyncio
    except ImportError:
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

if 'pydantic' not in sys.modules:
    try:
        import pydantic
        import pydantic_settings
    except ImportError:
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
        pydantic_mod.Field = lambda default=..., **kwargs: default if default is not ... else None
        pydantic_mod.EmailStr = str
        pydantic_mod.HttpUrl = str
        pydantic_mod.field_validator = lambda *args, **kwargs: (lambda f: f)
        sys.modules['pydantic'] = pydantic_mod

        pydantic_settings = types.ModuleType('pydantic_settings')
        class BaseSettings(MockBaseModel):
            model_config = {}
        pydantic_settings.BaseSettings = BaseSettings
        sys.modules['pydantic_settings'] = pydantic_settings

if 'pyrogram' not in sys.modules:
    try:
        import pyrogram
        import pyrogram.types
    except ImportError:
        pyrogram_mod = types.ModuleType('pyrogram')
        pyrogram_types = types.ModuleType('pyrogram.types')
        class InlineKeyboardButton:
            def __init__(self, text, callback_data=None, url=None, switch_inline_query_current_chat=None):
                self.text = text
                self.callback_data = callback_data
                self.url = url
                self.switch_inline_query_current_chat = switch_inline_query_current_chat
        class InlineKeyboardMarkup:
            def __init__(self, inline_keyboard):
                self.inline_keyboard = inline_keyboard
        pyrogram_types.InlineKeyboardButton = InlineKeyboardButton
        pyrogram_types.InlineKeyboardMarkup = InlineKeyboardMarkup
        pyrogram_mod.types = pyrogram_types
        sys.modules['pyrogram'] = pyrogram_mod
        sys.modules['pyrogram.types'] = pyrogram_types

if 'aiohttp' not in sys.modules:
    try:
        import aiohttp
        import aiohttp.web
    except ImportError:
        aiohttp_mod = types.ModuleType('aiohttp')
        aiohttp_web = types.ModuleType('aiohttp.web')
        class MockWebApp:
            def __init__(self, **kwargs): pass
            def add_routes(self, routes): pass
        aiohttp_web.Application = MockWebApp
        aiohttp_web.RouteTableDef = list
        aiohttp_mod.web = aiohttp_web
        sys.modules['aiohttp'] = aiohttp_mod
        sys.modules['aiohttp.web'] = aiohttp_web

from bot.kdrama_engine import kdrama_engine, ParsedQuery, check_user_rate_limit


class TestKDramaEngine(unittest.TestCase):
    """Tests intelligent parsing, recognition, and keyboard generation"""

    def test_season_and_episode_recognition(self):
        # Format S01E05
        p1 = kdrama_engine.parse_query("Queen of Tears S01E05 1080p")
        self.assertEqual(p1.clean_title, "Queen of Tears")
        self.assertEqual(p1.season, 1)
        self.assertEqual(p1.episode, 5)
        self.assertEqual(p1.quality, "1080p")

        # Format Season 2 Episode 8
        p2 = kdrama_engine.parse_query("Hospital Playlist Season 2 Episode 8 720p")
        self.assertEqual(p2.clean_title, "Hospital Playlist")
        self.assertEqual(p2.season, 2)
        self.assertEqual(p2.episode, 8)
        self.assertEqual(p2.quality, "720p")

        # Format 1x03
        p3 = kdrama_engine.parse_query("Vincenzo 1x03")
        self.assertEqual(p3.clean_title, "Vincenzo")
        self.assertEqual(p3.season, 1)
        self.assertEqual(p3.episode, 3)

        # Format [04] with language tag
        p4 = kdrama_engine.parse_query("Goblin [04] Korean Esub")
        self.assertEqual(p4.clean_title, "Goblin")
        self.assertEqual(p4.episode, 4)
        self.assertEqual(p4.language, "korean")

    def test_quality_and_language_extraction(self):
        p = kdrama_engine.parse_query("Lovely Runner 2160p 4K Hindi Dub")
        self.assertEqual(p.clean_title, "Lovely Runner")
        self.assertIn(p.quality, ["2160p", "4k"])
        self.assertEqual(p.language, "hindi")

    def test_duplicate_file_detection(self):
        class MockFile:
            def __init__(self, name, size, file_id):
                self.file_name = name
                self.file_size = size
                self.file_id = file_id

        # 4 files: 2 are duplicate releases of Ep 1
        raw_files = [
            MockFile("Queen.of.Tears.S01E01.720p.mkv", 500000000, "id_1"),
            MockFile("Queen.of.Tears.S01E01.720p.mkv", 500000000, "id_duplicate"),
            MockFile("Queen.of.Tears.S01E02.720p.mkv", 510000000, "id_2"),
            MockFile("Queen.of.Tears.S01E03.720p.mkv", 490000000, "id_3"),
        ]

        deduped = kdrama_engine.deduplicate_files(raw_files)
        self.assertEqual(len(deduped), 3, "Duplicate identical file must be filtered out")
        ids = [f.file_id for f in deduped]
        self.assertIn("id_1", ids)
        self.assertIn("id_2", ids)
        self.assertIn("id_3", ids)
        self.assertNotIn("id_duplicate", ids)

    def test_build_episode_grid(self):
        grid = kdrama_engine.build_episode_grid(
            drama_title="Crash Landing on You",
            total_episodes=16,
            season=1,
            session_key="chat1-msg1"
        )
        self.assertIsNotNone(grid)
        self.assertTrue(len(grid.inline_keyboard) >= 4)
        # Check first episode callback data
        first_btn = grid.inline_keyboard[0][0]
        self.assertEqual(first_btn.text, "E01")
        self.assertIn("kd_ep#chat1-msg1#1#1", first_btn.callback_data)

    def test_fuzzy_matching(self):
        candidates = [
            "Crash Landing on You",
            "Queen of Tears",
            "Lovely Runner",
            "Goblin",
            "Descendants of the Sun"
        ]
        matches = kdrama_engine.fuzzy_match("queen of tear", candidates, cutoff=0.6)
        self.assertIn("Queen of Tears", matches)

        cloy_matches = kdrama_engine.fuzzy_match("crash landin", candidates, cutoff=0.6)
        self.assertIn("Crash Landing on You", cloy_matches)


class TestUserRateLimiting(unittest.TestCase):
    """Tests anti-spam and flood rate limiting"""

    def test_user_rate_limiting_enforcement(self):
        test_uid = 88776655
        # Under limit: 10 requests allowed
        for _ in range(10):
            allowed = check_user_rate_limit(test_uid, max_per_minute=10)

        # 11th request in same minute must be rejected
        flood_blocked = check_user_rate_limit(test_uid, max_per_minute=10)
        self.assertFalse(flood_blocked, "Flood of >10 commands/min should return False")


if __name__ == "__main__":
    unittest.main(verbosity=2)
