"""Baseline security response headers (PRD Ch20 MVP security requirements).

Deliberately minimal — no CSP (the API serves JSON, not HTML, so a
content-security-policy belongs on the frontend/nginx layer, not here) and
no HSTS toggle beyond what `cookie_secure` already implies for cookies.
Just the small set of headers that cost nothing and have no behavioral
trade-off for a JSON API.
"""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response
