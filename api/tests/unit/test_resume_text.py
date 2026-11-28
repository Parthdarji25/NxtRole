from pathlib import Path

import pytest

from app.core.errors import AppError
from app.files import text
from app.files.storage import LocalStorage
from tests.files_helpers import (
    RESUME_TEXT,
    docx,
    locked_pdf,
    pdf,
    resume_pdf,
    zip_file,
)


async def refusal(data: bytes, content_type: str = text.PDF) -> str:
    with pytest.raises(AppError) as error:
        await text.read_resume(data, content_type)
    return error.value.code


@pytest.mark.parametrize(
    ("data", "content_type"), [(resume_pdf(), text.PDF), (docx(), text.DOCX)], ids=["pdf", "docx"]
)
async def test_a_resume_is_read(data: bytes, content_type: str) -> None:
    result = await text.read_resume(data, content_type)

    assert "Meera Iyer" in result.text
    assert "Rebuilt the reporting dashboard in Next.js" in result.text
    assert "AWS Certified Cloud Practitioner" in result.text
    assert not result.truncated and result.warnings == []


async def test_word_headers_tables_and_order_are_kept() -> None:
    data = docx(
        text=RESUME_TEXT,
        header="meera.iyer@example.com",
        table=[["Skill", "Years"], ["React", "4"]],
    )

    result = await text.read_resume(data, text.DOCX)

    assert result.text.startswith("meera.iyer@example.com")
    assert "React | 4" in result.text
    assert result.text.index("Experience") < result.text.index("Education")


@pytest.mark.parametrize(
    ("data", "content_type", "code"),
    [
        (b"", text.PDF, "empty_file"),
        (b"just some words, renamed to resume.pdf", text.PDF, "unsupported_type"),
        (b"%PDF-1.4 broken beyond reading", text.PDF, "unreadable"),
        (pdf(""), text.PDF, "no_text"),
        (pdf("Too short to be a resume"), text.PDF, "no_text"),
        (locked_pdf(), text.PDF, "protected_pdf"),
        (pdf(*["page"] * 21), text.PDF, "too_many_pages"),
        (b"%PDF-" + b"x" * (5 * 1024 * 1024), text.PDF, "file_too_large"),
        (resume_pdf(), text.DOCX, "unsupported_type"),
        (docx(), text.PDF, "unsupported_type"),
        (text.OFFICE_CONTAINER + b"locked", text.DOCX, "protected_file"),
        (zip_file({"hello.txt": b"hi"}), text.DOCX, "unsupported_type"),
        (b"PK\x03\x04 broken", text.DOCX, "unreadable"),
        (zip_file({"word/document.xml": b"<not-a-document/>"}), text.DOCX, "unreadable"),
    ],
    ids=[
        "empty",
        "renamed-text",
        "damaged-pdf",
        "scanned",
        "nearly-empty",
        "password",
        "too-many-pages",
        "too-big",
        "pdf-sent-as-word",
        "word-sent-as-pdf",
        "locked-word",
        "other-zip",
        "damaged-zip",
        "damaged-word",
    ],
)
async def test_upload_scanned_and_protected_pdf(data: bytes, content_type: str, code: str) -> None:
    """E-57, E-58 and the Phase 5 file cases."""
    assert await refusal(data, content_type) == code


async def test_a_word_file_that_unpacks_to_something_huge_is_refused() -> None:
    bomb = zip_file({"word/document.xml": b"0" * (60 * 1024 * 1024)})

    assert len(bomb) < text.MAX_BYTES
    assert await refusal(bomb, text.DOCX) == "unreadable"


async def test_a_very_long_resume_is_cut_with_a_warning() -> None:
    result = await text.read_resume(docx("Built things with React. " * 2_000), text.DOCX)

    assert len(result.text) == text.MAX_CHARACTERS
    assert result.truncated and result.warnings == ["truncated"]


async def test_a_resume_in_another_script_is_flagged_not_refused() -> None:
    hindi = "मैं एक सॉफ्टवेयर डेवलपर हूँ और React पर काम करता हूँ। " * 10

    result = await text.read_resume(docx(hindi), text.DOCX)

    assert result.warnings == ["not_english"]
    assert "सॉफ्टवेयर" in result.text


def test_control_characters_and_blank_runs_are_removed() -> None:
    assert text.clean("a\x00b\x07 \n\n\n\n\nc​") == "ab\n\nc"


async def test_storage_keeps_files_inside_its_folder_and_writes_once(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path / "uploads")

    assert await storage.create("user/file", b"first")
    assert not await storage.create("user/file", b"second")
    assert await storage.read("user/file") == b"first"
    await storage.delete("user/file")
    await storage.delete("user/file")
    assert await storage.read("user/file") is None
    for path in ("../outside", "user/../../outside", "/etc/passwd", ""):
        with pytest.raises(ValueError, match="storage folder"):
            await storage.create(path, b"x")
    assert not (tmp_path / "outside").exists()
