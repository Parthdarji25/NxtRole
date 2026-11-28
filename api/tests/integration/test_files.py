"""Uploading a resume through the API (D-029, FR-013, FR-023)."""

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy import select

from app.auth import tokens
from app.config import Settings
from app.core.logging import configure_logging
from app.files import text, upload_token
from app.files.models import File
from tests.files_helpers import RESUME_TEXT, docx, pdf, resume_pdf
from tests.integration.auth_helpers import Device, api, code_of, device, make_user
from tests.integration.factories import owner_session

pytestmark = pytest.mark.usefixtures("quick_hashing")


@dataclass
class Owner:
    client: httpx.AsyncClient
    device: Device
    settings: Settings
    folder: Path

    async def start(
        self, size: int, content_type: str = text.PDF, name: str = "resume.pdf"
    ) -> httpx.Response:
        return await self.client.post(
            "/api/files/uploads",
            json={"filename": name, "content_type": content_type, "size": size},
            headers=self.device.headers,
        )

    async def upload(
        self, data: bytes, content_type: str = text.PDF, name: str = "resume.pdf"
    ) -> tuple[str, httpx.Response]:
        """All three steps. Returns the file id and the answer of the check."""
        started = (await self.start(max(len(data), 1), content_type, name)).json()
        sent = await self.client.put(started["upload_url"], content=data)
        assert sent.status_code == 204, sent.text
        return started["file_id"], await self.complete(started["file_id"])

    async def complete(self, file_id: str) -> httpx.Response:
        return await self.client.post(f"/api/files/{file_id}/complete", headers=self.device.headers)

    async def get(self, file_id: str) -> httpx.Response:
        return await self.client.get(f"/api/files/{file_id}", headers=self.device.headers)

    def stored(self) -> list[Path]:
        return [path for path in self.folder.rglob("*") if path.is_file()]

    async def records(self) -> list[File]:
        async with owner_session(self.settings) as db:
            return list((await db.scalars(select(File))).all())


@pytest.fixture
async def owner(test_settings: Settings, tmp_path: Path) -> AsyncIterator[Owner]:
    await make_user(test_settings)
    folder = tmp_path / "uploads"
    async with api(test_settings, storage_dir=folder) as client:
        yield Owner(client, await device(client), test_settings, folder)


async def test_a_resume_is_uploaded_checked_and_kept_privately(owner: Owner) -> None:
    data = resume_pdf()

    file_id, response = await owner.upload(data, name="My Resume.pdf")

    body = response.json()
    assert response.status_code == 200, response.text
    assert body["file"]["status"] == "ready"
    assert body["file"]["name"] == "My Resume.pdf"
    assert body["file"]["size_bytes"] == len(data)
    assert body["duplicate"] is False and body["warnings"] == []
    assert body["detected"]["name"] == "Meera Iyer"
    assert body["detected"]["emails"] == ["meera.iyer@example.com"]
    assert body["detected"]["phones"] == ["+91 98765 43210"]
    assert body["detected"]["links"] == ["linkedin.com/in/meera-iyer-synthetic"]
    assert body["detected"]["addresses"] == ["14, Lake View Road, Pune 411045"]
    [stored] = owner.stored()
    assert stored.name == file_id
    assert stored.read_bytes() == data
    [record] = await owner.records()
    assert record.text_content is not None and "Lantern Works" in record.text_content


async def test_a_word_resume_works_too(owner: Owner) -> None:
    _, response = await owner.upload(docx(), text.DOCX, "resume.docx")

    assert response.json()["file"]["status"] == "ready"


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (b"words in a file renamed to .pdf", "unsupported_type"),
        (pdf(""), "no_text"),
        (b"", "empty_file"),
    ],
    ids=["renamed", "scanned", "empty"],
)
async def test_a_refused_file_is_deleted_and_marked(owner: Owner, data: bytes, code: str) -> None:
    file_id, response = await owner.upload(data)

    assert code_of(response) == code
    assert owner.stored() == []
    assert (await owner.get(file_id)).json()["status"] == "rejected"
    assert (await owner.complete(file_id)).status_code == 409


async def test_upload_size_limits(owner: Owner) -> None:
    """E-58: refused before sending, and again when the real size is larger than said."""
    announced = await owner.start(text.MAX_BYTES + 1)
    started = (await owner.start(1_000)).json()
    larger = await owner.client.put(started["upload_url"], content=b"%PDF-" + b"x" * text.MAX_BYTES)
    huge = await owner.client.put(started["upload_url"], content=b"x" * (text.MAX_BYTES + 5_000))
    # Between the ordinary request limit and the file limit: accepted by the upload address.
    big = resume_pdf() + b"\n%" + b"x" * (4 * 1024 * 1024)
    _, accepted = await owner.upload(big)

    assert code_of(announced) == "file_too_large"
    assert "5 MB" in announced.json()["detail"]["message"]
    assert code_of(larger) == "file_too_large"
    assert code_of(huge) == "too_large"
    assert accepted.status_code == 200, accepted.text


