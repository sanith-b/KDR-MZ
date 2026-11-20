"""
Structured Request Logging Middleware for FastAPI
Captures method, path, status, duration, and client information.
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from logging_helper import LOGGER

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        try:
            response: Response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            LOGGER.info(
                f"[API] {method} {path} - {response.status_code} ({duration_ms}ms) | Client: {client_ip}"
            )
            response.headers["X-Response-Time"] = f"{duration_ms}ms"
            return response
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            LOGGER.error(
                f"[API ERROR] {method} {path} - Failed after {duration_ms}ms | Client: {client_ip} | {exc}"
            )
            raise exc
