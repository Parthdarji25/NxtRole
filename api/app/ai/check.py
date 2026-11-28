"""uv run python -m app.cli check-ai: is the key accepted, and do the chosen models exist?

It lists the provider's models, which uses no tokens and sends nothing about the owner.
"""

from collections.abc import Callable

from app.ai.models import Role, chain
from app.ai.transport import GroqTransport, TransportError
from app.config import Settings

KEY_HINT = (
    "Create a key at console.groq.com > API Keys and add it to api/.env yourself:\n"
    "         GROQ_API_KEY=your-key"
)
ZDR_HINT = (
    "Turn it on at console.groq.com > Settings > Data Controls, then add to api/.env:\n"
    "         GROQ_ZDR_CONFIRMED_ON=the date, as YYYY-MM-DD"
)


async def check_ai(settings: Settings, say: Callable[[str], None] = print) -> int:
    if settings.groq_api_key is None:
        say("  [FAIL] GROQ_API_KEY is missing.")
        say(f"         {KEY_HINT}")
        return 1
    transport = GroqTransport(settings.groq_api_key.get_secret_value())
    try:
        available = await transport.list_models()
    except TransportError as error:
        say(f"  [FAIL] Groq: {error}.")
        say(f"         {KEY_HINT}")
        return 1
    finally:
        await transport.close()
    say(f"  [ OK ] Groq accepted the key and offers {len(available)} models.")

    passed = True
    for role in Role:
        name = chain(settings, role)[0]
        if name in available:
            say(f"  [ OK ] {role.value} model: {name}")
        else:
            passed = False
            say(f"  [FAIL] {role.value} model: {name} is not offered. Choose one of:")
            say(f"         {', '.join(available)}")
    if settings.groq_zdr_confirmed_on is None:
        passed = False
        say("  [FAIL] Zero Data Retention is not confirmed, so no personal data will be sent.")
        say(f"         {ZDR_HINT}")
    else:
        confirmed = settings.groq_zdr_confirmed_on.isoformat()
        say(f"  [ OK ] Zero Data Retention: you confirmed it on {confirmed}.")
    return 0 if passed else 1
