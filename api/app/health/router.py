"""Public health routes (D-043). They reveal no internal details."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.errors import error_response
from app.health.service import CheckResult, check_services

router = APIRouter(tags=["health"])


class Alive(BaseModel):
    status: str = "ok"


class Ready(BaseModel):
    database: CheckResult
    redis: CheckResult


@router.get("/health", response_model=Alive)
@router.get("/api/health", response_model=Alive)
async def alive() -> Alive:
    """The program is running. Does not touch the database or Redis."""
    return Alive()


@router.get(
    "/api/health/ready", response_model=Ready, responses={503: {"description": "A service is down"}}
)
async def ready(request: Request) -> Ready | JSONResponse:
    """The database and Redis answer. Returns 503 and says which part failed otherwise."""
    checks = await check_services(request.app.state.engine, request.app.state.redis)
    failed = [name for name, result in checks.items() if result != "ok"]
    if failed:
        return error_response(
            503,
            "not_ready",
            f"NxtRole cannot reach: {', '.join(failed)}. "
            "Check that the local containers are running.",
            checks=checks,
        )
    return Ready(**checks)
