"""Removes the owner's identity before text goes to an AI model, and puts it back after.

Emails, phone numbers and government ID numbers are always removed. The name, links and
address lines are the ones the owner confirmed on screen (D-053). Each removed value is
replaced by a marker such as [EMAIL_1], so the answer can be completed again afterwards.
"""

import re
import unicodedata
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

NO_BREAK_SPACE = chr(0xA0)
ZERO_WIDTH = chr(0x200B)

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")

# Indian mobiles (+91 98765 43210, 098765-43210, 9876543210), Indian landlines with a
# bracketed code, and other international numbers starting with "+".
PHONE = re.compile(
    r"(?<![\w.])(?:"
    r"(?:\+?91[\s.-]?|0)?\(?[6-9]\d{4}\)?[\s.-]?\d{5}"
    r"|(?:\+?91[\s.-]?)?[6-9]\d{2}[\s.-]\d{3}[\s.-]\d{4}"
    r"|\(?0\d{2,4}\)?[\s.-]\d{6,8}"
    r"|\+\d{1,3}(?:[\s.()-]{0,2}\d){7,12}"
    r")(?![\w])"
)

# Permanent Account Number and Aadhaar. Some Indian resumes print them.
GOVERNMENT_ID = re.compile(r"\b(?:[A-Z]{5}\d{4}[A-Z]|\d{4}[\s-]\d{4}[\s-]\d{4})\b")

# Lines that only describe the person and never help with a job search.
PRIVATE_LINE = re.compile(
    r"^[\s\N{BULLET}*-]*(?:date of birth|d\.?o\.?b\.?|father'?s? name|mother'?s? name|"
    r"husband'?s? name|passport(?: no\.?| number)?|aadhaar|pan(?: no\.?| number| card)?|"
    r"marital status|gender|nationality|religion)\b\s*[:\N{EN DASH}-].*$",
    re.IGNORECASE | re.MULTILINE,
)

PROFILE_SITES = (
    "linkedin.com|github.com|gitlab.com|bitbucket.org|behance.net|dribbble.com|medium.com|"
    "twitter.com|x.com|leetcode.com|hackerrank.com|codechef.com|kaggle.com|"
    "stackoverflow.com|instagram.com|facebook.com"
)
LINK = re.compile(
    r"(?<![@\w])(?:"
    r"https?://[^\s<>()|,]+"
    r"|www\.[^\s<>()|,]+"
    rf"|(?:[a-z0-9-]+\.)?(?:{PROFILE_SITES})(?:/[^\s<>()|,]*)?"
    r"|[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:dev|io|me|app|com|in|net|org|co|xyz|tech|site)"
    r"(?:/[^\s<>()|,]*)?"
    r")(?![\w@])",
    re.IGNORECASE,
)
# Technology names that look like web addresses.
NOT_LINKS = frozenset(
    {"asp.net", "vb.net", "ado.net", "socket.io", "draw.io", "dot.net", "express.io", "ml.net"}
)

PINCODE = re.compile(r"(?<!\d)[1-9]\d{2}\s?\d{3}(?!\d)")
ADDRESS_LABEL = re.compile(
    r"^\s*(?:permanent |current |present )?address\s*[:\N{EN DASH}-]", re.IGNORECASE
)

HEADINGS = frozenset(
    {
        "resume",
        "curriculum",
        "vitae",
        "cv",
        "profile",
        "summary",
        "objective",
        "contact",
        "experience",
        "education",
        "skills",
        "developer",
        "engineer",
        "manager",
        "analyst",
        "designer",
        "consultant",
    }
)

MIN_NAME_PART = 3


class Identity(BaseModel):
    """What the owner confirmed should be hidden. Every value is personal data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=80)
    emails: list[str] = Field(default_factory=list, max_length=10)
    phones: list[str] = Field(default_factory=list, max_length=10)
    links: list[str] = Field(default_factory=list, max_length=30)
    addresses: list[str] = Field(default_factory=list, max_length=10)
    # Anything else the owner wants hidden.
    other: list[str] = Field(default_factory=list, max_length=20)


class Detected(BaseModel):
    """What code found in a resume, shown to the owner before anything is sent."""

    name: str | None
    emails: list[str]
    phones: list[str]
    links: list[str]
    addresses: list[str]


def tidy(text: str) -> str:
    """The same characters in one form, so that searching finds them."""
    return unicodedata.normalize("NFKC", text).replace(NO_BREAK_SPACE, " ").replace(ZERO_WIDTH, "")


def _unique(values: Iterable[str]) -> list[str]:
    seen: dict[str, str] = {}
    for value in values:
        cleaned = value.strip().rstrip(".,;")
        if cleaned:
            seen.setdefault(cleaned.casefold(), cleaned)
    return list(seen.values())


def find_links(text: str) -> list[str]:
    found = (match.group(0) for match in LINK.finditer(text))
    return _unique(link for link in found if link.casefold().rstrip("./") not in NOT_LINKS)


def guess_name(text: str) -> str | None:
    """Resumes usually start with the person's name. The owner checks the guess."""
    for line in text.splitlines()[:8]:
        candidate = line.strip(" \t|,-•")
        words = candidate.split()
        if not 2 <= len(words) <= 5 or len(candidate) > 60:
            continue
        if not all(re.fullmatch(r"[^\W\d_](?:[^\W\d_]|[.'-])*", word) for word in words):
            continue
        if any(word.casefold().strip(".") in HEADINGS for word in words):
            continue
        if all(word[0].isupper() for word in words):
            return candidate
    return None


