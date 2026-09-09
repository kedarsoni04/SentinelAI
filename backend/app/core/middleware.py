import time
import uuid
from collections import defaultdict
from typing import Callable, Dict, List, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import request_id_ctx


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that establishes request tracing:
    1. Extracts incoming 'X-Request-ID' header or generates a new UUID.
    2. Binds request_id to contextvars for structured log attribution.
    3. Attaches 'X-Request-ID' header to the response.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)
        request.state.request_id = request_id

        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces standard HTTP security headers across all responses.
    Protects against MIME sniffing, clickjacking, and XSS attacks.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class InMemoryRateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Lightweight, dependency-free in-memory rate limiter for sensitive endpoints.
    Tracks request timestamps in a sliding 60-second window per client IP.
    """

    def __init__(self, app):
        super().__init__(app)
        # (ip, path_prefix) -> list of epoch timestamps
        self._history: Dict[Tuple[str, str], List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.RATE_LIMIT_ENABLED or settings.is_testing:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Determine rate limit based on route
        max_requests = None
        rate_key = None

        if path.startswith("/api/auth/login") or path.startswith("/api/auth/register"):
            max_requests = settings.RATE_LIMIT_AUTH_PER_MINUTE
            rate_key = "auth"
        elif path.startswith("/api/incidents") and request.method == "POST":
            max_requests = settings.RATE_LIMIT_AI_PER_MINUTE
            rate_key = "ai_incident"

        if max_requests and rate_key:
            now = time.time()
            window_start = now - 60.0
            history_key = (client_ip, rate_key)

            # Purge timestamps outside the 60-second window
            self._history[history_key] = [
                t for t in self._history[history_key] if t > window_start
            ]

            if len(self._history[history_key]) >= max_requests:
                req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={
                        "Retry-After": "60",
                        "X-Request-ID": req_id,
                    },
                    content={
                        "detail": f"Rate limit exceeded. Maximum {max_requests} requests per minute allowed.",
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Too many requests to sensitive endpoint. Try again in 60 seconds.",
                            "request_id": req_id,
                        },
                    },
                )

            self._history[history_key].append(now)

        return await call_next(request)
