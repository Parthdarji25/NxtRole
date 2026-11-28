"""History, undo, and proposals that wait for approval (FR-099, FR-138)."""

import asyncio
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.db.session import create_engine, create_session_factory, set_current_user
from app.history import service
from tests.integration.auth_helpers import Account, Device, api, code_of, device, make_user

pytestmark = pytest.mark.usefixtures("quick_hashing")


@dataclass
class Owner:
    client: httpx.AsyncClient
    account: Account
    device: Device

    async def rename(self, name: str | None, version: int) -> httpx.Response:
        return await self.client.patch(
            "/api/account/profile",
            json={"display_name": name, "version": version},
            headers=self.device.headers,
        )

    async def me(self) -> dict[str, object]:
        response = await self.client.get("/api/me", headers=self.device.headers)
        return dict(response.json())

    async def post(self, path: str, body: object = None) -> httpx.Response:
        return await self.client.post(path, json=body, headers=self.device.headers)

    async def get(self, path: str) -> httpx.Response:
        return await self.client.get(path, headers=self.device.headers)


@pytest.fixture
async def owner(test_settings: Settings) -> AsyncIterator[Owner]:
    account = await make_user(test_settings)
    async with api(test_settings) as client:
        yield Owner(client, account, await device(client))


@pytest.fixture
async def sessions(test_settings: Settings) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_engine(test_settings.database_url.get_secret_value())
    yield create_session_factory(engine)
    await engine.dispose()


async def suggest(sessions: async_sessionmaker[AsyncSession], user_id: uuid.UUID, name: str) -> str:
    """What an agent will do in later phases: propose, and change nothing."""
    async with sessions.begin() as db:
        await set_current_user(db, user_id)
        proposal = await service.propose(
            db, user_id, "rename_profile", user_id, {"display_name": name}, created_by="agent:test"
        )
        return str(proposal.id)


async def test_a_change_is_saved_with_history(owner: Owner) -> None:
    response = await owner.rename("  Asha  ", 1)

    assert response.status_code == 200
    assert response.json()["user"]["display_name"] == "Asha"
    assert response.json()["user"]["version"] == 2
    [event] = (await owner.get("/api/history")).json()["items"]
    assert event["id"] == response.json()["event_id"]
    assert (event["actor"], event["action"]) == ("you", "profile.name_changed")
    assert event["before"] == {"display_name": None}
    assert event["after"] == {"display_name": "Asha"}


async def test_saving_the_same_name_writes_no_history(owner: Owner) -> None:
    await owner.rename("Asha", 1)

    again = await owner.rename("Asha", 2)

    assert again.json()["event_id"] is None
    assert again.json()["user"]["version"] == 2


async def test_a_change_based_on_an_old_version_is_a_conflict(owner: Owner) -> None:
    await owner.rename("Asha", 1)

    stale = await owner.rename("Other", 1)

    assert stale.status_code == 409
    assert code_of(stale) == "conflict"
    assert stale.json()["detail"]["current_version"] == 2
    assert (await owner.me())["display_name"] == "Asha"


@pytest.mark.parametrize("name", ["", "   ", "x" * 81, "two\nlines"])
async def test_unusable_names_are_refused(owner: Owner, name: str) -> None:
    response = await owner.rename(name, 1)

    assert response.status_code == 422


async def test_unicode_names_work_and_can_be_removed(owner: Owner) -> None:
    await owner.rename("आशा Ōtani", 1)
    assert (await owner.me())["display_name"] == "आशा Ōtani"

    await owner.rename(None, 2)

    assert (await owner.me())["display_name"] is None


async def test_undo_puts_it_back_and_is_itself_history(owner: Owner) -> None:
    event_id = (await owner.rename("Asha", 1)).json()["event_id"]

    undone = await owner.post(f"/api/events/{event_id}/undo")
    twice = await owner.post(f"/api/events/{event_id}/undo")

    assert undone.status_code == 200
    assert (await owner.me())["display_name"] is None
    assert code_of(twice) == "already_undone"
    newest, oldest = (await owner.get("/api/history")).json()["items"]
    assert newest["undo_of"] == event_id
    assert oldest["undone_by"] == newest["id"]


async def test_undo_blocked_explains_dependency(owner: Owner) -> None:
    """E-28: undoing an older change would overwrite a newer one."""
    first = (await owner.rename("Asha", 1)).json()["event_id"]
    second = (await owner.rename("Asha Rao", 2)).json()["event_id"]

    blocked = await owner.post(f"/api/events/{first}/undo")

    assert blocked.status_code == 409
    assert code_of(blocked) == "undo_blocked"
    assert blocked.json()["detail"]["blocked_by"] == ["display_name"]
    assert (await owner.me())["display_name"] == "Asha Rao"
    # In the right order both can be undone.
    assert (await owner.post(f"/api/events/{second}/undo")).status_code == 200
    assert (await owner.post(f"/api/events/{first}/undo")).status_code == 200
    assert (await owner.me())["display_name"] is None


async def test_two_undo_requests_at_once_undo_once(owner: Owner) -> None:
    event_id = (await owner.rename("Asha", 1)).json()["event_id"]

    answers = await asyncio.gather(*(owner.post(f"/api/events/{event_id}/undo") for _ in range(4)))

    assert sorted(answer.status_code for answer in answers) == [200, 409, 409, 409]
    assert len((await owner.get("/api/history")).json()["items"]) == 2