@pytest.mark.parametrize("content_type", ["text/plain", "image/png", "application/msword"])
async def test_other_kinds_are_refused_before_sending(owner: Owner, content_type: str) -> None:
    response = await owner.start(10, content_type)

    assert code_of(response) == "unsupported_type"
    assert await owner.records() == []


async def test_an_upload_address_works_once_and_only_for_its_file(
    owner: Owner, test_settings: Settings
) -> None:
    first = (await owner.start(100)).json()
    second = (await owner.start(100)).json()
    token = first["upload_url"].split("token=")[1]
    secret = test_settings.require_jwt_secret()
    [user_file] = [record for record in await owner.records() if str(record.id) == first["file_id"]]
    access = tokens.create_access_token(tokens.Identity(user_file.user_id, uuid.uuid4()), secret)

    async def put(file_id: str, pass_token: str) -> httpx.Response:
        return await owner.client.put(
            f"/api/files/{file_id}/content?token={pass_token}", content=resume_pdf()
        )

    good = await put(first["file_id"], token)
    again = await put(first["file_id"], token)
    other_file = await put(second["file_id"], token)
    with_access_token = await put(second["file_id"], access)
    forged = await put(second["file_id"], token[:-3] + "AAA")
    expired, _ = upload_token.create(user_file.user_id, user_file.id, secret[::-1])
    wrong_secret = await put(first["file_id"], expired)
    as_sign_in = await owner.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})

    assert good.status_code == 204
    assert code_of(again) == "already_uploaded"
    assert [
        code_of(answer) for answer in (other_file, with_access_token, forged, wrong_secret)
    ] == ["upload_expired"] * 4
    assert as_sign_in.status_code == 401
    assert len(owner.stored()) == 1


async def test_the_same_file_twice_is_noticed(owner: Owner) -> None:
    first_id, _ = await owner.upload(resume_pdf())
    _, second = await owner.upload(resume_pdf(), name="copy.pdf")

    assert second.json()["duplicate"] is True
    assert second.json()["file"]["id"] == first_id
    assert len(owner.stored()) == 1
    assert len(await owner.records()) == 1


async def test_checking_again_gives_the_same_answer(owner: Owner) -> None:
    file_id, first = await owner.upload(resume_pdf())

    again = await owner.complete(file_id)

    assert again.json()["detected"] == first.json()["detected"]


async def test_completing_before_uploading_is_explained(owner: Owner) -> None:
    started = (await owner.start(100)).json()

    response = await owner.complete(started["file_id"])

    assert code_of(response) == "file_not_ready"


async def test_a_typed_file_name_never_becomes_a_path(owner: Owner) -> None:
    file_id, response = await owner.upload(resume_pdf(), name="..\\..\\windows\\evil\x01.pdf")

    assert response.json()["file"]["name"] == "evil.pdf"
    [stored] = owner.stored()
    assert stored.name == file_id
    assert stored.resolve().is_relative_to(owner.folder.resolve())


async def test_deleting_removes_the_file_and_its_text(owner: Owner) -> None:
    file_id, _ = await owner.upload(resume_pdf())

    response = await owner.client.delete(f"/api/files/{file_id}", headers=owner.device.headers)

    assert response.status_code == 204
    assert owner.stored() == []
    assert (await owner.get(file_id)).status_code == 404
    [record] = await owner.records()
    assert (record.status, record.text_content, record.sha256) == ("deleted", None, None)


async def test_another_person_cannot_see_or_touch_the_file(
    owner: Owner, test_settings: Settings
) -> None:
    file_id, _ = await owner.upload(resume_pdf())
    await make_user(test_settings, "other@example.com")
    other = await device(owner.client, "other@example.com")
    call: Any = owner.client.request

    answers = [
        await call("GET", f"/api/files/{file_id}", headers=other.headers),
        await call("POST", f"/api/files/{file_id}/complete", headers=other.headers),
        await call("DELETE", f"/api/files/{file_id}", headers=other.headers),
    ]

    assert [(answer.status_code, code_of(answer)) for answer in answers] == [(404, "not_found")] * 3
    assert len(owner.stored()) == 1


async def test_no_resume_text_reaches_the_logs(
    owner: Owner, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_logging("DEBUG")
    await owner.upload(resume_pdf())
    await owner.upload(b"%PDF-1.4 broken " + RESUME_TEXT.encode())

    output = capsys.readouterr().out
    configure_logging("INFO")
    for secret in ("Meera", "meera.iyer", "98765", "Lantern", "token="):
        assert secret not in output
