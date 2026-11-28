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


def _fact(
    kind: str, value: str, quote: str, company: str | None = None, dates: str | None = None
) -> dict[str, Any]:
    return {"kind": kind, "value": value, "company": company, "dates": dates, "quote": quote}


_SKILLS = (
    "JavaScript, TypeScript, React, Next.js, Redux, Tailwind CSS, Jest, Playwright, Git, Figma"
)
# What a model might answer about the synthetic resume. The last skill is not in it, so the
# quote check must leave it out.
SYNTHETIC_ANSWER = {
    "facts": [
        _fact(
            "experience_years",
            "4",
            "Frontend developer with 4 years of experience building dashboards",
        ),
        _fact(
            "role",
            "Frontend Developer",
            "Frontend Developer, Lantern Works Studio, Jan 2024 - Present",
            "Lantern Works Studio",
            "Jan 2024 - Present",
        ),
        _fact("skill", "React", _SKILLS),
        _fact("skill", "TypeScript", _SKILLS),
        _fact("skill", "Git", _SKILLS),
        _fact(
            "education",
            "B.E. in Computer Engineering",
            "B.E. in Computer Engineering, Deccan Hills College of Engineering, 2017 - 2021",
        ),
        _fact("skill", "Kubernetes", "Kubernetes, Docker"),
    ]
}
