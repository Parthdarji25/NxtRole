# NxtRole

A personal AI job-search agent for India. It finds real jobs from official sources, checks them for scams, scores the fit against your real
profile with quoted proof, and helps you apply and follow up, without ever acting behind your back.

**Current state:** sign-in and the approve-and-undo engine (Phase 4). You can create your account, sign in on several devices and set your name. The screens have no job data yet.
The plan is in [docs/ROADMAP.md](docs/ROADMAP.md) and the requirements in [docs/PRD.md](docs/PRD.md).

| Folder | What is in it |
|---|---|
| `web/` | The screens: Next.js, TypeScript, Tailwind CSS |
| `api/` | The API and (later) the background worker: Python, FastAPI |
| `docker/`, `docker-compose.yml` | Local PostgreSQL (with pgvector) and Redis |
| `scripts/` | One-time setup helpers |
| `docs/` | Requirements, decisions, architecture, security, testing |

All commands below are for **Windows PowerShell**, run from the repository root unless a step says otherwise.

## 1. Install once

| Tool | Version | How to check |
|---|---|---|
| Git | any recent | `git --version` |
| Node.js | 22.14 or newer 22.x | `node -v` |
| pnpm | 12 | `pnpm -v` |
| uv (installs Python 3.13 for you) | current | `uv --version` |
| WSL 2 with Ubuntu | current | `wsl -l -v` |

Docker runs **inside Ubuntu** (Docker Desktop is not used, see D-041 in [docs/DECISIONS.md](docs/DECISIONS.md)).

1. Install Ubuntu (PowerShell **as Administrator**), restart if asked, then open Ubuntu once and create a Linux user:
   ```powershell
   wsl --install -d Ubuntu
   ```
2. Limit Linux's memory and keep it running while you work. This **creates** `.wslconfig`; if you already have one, edit it instead:
   ```powershell
   @"
   [wsl2]
   memory=3GB
   swap=2GB

   [general]
   instanceIdleTimeout=-1
   "@ | Set-Content -Encoding ascii "$env:USERPROFILE\.wslconfig"
   ```
3. Install Docker inside Ubuntu. Open the **Ubuntu** app and run (adjust the path if your repository is elsewhere):
   ```bash
   sudo bash "/mnt/c/Users/<your-windows-user>/Desktop/Projects/NxtRole/scripts/install-docker-ubuntu.sh"
   ```
   The script lets your Linux user run Docker without `sudo`. Docker warns that this group has root-level power inside Ubuntu.
4. Restart Linux:
   ```powershell
   wsl --shutdown
   ```

## 2. Set up the project

```powershell
# Local settings files with a random database password (never committed, never printed)
powershell -ExecutionPolicy Bypass -File scripts/new-local-env.ps1

# Database and Redis
wsl docker compose up -d
wsl docker compose ps            # wait until both show "healthy"

# API
cd api
uv sync
uv run python -m app.cli setup-local   # a limited database user and a signing secret, written to api/.env
uv run alembic upgrade head            # creates the database structure (a "migration")
uv run python -m app.cli check-config  # every line should say OK
uv run python -m app.cli create-owner  # your account: type a password, then save the recovery code
cd ..

# Web
cd web
pnpm install
pnpm exec playwright install chromium
cd ..

# Checks before every commit (optional but recommended)
uv run --project api pre-commit install
```

## 3. Run it

Use two PowerShell windows.

```powershell
# Window 1: API on http://127.0.0.1:8000  (API description at /api/docs, local only)
cd api
uv run python -m app.serve --reload
```

```powershell
# Window 2: web on http://127.0.0.1:3000
cd web
pnpm dev
```

Open <http://127.0.0.1:3000> for the landing page, or <http://127.0.0.1:3000/login> to sign in.
To check that the web app reaches the API, database and Redis, open <http://127.0.0.1:3000/api/health/ready>: it should show `{"database":"ok","redis":"ok"}`.

While `pnpm dev` runs, <http://127.0.0.1:3000/design> shows every component, and `/design/states` the loading, empty and error designs. Neither exists in production.

**See the design mocks:** `node scripts/mock-viewer/server.mjs`, then open <http://127.0.0.1:4173>.

Stop the database and Redis with `wsl docker compose down`. Your data is kept. Adding `-v` **deletes the local data**.

### Your account

There is no sign-up page. These commands run in `api/` and ask in the terminal; nothing you type is shown or saved to a file.

