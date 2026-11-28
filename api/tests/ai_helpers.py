"""A stand-in AI provider for tests. Test code only."""

import json
from collections.abc import Sequence
from typing import Any

from app.ai.transport import ChatReply, ChatRequest, TransportError

Step = TransportError | str | dict[str, Any]


class FakeTransport:
    """Answers each request with the next step: an error to raise, or an answer to return.
    Remembers what it was sent."""

    def __init__(self, *steps: Step) -> None:
        self.steps: list[Step] = list(steps)
        self.sent: list[ChatRequest] = []

    async def complete(self, request: ChatRequest) -> ChatReply:
        self.sent.append(request)
        if not self.steps:
            raise AssertionError("the AI was called more often than the test expected")
        step = self.steps.pop(0) if len(self.steps) > 1 else self.steps[0]
        if isinstance(step, TransportError):
            raise step
        content = step if isinstance(step, str) else json.dumps(step)
        return ChatReply(content=content, tokens_in=100, tokens_out=50)

    def models(self) -> Sequence[str]:
        return [request.model for request in self.sent]

    def everything_sent(self) -> str:
        return "\n".join(request.system + request.user for request in self.sent)
