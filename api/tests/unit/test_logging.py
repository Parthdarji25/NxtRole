import json
import logging

import pytest
import structlog

from app.core.logging import REDACTED, configure_logging, redact_text


def test_redact_text_hides_url_password_and_email() -> None:
    text = "failed for postgresql://owner:hidden-value@db:5432/x and person@example.com"

    cleaned = redact_text(text)

    assert "hidden-value" not in cleaned
    assert "person@example.com" not in cleaned
    assert "db:5432" in cleaned


def test_logs_are_json_and_hide_sensitive_fields(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO")

    structlog.get_logger("test").info(
        "example",
        password="hidden-value",
        nested={"refresh_token": "hidden-token", "count": 2},
        note="mail person@example.com",
    )

    output = capsys.readouterr().out.strip()
    record = json.loads(output)
    assert record["event"] == "example"
    assert record["level"] == "info"
    assert record["password"] == REDACTED
    assert record["nested"] == {"refresh_token": REDACTED, "count": 2}
    assert "person@example.com" not in output
    assert "hidden-token" not in output


def test_library_logs_are_redacted_too(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO")

    logging.getLogger("some.library").warning("cannot reach redis://:hidden-value@cache:6379/0")

    output = capsys.readouterr().out
    assert "hidden-value" not in output
    assert json.loads(output.strip())["level"] == "warning"
