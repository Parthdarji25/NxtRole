"""Reads the words out of a resume, and says plainly why it cannot.

The file is untrusted: its real kind is checked from its contents, and size, page and time
limits stop a hostile file from using up the server (T-FILE-1, T-FILE-3).
"""

import asyncio
import io
import logging
import re
import unicodedata
import zipfile
from dataclasses import dataclass, field

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

from app.core.errors import AppError

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
KINDS = (PDF, DOCX)

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 20
MAX_CHARACTERS = 30_000
# Fewer characters than this means there is no real text, as in a scanned picture.
MIN_CHARACTERS = 200
# Limits for what is packed inside a Word file.
MAX_PARTS = 2_000
MAX_UNPACKED_BYTES = 50 * 1024 * 1024
READ_TIMEOUT_SECONDS = 30.0

# The first bytes of an old-style or password-protected Office file.
OFFICE_CONTAINER = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

# The PDF reader's notes about damaged files can quote their contents.
logging.getLogger("pypdf").setLevel(logging.CRITICAL)


@dataclass(frozen=True)
class Extracted:
    text: str
    truncated: bool = False
    # Things the owner should know: "truncated", "not_english".
    warnings: list[str] = field(default_factory=list)


def refused(code: str, message: str, status_code: int = 422) -> AppError:
    return AppError(code, message, status_code=status_code)


def unreadable() -> AppError:
    return refused("unreadable", "That file could not be read. Save it again and retry.")


def wrong_kind() -> AppError:
    return refused("unsupported_type", "Upload a PDF or a Word (.docx) file.", 415)


def check_kind(data: bytes, content_type: str) -> None:
    """The contents must be what the browser said they are, whatever the file is named."""
    if not data:
        raise refused("empty_file", "That file is empty.")
    if len(data) > MAX_BYTES:
        raise refused("file_too_large", "That file is over 5 MB.", 413)
    if data.startswith(OFFICE_CONTAINER):
        raise refused(
            "protected_file",
            "That Word file is locked with a password, or is the old .doc format. Save it "
            "as .docx without a password.",
        )
    if content_type == PDF and data.startswith(b"%PDF-"):
        return
    if content_type == DOCX and data.startswith(b"PK"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                parts = archive.infolist()
        except zipfile.BadZipFile:
            raise unreadable() from None
        if "word/document.xml" not in {part.filename for part in parts}:
            raise wrong_kind()
        if len(parts) > MAX_PARTS or sum(part.file_size for part in parts) > MAX_UNPACKED_BYTES:
            raise unreadable()
        return
    raise wrong_kind()


def _pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted and not reader.decrypt(""):
        raise refused(
            "protected_pdf",
            "That PDF is locked with a password. Save a copy without one and upload that.",
        )
    if len(reader.pages) > MAX_PAGES:
        raise refused("too_many_pages", f"That PDF has more than {MAX_PAGES} pages.")
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _docx_text(data: bytes) -> str:
    document = Document(io.BytesIO(data))
    lines: list[str] = []

    def add_paragraphs(paragraphs: list[Paragraph]) -> None:
        lines.extend(paragraph.text for paragraph in paragraphs)

    # Names and contact details often sit in the header.
    for section in document.sections:
        add_paragraphs(section.header.paragraphs)
    # Text and tables in the order they appear.
    for block in document.iter_inner_content():
        if isinstance(block, Table):
            for row in block.rows:
                cells = dict.fromkeys(cell.text.strip() for cell in row.cells)
                lines.append(" | ".join(cell for cell in cells if cell))
        else:
            lines.append(block.text)
    for section in document.sections:
        add_paragraphs(section.footer.paragraphs)
    return "\n".join(lines)


def clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(
        character
        for character in text
        if character in "\n\t" or unicodedata.category(character)[0] != "C"
    )
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def looks_english(text: str) -> bool:
    letters = [character for character in text if character.isalpha()]
    latin = sum(character.isascii() for character in letters)
    return not letters or latin / len(letters) >= 0.6


def _read(data: bytes, content_type: str) -> Extracted:
    check_kind(data, content_type)
    try:
        raw = _pdf_text(data) if content_type == PDF else _docx_text(data)
    except AppError:
        raise
    except Exception:
        # The parsers raise many kinds of error for damaged files.
        raise unreadable() from None
    text = clean(raw)
    if len(text) < MIN_CHARACTERS:
        raise refused(
            "no_text",
            "No text was found. A scanned or photographed resume cannot be read: upload the "
            "file your editor saved.",
        )
    warnings = []
    truncated = len(text) > MAX_CHARACTERS
    if truncated:
        text = text[:MAX_CHARACTERS]
        warnings.append("truncated")
    if not looks_english(text):
        warnings.append("not_english")
    return Extracted(text, truncated, warnings)


async def read_resume(data: bytes, content_type: str) -> Extracted:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_read, data, content_type), timeout=READ_TIMEOUT_SECONDS
        )
    except TimeoutError:
        raise unreadable() from None