| Command | What it does |
|---|---|
| `uv run python -m app.cli create-owner` | Creates your account and shows the recovery code once |
| `uv run python -m app.cli reset-password` | New password and recovery code; signs every device out |
| `uv run python -m app.cli list-sessions` | Which devices are signed in |
| `uv run python -m app.cli revoke-sessions` | Signs every device out (`--session ID` for one) |

Forgot your password but have the recovery code? Open <http://127.0.0.1:3000/login/recover>.

## 4. Scripts

| Where | Command | What it does |
|---|---|---|
| `api/` | `uv run ruff check .` | Lint (finds likely mistakes) |
| `api/` | `uv run ruff format .` | Format |
| `api/` | `uv run mypy app tests migrations` | Type check |
| `api/` | `uv run pytest` | All tests (needs the containers) |
| `api/` | `uv run pytest tests/unit` | Tests that need no containers |
| `api/` | `uv run pip-audit` | Known vulnerabilities in dependencies |
| `web/` | `pnpm lint` | ESLint and Prettier |
| `web/` | `pnpm format` | Format |
| `web/` | `pnpm typecheck` | Type check |
| `web/` | `pnpm test` | Component tests |
| `web/` | `pnpm build` | Production build |
| `web/` | `pnpm e2e` | Browser tests (needs the containers; builds the web app, port 3100) |
| `web/` | `pnpm e2e:update-pictures` | Replace the approved screen pictures after an intended change |
| root | `node scripts/mock-viewer/review.mjs` | Build the mock-against-app page in `docs/visual-review/` |
| `web/` | `pnpm audit --audit-level high` | Known vulnerabilities in dependencies |

## 5. Settings

Every setting comes from an environment variable. The real files are never committed; the `*.example` files list every name.

| File | Used by | Template |
|---|---|---|
| `.env` | Docker containers | `.env.example` |
| `api/.env` | API, migrations, tests | `api/.env.example` |
| `web/.env.local` | Web app | `web/.env.example` |

## 6. Troubleshooting

| Problem | What to do |
|---|---|
| `check-config` says it cannot connect, or the page shows `database error` | Docker is not running. Run `wsl docker compose up -d`, then `wsl docker compose ps` |
| `docker: command not found` | Finish section 1, step 3 |
| `permission denied` for the Docker socket | Run `wsl --shutdown`, then try again (your new group membership needs a restart) |
| Containers stop on their own after a short while | Check that `.wslconfig` has `instanceIdleTimeout=-1`, run `wsl --shutdown`. If it still happens, keep one Ubuntu window open while you work |
| Port 5432 or 6379 is already in use | Set another number in `.env` (`POSTGRES_PORT` or `REDIS_PORT`) **and** in the matching addresses in `api/.env`, then `wsl docker compose up -d` |
| Port 8000 or 3000 is already in use | API: `uv run python -m app.serve --port 8001` and set `API_URL` in `web/.env.local` to match. Web: `pnpm exec next dev --port 3001` |
| `JWT_SECRET is missing` or `MIGRATION_DATABASE_URL is missing` | In `api/`: `uv run python -m app.cli setup-local`, then `uv run alembic upgrade head` |
| `check-config` says the database user is unlimited | Same as above |
| Locked out after wrong passwords | Wait 15 minutes, or `uv run python -m app.cli reset-password` |
| `NxtRole cannot start because some settings are wrong` | The message names the variable. Compare with the `.env.example` file |
| `API_URL is missing` | Create `web/.env.local` (section 2, first command) |
| `powershell` is "not recognized" | You are already in PowerShell: run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force`, then `.\scripts\new-local-env.ps1`. Then fix your PATH (last row) |
| `pnpm e2e` finishes the tests but never exits | Windows `taskkill` is not on your PATH. Fix your PATH (last row), then close the stuck window |
| `sudo` is "not recognized" | `sudo` is a Linux command: run it in the Ubuntu app, or prefix it with `wsl -d Ubuntu` |
| Database password rejected after you recreated `.env` | The database keeps its first password. Delete the local data with `wsl docker compose down -v`, then `up -d` again |
| `winget`, `cmd` or a pre-commit step "not found" | Your Windows **PATH** is missing the system folders. Start menu → "Edit the system environment variables" → Environment Variables → under *System variables* select **Path** → Edit → add `C:\Windows\System32`, `C:\Windows`, `C:\Windows\System32\Wbem` and `C:\Windows\System32\WindowsPowerShell\v1.0\` → OK. Restart VS Code |
