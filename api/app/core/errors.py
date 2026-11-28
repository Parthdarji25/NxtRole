"""One error shape for the whole API: {"detail": {"code": "...", "message": "..."}}."""

from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

HTTP_ERRORS = {
    404: ("not_found", "That address does not exist."),
    405: ("method_not_allowed", "That action is not allowed on this address."),
}


class AppError(Exception):
    """An expected problem with a message a beginner understands.

    `extra` adds fields beside the code and message; `headers` adds response headers.
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        *,
        headers: Mapping[str, str] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.headers = dict(headers or {})
        self.extra = dict(extra or {})


def error_response(status_code: int, code: str, message: str, **extra: Any) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": {"code": code, "message": message, **extra}},
    )


async def handle_app_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):
        raise exc
    response = error_response(exc.status_code, exc.code, exc.message, **exc.extra)
    response.headers.update(exc.headers)
    return response


async def handle_validation_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    # Only the field name and the reason are returned, never the submitted value.
    fields = [
        {
            "field": ".".join(str(part) for part in error["loc"][1:]) or str(error["loc"][0]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return error_response(
        422, "validation_error", "Some of the information sent is not valid.", fields=fields
    )


async def handle_http_error(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, HTTPException):
        raise exc
    code, message = HTTP_ERRORS.get(
        exc.status_code, ("request_error", "The request could not be completed.")
    )
    response = error_response(exc.status_code, code, message)
    if exc.headers:
        response.headers.update(exc.headers)
    return response


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(HTTPException, handle_http_error)
    # Unexpected errors are handled in core/middleware.py so they keep their request id.