def detect(text: str) -> Detected:
    text = tidy(text)
    emails = _unique(match.group(0) for match in EMAIL.finditer(text))
    without_emails = EMAIL.sub(" ", text)
    addresses = [
        line.strip()
        for line in text.splitlines()
        if (PINCODE.search(PHONE.sub(" ", line)) or ADDRESS_LABEL.match(line))
        and len(line.strip()) <= 200
    ]
    return Detected(
        name=guess_name(text),
        emails=emails,
        phones=_unique(match.group(0) for match in PHONE.finditer(without_emails)),
        links=find_links(without_emails),
        addresses=_unique(addresses),
    )


class Redaction:
    """Hides values in text and remembers what each marker stands for."""

    def __init__(self, identity: Identity) -> None:
        self.identity = identity
        self.originals: dict[str, str] = {}
        self._markers: dict[str, str] = {}

    def _marker(self, kind: str, value: str) -> str:
        known = self._markers.get(value.casefold())
        if known is not None:
            return known
        number = 1 + sum(marker.startswith(f"[{kind}_") for marker in self.originals)
        marker = f"[{kind}_{number}]"
        self._markers[value.casefold()] = marker
        self.originals[marker] = value
        return marker

    def _hide_value(self, text: str, kind: str, value: str, *, whole_word: bool = False) -> str:
        # Spaces in the value also match line breaks and repeated spaces.
        pattern = r"\s+".join(re.escape(part) for part in tidy(value).split())
        if not pattern:
            return text
        if whole_word:
            pattern = rf"(?<![^\W_]){pattern}(?![^\W_])"
        return re.sub(
            pattern,
            lambda match: self._marker(kind, match.group(0)),
            text,
            flags=re.IGNORECASE,
        )

    def _hide_pattern(self, text: str, kind: str, pattern: re.Pattern[str]) -> str:
        return pattern.sub(lambda match: self._marker(kind, match.group(0)), text)

    def hide(self, text: str) -> str:
        identity = self.identity
        text = tidy(text)
        # Longest first, so that part of a longer value is not replaced on its own.
        for kind, values in (
            ("ADDRESS", identity.addresses),
            ("EMAIL", identity.emails),
            ("LINK", identity.links),
            ("PHONE", identity.phones),
            ("PRIVATE", identity.other),
        ):
            for value in sorted(values, key=len, reverse=True):
                text = self._hide_value(text, kind, value)
        text = self._hide_pattern(text, "PRIVATE", PRIVATE_LINE)
        text = self._hide_pattern(text, "EMAIL", EMAIL)
        text = self._hide_pattern(text, "PRIVATE", GOVERNMENT_ID)
        text = self._hide_pattern(text, "PHONE", PHONE)
        text = self._hide_value(text, "NAME", identity.name, whole_word=True)
        # First and last names on their own, such as "Reference letter for Asha".
        for part in identity.name.split():
            if len(part.strip(".")) >= MIN_NAME_PART:
                text = self._hide_value(text, "NAME", part.strip("."), whole_word=True)
        return text

    def restore(self, value: Any) -> Any:
        """Puts the originals back into a text, or into every text inside lists and maps."""
        if isinstance(value, str):
            for marker, original in self.originals.items():
                value = value.replace(marker, original)
            return value
        if isinstance(value, list):
            return [self.restore(item) for item in value]
        if isinstance(value, dict):
            return {key: self.restore(item) for key, item in value.items()}
        return value

    def leaks(self, text: str) -> list[str]:
        """The kinds of personal data still present. Empty when the text is safe to send."""
        found = []
        folded = tidy(text).casefold()
        # Markers are ours and may contain digits; they are not the owner's data.
        folded = re.sub(r"\[(?:name|email|phone|link|address|private)_\d+\]", " ", folded)
        if EMAIL.search(folded):
            found.append("email")
        if PHONE.search(folded):
            found.append("phone")
        if GOVERNMENT_ID.search(folded.upper()):
            found.append("government id")
        identity = self.identity
        if re.search(rf"(?<![^\W_]){re.escape(identity.name.casefold())}(?![^\W_])", folded):
            found.append("name")
        squashed = re.sub(r"\s+", "", folded)
        digits = re.sub(r"\D", "", folded)
        for kind, values in (
            ("email", identity.emails),
            ("link", identity.links),
            ("address", identity.addresses),
            ("private", identity.other),
        ):
            if any(re.sub(r"\s+", "", tidy(v).casefold()) in squashed for v in values if v):
                found.append(kind)
        # The last ten digits of a confirmed number, however it is written.
        for phone in identity.phones:
            number = re.sub(r"\D", "", phone)[-10:]
            if len(number) >= 8 and number in digits:
                found.append("phone")
        return sorted(set(found))
