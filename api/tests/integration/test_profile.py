"""From an uploaded resume to an approved profile (FR-014 to FR-018). The AI is a stand-in
whose answers are written here; tests/integration/test_recorded_ai.py uses real ones."""

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import select, update

from app.ai.transport import RateLimited, Unavailable
from app.config import Settings
from app.core.redis import create_redis
from app.db.models import BackgroundJob, File
from tests.ai_helpers import FakeTransport, Step
from tests.files_helpers import RESUME_TEXT, docx, resume_pdf
from tests.integration.auth_helpers import Device, api, code_of, device, make_user
from tests.integration.factories import owner_session

pytestmark = pytest.mark.usefixtures("quick_hashing")

SKILLS = "JavaScript, TypeScript, React, Next.js, Redux, Tailwind CSS, Jest, Playwright, Git, Figma"
ROLE = "Frontend Developer, Lantern Works Studio, Jan 2024 - Present"


def item(
    kind: str, value: str, quote: str, company: str | None = None, dates: str | None = None
) -> dict[str, Any]:
    return {"kind": kind, "value": value, "company": company, "dates": dates, "quote": quote}


ANSWER = {
    "facts": [
        item("experience_years", "4", "Frontend developer with 4 years of experience"),
        item("role", "Frontend Developer", ROLE, "Lantern Works Studio", "Jan 2024 - Present"),
        item("skill", "React", SKILLS),
        item("skill", "TypeScript", SKILLS),
        item("skill", "react", SKILLS),
        # Two inventions.
        item("skill", "Kubernetes", SKILLS + ", Kubernetes"),
        item("achievement", "Grew revenue by 300%", ROLE),
    ]
}
HIDE = {
    "name": "Meera Iyer",
    "emails": ["meera.iyer@example.com"],
    "phones": ["+91 98765 43210"],
    "links": ["linkedin.com/in/meera-iyer-synthetic"],
    "addresses": ["14, Lake View Road, Pune 411045"],
}


