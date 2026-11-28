"""Which model does which job (D-053)."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from app.config import Settings


class Role(StrEnum):
    # The large model that does the careful work.
    MAIN = "main"
    # A smaller model for light work, and the first backup.
    SMALL = "small"
    # A different family of model that checks another model's work.
    JUDGE = "judge"


Effort = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class Purpose:
    """What a call is for. It decides the model, how it answers and what it may be sent."""

    name: str
    role: Role
    # True when the text comes from the owner's life: identity is removed, and Zero Data
    # Retention must be confirmed.
    personal: bool
    max_output_tokens: int
    # 0 is steady and repeatable; higher is more varied.
    temperature: float = 0.2
    # How long a gpt-oss model thinks before answering. Thinking uses tokens.
    reasoning_effort: Effort = "high"


# Copying facts and their quotes needs little thought, and the free limit per minute must
# hold both the resume and the answer.
PROFILE_EXTRACT = Purpose(
    name="profile_extract",
    role=Role.MAIN,
    personal=True,
    max_output_tokens=4_500,
    reasoning_effort="low",
)


def chain(settings: Settings, role: Role) -> list[str]:
    """The models to try, in order."""
    names = {
        Role.MAIN: [settings.ai_main_model, settings.ai_small_model],
        Role.SMALL: [settings.ai_small_model],
        Role.JUDGE: [settings.ai_judge_model, settings.ai_small_model],
    }[role]
    return list(dict.fromkeys(names))
