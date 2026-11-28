"""Sending one request to the AI provider, and turning its errors into our own."""

from dataclasses import dataclass
from typing import Any, Protocol

import groq
import httpx

from app.ai.models import Effort

TIMEOUT_SECONDS = 60.0
DEFAULT_RETRY_AFTER_SECONDS = 60.0


@dataclass(frozen=True)
class ChatRequest:
    model: str
    prompt: str
    system: str
    user: str
    # The shape the answer must have.
    schema: dict[str, Any]
    temperature: float
    reasoning_effort: Effort
    max_output_tokens: int


@dataclass(frozen=True)
class ChatReply:
    content: str
    tokens_in: int
    tokens_out: int


class TransportError(Exception):
    """A call that gave no usable answer. Messages never contain what was sent."""


class RateLimited(TransportError):
    def __init__(self, retry_after: float = DEFAULT_RETRY_AFTER_SECONDS) -> None:
        super().__init__("the provider's limit was reached")
        self.retry_after = retry_after


class Unavailable(TransportError):
    """The provider or this model cannot be used right now."""


class BadAnswer(TransportError):
    """The model did not produce an answer of the required shape."""


class NotConfigured(TransportError):
    """The key is missing or refused."""


class TooLarge(TransportError):
    """The request is bigger than the limits allow."""


class Transport(Protocol):
    async def complete(self, request: ChatRequest) -> ChatReply: ...


def _retry_after(error: groq.APIStatusError) -> float:
    try:
        return max(1.0, float(error.response.headers.get("retry-after", "")))
    except ValueError:
        return DEFAULT_RETRY_AFTER_SECONDS


def _error_code(error: groq.APIStatusError) -> str:
    body = error.body
    if isinstance(body, dict):
        detail = body.get("error", body)
        if isinstance(detail, dict):
            return str(detail.get("code", ""))
    return ""


class GroqTransport:
    def __init__(self, api_key: str, http_client: httpx.AsyncClient | None = None) -> None:
        # Retries are decided by the gateway, which knows the budget and the other models.
        self.client = groq.AsyncGroq(
            api_key=api_key, max_retries=0, timeout=TIMEOUT_SECONDS, http_client=http_client
        )

    async def complete(self, request: ChatRequest) -> ChatReply:
        extra: dict[str, Any] = {}
        # Only the gpt-oss models take these settings.
        if request.model.startswith("openai/gpt-oss"):
            extra = {"reasoning_effort": request.reasoning_effort, "include_reasoning": False}
        try:
            completion = await self.client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.user},
                ],
                temperature=request.temperature,
                max_completion_tokens=request.max_output_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "answer", "strict": True, "schema": request.schema},
                },
                **extra,
            )
        except groq.RateLimitError as error:
            raise RateLimited(_retry_after(error)) from None
        except (groq.AuthenticationError, groq.PermissionDeniedError):
            raise NotConfigured("the provider refused the key") from None
        except groq.APIStatusError as error:
            if error.status_code == 413:
                raise TooLarge("the request is too large for the limits") from None
            if _error_code(error) == "json_validate_failed":
                raise BadAnswer("the model could not produce the required shape") from None
            raise Unavailable(f"the provider answered {error.status_code}") from None
        except groq.APIConnectionError as error:
            raise Unavailable(type(error).__name__) from None

        usage = completion.usage
        choice = completion.choices[0] if completion.choices else None
        if choice is None or choice.finish_reason == "length" or not choice.message.content:
            raise BadAnswer("the answer was empty or cut off")
        return ChatReply(
            content=choice.message.content,
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
        )

    async def list_models(self) -> list[str]:
        try:
            listing = await self.client.models.list()
        except (groq.AuthenticationError, groq.PermissionDeniedError):
            raise NotConfigured("the provider refused the key") from None
        except groq.APIError as error:
            raise Unavailable(type(error).__name__) from None
        return sorted(model.id for model in listing.data)

    async def close(self) -> None:
        await self.client.close()
