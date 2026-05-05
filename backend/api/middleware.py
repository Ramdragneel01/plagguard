"""Request validation & rate-limiting middleware."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Simple in-memory rate limiter (per-IP, 30 requests/minute)
_RATE_LIMIT = 30
_WINDOW = 60
_requests: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        _requests[client_ip] = [
            t for t in _requests[client_ip] if t > now - _WINDOW
        ]

        if len(_requests[client_ip]) >= _RATE_LIMIT:
            return Response(
                content='{"detail":"Rate limit exceeded. Try again shortly."}',
                status_code=429,
                media_type="application/json",
            )

        _requests[client_ip].append(now)
        response = await call_next(request)
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject request bodies larger than 5 MB."""

    MAX_SIZE = 5 * 1024 * 1024  # 5 MB

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_SIZE:
            return Response(
                content='{"detail":"Request body too large (max 5 MB)."}',
                status_code=413,
                media_type="application/json",
            )
        return await call_next(request)
