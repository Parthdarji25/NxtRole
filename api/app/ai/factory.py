"""Builds the gateway for one user's work from what the running app holds."""

import uuid

from starlette.datastructures import State

from app.ai.budget import Budget
from app.ai.gateway import Gateway
from app.ai.transport import ChatReply, ChatRequest, GroqTransport, NotConfigured, Transport
from app.ai.usage import UsageLog
from app.config import Settings


class NoProvider:
    """Stands in when there is no key, so that nothing can be sent by mistake."""

    async def complete(self, request: ChatRequest) -> ChatReply:
        raise NotConfigured("no key")


def create_transport(settings: Settings) -> Transport:
    if settings.groq_api_key is None:
        return NoProvider()
    return GroqTransport(settings.groq_api_key.get_secret_value())


def gateway_for(state: State, user_id: uuid.UUID) -> Gateway:
    return Gateway(
        state.ai_transport,
        Budget(state.redis, state.settings),
        state.settings,
        UsageLog(state.sessions, user_id),
    )
