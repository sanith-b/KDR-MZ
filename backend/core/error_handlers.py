"""
Standardized Global Exception Handlers for My K-Drama 2.0 Backend
Formats all errors into consistent JSON envelopes with error code and details.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from shared.database.errors import (
    DuplicateKeyError, DocumentNotFoundError, DatabaseError, ValidationError as DomainValidationError
)
from logging_helper import LOGGER

def create_error_response(status_code: int, code: str, message: str, details: any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details
            }
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    code = "HTTP_ERROR"
    if exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 429:
        code = "RATE_LIMITED"
    return create_error_response(exc.status_code, code, str(exc.detail))

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join([str(x) for x in err.get("loc", [])])
        errors.append(f"{loc}: {err.get('msg')}")
    return create_error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "VALIDATION_ERROR",
        "Request body or parameter validation failed",
        errors
    )

async def duplicate_key_exception_handler(request: Request, exc: DuplicateKeyError):
    return create_error_response(
        status.HTTP_409_CONFLICT,
        "DUPLICATE_RESOURCE",
        str(exc),
        exc.details
    )

async def not_found_exception_handler(request: Request, exc: DocumentNotFoundError):
    return create_error_response(
        status.HTTP_404_NOT_FOUND,
        "RESOURCE_NOT_FOUND",
        str(exc)
    )

async def database_exception_handler(request: Request, exc: DatabaseError):
    LOGGER.error(f"Database error during request {request.url.path}: {exc}")
    return create_error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "DATABASE_ERROR",
        "An unexpected database error occurred"
    )

async def generic_exception_handler(request: Request, exc: Exception):
    LOGGER.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return create_error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "INTERNAL_SERVER_ERROR",
        "An internal server error occurred"
    )

def register_exception_handlers(app):
    """Registers all standardized exception handlers onto the FastAPI application"""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DuplicateKeyError, duplicate_key_exception_handler)
    app.add_exception_handler(DocumentNotFoundError, not_found_exception_handler)
    app.add_exception_handler(DatabaseError, database_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
