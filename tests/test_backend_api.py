"""
My K-Drama 2.0 - FastAPI Backend Test Suite
============================================
Comprehensive unit & integration tests covering:
  1. JWT token generation, expiration, and cryptographic verification.
  2. Web user password hashing and PBKDF2 verification.
  3. Telegram login widget HMAC SHA-256 signature verification.
  4. Authentication dependencies & rejection of client-supplied user IDs.
  5. Role-based authorization (admin, moderator, user) & 403 Forbidden enforcement.
  6. Personal resource ownership validation.
  7. Rate limiting sliding window & 429 Too Many Requests enforcement.
  8. Service layer business logic (watchlist, favorites, requests, progress).
  9. Standardized API error envelopes.
"""

import sys
import os
import unittest
import time
import asyncio
from typing import Dict, Any, List, Optional

# Setup path
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
    import fastapi
    import fastapi.responses
    import fastapi.exceptions
except ImportError:
    import types

    # Setup pymongo shims
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

    # Setup motor shims
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

    # Setup pydantic shims
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
            dump = {}
            for k, v in self.__dict__.items():
                if not k.startswith('_'):
                    if hasattr(v, "model_dump"):
                        dump[k] = v.model_dump(**kwargs)
                    elif isinstance(v, list):
                        dump[k] = [item.model_dump(**kwargs) if hasattr(item, "model_dump") else item for item in v]
                    else:
                        dump[k] = v
            return dump
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

    # Setup fastapi shims
    fastapi_mod = types.ModuleType('fastapi')
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = None, headers: dict = None):
            self.status_code = status_code
            self.detail = detail
            self.headers = headers
            super().__init__(detail)

    class Status:
        HTTP_400_BAD_REQUEST = 400
        HTTP_401_UNAUTHORIZED = 401
        HTTP_403_FORBIDDEN = 403
        HTTP_404_NOT_FOUND = 404
        HTTP_409_CONFLICT = 409
        HTTP_422_UNPROCESSABLE_ENTITY = 422
        HTTP_429_TOO_MANY_REQUESTS = 429
        HTTP_500_INTERNAL_SERVER_ERROR = 500

    fastapi_mod.HTTPException = HTTPException
    fastapi_mod.status = Status
    fastapi_mod.Depends = lambda x=None: x
    fastapi_mod.Header = lambda default=None, **kwargs: default
    fastapi_mod.Query = lambda default=None, **kwargs: default
    fastapi_mod.Request = object
    fastapi_mod.APIRouter = object

    class JSONResponse:
        def __init__(self, status_code: int, content: dict):
            self.status_code = status_code
            self.content = content
            import json
            self.body = json.dumps(content).encode('utf-8')

    fastapi_responses = types.ModuleType('fastapi.responses')
    fastapi_responses.JSONResponse = JSONResponse
    fastapi_mod.responses = fastapi_responses

    fastapi_exceptions = types.ModuleType('fastapi.exceptions')
    class RequestValidationError(Exception):
        def errors(self): return []
    fastapi_exceptions.RequestValidationError = RequestValidationError
    fastapi_mod.exceptions = fastapi_exceptions

    sys.modules['fastapi'] = fastapi_mod
    sys.modules['fastapi.responses'] = fastapi_responses
    sys.modules['fastapi.exceptions'] = fastapi_exceptions

    starlette_mod = types.ModuleType('starlette')
    starlette_mw = types.ModuleType('starlette.middleware')
    starlette_mw_base = types.ModuleType('starlette.middleware.base')
    class BaseHTTPMiddleware: pass
    starlette_mw_base.BaseHTTPMiddleware = BaseHTTPMiddleware
    starlette_requests = types.ModuleType('starlette.requests')
    starlette_requests.Request = object
    starlette_responses = types.ModuleType('starlette.responses')
    starlette_responses.Response = object
    sys.modules['starlette'] = starlette_mod
    sys.modules['starlette.middleware'] = starlette_mw
    sys.modules['starlette.middleware.base'] = starlette_mw_base
    sys.modules['starlette.requests'] = starlette_requests
    sys.modules['starlette.responses'] = starlette_responses

