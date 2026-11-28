"""Refuses oversized requests before they are read into the app (T-INJ-2).

Uploads do not pass through the API (D-029), so every request body here is small.
"""

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import error_response

MAX_BODY_BYTES = 1_000_000


class BodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = MAX_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = Headers(scope=scope).get("content-length", "")
        if declared.isdigit() and int(declared) > self.max_bytes:
            await self._refuse(scope, receive, send)
            return

        # A caller can leave the length out or understate it, so the bytes are counted too.
        received: list[Message] = []
        size = 0
        while True:
            message = await receive()
            received.append(message)
            size += len(message.get("body", b""))
            if size > self.max_bytes:
                await self._refuse(scope, receive, send)
                return
            if message["type"] != "http.request" or not message.get("more_body", False):
                break

        async def replay() -> Message:
            return received.pop(0) if received else await receive()

        await self.app(scope, replay, send)

    async def _refuse(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = error_response(413, "too_large", "That is too much data to send at once.")
        await response(scope, receive, send)
