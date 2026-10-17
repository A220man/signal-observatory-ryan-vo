"""Signal Observatory — FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from app.core.config import get_settings
from app.core.database import init_db
from app.api.auth import router as auth_router
from app.api.handoff import router as handoff_router
from app.api.signals import router as signals_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    settings = get_settings()
    db_path = settings.db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    await init_db(db_path)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title="Signal Observatory",
        description="Long-term memory for agent coding CLIs and handoff between agent vendors.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "prod" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.app_env != "prod" else None,
    )

    # CORS — bound to localhost in dev/demo
    allowed_origins = (
        ["http://localhost:3000", "http://127.0.0.1:3000"]
        if settings.app_env in ("dev", "demo")
        else []
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins if allowed_origins else ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(signals_router)
    app.include_router(handoff_router)

    @app.get("/health")
    async def health() -> dict:
        """Health check endpoint."""
        return {"status": "ok", "service": "signal-observatory", "version": "1.0.0"}

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Internal service error", "error": str(exc)[:500]},
        )

    return app


app = create_app()