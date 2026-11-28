"""The check that a fact is really in the resume, and the other profile rules."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.preferences.schemas import PreferenceValues
from app.preferences.values import lakhs, normalise_place, rupees
from app.profile.extract import is_stated, normalise, part_size, split
from app.profile.schemas import ExtractedFact, Fact, FactKind, ProfileFacts
from app.profile.service import summarise

SOURCE = normalise(
    """Experience
Frontend Developer, Lantern Works Studio, Jan 2024 EN_DASH Present
BULLET Rebuilt the reporting dashboard in Next.js and TypeScript, cutting \
load time from 4.2 s to 1.1 s.
BULLET Built a design system of 38 React components used by 6 product teams.
4 years of experience with C++ and C#.
Skills: React, Node.js, Git
[NAME_1] [EMAIL_1]"""
    # The long dash and bullets that word processors write.
    .replace("EN_DASH", chr(0x2013)).replace("BULLET", chr(0x2022))
)


def fact(
    kind: FactKind, value: str, quote: str, company: str | None = None, dates: str | None = None
) -> ExtractedFact:
    return ExtractedFact(kind=kind, value=value, quote=quote, company=company, dates=dates)


DASHBOARD = (
    "Rebuilt the reporting dashboard in Next.js and TypeScript, cutting load time from "
    "4.2 s to 1.1 s."
)


@pytest.mark.parametrize(
    "stated",
    [
        fact(
            "role",
            "Frontend Developer",
            "Frontend Developer, Lantern Works Studio, Jan 2024 - Present",
            "Lantern Works Studio",
            "Jan 2024 - Present",
        ),
        # Different capitals, spacing and dash, same words.
        fact(
            "achievement",
            "Rebuilt the reporting dashboard in Next.js",
            "  rebuilt the REPORTING dashboard in Next.js and TypeScript",
        ),
        fact("role", "Frontend Developer", f"Studio, Jan 2024 {chr(0x2014)} Present"),
        fact("achievement", DASHBOARD, DASHBOARD, "Lantern Works Studio"),
        fact("skill", "Node.js", "Skills: React, Node.js, Git"),
        fact("skill", "C++", "4 years of experience with C++ and C#."),
        fact("experience_years", "4", "4 years of experience"),
    ],
    ids=["role", "capitals", "other-dash", "achievement", "skill", "symbols", "years"],
)
def test_stated_facts_are_kept(stated: ExtractedFact) -> None:
    assert is_stated(stated, SOURCE)


@pytest.mark.parametrize(
    "invented",
    [
        fact("skill", "Kubernetes", "Skills: React, Node.js, Git, Kubernetes"),
        # A real quote, but the skill is not in it.
        fact("skill", "Kubernetes", "Skills: React, Node.js, Git"),
        # A number that was changed.
        fact("achievement", "Cut load time from 4.2 s to 0.3 s", DASHBOARD),
        fact("achievement", "Led a team of 12 engineers across Europe", DASHBOARD),
        fact("role", "Engineering Manager", "Frontend Developer, Lantern Works Studio"),
        fact("role", "Frontend Developer", "Frontend Developer", "Another Company Ltd"),
        fact("role", "Frontend Developer", "Frontend Developer", None, "Jan 2019 - Present"),
        fact("experience_years", "9", "4 years of experience"),
        fact("skill", "React", ""),
        fact("location", "[NAME_1]", "[NAME_1] [EMAIL_1]"),
    ],
    ids=[
        "quote-not-in-resume",
        "skill-not-in-quote",
        "changed-number",
        "added-claim",
        "invented-title",
        "invented-company",
        "invented-dates",
        "invented-years",
        "no-quote",
        "only-a-marker",
    ],
)
def test_invented_facts_are_dropped(invented: ExtractedFact) -> None:
    assert not is_stated(invented, SOURCE)


def test_long_text_is_cut_between_lines() -> None:
    text = "\n".join(f"line {number} " + "x" * 50 for number in range(100))

    parts = split(text, 1_000)

    assert all(len(part) <= 1_000 for part in parts)
    assert "\n".join(parts) == text
    assert split("word " * 1_000, 1_000)[0].endswith("word ")
    assert split("short", 1_000) == ["short"]


def test_the_part_size_follows_the_limit_per_minute() -> None:
    assert part_size(8_000) == 8_000 or 2_000 < part_size(8_000) < 8_000
    assert part_size(100_000) == 8_000
    assert part_size(1_000) == 2_000


def stored(kind: FactKind, value: str, dates: str | None = None) -> Fact:
    return Fact(
        fact_id=value[:8].replace(" ", ""), kind=kind, value=value, dates=dates, source="you"
    )


def test_the_summary_picks_the_current_role() -> None:
    summary = summarise(
        [
            stored("role", "Junior Developer", "2021 - 2023"),
            stored("role", "Frontend Developer", "Jan 2024 - Present"),
            stored("skill", "React"),
        ]
    )

    assert summary.latest_role == "Frontend Developer"
    assert summary.skills == ["React"]
    assert summary.experience_years is None
    assert summarise([]).latest_role is None


def test_two_facts_may_not_share_an_id() -> None:
    with pytest.raises(ValidationError, match="same id"):
        ProfileFacts(facts=[stored("skill", "React"), stored("skill", "React")])


@pytest.mark.parametrize(
    ("typed", "stored_name"),
    [
        ("Bangalore", "Bengaluru"),
        ("bengaluru", "Bengaluru"),
        ("Gurgaon", "Gurugram"),
        ("Bombay", "Mumbai"),
        ("Mumbai, India", "Mumbai"),
        ("remote", "Remote (India)"),
        ("Work From Home", "Remote (India)"),
        ("Indore", "Indore"),
        ("  navi   mumbai ", "Navi Mumbai"),
    ],
)
def test_city_normalisation_aliases(typed: str, stored_name: str) -> None:
    """E-15."""
    assert normalise_place(typed) == stored_name


@pytest.mark.parametrize(
    ("typed", "amount", "shown"),
    [
        ("14", 1_400_000, "14"),
        ("14.50", 1_450_000, "14.5"),
        ("0.5", 50_000, "0.5"),
        ("100", 10_000_000, "100"),
        ("14.05", 1_405_000, "14.05"),
    ],
)
def test_lakhs_are_stored_as_rupees(typed: str, amount: int, shown: str) -> None:
    """FR-019: 14 LPA is 1,400,000 rupees and is shown as 14 again."""
    assert rupees(Decimal(typed)) == amount
    assert str(lakhs(amount)) == shown
    assert (
        PreferenceValues(min_salary_lpa=Decimal(typed)).model_dump(mode="json")["min_salary_lpa"]
        == shown
    )


@pytest.mark.parametrize(
    "bad",
    [
        {"min_salary_lpa": 0},
        {"min_salary_lpa": -1},
        {"min_salary_lpa": 1_001},
        {"min_salary_lpa": "14.123"},
        {"min_salary_lpa": "lots"},
        {"experience_min": 5, "experience_max": 2},
        {"notice_days": 400},
        {"work_modes": []},
        {"work_modes": ["office"]},
        {"titles": ["x"]},
        {"titles": [f"Title {n}" for n in range(21)]},
        {"surprise": 1},
    ],
)
def test_unusable_preferences_are_refused(bad: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        PreferenceValues.model_validate(bad)


def test_preference_lists_are_tidied() -> None:
    values = PreferenceValues.model_validate(
        {
            "titles": ["React  Developer", "react developer", " UI Engineer "],
            "places": ["Bangalore", "Bengaluru", "Pune"],
            "work_modes": ["onsite", "remote", "remote"],
        }
    )

    assert values.titles == ["React Developer", "UI Engineer"]
    assert values.places == ["Bengaluru", "Pune"]
    assert values.work_modes == ["remote", "onsite"]
