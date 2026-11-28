"""The privacy guard. All names, numbers and addresses here are invented."""

import pytest

from app.ai.privacy import Identity, Redaction, detect, guess_name

IDENTITY = Identity(
    name="Meera Sundaram Iyer",
    emails=["meera.iyer@example.com"],
    phones=["+91 98765 43210"],
    links=["linkedin.com/in/meera-iyer-test", "meeraiyer.dev"],
    addresses=["14, Lake View Road, Pune 411045"],
)

RESUME = """Meera Sundaram Iyer
Frontend Developer
14, Lake View Road, Pune 411045
meera.iyer@example.com | +91 98765 43210 | linkedin.com/in/meera-iyer-test
Portfolio: meeraiyer.dev
Date of Birth: 12 March 1998

Experience
Built dashboards with React, Next.js, ASP.NET and socket.io for 40,000 users.
Reduced load time from 4.2 s to 1.1 s between 2021 and 2024.
"""


@pytest.mark.parametrize(
    "phone",
    [
        "+91 98765 43210",
        "+91-98765-43210",
        "+919876543210",
        "91 98765 43210",
        "09876543210",
        "9876543210",
        "98765 43210",
        "987-654-3210",
        "(022) 26543210",
        "020-26543210",
        "+1 (415) 555-0132",
        "+44 20 7946 0958",
    ],
)
def test_every_common_phone_format_is_removed(phone: str) -> None:
    redaction = Redaction(Identity(name="Asha Rao"))

    hidden = redaction.hide(f"Call me on {phone} after six.")

    assert phone not in hidden
    assert "[PHONE_1]" in hidden
    assert redaction.restore(hidden) == f"Call me on {phone} after six."
    assert redaction.leaks(hidden) == []


@pytest.mark.parametrize(
    "text",
    [
        "Worked from 2019 to 2024.",
        "Served 10,00,000 requests a day.",
        "Cut cost by 35% across 12 services.",
        "Version 18.2.0 of React.",
        "Salary was 1400000 a year.",
    ],
)
def test_ordinary_numbers_are_left_alone(text: str) -> None:
    assert Redaction(Identity(name="Asha Rao")).hide(text) == text


@pytest.mark.parametrize(
    "email",
    ["asha.rao+jobs@example.co.in", "ASHA_RAO@Example.COM", "a-1@mail.example.org"],
)
def test_emails_are_removed_even_when_not_confirmed(email: str) -> None:
    hidden = Redaction(Identity(name="Asha Rao")).hide(f"Write to {email}.")

    assert email not in hidden


@pytest.mark.parametrize(
    "line",
    [
        "Date of Birth: 12/03/1998",
        "DOB - 12 March 1998",
        "Father's Name: R. Sundaram",
        "Passport No: Z1234567",
        "Marital Status: Single",
        "PAN: ABCDE1234F",
        "• Gender: Female",
    ],
)
def test_private_lines_are_removed(line: str) -> None:
    hidden = Redaction(Identity(name="Asha Rao")).hide(f"Skills: React\n{line}\nHobbies: chess")

    assert hidden.count("[PRIVATE_1]") == 1
    assert line.split(":")[-1].split("-")[-1].strip() not in hidden
    assert "Skills: React" in hidden and "Hobbies: chess" in hidden


@pytest.mark.parametrize("number", ["ABCDE1234F", "1234 5678 9012", "1234-5678-9012"])
def test_government_id_numbers_are_removed_anywhere(number: str) -> None:
    assert number not in Redaction(Identity(name="Asha Rao")).hide(f"My number {number} here")


def test_nothing_personal_survives_a_whole_resume() -> None:
    redaction = Redaction(IDENTITY)

    hidden = redaction.hide(RESUME)

    for value in (
        "Meera",
        "Sundaram",
        "Iyer",
        "meera",
        "98765",
        "43210",
        "Lake View",
        "411045",
        "linkedin",
        "meeraiyer.dev",
        "12 March 1998",
    ):
        assert value.casefold() not in hidden.casefold(), value
    assert redaction.leaks(hidden) == []
    # The useful content stays.
    for kept in ("React", "Next.js", "ASP.NET", "socket.io", "40,000 users", "4.2 s", "2021"):
        assert kept in hidden, kept
    assert redaction.restore(hidden) == RESUME


def test_the_name_is_found_in_other_capitals_and_across_lines() -> None:
    hidden = Redaction(IDENTITY).hide("MEERA SUNDARAM\nIYER wrote this. Reference for Meera.")

    assert "meera" not in hidden.casefold()


def test_a_name_inside_another_word_is_not_cut_out() -> None:
    hidden = Redaction(Identity(name="Ann Lee")).hide("Annual planning with Leeds team")

    assert hidden == "Annual planning with Leeds team"


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("reach meera sundaram iyer", "name"),
        ("meera.iyer@example.com", "email"),
        ("tel 98765-43210", "phone"),
        ("98 76 54 32 10", "phone"),
        ("see meeraiyer.dev", "link"),
        ("14, Lake View Road,  Pune 411045", "address"),
        ("id ABCDE1234F", "government id"),
    ],
)
def test_the_final_check_notices_anything_left(text: str, kind: str) -> None:
    assert kind in Redaction(IDENTITY).leaks(text)


def test_detection_finds_what_the_owner_will_be_shown() -> None:
    found = detect(RESUME)

    assert found.name == "Meera Sundaram Iyer"
    assert found.emails == ["meera.iyer@example.com"]
    assert found.phones == ["+91 98765 43210"]
    assert found.links == ["linkedin.com/in/meera-iyer-test", "meeraiyer.dev"]
    assert found.addresses == ["14, Lake View Road, Pune 411045"]


@pytest.mark.parametrize(
    ("top", "name"),
    [
        ("CURRICULUM VITAE\nAsha Rao\n", "Asha Rao"),
        ("Resume\n\nR. K. Narayan\n", "R. K. Narayan"),
        ("Software Engineer\nasha@example.com\n", None),
        ("worked on many things\n", None),
    ],
)
def test_the_name_guess(top: str, name: str | None) -> None:
    assert guess_name(top) == name
