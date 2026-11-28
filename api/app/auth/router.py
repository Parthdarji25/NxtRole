"""The sign-in addresses under /api/auth."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.auth.passwords import MAX_LENGTH
from app.auth.tokens import ACCESS_LIFETIME, REFRESH_LIFETIME
from app.core.deps import Auth, CurrentUser, CurrentVisitor
from app.core.errors import AppError
from app.users import service as accounts
from app.users.schemas import UserOut

COOKIE_NAME = "__Secure-nr_refresh"
COOKIE_PATH = "/api/auth"
CSRF_HEADER = "X-NxtRole-CSRF"

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Request(BaseModel):
    # Unknown fields are refused.
    model_config = ConfigDict(extra="forbid")


class LoginRequest(Request):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=1, max_length=MAX_LENGTH)


class RecoverRequest(Request):
    email: EmailStr = Field(max_length=254)
    recovery_code: str = Field(min_length=1, max_length=80)
    # Longer than allowed passes here so that it is explained as a weak password.
    new_password: str = Field(min_length=1, max_length=1000)


class AccessToken(BaseModel):
    access_token: str
    expires_in: int = int(ACCESS_LIFETIME.total_seconds())


class SignedIn(AccessToken):
    user: UserOut


class NewRecoveryCode(BaseModel):
    recovery_code: str


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=int(REFRESH_LIFETIME.total_seconds()),
        path=COOKIE_PATH,
        # Scripts cannot read it, it travels only over HTTPS (or to this computer),
        # and other websites cannot make the browser send it.
        httponly=True,
        secure=True,
        samesite="strict",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        COOKIE_NAME, path=COOKIE_PATH, httponly=True, secure=True, samesite="strict"
    )


def cleared_cookie_header() -> dict[str, str]:
    """For error answers, which are built after the route has stopped."""
    response = Response()
    clear_refresh_cookie(response)
    return {"Set-Cookie": response.headers["set-cookie"]}


def require_csrf_header(
    marker: Annotated[str | None, Header(alias=CSRF_HEADER)] = None,
) -> None:
    """Another website can make a browser send our cookie, but cannot add this header."""
    if not marker:
        raise AppError("csrf_missing", "That request did not come from NxtRole.", status_code=403)


RefreshCookie = Annotated[str | None, Cookie(alias=COOKIE_NAME)]
CsrfChecked = Depends(require_csrf_header)


@router.post("/login", response_model=SignedIn)
async def login(
    body: LoginRequest, response: Response, auth: Auth, visitor: CurrentVisitor
) -> SignedIn:
    granted, user = await auth.login(body.email, body.password, visitor)
    assert granted.refresh_token is not None  # noqa: S101  (a new sign-in always has one)
    set_refresh_cookie(response, granted.refresh_token)
    return SignedIn(access_token=granted.access_token, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=AccessToken, dependencies=[CsrfChecked])
async def refresh(
    response: Response, auth: Auth, visitor: CurrentVisitor, token: RefreshCookie = None
) -> AccessToken:
    try:
        granted = await auth.refresh(token, visitor)
    except AppError as error:
        error.headers.update(cleared_cookie_header())
        raise
    if granted.refresh_token is not None:
        set_refresh_cookie(response, granted.refresh_token)
    return AccessToken(access_token=granted.access_token)


@router.post("/logout", status_code=204, dependencies=[CsrfChecked])
async def logout(response: Response, auth: Auth, token: RefreshCookie = None) -> None:
    try:
        await auth.logout(token)
    except AppError as error:
        error.headers.update(cleared_cookie_header())
        raise
    clear_refresh_cookie(response)


@router.post("/logout-all", status_code=204)
async def logout_all(response: Response, current: CurrentUser) -> None:
    """Signs out every device, this one included."""
    await accounts.sign_out_everywhere(current)
    clear_refresh_cookie(response)


@router.post("/recover", response_model=NewRecoveryCode)
async def recover(body: RecoverRequest, auth: Auth, visitor: CurrentVisitor) -> NewRecoveryCode:
    code = await auth.recover(body.email, body.recovery_code, body.new_password, visitor)
    return NewRecoveryCode(recovery_code=code)
