"""NomOS Fleet API — FastAPI application."""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

import jwt
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from nomos_api.config import settings
from nomos_api.database import engine
from nomos_api.routers import (
    agents,
    approvals,
    audit,
    auth,
    budget,
    compliance,
    costs,
    dsgvo,
    fleet,
    health,
    incidents,
    pii,
    proxy,
    system,
    tasks,
    users,
    workspace,
)
from nomos_api.routers import settings as settings_router

from nomos_api.middleware.logging import JSONFormatter

_handler = logging.StreamHandler()
_handler.setFormatter(JSONFormatter())
logging.root.handlers = [_handler]
logging.root.setLevel(logging.INFO)

logger = logging.getLogger("nomos-api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        logger.info(
            "%s %s",
            request.method,
            request.url.path,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


def _run_alembic_upgrade() -> None:
    """Run Alembic migrations synchronously (called via run_in_executor)."""
    try:
        project_root = Path(__file__).resolve().parent.parent
        alembic_ini = project_root / "alembic.ini"
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        logger.warning("Alembic migration skipped: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate settings and run Alembic migrations on startup."""
    from nomos_api.config import validate_settings

    validate_settings(settings)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_alembic_upgrade)
    yield
    await engine.dispose()


# Public routes that don't need authentication
PUBLIC_PATHS = {
    "/health",
    "/api/health",
    "/api/auth/login",
    "/api/auth/recovery",
    "/api/users/bootstrap",
    "/api/system/status",
    "/api/system/unseal-key",
    "/docs",
    "/openapi.json",
}

PUBLIC_PREFIXES = ("/api/auth/2fa",)


class AuthMiddleware(BaseHTTPMiddleware):
    """Global authentication — JWT cookie or Plugin API key."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if request.method == "OPTIONS" or path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        # Service-to-service auth (Plugin → API)
        api_key = request.headers.get("X-NomOS-API-Key")
        if api_key and api_key == settings.plugin_api_key:
            request.state.user = {"role": "service", "email": "plugin@nomos.local"}
            return await call_next(request)

        # User auth via JWT cookie
        token = request.cookies.get("nomos_token")
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
            request.state.user = payload
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})
        return await call_next(request)


app = FastAPI(title=settings.api_title, version=settings.api_version, lifespan=lifespan)

app.add_middleware(AuthMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Build CORS origins
cors_origins = list(settings.cors_origins)
if settings.dev_mode:
    cors_origins.append("http://localhost:3040")
    cors_origins.append("http://localhost:3045")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "X-NomOS-API-Key"],
)

app.include_router(health.router)
app.include_router(system.router)
app.include_router(fleet.router)
app.include_router(agents.router)
app.include_router(compliance.router)
app.include_router(audit.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(approvals.router)
app.include_router(costs.router)
app.include_router(budget.router)
app.include_router(pii.router)
app.include_router(incidents.router)
app.include_router(workspace.router)
app.include_router(dsgvo.router)
app.include_router(proxy.router)
app.include_router(settings_router.router)
