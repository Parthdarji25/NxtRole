"""Every AI call goes through here (D-025).

In order: refuse personal data unless Zero Data Retention is confirmed; remove identity;
check nothing personal is left; stay inside the limits; try the models in turn; accept only
an answer of the required shape, asking again at most twice.
"""

import asyncio
import copy
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from typing import Any

import structlog
from pydantic import BaseModel, ValidationError

from app.ai.budget import Budget, Exhausted, Wait, estimate_tokens
from app.ai.models import Purpose, chain
from app.ai.privacy import Identity, Redaction
from app.ai.prompts import Prompt
from app.ai.transport import (
    BadAnswer,
    ChatReply,
    ChatRequest,
    NotConfigured,
    RateLimited,
    TooLarge,
    Transport,
    Unavailable,
)
from app.ai.usage import Used
from app.config import Settings
from app.core.errors import AppError

MAX_ANSWER_ATTEMPTS = 3  # the first try and two retries
MAX_UNAVAILABLE_ATTEMPTS = 2
RETRY_PAUSE_SECONDS = 2.0
# Longer waits than this are not worth holding the work for.
MAX_WAIT_SECONDS = 75.0

# Keywords the provider's strict mode does not accept. Pydantic still checks them.
UNSUPPORTED = frozenset(
    {
        "default",
        "title",
        "format",
        "pattern",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "minimum",
        "maximum",
    }
)

log = structlog.get_logger("nxtrole.ai")

RecordUsage = Callable[[str, Used], Awaitable[None]]


def ai_not_set_up() -> AppError:
    return AppError(
        "ai_not_set_up",
        "AI is not set up: the Groq key is missing or was refused. See the README.",
        status_code=503,
    )


def privacy_not_confirmed() -> AppError:
    return AppError(
        "privacy_not_confirmed",
        "Turn on Zero Data Retention in Groq, then record the date in api/.env. Nothing "
        "personal is sent to AI before that.",
        status_code=409,
    )


def limits_reached(retry_after: float) -> AppError:
    return AppError(
        "ai_limits_reached",
        "The free AI limit is used up for now. Nothing is lost: try again later.",
        status_code=503,
        extra={"retry_after_seconds": int(retry_after) + 1},
    )


def ai_unavailable() -> AppError:
    return AppError(
        "ai_unavailable",
        "The AI service could not be reached. Nothing is lost: try again in a while.",
        status_code=503,
    )


def ai_bad_answer() -> AppError:
    return AppError(
        "ai_bad_answer",
        "The AI did not give a usable answer. Please try again.",
        status_code=502,
    )


def ai_too_large() -> AppError:
    return AppError(
        "ai_too_large",
        "That text is too long for the free AI limit. Use a shorter file.",
        status_code=413,
    )


def ai_blocked() -> AppError:
    return AppError(
        "ai_blocked",
        "NxtRole stopped this because personal details were still in the text. Add them to "
        "the hidden list and try again.",
        status_code=422,
    )


