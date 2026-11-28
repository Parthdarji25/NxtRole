"""Refuses oversized requests before they are read into the app (T-INJ-2).

Almost every request is small. The few addresses that receive files are named, each with
its own limit.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import error_response

MAX_BODY_BYTES = 1_000_000
TOO_LARGE = "That is too much data to send at once."


@dataclass(frozen=True)
class Allowance:
    method: str
    path: re.Pattern[str]
    max_bytes: int
    message: str


class BodyLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        max_bytes: int = MAX_BODY_BYTES,
        larger: Sequence[Allowance] = (),
    ) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.larger = larger

    def _limit(self, scope: Scope) -> tuple[int, str]:
        for allowance in self.larger:
            if scope["method"] == allowance.method and allowance.path.fullmatch(scope["path"]):
                return allowance.max_bytes, allowance.message
        return self.max_bytes, TOO_LARGE

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        limit, message_text = self._limit(scope)

        async def refuse() -> None:
            response = error_response(413, "too_large", message_text)
            await response(scope, receive, send)

        declared = Headers(scope=scope).get("content-length", "")
        if declared.isdigit() and int(declared) > limit:
            await refuse()
            return

        # A caller can leave the length out or understate it, so the bytes are counted too.
        received: list[Message] = []
        size = 0
        while True:
            message = await receive()
            received.append(message)
            size += len(message.get("body", b""))
            if size > limit:
                await refuse()
                return
            if message["type"] != "http.request" or not message.get("more_body", False):
                break

        async def replay() -> Message:
            return received.pop(0) if received else await receive()

        await self.app(scope, replay, send)
