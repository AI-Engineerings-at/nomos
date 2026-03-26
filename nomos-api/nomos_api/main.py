"""NomOS Fleet API — FastAPI application."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

import jwt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from nomos_api.config import settings
from nomos_api.database import engine
from nomos_api.models import Base
from nomos_api.routers import agents, approvals, audit, auth, budget, compliance, costs, dsgvo, fleet, health, incidents, pii, proxy, tasks, users, workspace

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("nomos-api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration = (time.monotonic() - start) * 1000
        logger.info(
            "%s %s %d %.0fms",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup, dispose engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# Public routes that don't need authentication
PUBLIC_PATHS = {
    "/health",
    "/api/auth/login",
    "/api/auth/recovery",
    "/api/users/bootstrap",
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^http://localhost(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "X-NomOS-API-Key"],
)

app.include_router(health.router)
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