async def test_history_comes_in_pages(owner: Owner) -> None:
    for version, name in enumerate(["a", "b", "c"], start=1):
        await owner.rename(name, version)

    first = (await owner.get("/api/history?limit=2")).json()
    second = (await owner.get(f"/api/history?limit=2&cursor={first['next_cursor']}")).json()

    names = [item["after"]["display_name"] for item in first["items"] + second["items"]]
    assert names == ["c", "b", "a"]
    assert second["next_cursor"] is None


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "cursor=damaged"])
async def test_bad_page_requests_are_refused(owner: Owner, query: str) -> None:
    response = await owner.get(f"/api/history?{query}")

    assert response.status_code == 422


async def test_history_can_be_filtered_by_record(owner: Owner) -> None:
    await owner.rename("Asha", 1)
    mine = (
        await owner.get(f"/api/history?target_type=profile&target_id={owner.account.user.id}")
    ).json()
    other = (await owner.get("/api/history?target_type=application")).json()

    assert len(mine["items"]) == 1
    assert other["items"] == []


async def test_a_proposal_changes_nothing_until_approved(
    owner: Owner, sessions: async_sessionmaker[AsyncSession]
) -> None:
    proposal_id = await suggest(sessions, owner.account.user.id, "Suggested")

    waiting = (await owner.get("/api/proposals")).json()["items"]
    unchanged = (await owner.me())["display_name"]
    approved = await owner.post(f"/api/proposals/{proposal_id}/approve")

    assert [item["id"] for item in waiting] == [proposal_id]
    assert unchanged is None
    assert approved.status_code == 200
    assert approved.json()["proposal"]["status"] == "applied"
    assert (await owner.me())["display_name"] == "Suggested"
    [event] = (await owner.get("/api/history")).json()["items"]
    assert (event["actor"], event["proposal_id"]) == ("agent:test", proposal_id)
    assert (await owner.get("/api/proposals")).json()["items"] == []
    # An approved change can be undone like any other.
    await owner.post(f"/api/events/{approved.json()['event_id']}/undo")
    assert (await owner.me())["display_name"] is None


async def test_approving_twice_changes_once(
    owner: Owner, sessions: async_sessionmaker[AsyncSession]
) -> None:
    proposal_id = await suggest(sessions, owner.account.user.id, "Suggested")

    answers = await asyncio.gather(
        *(owner.post(f"/api/proposals/{proposal_id}/approve") for _ in range(4))
    )

    assert sorted(answer.status_code for answer in answers) == [200, 409, 409, 409]
    assert len((await owner.get("/api/history")).json()["items"]) == 1


async def test_a_stale_proposal_is_refused(
    owner: Owner, sessions: async_sessionmaker[AsyncSession]
) -> None:
    proposal_id = await suggest(sessions, owner.account.user.id, "Suggested")
    await owner.rename("Chosen by me", 1)

    response = await owner.post(f"/api/proposals/{proposal_id}/approve")

    assert response.status_code == 409
    assert code_of(response) == "stale_proposal"
    assert (await owner.me())["display_name"] == "Chosen by me"
    assert len((await owner.get("/api/history")).json()["items"]) == 1
    assert (await owner.post(f"/api/proposals/{proposal_id}/reject")).status_code == 200


async def test_rejecting_changes_nothing_and_is_final(
    owner: Owner, sessions: async_sessionmaker[AsyncSession]
) -> None:
    proposal_id = await suggest(sessions, owner.account.user.id, "Suggested")

    rejected = await owner.post(f"/api/proposals/{proposal_id}/reject")
    later = await owner.post(f"/api/proposals/{proposal_id}/approve")

    assert rejected.json()["status"] == "rejected"
    assert code_of(later) == "conflict"
    assert (await owner.me())["display_name"] is None
    assert (await owner.get("/api/history")).json()["items"] == []
    listed = (await owner.get("/api/proposals?status=rejected")).json()["items"]
    assert [item["id"] for item in listed] == [proposal_id]


async def test_the_owner_can_edit_a_proposal_before_approving(
    owner: Owner, sessions: async_sessionmaker[AsyncSession]
) -> None:
    proposal_id = await suggest(sessions, owner.account.user.id, "Suggested")

    bad = await owner.post(
        f"/api/proposals/{proposal_id}/approve", {"edited_payload": {"is_active": False}}
    )
    good = await owner.post(
        f"/api/proposals/{proposal_id}/approve",
        {"edited_payload": {"display_name": "Edited"}},
    )

    assert bad.status_code == 422
    assert good.json()["proposal"]["payload"] == {"display_name": "Edited"}
    assert (await owner.me())["display_name"] == "Edited"


async def test_cross_user_ids_are_not_found(
    test_settings: Settings,
    owner: Owner,
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    """E-70: another person's ids behave as if they did not exist."""
    event_id = (await owner.rename("Asha", 1)).json()["event_id"]
    proposal_id = await suggest(sessions, owner.account.user.id, "Suggested")
    family = (await owner.get("/api/account/sessions")).json()["items"][0]["family_id"]
    other_account = await make_user(test_settings, "other@example.com")
    other = Owner(owner.client, other_account, await device(owner.client, "other@example.com"))

    answers = [
        await other.post(f"/api/events/{event_id}/undo"),
        await other.post(f"/api/proposals/{proposal_id}/approve"),
        await other.post(f"/api/proposals/{proposal_id}/reject"),
        await other.client.delete(f"/api/account/sessions/{family}", headers=other.device.headers),
    ]

    assert [(answer.status_code, code_of(answer)) for answer in answers] == [(404, "not_found")] * 4
    assert (await other.get("/api/history")).json()["items"] == []
    assert (await other.get("/api/proposals")).json()["items"] == []
    assert (await owner.me())["display_name"] == "Asha"
