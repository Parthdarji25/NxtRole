"""JSON logs with a request id and no personal data or secrets.

Redaction is a safety net. The first rule is still: do not pass personal data to the logger.
"""

import logging
import re
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog

REDACTED = "[redacted]"

# Field names whose values are never written to a log.
SENSITIVE_KEY_PARTS = (
    "password",
    "secret",
    "token",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "database_url",
    "redis_url",
    "email",
    "phone",
    "resume",
)

# Patterns removed from any text value.
URL_CREDENTIALS = re.compile(r"(?<=://)[^/\s:@]*:[^/\s@]+(?=@)")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def redact_text(text: str) -> str:
    text = URL_CREDENTIALS.sub(REDACTED, text)
    return EMAIL.sub(REDACTED, text)


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {key: _redact_item(str(key), item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


def _redact_item(key: str, value: Any) -> Any:
    if any(part in key.lower() for part in SENSITIVE_KEY_PARTS):
        return REDACTED
    return _redact(value)


def redact_processor(
    _logger: Any, _method: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    for key in list(event_dict):
        event_dict[key] = _redact_item(key, event_dict[key])
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    """Send both our logs and library logs through the same JSON, redacting pipeline."""
    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            redact_processor,
            structlog.processors.JSONRenderer(),
        ],
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    # Uvicorn's own handlers are removed so its messages use the format above.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        library_logger = logging.getLogger(name)
        library_logger.handlers = []
        library_logger.propagate = True