def strict_schema(model: type[BaseModel]) -> dict[str, Any]:
    """The model's shape in the form the provider's strict mode wants: no references, every
    field required, nothing extra allowed."""
    schema = model.model_json_schema()
    definitions = schema.pop("$defs", {})

    def walk(node: Any) -> Any:
        if isinstance(node, list):
            return [walk(item) for item in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            return walk(copy.deepcopy(definitions[node["$ref"].rsplit("/", 1)[-1]]))
        result = {
            key: (
                {name: walk(value) for name, value in item.items()}
                if key == "properties"
                else walk(item)
            )
            for key, item in node.items()
            if key not in UNSUPPORTED
        }
        if "properties" in result:
            result["required"] = list(result["properties"])
            result["additionalProperties"] = False
        return result

    walked: dict[str, Any] = walk(schema)
    return walked


@dataclass(frozen=True)
class Answer[Output: BaseModel]:
    # The checked answer. Hidden details still appear as markers: see `redaction`.
    value: Output
    model: str
    prompt: str
    redaction: Redaction | None


class Gateway:
    def __init__(
        self,
        transport: Transport,
        budget: Budget,
        settings: Settings,
        record_usage: RecordUsage,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.transport = transport
        self.budget = budget
        self.settings = settings
        self.record_usage = record_usage
        self.sleep = sleep

    async def run[Output: BaseModel](
        self,
        purpose: Purpose,
        prompt: Prompt,
        data: dict[str, str],
        output: type[Output],
        identity: Identity | None = None,
    ) -> Answer[Output]:
        redaction = self._protect(purpose, identity)
        if redaction is not None:
            data = {name: redaction.hide(value) for name, value in data.items()}
        system, user = prompt.render(data)
        if redaction is not None:
            left = redaction.leaks(user)
            if left:
                # Only the kinds are logged, never the text.
                log.error("ai_call_blocked", purpose=purpose.name, kinds=left)
                raise ai_blocked()
        request = ChatRequest(
            model="",
            prompt=prompt.name,
            system=system,
            user=user,
            schema=strict_schema(output),
            temperature=purpose.temperature,
            reasoning_effort=purpose.reasoning_effort,
            max_output_tokens=purpose.max_output_tokens,
        )

        waits: list[float] = []
        for model in chain(self.settings, purpose.role):
            outcome = await self._try_model(replace(request, model=model), output)
            if isinstance(outcome, BaseModel):
                log.info("ai_answer", purpose=purpose.name, model=model, prompt=prompt.name)
                return Answer(outcome, model, prompt.name, redaction)
            if outcome is not None:
                waits.append(outcome)
        if waits:
            raise limits_reached(min(waits))
        raise ai_unavailable()

    def _protect(self, purpose: Purpose, identity: Identity | None) -> Redaction | None:
        if self.settings.groq_api_key is None:
            raise ai_not_set_up()
        if not purpose.personal:
            return None
        if self.settings.groq_zdr_confirmed_on is None:
            raise privacy_not_confirmed()
        if identity is None:
            raise ValueError(f"{purpose.name} sends personal text and needs an identity")
        return Redaction(identity)

    async def _try_model[Output: BaseModel](
        self, request: ChatRequest, output: type[Output]
    ) -> Output | float | None:
        """The answer; or the seconds until this model is free; or None if it cannot be
        used. Raises when asking again would not help."""
        model = request.model
        unavailable = 0
        attempts = 0
        correction = ""
        while attempts < MAX_ANSWER_ATTEMPTS:
            current = replace(request, user=request.user + correction)
            needed = estimate_tokens(current.system + current.user) + current.max_output_tokens
            if needed > self.settings.ai_tokens_per_minute:
                raise ai_too_large()
            slot = await self.budget.acquire(model, needed)
            if isinstance(slot, Exhausted):
                return slot.seconds
            if isinstance(slot, Wait):
                if slot.seconds > MAX_WAIT_SECONDS:
                    return slot.seconds
                await self.sleep(slot.seconds)
                continue

            reply: ChatReply | None = None
            try:
                reply = await self.transport.complete(current)
            except RateLimited as error:
                await self.budget.release(model, slot.reservation)
                await self.budget.pause(model, error.retry_after)
                await self.record_usage(model, Used(rate_limited=1))
                log.warning("ai_rate_limited", model=model)
                return error.retry_after
            except Unavailable as error:
                await self.budget.release(model, slot.reservation)
                await self.record_usage(model, Used(errors=1))
                log.warning("ai_unavailable", model=model, reason=str(error))
                unavailable += 1
                if unavailable >= MAX_UNAVAILABLE_ATTEMPTS:
                    return None
                await self.sleep(RETRY_PAUSE_SECONDS)
                continue
            except NotConfigured:
                raise ai_not_set_up() from None
            except TooLarge:
                await self.budget.release(model, slot.reservation)
                await self.record_usage(model, Used(errors=1))
                raise ai_too_large() from None
            except BadAnswer:
                reply = None

            tokens_in = reply.tokens_in if reply else needed - request.max_output_tokens
            tokens_out = reply.tokens_out if reply else request.max_output_tokens
            await self.budget.settle(model, slot.reservation, tokens_in + tokens_out)
            attempts += 1
            problem = "it was not complete, valid JSON of the required shape"
            if reply is not None:
                try:
                    value = output.model_validate_json(reply.content)
                except ValidationError as error:
                    # Places and reasons only: the values may hold personal text.
                    problem = "; ".join(
                        f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
                        for item in error.errors(include_input=False, include_url=False)[:5]
                    )
                else:
                    await self.record_usage(
                        model, Used(requests=1, tokens_in=tokens_in, tokens_out=tokens_out)
                    )
                    return value
            await self.record_usage(
                model, Used(requests=1, tokens_in=tokens_in, tokens_out=tokens_out, errors=1)
            )
            log.warning("ai_answer_rejected", model=model, attempt=attempts)
            correction = f"\n\nYour previous answer was rejected: {problem}. Answer again."
        raise ai_bad_answer()
