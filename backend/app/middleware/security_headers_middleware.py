"""Baseline security response headers (PRD Ch20 MVP security requirements).

Deliberately minimal — no CSP (the API serves JSON, not HTML, so a
content-security-policy belongs on the frontend/nginx layer, not here).
HSTS (PRD Ch4.14 / Ch7.18 "HTTPS-only communication") is sent in production
only: browsers ignore it over plain HTTP, and pinning HTTPS on a developer's
`localhost` would break other local projects.
"""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
