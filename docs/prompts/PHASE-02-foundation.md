# Phase 2 — Project foundation

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-02-foundation.md and follow it.`
> Follow `CLAUDE.md`. No commits.

## 1. Phase name and objective
**Project foundation.** Create a clean, working skeleton for the web app and the API, a local database
and Redis in Docker, one configuration module, code-quality tools, a CI workflow file and the first
passing tests, so every later phase starts from solid ground.

## 2. Context and dependencies
- Requires Phases 0 and 1 approved. Follow `docs/ARCHITECTURE.md` (folder structure) and
  `docs/TECH_STACK.md` (versions).
- If `web/` or `api/` already exist, review them first and adapt instead of starting over (tell me
  what you keep, change or remove, and why).
- My machine: Windows. Give every command for PowerShell. I have Node.js, pnpm and uv; check for
  Docker Desktop (with WSL 2). **It is not installed on my laptop (Phase 1 check, D-037): guide me through
  installing it first, step by step, including the restart.** Use exact pins in lockfiles (`uv.lock`,
  `package-lock.json`), install only from them in CI, and adopt releases only when 7 days old unless they
  fix a security issue (D-036). Check that TypeScript 7 works with Next 16.4 and the test and lint tools;
  if not, pin the newest 5.x.

## 3. Detailed implementation tasks
1. **Repository layout:** `web/`, `api/`, `docs/`, `.github/`, root `docker-compose.yml`,
   `.gitignore` (env files, `node_modules`, `.venv`, `.next`, uploads, coverage),
   `.gitattributes` (`* text=auto eol=lf`), `.editorconfig`.
2. **Docker Compose (local only):** `pgvector/pgvector:pg17` and `redis:7-alpine`, ports bound to
   `127.0.0.1`, named volume, health checks, an init script that creates a separate test database.
   Local-only credentials come from a root `.env` (listed in `.env.example`), never real secrets.
3. **API (`api/`):** uv project (Python 3.13); FastAPI app factory; `app/config.py` with
   pydantic-settings (every setting from env, clear error listing missing variables and pointing to
   `.env.example`); async SQLAlchemy engine and session; Alembic set up for async with a first migration
   that enables the `vector` extension; Redis client; JSON logging with a request id and no personal
   data; routes `GET /health` (alive) and `GET /api/health/ready` (database + Redis); one error shape
   for all errors; `app/cli.py` with `check-config` (reports each setting and tests database and Redis
   now; later phases add more checks).
4. **Web (`web/`):** Next.js 16 App Router, TypeScript strict, Tailwind CSS v4, ESLint, Prettier;
   `next.config.ts` rewrites `/api/:path*` to `API_URL`; basic security headers; a temporary home
   page that calls `/api/health/ready` and shows the result (this is a developer check, not a product
   screen; Phase 3 replaces it).
5. **Quality tools:** ruff (lint + format) and mypy for Python; ESLint + Prettier + `tsc --noEmit`
   for web; pre-commit hooks (ruff, prettier, eslint, end-of-file, large files, a secret scanner such
   as gitleaks). Scripts: `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, `pnpm e2e`;
   `uv run ruff check`, `uv run mypy app`, `uv run pytest`.
6. **Tests:** pytest with a real test database and Redis (fixtures create and clean tables);
   Vitest + React Testing Library with one component test; Playwright with one smoke test
   (home page loads, health shows OK) on Chromium.
7. **CI:** `.github/workflows/ci.yml` with Postgres and Redis services: API lint, types, tests; web
   lint, types, tests, build; Playwright smoke. `.github/dependabot.yml` for pip, npm and GitHub Actions.
   (These files are created only; nothing is pushed.)
8. **Docs:** `README.md` (what NxtRole is, how to run locally on Windows step by step, scripts),
   `api/.env.example`, `web/.env.example`, root `.env.example`, `docs/DEPLOYMENT.md` local section.

## 4. UI mock references
None yet (the temporary page is a developer check). Load Geist and Geist Mono now so Phase 3 can use them.

## 5. Recommended technologies
Docker Compose, uv, FastAPI, SQLAlchemy 2 async + psycopg, Alembic, pydantic-settings, redis-py,
Next.js 16, Tailwind v4, ESLint, Prettier, ruff, mypy, pytest, pytest-asyncio, httpx, Vitest,
Testing Library, Playwright, pre-commit, GitHub Actions, Dependabot.

## 6. Files and modules to create or modify
`docker-compose.yml`, `docker/postgres/init/01-test-db.sql`, `.env.example`, `.gitignore`,
`.gitattributes`, `.editorconfig`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`,
`.github/dependabot.yml`, `api/pyproject.toml`, `api/uv.lock`, `api/alembic.ini`, `api/alembic/…`,
`api/app/{__init__,main,config,db,redis_client,logging_setup,errors,cli}.py`, `api/app/api/health.py`,
`api/tests/{conftest,test_health,test_config}.py`, `api/.env.example`, `web/` (Next.js app),
`web/next.config.ts`, `web/vitest.config.ts`, `web/playwright.config.ts`, `web/.env.example`,
`README.md`, `docs/DEPLOYMENT.md`, `docs/TESTING.md`.

## 7. Database and API requirements
- Database: only the Alembic baseline (vector extension). Feature tables start in Phase 4.
- API: `GET /health` → `{"status":"ok"}`; `GET /api/health/ready` → `{"database":"ok","redis":"ok"}`
  or 503 with which part failed.

## 8. Implementation sequence
Layout and ignore files → Docker Compose up and healthy → API skeleton + config + health → Alembic
baseline → pytest green → Web skeleton + proxy + temporary health page → Vitest and Playwright green →
quality tools and pre-commit → CI and Dependabot files → README and env examples → full local run-through
from a clean clone, following the README exactly.

## 9. Testing requirements
- pytest: health 200; ready 200 with services up; ready 503 when Redis is stopped; config error lists
  missing variables.
- Vitest: one component renders.
- Playwright: home page shows "database ok, redis ok" through the proxy.
- All lint and type checks pass. Report the commands and the pass counts.

## 10. Edge-case checklist
- [ ] Docker not running → clear message in README and in `check-config`.
- [ ] Port 5432 or 6379 already in use → documented fix (change the host port in `.env`).
- [ ] Missing or invalid env variable → one readable error naming the variable.
- [ ] Database not ready yet when the API starts → health reports it; no crash loop.
- [ ] Windows line endings and paths → `.gitattributes` and commands tested in PowerShell.

## 11. Security considerations
No secrets in code or git; `.env` ignored; ports bound to localhost; security headers in Next.js;
secret scanner in pre-commit; logs never include env values.

## 12. Acceptance criteria
- [ ] From a clean clone, following README only: `docker compose up -d`, API and web start, the
      temporary page shows database and Redis OK.
- [ ] `uv run python -m app.cli check-config` shows each setting and passes for database and Redis.
- [ ] All tests, lint and type checks pass locally (commands and results in the report).
- [ ] CI and Dependabot files exist and are valid YAML.
- [ ] No product screens, no dummy data.

## 13. Documentation updates
README, `docs/DEPLOYMENT.md` (local setup), `docs/TESTING.md` (how to run tests), `docs/TECH_STACK.md`
(exact installed versions), `docs/DECISIONS.md` (any new choice), `docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format. Explain: what Docker and a container are, what an environment variable is,
what a migration is, what CI is, what a linter is.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 3." Do not commit.