@dataclass
class Owner:
    client: httpx.AsyncClient
    device: Device
    settings: Settings
    ai: FakeTransport

    async def call(self, method: str, path: str, body: object = None) -> httpx.Response:
        return await self.client.request(method, path, json=body, headers=self.device.headers)

    async def upload(self, data: bytes | None = None) -> str:
        content = data or resume_pdf()
        content_type = (
            "application/pdf"
            if content.startswith(b"%PDF")
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        started = (
            await self.call(
                "POST",
                "/api/files/uploads",
                {"filename": "resume", "content_type": content_type, "size": len(content)},
            )
        ).json()
        await self.client.put(started["upload_url"], content=content)
        checked = await self.call("POST", f"/api/files/{started['file_id']}/complete")
        assert checked.status_code == 200, checked.text
        return str(checked.json()["file"]["id"])

    async def read(self, file_id: str) -> httpx.Response:
        return await self.call("POST", "/api/profile/parse", {"file_id": file_id, "hide": HIDE})

    async def profile(self) -> dict[str, Any]:
        return dict((await self.call("GET", "/api/profile")).json())

    async def suggest(self, data: bytes | None = None) -> dict[str, Any]:
        """Uploads and reads. Returns the suggestion waiting for approval."""
        response = await self.read(await self.upload(data))
        assert response.status_code == 202, response.text
        suggestion = (await self.profile())["suggestion"]
        assert suggestion is not None
        return dict(suggestion)

    async def approve(self, suggestion: dict[str, Any], body: object = None) -> httpx.Response:
        return await self.call("POST", f"/api/proposals/{suggestion['proposal_id']}/approve", body)


def ready(settings: Settings) -> Settings:
    return settings.model_copy(
        update={
            "groq_api_key": SecretStr("test-key-that-opens-nothing"),
            "groq_zdr_confirmed_on": date(2026, 11, 28),
        }
    )


@pytest.fixture
async def owner(test_settings: Settings, request: pytest.FixtureRequest) -> AsyncIterator[Owner]:
    steps: tuple[Step, ...] = getattr(request, "param", (ANSWER,))
    await make_user(test_settings)
    transport = FakeTransport(*steps)
    async with api(ready(test_settings), transport=transport) as client:
        yield Owner(client, await device(client), test_settings, transport)


async def test_profile_is_proposed_then_approved_as_version_one(owner: Owner) -> None:
    suggestion = await owner.suggest()

    before = await owner.profile()
    assert before["approved"] is None and before["version"] == 0
    assert before["reading"]["state"] == "done"
    values = [fact["value"] for fact in suggestion["facts"]]
    assert values == ["4", "Frontend Developer", "React", "TypeScript"]
    assert suggestion["dropped"] == 2
    assert all(fact["quote"] and fact["source"] == "resume" for fact in suggestion["facts"])

    approved = await owner.approve(suggestion)

    assert approved.status_code == 200, approved.text
    after = await owner.profile()
    assert after["suggestion"] is None
    assert (after["version"], after["approved"]["version_no"]) == (1, 1)
    assert after["summary"] == {
        "experience_years": "4",
        "latest_role": "Frontend Developer",
        "skills": ["React", "TypeScript"],
    }
    [event] = (await owner.call("GET", "/api/history")).json()["items"]
    assert (event["actor"], event["action"]) == ("agent:profile", "profile.facts_changed")


async def test_nothing_personal_is_in_any_ai_request(owner: Owner) -> None:
    await owner.suggest()

    sent = owner.ai.everything_sent().casefold()
    for secret in ("meera", "iyer", "98765", "43210", "lake view", "411045", "linkedin", "1998"):
        assert secret not in sent, secret
    assert "lantern works studio" in sent


async def test_resume_replace_makes_new_version(owner: Owner) -> None:
    """E-37, FR-018: nothing is replaced until approved; old versions are kept."""
    await owner.approve(await owner.suggest())
    second = await owner.suggest(docx(RESUME_TEXT + "\nNew line about React."))

    assert (await owner.profile())["approved"]["version_no"] == 1
    await owner.approve(second)

    versions = (await owner.call("GET", "/api/profile/versions")).json()["items"]
    assert [(v["version_no"], v["in_use"]) for v in versions] == [(2, True), (1, False)]

    restored = await owner.call("POST", f"/api/profile/versions/{versions[1]['id']}/restore")

    assert restored.json()["profile"]["approved"]["version_no"] == 3
    assert (
        await owner.call("POST", f"/api/profile/versions/{uuid.uuid4()}/restore")
    ).status_code == 404


async def test_the_owner_can_edit_before_approving(owner: Owner) -> None:
    suggestion = await owner.suggest()
    kept = suggestion["facts"][:2]
    kept[1]["value"] = "Senior Frontend Developer"
    added = {"fact_id": "mine-1", "kind": "skill", "value": "Docker", "source": "you"}

    response = await owner.approve(
        suggestion,
        {
            "edited_payload": {
                "facts": [*kept, added],
                "source_file_id": suggestion["source_file_id"],
            }
        },
    )

    assert response.status_code == 200, response.text
    facts = (await owner.profile())["approved"]["facts"]
    assert [fact["value"] for fact in facts] == ["4", "Senior Frontend Developer", "Docker"]
    assert facts[2]["quote"] is None


async def test_rejecting_changes_nothing(owner: Owner) -> None:
    suggestion = await owner.suggest()

    await owner.call("POST", f"/api/proposals/{suggestion['proposal_id']}/reject")

    profile = await owner.profile()
    assert profile["approved"] is None and profile["suggestion"] is None


async def test_editing_after_approval_makes_a_version_that_can_be_undone(owner: Owner) -> None:
    await owner.approve(await owner.suggest())
    approved = (await owner.profile())["approved"]
    fewer = {
        "facts": approved["facts"][:1],
        "source_file_id": approved["source_file_id"],
        "version": 1,
    }

    saved = await owner.call("PUT", "/api/profile", fewer)
    stale = await owner.call("PUT", "/api/profile", {**fewer, "facts": []})
    undone = await owner.call("POST", f"/api/events/{saved.json()['event_id']}/undo")

    assert saved.json()["profile"]["version"] == 2
    assert code_of(stale) == "conflict"
    assert undone.status_code == 200
    after = await owner.profile()
    assert after["version"] == 3
    assert after["approved"]["facts"] == approved["facts"]


async def test_undoing_the_first_approval_leaves_no_profile(owner: Owner) -> None:
    approved = await owner.approve(await owner.suggest())

    await owner.call("POST", f"/api/events/{approved.json()['event_id']}/undo")

    profile = await owner.profile()
    assert profile["approved"] is None and profile["summary"] is None
    assert (await owner.call("GET", "/api/profile/versions")).json()["items"][0]["in_use"] is False


async def test_a_newer_suggestion_replaces_the_waiting_one(owner: Owner) -> None:
    first = await owner.suggest()
    second = await owner.suggest(docx())

    assert first["proposal_id"] != second["proposal_id"]
    assert code_of(await owner.approve(first)) == "conflict"
    assert (await owner.approve(second)).status_code == 200


@pytest.mark.parametrize("owner", [("not json", "not json", "not json", ANSWER)], indirect=True)
async def test_a_bad_answer_is_explained_and_can_be_retried(owner: Owner) -> None:
    """E-08."""
    job = (await owner.read(await owner.upload())).json()

    failed = (await owner.profile())["reading"]
    retried = await owner.call("POST", f"/api/profile/parse/{job['job_id']}/retry")

    assert (failed["state"], failed["code"]) == ("failed", "ai_bad_answer")
    assert "try again" in failed["problem"].lower()
    assert retried.status_code == 202
    profile = await owner.profile()
    assert profile["reading"]["state"] == "done" and profile["suggestion"] is not None


@pytest.mark.parametrize("owner", [(RateLimited(60), ANSWER)], indirect=True)
async def test_a_limited_model_is_replaced_by_the_backup(owner: Owner) -> None:
    await owner.suggest()

    assert owner.ai.models() == ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    assert (await owner.call("GET", "/api/settings/ai")).json()["status"] == "using_backup"


@pytest.mark.parametrize("owner", [(RateLimited(60), RateLimited(60), ANSWER)], indirect=True)
async def test_when_all_limits_are_used_the_work_waits_and_nothing_is_lost(
    owner: Owner,
) -> None:
    """E-06."""
    job = (await owner.read(await owner.upload())).json()

    waiting = (await owner.profile())["reading"]
    status = (await owner.call("GET", "/api/settings/ai")).json()["status"]
    # The provider's pause ends.
    redis = create_redis(owner.settings.redis_url.get_secret_value())
    await redis.delete("ai:block:openai/gpt-oss-120b", "ai:block:openai/gpt-oss-20b")
    await redis.aclose()
    await owner.call("POST", f"/api/profile/parse/{job['job_id']}/retry")

    assert (waiting["state"], waiting["code"]) == ("queued", "ai_limits_reached")
    assert "Nothing is lost" in waiting["problem"]
    assert status == "limits_used"
    assert (await owner.profile())["suggestion"] is not None


@pytest.mark.parametrize("owner", [(Unavailable("down"),)], indirect=True)
async def test_an_unreachable_provider_is_explained(owner: Owner) -> None:
    await owner.read(await owner.upload())

    reading = (await owner.profile())["reading"]
    assert (reading["state"], reading["code"]) == ("failed", "ai_unavailable")


@pytest.mark.parametrize("owner", [({"facts": []},)], indirect=True)
async def test_a_resume_with_no_confirmed_facts_says_so(owner: Owner) -> None:
    await owner.read(await owner.upload())

    profile = await owner.profile()
    assert profile["reading"]["code"] == "no_facts"
    assert profile["suggestion"] is None


async def running_job(owner: Owner, minutes_ago: int) -> str:
    job = (await owner.read(await owner.upload())).json()
    async with owner_session(owner.settings) as db:
        await db.execute(
            update(BackgroundJob).values(
                state="running",
                locked_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
                dedupe_key="profile_extract:test",
            )
        )
    return str(job["job_id"])


async def jobs_in(settings: Settings) -> list[BackgroundJob]:
    async with owner_session(settings) as db:
        statement = select(BackgroundJob).order_by(BackgroundJob.created_at)
        return list((await db.scalars(statement)).all())


async def test_a_second_tap_while_reading_makes_no_second_job(owner: Owner) -> None:
    """E-45."""
    job_id = await running_job(owner, minutes_ago=1)
    calls = len(owner.ai.sent)
    async with owner_session(owner.settings) as db:
        file_id = str((await db.scalars(select(File.id))).one())

    again = await owner.read(file_id)
    retried = await owner.call("POST", f"/api/profile/parse/{job_id}/retry")

    assert again.json()["job_id"] == retried.json()["job_id"] == job_id
    assert len(await jobs_in(owner.settings)) == 1
    assert len(owner.ai.sent) == calls


async def test_a_job_cut_off_by_a_restart_can_be_started_again(owner: Owner) -> None:
    job_id = await running_job(owner, minutes_ago=11)

    shown = (await owner.profile())["reading"]
    retried = await owner.call("POST", f"/api/profile/parse/{job_id}/retry")

    assert (shown["state"], shown["code"]) == ("failed", "interrupted")
    assert retried.status_code == 202
    assert (await owner.profile())["reading"]["state"] == "done"


@pytest.mark.parametrize(
    ("minutes_ago", "waiting_for", "state"),
    [(3, None, "failed"), (1, None, "queued"), (3, "ai_limits_reached", "queued")],
    ids=["lost", "just-saved", "waiting-for-the-limit"],
)
async def test_a_job_that_never_started_can_be_started_again(
    owner: Owner, minutes_ago: int, waiting_for: str | None, state: str
) -> None:
    """The API restarted between saving the job and starting it."""
    job = (await owner.read(await owner.upload())).json()
    async with owner_session(owner.settings) as db:
        await db.execute(
            update(BackgroundJob).values(
                state="queued",
                last_error=waiting_for,
                run_after=datetime.now(UTC) - timedelta(minutes=minutes_ago),
                dedupe_key="profile_extract:test",
            )
        )

    shown = (await owner.profile())["reading"]
    retried = await owner.call("POST", f"/api/profile/parse/{job['job_id']}/retry")

    assert shown["state"] == state
    assert shown["code"] == ("interrupted" if state == "failed" else waiting_for)
    assert retried.status_code == 202
    assert (await owner.profile())["reading"]["state"] == "done"


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"groq_api_key": None}, "ai_not_set_up"),
        ({"groq_zdr_confirmed_on": None}, "privacy_not_confirmed"),
    ],
)
async def test_reading_is_refused_until_ai_is_ready(
    changes: dict[str, Any], code: str, test_settings: Settings
) -> None:
    await make_user(test_settings)
    transport = FakeTransport(ANSWER)
    async with api(ready(test_settings), transport=transport, **changes) as client:
        test = Owner(client, await device(client), test_settings, transport)
        response = await test.read(await test.upload())

    assert code_of(response) == code
    assert transport.sent == []
    assert await jobs_in(test_settings) == []