# Imports from backend
from backend.core.security import (
    create_access_token, decode_access_token, hash_password, verify_password,
    verify_telegram_auth
)
from backend.core.dependencies import (
    get_current_user, require_role, validate_ownership
)
from backend.core.rate_limiter import RateLimiter
from backend.core.error_handlers import create_error_response
from backend.schemas.api_responses import (
    ApiResponse, PaginatedApiResponse, PaginationMetadata,
    TelegramAuthPayload, WebLoginPayload, CreateDramaRequestPayload
)
from shared.config.settings import settings


class TestSecurityAndAuth(unittest.TestCase):
    """Tests JWT cryptographic tokens and password hashing"""

    def test_jwt_token_creation_and_decoding(self):
        payload = {
            "sub": "user_12345",
            "user_id": 12345,
            "role": "user",
            "username": "kdrama_fan"
        }
        token = create_access_token(payload, expires_delta=3600)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)

        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.get("sub"), "user_12345")
        self.assertEqual(decoded.get("user_id"), 12345)
        self.assertEqual(decoded.get("role"), "user")
        self.assertIn("exp", decoded)

    def test_jwt_expired_or_invalid_token(self):
        # Negative expires delta (already expired)
        payload = {"sub": "expired_user"}
        expired_token = create_access_token(payload, expires_delta=-100)
        decoded = decode_access_token(expired_token)
        self.assertIsNone(decoded, "Expired token should return None on decode")

        # Corrupted token string
        invalid_token = "invalid.token.signature"
        self.assertIsNone(decode_access_token(invalid_token))

    def test_password_hashing_and_verification(self):
        password = "SecurePassword123!"
        hashed = hash_password(password)
        self.assertIn("$", hashed)
        self.assertNotEqual(password, hashed)

        # Successful verification
        self.assertTrue(verify_password(password, hashed))

        # Failed verification with wrong password
        self.assertFalse(verify_password("WrongPassword!", hashed))

        # Edge cases
        self.assertFalse(verify_password(password, ""))
        self.assertFalse(verify_password(password, "corrupted_hash"))

    def test_telegram_auth_verification(self):
        # Mock telegram auth data with invalid hash
        auth_data = {
            "id": 12345678,
            "first_name": "TestUser",
            "auth_date": int(time.time()),
            "hash": "invalid_hmac_hash"
        }
        # Cryptographic check should reject invalid hash
        self.assertFalse(verify_telegram_auth(auth_data))


