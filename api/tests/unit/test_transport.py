"""The real Groq client, talking to a stand-in server: what is sent and how errors map."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import BaseModel, ConfigDict

from app.ai import prompts
from app.ai.cassettes import NoRecording, Recorder, Replay
from app.ai.gateway import strict_schema
from app.ai.transport import (
    BadAnswer,
    ChatRequest,
    GroqTransport,
    NotConfigured,
    RateLimited,
    TooLarge,
    TransportError,
    Unavailable,
)

REQUEST = ChatRequest(
    model="openai/gpt-oss-120b",
    prompt="test@v1",
    system="rules",
    user="text",
    schema={"type": "object"},
    temperature=0.2,
    reasoning_effort="low",
    max_output_tokens=100,
)


def completion(content: str | None = '{"a": 1}', finish: str = "stop") -> dict[str, Any]:
    return {
        "id": "chat-1",
        "object": "chat.completion",
        "created": 1,
        "model": REQUEST.model,
        "choices": [
            {
                "index": 0,
                "finish_reason": finish,
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {"prompt_tokens": 12, "completion_tokens": 7, "total_tokens": 19},
    }


def transport(handler: Callable[[httpx.Request], httpx.Response]) -> GroqTransport:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return GroqTransport("test-key-that-opens-nothing", http_client=client)


async def test_the_request_asks_for_a_strict_shape() -> None:
    seen: list[dict[str, Any]] = []

    def server(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=completion())

    reply = await transport(server).complete(REQUEST)

    assert (reply.content, reply.tokens_in, reply.tokens_out) == ('{"a": 1}', 12, 7)
    [body] = seen
    assert body["model"] == "openai/gpt-oss-120b"
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["reasoning_effort"] == "low"
    assert body["include_reasoning"] is False
    assert body["max_completion_tokens"] == 100
    assert [message["role"] for message in body["messages"]] == ["system", "user"]


async def test_other_models_get_no_reasoning_settings() -> None:
    seen: list[dict[str, Any]] = []

    def server(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=completion())

    from dataclasses import replace

    await transport(server).complete(replace(REQUEST, model="qwen/qwen3.8-27b"))

    assert "reasoning_effort" not in seen[0]


@pytest.mark.parametrize(
    ("status", "body", "expected"),
    [
        (429, {"error": {"message": "slow down"}}, RateLimited),
        (401, {"error": {"message": "bad key"}}, NotConfigured),
        (403, {"error": {"message": "no"}}, NotConfigured),
        (413, {"error": {"message": "too big"}}, TooLarge),
        (400, {"error": {"code": "json_validate_failed"}}, BadAnswer),
        (404, {"error": {"code": "model_not_found"}}, Unavailable),
        (500, {"error": {"message": "oops"}}, Unavailable),
        (503, "<html>down</html>", Unavailable),
    ],
)
async def test_provider_errors_become_ours(
    status: int, body: Any, expected: type[TransportError]
) -> None:
    calls = 0

    def server(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if isinstance(body, str):
            return httpx.Response(status, text=body)
        return httpx.Response(status, json=body, headers={"retry-after": "42"})

    with pytest.raises(expected) as caught:
        await transport(server).complete(REQUEST)

    # The library does not retry on its own: the gateway decides.
    assert calls == 1
    if isinstance(caught.value, RateLimited):
        assert caught.value.retry_after == 42


async def test_a_network_failure_is_unavailable() -> None:
    def server(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no network", request=request)

    with pytest.raises(Unavailable):
        await transport(server).complete(REQUEST)


@pytest.mark.parametrize(
    "body", [completion(content=None), completion(finish="length"), completion(content="")]
)
async def test_an_empty_or_cut_off_answer_is_bad(body: dict[str, Any]) -> None:
    with pytest.raises(BadAnswer):
        await transport(lambda _request: httpx.Response(200, json=body)).complete(REQUEST)


async def test_recorded_answers_replay_without_the_network(tmp_path: Path) -> None:
    server = transport(lambda _request: httpx.Response(200, json=completion()))
    recorder = Recorder(server, tmp_path)

    live = await recorder.complete(REQUEST)
    replayed = await Replay(tmp_path).complete(REQUEST)

    assert replayed == live
    [path] = recorder.written
    assert path.name.startswith("test@v1__openai-gpt-oss-120b__")
    assert "test-key" not in path.read_text(encoding="utf-8")


async def test_a_changed_request_has_no_recording(tmp_path: Path) -> None:
    with pytest.raises(NoRecording, match="record it again"):
        await Replay(tmp_path).complete(REQUEST)


class Inner(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    note: str | None = None


class Outer(BaseModel):
    items: list[Inner]
    count: int = 3


def test_the_strict_schema_has_no_references_and_requires_everything() -> None:
    schema = strict_schema(Outer)

    text = json.dumps(schema)
    assert "$ref" not in text and "$defs" not in text and "default" not in text
    assert schema["required"] == ["items", "count"]
    assert schema["additionalProperties"] is False
    item = schema["properties"]["items"]["items"]
    # A field called "title" is kept; only the schema's own titles are removed.
    assert item["required"] == ["title", "note"]
    assert item["additionalProperties"] is False


def test_a_prompt_loads_and_insists_on_its_data() -> None:
    prompt = prompts.load("profile_extract", 1)
    system, user = prompt.render({"resume": "Asha knows React."})

    assert prompt.name == "profile_extract@v1"
    assert "copied exactly" in system
    assert '<untrusted_data name="resume">' in user
    with pytest.raises(ValueError, match="needs"):
        prompt.render({})


async def test_nothing_sent_or_received_reaches_the_logs_even_in_debug(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from dataclasses import replace

    from app.core.logging import configure_logging

    configure_logging("DEBUG")
    server = transport(
        lambda _request: httpx.Response(200, json=completion('{"a": "answer-words"}'))
    )

    await server.complete(replace(REQUEST, user="private-resume-words"))

    output = capsys.readouterr().out
    configure_logging("INFO")
    for secret in ("private-resume-words", "answer-words", "test-key"):
        assert secret not in output
