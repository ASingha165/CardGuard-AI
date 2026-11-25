"""FastAPI application entrypoint for CardGuard AI."""
import os
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    dashboard,
    datasets,
    health,
    investigations,
    models,
    network,
    reports,
    settings as settings_route,
    transactions,
)
from app.core.config import get_settings
from app.core.logging import logger
from app.db.session import SessionLocal, init_db
from app.services.bootstrap_service import ensure_initial_state


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        ensure_initial_state(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    cfg = get_settings()
    app = FastAPI(
        title=cfg.APP_NAME,
        version=cfg.APP_VERSION,
        description="Intelligent credit-card fraud detection and explainable investigation platform.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def secure_exception_handler(_request: Request, exc: Exception):
        logger.error(f"Unhandled error: {type(exc).__name__}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal processing error occurred."},
        )

    app.include_router(health.router)
    app.include_router(dashboard.router)
    app.include_router(datasets.router)
    app.include_router(models.router)
    app.include_router(transactions.router)
    app.include_router(investigations.router)
    app.include_router(network.router)
    app.include_router(reports.router)
    app.include_router(settings_route.router)

    return app


app = create_app()
