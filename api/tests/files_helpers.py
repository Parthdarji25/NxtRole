"""Builds small PDF and Word files inside tests. Test code only."""

import io
import zipfile
from pathlib import Path

from docx import Document
from pypdf import PdfReader, PdfWriter

FIXTURES = Path(__file__).resolve().parent / "fixtures"
RESUME_TEXT = (FIXTURES / "resume_synthetic_2026-11-28.txt").read_text(encoding="utf-8").strip()
LINES_PER_PAGE = 55


def pdf(*pages: str) -> bytes:
    """A PDF whose pages hold these lines of text (Latin letters). An empty string makes a
    page without text, like a scanned picture."""
    objects: list[bytes] = [b"", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for text in pages:
        commands = ["BT", "/F1 10 Tf", "40 800 Td"]
        for line in text.split("\n") if text else []:
            safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands += [f"({safe}) Tj", "0 -13 Td"]
        stream = "\n".join([*commands, "ET"]).encode("latin-1")
        page_number = len(objects) + 1
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % (page_number + 1)
        )
        objects.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
        kids.append(f"{page_number} 0 R")
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>".encode()

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n%s\nendobj\n" % (number, body))
    table = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1))
    for offset in offsets:
        out.write(b"%010d 00000 n \n" % offset)
    out.write(
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, table)
    )
    return out.getvalue()


def resume_pdf(text: str = RESUME_TEXT) -> bytes:
    lines = text.split("\n")
    pages = [
        "\n".join(lines[start : start + LINES_PER_PAGE])
        for start in range(0, len(lines), LINES_PER_PAGE)
    ]
    return pdf(*pages)


def locked_pdf() -> bytes:
    writer = PdfWriter()
    writer.append(PdfReader(io.BytesIO(resume_pdf())))
    writer.encrypt("a password", algorithm="RC4-128")
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def docx(text: str = RESUME_TEXT, header: str = "", table: list[list[str]] | None = None) -> bytes:
    document = Document()
    if header:
        document.sections[0].header.paragraphs[0].text = header
    for line in text.split("\n"):
        document.add_paragraph(line)
    if table:
        added = document.add_table(rows=len(table), cols=len(table[0]))
        for row, values in zip(added.rows, table, strict=True):
            for cell, value in zip(row.cells, values, strict=True):
                cell.text = value
    out = io.BytesIO()
    document.save(out)
    return out.getvalue()


def zip_file(files: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return out.getvalue()
