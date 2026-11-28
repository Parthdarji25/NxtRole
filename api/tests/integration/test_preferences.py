"""What the owner is looking for, and the rules it creates (FR-019, FR-020, FR-071)."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx
import pytest
from sqlalchemy import select

from app.config import Settings
from app.db.models import Rule, SearchPreferences
from tests.integration.auth_helpers import Device, api, code_of, device, make_user
from tests.integration.factories import owner_session

pytestmark = pytest.mark.usefixtures("quick_hashing")

WANTED = {
    "titles": ["Frontend Developer", "React Developer"],
    "places": ["Bangalore", "Pune", "remote"],
    "min_salary_lpa": 14,
    "work_modes": ["remote", "hybrid", "onsite"],
    "avoid_company_types": [],
    "experience_min": 3,
    "experience_max": 6,
    "notice_days": 60,
    "expected_ctc_lpa": "18.5",
}


@dataclass
class Owner:
    client: httpx.AsyncClient
    device: Device
    settings: Settings

    async def call(self, method: str, path: str, body: object = None) -> httpx.Response:
        return await self.client.request(method, path, json=body, headers=self.device.headers)

    async def save(self, version: int, **changes: Any) -> httpx.Response:
        return await self.call("PUT", "/api/preferences", {**WANTED, **changes, "version": version})

    async def preferences(self) -> dict[str, Any]:
        return dict((await self.call("GET", "/api/preferences")).json())

    async def rules(self) -> list[str]:
        items = (await self.call("GET", "/api/rules")).json()["items"]
        return [item["text"] for item in items]


@pytest.fixture
async def owner(test_settings: Settings) -> AsyncIterator[Owner]:
    await make_user(test_settings)
    async with api(test_settings) as client:
        yield Owner(client, await device(client), test_settings)


async def test_before_saving_nothing_is_filtered(owner: Owner) -> None:
    preferences = await owner.preferences()

    assert (preferences["version"], preferences["onboarding_step"]) == (0, 1)
    assert preferences["titles"] == [] and preferences["min_salary_lpa"] is None
    assert preferences["work_modes"] == ["remote", "hybrid", "onsite"]
    assert await owner.rules() == []


async def test_saving_stores_each_value_once(owner: Owner) -> None:
    response = await owner.save(0)

    assert response.status_code == 200, response.text
    shown = response.json()["preferences"]
    assert shown["places"] == ["Bengaluru", "Pune", "Remote (India)"]
    assert (shown["min_salary_lpa"], shown["expected_ctc_lpa"], shown["version"]) == (
        "14",
        "18.5",
        1,
    )
    async with owner_session(owner.settings) as db:
        row = (await db.scalars(select(SearchPreferences))).one()
        [rule] = (await db.scalars(select(Rule))).all()
    assert row.expected_ctc_inr == 1_850_000
    assert (rule.kind, rule.value, rule.origin) == (
        "min_fixed_pay",
        {"amount_inr": 1_400_000},
        "you",
    )
    assert await owner.rules() == ["Fixed pay of ₹14 lakh a year or more"]


async def test_hard_filters_become_rules_you_set(owner: Owner) -> None:
    await owner.save(0, work_modes=["remote"], avoid_company_types=["IT services", "Staffing"])

    items = (await owner.call("GET", "/api/rules")).json()["items"]
    assert {item["origin"] for item in items} == {"you"}
    assert sorted(item["text"] for item in items) == [
        "Fixed pay of ₹14 lakh a year or more",
        "Only remote jobs",
        "Skip these kinds of company: IT services, Staffing",
    ]

    await owner.save(1, min_salary_lpa=None)

    assert await owner.rules() == []


async def test_undo_restores_preferences_and_rules_together(owner: Owner) -> None:
    await owner.save(0)
    changed = await owner.save(1, titles=["UI Engineer"], work_modes=["remote"], min_salary_lpa=20)

    undone = await owner.call("POST", f"/api/events/{changed.json()['event_id']}/undo")

    assert undone.status_code == 200, undone.text
    preferences = await owner.preferences()
    assert preferences["titles"] == WANTED["titles"]
    assert preferences["min_salary_lpa"] == "14"
    assert await owner.rules() == ["Fixed pay of ₹14 lakh a year or more"]


async def test_saving_the_same_again_writes_no_history(owner: Owner) -> None:
    await owner.save(0)

    again = await owner.save(1, min_salary_lpa="14.00", places=["Bengaluru", "Pune", "Remote"])

    assert again.json()["event_id"] is None
    assert again.json()["preferences"]["version"] == 1


async def test_an_old_version_is_a_conflict(owner: Owner) -> None:
    await owner.save(0)

    stale = await owner.save(0, titles=["Other"])

    assert code_of(stale) == "conflict"
    assert (await owner.preferences())["titles"] == WANTED["titles"]


@pytest.mark.parametrize(
    "changes",
    [{"min_salary_lpa": 0}, {"experience_min": 9, "experience_max": 1}, {"work_modes": []}],
)
async def test_invalid_preferences_change_nothing(owner: Owner, changes: dict[str, Any]) -> None:
    response = await owner.save(0, **changes)

    assert response.status_code == 422
    assert (await owner.preferences())["version"] == 0


async def test_the_setup_step_is_remembered(owner: Owner) -> None:
    await owner.call("PUT", "/api/preferences/setup-step", {"step": 2})
    first = (await owner.preferences())["onboarding_step"]
    await owner.save(0)

    assert first == 2
    assert (await owner.preferences())["onboarding_step"] == 2
    bad = await owner.call("PUT", "/api/preferences/setup-step", {"step": 9})
    assert bad.status_code == 422


async def test_rules_belong_to_one_person(owner: Owner, test_settings: Settings) -> None:
    await owner.save(0)
    await make_user(test_settings, "other@example.com")
    other = Owner(owner.client, await device(owner.client, "other@example.com"), test_settings)

    assert await other.rules() == []
    assert (await other.preferences())["titles"] == []
