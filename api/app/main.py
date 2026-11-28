"""Builds the FastAPI application."""

import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.ai.factory import create_transport
from app.ai.router import router as ai_router
from app.ai.transport import GroqTransport, Transport
from app.auth.router import router as auth_router
from app.config import Settings, get_settings
from app.core.body_limit import Allowance, BodyLimitMiddleware
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.redis import create_redis
from app.db.session import create_engine, create_session_factory
from app.files.router import router as files_router
from app.files.storage import LocalStorage
from app.files.text import MAX_BYTES
from app.health.router import router as health_router
from app.history.router import router as history_router
from app.preferences.router import router as preferences_router
from app.profile.router import router as profile_router
from app.rules.router import router as rules_router
from app.users.router import router as account_router

# The one address that receives files. A little room is left so that an oversized file is
# explained by the file rules.
UPLOADS = Allowance(
    "PUT",
    re.compile(r"/api/files/[0-9a-fA-F-]{36}/content"),
    MAX_BYTES + 1_000,
    "That file is over 5 MB.",
)


def create_app(settings: Settings | None = None, ai_transport: Transport | None = None) -> FastAPI:
    """`ai_transport` lets tests supply the AI provider's answers."""
    settings = settings or get_settings()
    # Fail at start-up, with a clear message, when tokens could not be signed.
    settings.require_jwt_secret()
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
        app.state.storage = LocalStorage(settings.storage_dir)
        transport = ai_transport or create_transport(settings)
        app.state.ai_transport = transport
        try:
            yield
        finally:
            if isinstance(transport, GroqTransport):
                await transport.close()
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
    # The last one added runs first, so the size check sits inside the request log.
    app.add_middleware(BodyLimitMiddleware, larger=(UPLOADS,))
    app.add_middleware(RequestContextMiddleware)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(account_router)
    app.include_router(history_router)
    app.include_router(files_router)
    app.include_router(profile_router)
    app.include_router(preferences_router)
    app.include_router(rules_router)
    app.include_router(ai_router)
    return app