async def test_an_unchecked_file_cannot_be_read(owner: Owner) -> None:
    started = (
        await owner.call(
            "POST",
            "/api/files/uploads",
            {"filename": "r.pdf", "content_type": "application/pdf", "size": 100},
        )
    ).json()

    assert code_of(await owner.read(started["file_id"])) == "file_not_ready"
    assert code_of(await owner.read(str(uuid.uuid4()))) == "not_found"


async def test_ai_use_is_counted_and_privacy_is_reported(owner: Owner) -> None:
    await owner.suggest()

    ai = (await owner.call("GET", "/api/settings/ai")).json()
    privacy = (await owner.call("GET", "/api/settings/privacy")).json()

    [day] = ai["usage"]
    assert (day["requests"], day["tokens_in"], day["tokens_out"]) == (1, 100, 50)
    assert ai["status"] == "normal"
    assert [model["role"] for model in ai["models"]] == ["main", "small", "judge"]
    assert privacy == {
        "identity_hidden": True,
        "zero_data_retention_confirmed_on": "2026-11-28",
        "status": "normal",
    }
    assert "test-key" not in str(ai)


async def test_profile_belongs_to_one_person(owner: Owner, test_settings: Settings) -> None:
    suggestion = await owner.suggest()
    job = (await owner.profile())["reading"]
    await make_user(test_settings, "other@example.com")
    other = Owner(
        owner.client, await device(owner.client, "other@example.com"), test_settings, owner.ai
    )

    answers = [
        await other.approve(suggestion),
        await other.call("POST", f"/api/profile/parse/{job['job_id']}/retry"),
        await other.read(str(job["file_id"])),
    ]

    assert [answer.status_code for answer in answers] == [404, 404, 404]
    assert (await other.profile()) == {
        "version": 0,
        "approved": None,
        "summary": None,
        "suggestion": None,
        "reading": None,
    }
