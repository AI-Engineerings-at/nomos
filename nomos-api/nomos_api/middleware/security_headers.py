"""L2: security response headers.

Adds defensive headers to every response:
- X-Content-Type-Options: nosniff   (no MIME sniffing)
- X-Frame-Options: DENY             (clickjacking)
- Referrer-Policy                   (no referrer leakage)
- Content-Security-Policy           (conservative; this is a JSON API)
- Strict-Transport-Security         (ONLY when cookie_secure / HTTPS, so it
                                      is not sent on plain-HTTP dev/test)
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Conservative CSP for a JSON API surface: deny everything by default and
# forbid being framed. The console is a separate origin/app and serves its
# own documents, so the API itself needs no script/style allowances.
_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"

_STATIC_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": _CSP,
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach security headers to every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for key, value in _STATIC_HEADERS.items():
            response.headers.setdefault(key, value)

        # HSTS only over HTTPS deployments (cookie_secure is the existing
        # signal for "served behind TLS/Caddy"). Never send it on plain
        # HTTP, where it would be ignored or could brick local/dev access.
        from nomos_api.config import settings

        if settings.cookie_secure:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response
