"""Request id, one log line per request, and a safe answer for unexpected errors."""

import re
import time
import traceback
import uuid

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import error_response

REQUEST_ID_HEADER = "X-Request-Id"
# An id sent by a caller is reused only if it is short and plain, so it cannot inject log text.
SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")

log = structlog.get_logger("nxtrole.request")


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = Headers(scope=scope).get(REQUEST_ID_HEADER, "")
        request_id = incoming if SAFE_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        started = time.perf_counter()
        status_code = 500
        response_started = False

        async def send_with_headers(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                headers = MutableHeaders(scope=message)
                headers[REQUEST_ID_HEADER] = request_id
                headers["Cache-Control"] = "no-store"
                headers["X-Content-Type-Options"] = "nosniff"
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        except Exception as exc:
            # The error text is not logged: it can contain personal data or a password.
            # The type and the code locations are enough to find the bug.
            frames = traceback.extract_tb(exc.__traceback__)
            log.error(
                "unhandled_error",
                error_type=type(exc).__name__,
                where=[f"{frame.filename}:{frame.lineno} {frame.name}" for frame in frames[-8:]],
            )
            if response_started:
                raise
            response = error_response(
                500, "internal_error", "Something went wrong on our side. Please try again."
            )
            await response(scope, receive, send_with_headers)
        finally:
            # The query string is left out on purpose: it can hold search text.
            log.info(
                "request",
                method=scope["method"],
                path=scope["path"],
                status=status_code,
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
            )
