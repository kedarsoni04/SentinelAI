import logging
import traceback
import uuid
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings

logger = logging.getLogger("sentinel.core.exceptions")


def setup_exception_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers on the FastAPI application."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.warning(
            "HTTP %d error on %s %s: %s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )

        content: Dict[str, Any] = {
            "detail": exc.detail,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "request_id": req_id,
            },
        }

        headers = exc.headers or {}
        headers["X-Request-ID"] = req_id
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        raw_errors = jsonable_encoder(exc.errors())
        logger.warning(
            "Validation error on %s %s: %s",
            request.method,
            request.url.path,
            raw_errors,
        )

        content: Dict[str, Any] = {
            "detail": raw_errors,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed. Please check your request parameters.",
                "details": raw_errors,
                "request_id": req_id,
            },
        }

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=content,
            headers={"X-Request-ID": req_id},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.error(
            "Unhandled server exception on %s %s: %s\n%s",
            request.method,
            request.url.path,
            str(exc),
            traceback.format_exc(),
        )

        # In production, never leak internal error strings or tracebacks to clients
        if settings.is_production:
            error_message = "An internal server error occurred. Please contact security operations."
        else:
            error_message = f"Internal server error: {str(exc)}"

        content: Dict[str, Any] = {
            "detail": error_message,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": error_message,
                "request_id": req_id,
            },
        }

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=content,
            headers={"X-Request-ID": req_id},
        )