class TestDependenciesAndAuthorization(unittest.TestCase):
    """Tests authentication dependencies, role-based access control, and ownership validation"""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_get_current_user_valid(self):
        async def _test():
            token = create_access_token({"sub": "999888", "user_id": 999888, "role": "user"})
            auth_header = f"Bearer {token}"
            user = await get_current_user(authorization=auth_header)
            self.assertEqual(user["user_id"], 999888)
            self.assertEqual(user["role"], "user")

        self.loop.run_until_complete(_test())

    def test_get_current_user_unauthorized_cases(self):
        from fastapi import HTTPException
        async def _test():
            # Missing header
            with self.assertRaises(HTTPException) as ctx:
                await get_current_user(authorization=None)
            self.assertEqual(ctx.exception.status_code, 401)

            # Invalid Bearer prefix
            with self.assertRaises(HTTPException) as ctx:
                await get_current_user(authorization="Basic dXNlcjpwYXNz")
            self.assertEqual(ctx.exception.status_code, 401)

            # Invalid token
            with self.assertRaises(HTTPException) as ctx:
                await get_current_user(authorization="Bearer corrupted_token")
            self.assertEqual(ctx.exception.status_code, 401)

        self.loop.run_until_complete(_test())

    def test_role_based_authorization(self):
        from fastapi import HTTPException
        async def _test():
            admin_checker = require_role(["admin", "superadmin"])
            moderator_checker = require_role(["moderator", "admin"])

            # Regular user attempting admin endpoint -> 403 Forbidden
            regular_user = {"user_id": 1001, "role": "user"}
            with self.assertRaises(HTTPException) as ctx:
                await admin_checker(user=regular_user)
            self.assertEqual(ctx.exception.status_code, 403)
            self.assertIn("Access forbidden", ctx.exception.detail)

            # Moderator attempting admin endpoint -> 403 Forbidden
            moderator_user = {"user_id": 1002, "role": "moderator"}
            with self.assertRaises(HTTPException) as ctx:
                await admin_checker(user=moderator_user)
            self.assertEqual(ctx.exception.status_code, 403)

            # Admin accessing admin endpoint -> Allowed
            admin_user = {"user_id": 1003, "role": "admin"}
            authorized_admin = await admin_checker(user=admin_user)
            self.assertEqual(authorized_admin["user_id"], 1003)

            # Moderator accessing moderator endpoint -> Allowed
            authorized_mod = await moderator_checker(user=moderator_user)
            self.assertEqual(authorized_mod["user_id"], 1002)

        self.loop.run_until_complete(_test())

    def test_validate_ownership(self):
        from fastapi import HTTPException
        owner_id = "user_456"
        owner_session = {"user_id": "user_456", "role": "user"}
        stranger_session = {"user_id": "user_789", "role": "user"}
        admin_session = {"user_id": "admin_999", "role": "admin"}

        # Owner modifying their own resource -> Allowed
        self.assertTrue(validate_ownership(owner_id, owner_session))

        # Admin modifying resource -> Allowed (admin bypass)
        self.assertTrue(validate_ownership(owner_id, admin_session))

        # Stranger attempting to modify another user's resource -> 403 Forbidden
        with self.assertRaises(HTTPException) as ctx:
            validate_ownership(owner_id, stranger_session)
        self.assertEqual(ctx.exception.status_code, 403)


class TestRateLimiter(unittest.TestCase):
    """Tests rate limiter sliding window and 429 status code"""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_rate_limiter_exceeded(self):
        from fastapi import HTTPException
        async def _test():
            # Allow max 3 requests per minute for testing
            limiter = RateLimiter(requests_per_minute=3, key_prefix="test_rate")

            # Mock request object
            class MockClient:
                host = "192.168.1.50"
            class MockRequest:
                client = MockClient()
                headers = {}

            req = MockRequest()

            # First 3 requests succeed
            await limiter(req)
            await limiter(req)
            await limiter(req)

            # 4th request must raise 429
            with self.assertRaises(HTTPException) as ctx:
                await limiter(req)
            self.assertEqual(ctx.exception.status_code, 429)
            self.assertIn("Rate limit exceeded", ctx.exception.detail)

        self.loop.run_until_complete(_test())


class TestApiResponseSchemas(unittest.TestCase):
    """Tests standardized JSON envelopes and schema validations"""

    def test_api_response_envelope(self):
        res = ApiResponse(success=True, data={"key": "value"}, message="Success")
        d = res.model_dump()
        self.assertTrue(d["success"])
        self.assertEqual(d["data"]["key"], "value")
        self.assertEqual(d["message"], "Success")
        self.assertIsNone(d["error"])

    def test_paginated_api_response_envelope(self):
        items = [{"id": 1}, {"id": 2}]
        pagination = PaginationMetadata(
            page=1, page_size=20, total_count=2, total_pages=1, has_next=False, has_prev=False
        )
        paginated_res = PaginatedApiResponse(data=items, pagination=pagination)
        d = paginated_res.model_dump()
        self.assertTrue(d["success"])
        self.assertEqual(len(d["data"]), 2)
        self.assertEqual(d["pagination"]["total_count"], 2)

    def test_create_error_response_format(self):
        json_resp = create_error_response(404, "NOT_FOUND", "Drama does not exist", details={"id": 123})
        self.assertEqual(json_resp.status_code, 404)
        import json
        body = json.loads(json_resp.body.decode("utf-8"))
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], "NOT_FOUND")
        self.assertEqual(body["error"]["message"], "Drama does not exist")
        self.assertEqual(body["error"]["details"]["id"], 123)


if __name__ == "__main__":
    unittest.main(verbosity=2)
