"""Builds the FastAPI application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.redis import create_redis
from app.db.session import create_engine, create_session_factory
from app.health.router import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Nothing connects here, so the API still starts when the database is not ready yet;
        # /api/health/ready reports the problem instead of the program crashing.
        engine = create_engine(settings.database_url.get_secret_value())
        redis = create_redis(settings.redis_url.get_secret_value())
        app.state.settings = settings
        app.state.engine = engine
        app.state.sessions = create_session_factory(engine)
        app.state.redis = redis
        try:
            yield
        finally:
            await redis.aclose()
            await engine.dispose()

    # The interactive API description is available in local development only.
    show_docs = settings.app_env == "local"
    app = FastAPI(
        title="NxtRole API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if show_docs else None,
        openapi_url="/api/openapi.json" if show_docs else None,
        redoc_url=None,
    )
    app.add_middleware(RequestContextMiddleware)
    register_error_handlers(app)
    app.include_router(health_router)
    return app
