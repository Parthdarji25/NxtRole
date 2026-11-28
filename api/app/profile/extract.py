"""Turns resume text into facts, keeping only those the resume really states (FR-014)."""

import re
import unicodedata
import uuid
from dataclasses import dataclass

from app.ai import prompts
from app.ai.budget import CHARACTERS_PER_TOKEN
from app.ai.gateway import Gateway
from app.ai.models import PROFILE_EXTRACT
from app.ai.privacy import Identity
from app.profile.schemas import MAX_FACTS, ExtractedFact, Extraction, Fact

PROMPT = ("profile_extract", 1)
# The most resume text sent in one call.
MAX_PART = 8_000
MIN_PART = 2_000
# Room in each call for our instructions.
INSTRUCTION_TOKENS = 800
# How much of a fact's words must appear in its quote.
WORDS_IN_QUOTE = 0.7

DASHES = dict.fromkeys((0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2212), "-")
QUOTES = {0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"'}
BULLETS = dict.fromkeys((0x2022, 0x25AA, 0x25CF, 0x25E6, 0x2023, 0x00B7), " ")
MARKER_ONLY = re.compile(r"^(?:\[(?:name|email|phone|link|address|private)_\d+\]\W*)+$")


def normalise(text: str) -> str:
    """Differences that do not change the words: capitals, spacing, kinds of dash."""
    text = unicodedata.normalize("NFKC", text).translate(DASHES).translate(QUOTES)
    return " ".join(text.translate(BULLETS).casefold().split())


def words(text: str) -> list[str]:
    return re.findall(r"[^\W_]+(?:[.+#][^\W_]+)*[+#]*", text)


def numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)*", text))


def is_stated(fact: ExtractedFact, source: str) -> bool:
    """True only if the fact's quote is in the resume and the fact adds nothing to it.

    `source` is the text the AI was given, already normalised.
    """
    quote = normalise(fact.quote)
    value = normalise(fact.value)
    if len(quote) < 2 or not value or quote not in source or MARKER_ONLY.match(value):
        return False
    # No number may appear that the resume does not hold.
    extra = numbers(" ".join(normalise(part or "") for part in (fact.company, fact.dates)))
    if not extra <= numbers(source) or not numbers(value) <= numbers(quote):
        return False
    if fact.company and normalise(fact.company) not in source:
        return False
    if fact.kind in ("skill", "certification"):
        return value in quote
    wanted = words(value)
    present = set(words(quote))
    if fact.kind == "role":
        # A job title is often on its own line, apart from the quoted line.
        present = set(words(source))
    return bool(wanted) and sum(word in present for word in wanted) / len(wanted) >= WORDS_IN_QUOTE


def split(text: str, size: int) -> list[str]:
    """Parts of at most `size` characters, cut between lines."""
    parts: list[str] = []
    current = ""
    for line in text.split("\n"):
        while len(line) > size:
            cut = line.rfind(" ", 0, size) + 1 or size
            parts, current, line = [*parts, current, line[:cut]], "", line[cut:]
        if current and len(current) + len(line) + 1 > size:
            parts.append(current)
            current = ""
        current = f"{current}\n{line}" if current else line
    parts.append(current)
    return [part for part in parts if part.strip()]


def part_size(tokens_per_minute: int) -> int:
    """How much text fits one call under the limit per minute."""
    room = tokens_per_minute - PROFILE_EXTRACT.max_output_tokens - INSTRUCTION_TOKENS
    return max(MIN_PART, min(MAX_PART, int(room * CHARACTERS_PER_TOKEN)))


@dataclass(frozen=True)
class Result:
    facts: list[Fact]
    # Facts left out because the resume does not state them.
    dropped: int
    model: str
    prompt: str


async def extract_facts(gateway: Gateway, text: str, identity: Identity) -> Result:
    prompt = prompts.load(*PROMPT)
    found: dict[tuple[str, str, str], Fact] = {}
    dropped = 0
    model = ""
    for part in split(text, part_size(gateway.settings.ai_tokens_per_minute)):
        answer = await gateway.run(PROFILE_EXTRACT, prompt, {"resume": part}, Extraction, identity)
        model = answer.model
        redaction = answer.redaction
        assert redaction is not None  # noqa: S101  (a personal call always hides identity)
        # Quotes are checked against exactly what the AI was shown.
        source = normalise(redaction.hide(part))
        for item in answer.value.facts:
            if not is_stated(item, source):
                dropped += 1
                continue
            key = (item.kind, normalise(item.value), normalise(item.company or ""))
            if key in found:
                continue
            found[key] = Fact(
                fact_id=uuid.uuid4().hex[:12],
                kind=item.kind,
                value=redaction.restore(item.value.strip())[:500],
                company=redaction.restore((item.company or "").strip())[:160] or None,
                dates=(item.dates or "").strip()[:160] or None,
                quote=redaction.restore(item.quote.strip())[:600],
                source="resume",
            )
    return Result(list(found.values())[:MAX_FACTS], dropped, model, prompt.name)
