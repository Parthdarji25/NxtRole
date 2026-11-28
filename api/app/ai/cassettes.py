"""Recorded AI answers ("cassettes"), so tests run without the network or a key.

Recording calls the real provider once and saves what was sent (identity already removed)
and what came back, in a file named by prompt, model and date. Replaying finds the file for
exactly the same request; a changed prompt must be recorded again.
"""

import hashlib
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from app.ai.transport import ChatReply, ChatRequest, Transport


def fingerprint(request: ChatRequest) -> str:
    canonical = json.dumps(asdict(request), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


class Recorder:
    """Passes each request on and saves the answer. Used only to make test fixtures."""

    def __init__(self, inner: Transport, folder: Path) -> None:
        self.inner = inner
        self.folder = folder
        self.written: list[Path] = []

    async def complete(self, request: ChatRequest) -> ChatReply:
        reply = await self.inner.complete(request)
        model = request.model.replace("/", "-")
        today = date.today().isoformat()
        path = self.folder / f"{request.prompt}__{model}__{today}__{fingerprint(request)}.json"
        self.folder.mkdir(parents=True, exist_ok=True)
        content = {"recorded_on": today, "request": asdict(request), "reply": asdict(reply)}
        path.write_text(
            json.dumps(content, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        self.written.append(path)
        return reply


class NoRecording(LookupError):
    pass


class Replay:
    """Answers from the saved files. Never touches the network."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder

    async def complete(self, request: ChatRequest) -> ChatReply:
        found = sorted(self.folder.glob(f"*__{fingerprint(request)}.json"))
        if not found:
            raise NoRecording(
                f"No recording for {request.prompt} with {request.model}. The request has "
                "changed: record it again (docs/TESTING.md)."
            )
        saved = json.loads(found[-1].read_text(encoding="utf-8"))
        return ChatReply(**saved["reply"])
