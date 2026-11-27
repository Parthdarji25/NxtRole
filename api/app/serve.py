"""Starts the API for local development:  uv run python -m app.serve --reload"""

import argparse
import sys

import uvicorn

from app.config import ConfigError, load_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the NxtRole API locally.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="restart when code changes")
    args = parser.parse_args(argv)

    try:
        load_settings()
    except ConfigError as error:
        print(error, file=sys.stderr)
        return 1

    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host="127.0.0.1",
        port=args.port,
        reload=args.reload,
        # Needed on Windows: see app/core/loop.py.
        loop="app.core.loop:new_event_loop",
        # Logging is configured by the app; uvicorn's access log would record query strings.
        log_config=None,
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
