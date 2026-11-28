# Deployment

Status: **skeleton, Phase 1, 27 Nov 2026.** Phase 2 fills in the local part, Phase 15 the production part, Phase 16 the launch and maintenance routine.
Rules (CLAUDE.md section 3 and D-020): secrets only in `.env` files or hosting secret stores **that you fill in yourself**; never paste a key in chat; never commit `.env`; this document lists **names and purposes only, never values**.

## 1. Local and production at a glance

| | Local (your laptop) | Production (free tiers) |
|---|---|---|
| Web and API | `next dev` on port 3000, `uvicorn` on port 8000 | Vercel (Hobby, non-commercial use only) at a `*.vercel.app` address |
| Database | PostgreSQL + pgvector in Docker | Supabase free project (Data API **off**) |
| Files | Local folder behind the same signed-URL interface | Supabase Storage, private bucket |
| Redis | Docker | Upstash free database |
| Worker and schedules | `uv run python -m app.worker` | GitHub Actions workflows (`docs/ARCHITECTURE.md` section 9) |
| AI | Groq free key in `.env` | Same key in Vercel and GitHub secrets |
| Domain and HTTPS | `http://localhost` | Automatic HTTPS on `vercel.app` |

### Local setup (built in Phase 2)

The step-by-step guide is in [README.md](../README.md) sections 1 to 3. Summary:

| Part | How it runs locally |
|---|---|
| Linux | Ubuntu on WSL 2. `%USERPROFILE%\.wslconfig` limits memory to 3 GB and sets `instanceIdleTimeout=-1` so the containers keep running (verified on Windows 10) |
| Docker | Docker Engine and Compose inside Ubuntu (D-041), installed by `scripts/install-docker-ubuntu.sh` |
| Database and Redis | `wsl docker compose up -d`: `pgvector/pgvector:pg17` and `redis:7-alpine`, bound to `127.0.0.1` only, data in named volumes; a second database `nxtrole_test` is created on first start |
| Settings | `scripts/new-local-env.ps1` writes `.env`, `api/.env`, `web/.env.local` with a random password; then `uv run python -m app.cli setup-local` adds the limited database user and the signing secret; never committed |
| Structure | `uv run alembic upgrade head` |
| Check | `uv run python -m app.cli check-config` |
| API | `uv run python -m app.serve --reload` on `127.0.0.1:8000` |
| Web | `pnpm dev` on `127.0.0.1:3000` (forwards `/api/*` to the API) |

## 2. Accounts and keys checklist

"Phase" is when you create it (D-020). "Where the value goes" names the file or secret store and the **variable name**; you fill the value yourself.

| # | Service | What it is for | Cost | Phase | Where the value goes (variable names) | Notes |
|---|---|---|---|---|---|---|
| 1 | **Ubuntu on WSL 2 with Docker Engine** | Local Postgres and Redis | Free | 2 (done) | `.env` (created by the script) | Docker Desktop is not used (D-041) |
| 2 | **GitHub** repository (private) | Code, CI, scheduled runs | Free (2,000 Actions minutes a month, `docs/ARCHITECTURE.md` 9) | 2 | none locally | Make the repository private first |
| 3 | **Groq** | The only AI provider (D-024) | Free | 5 | `api/.env`: `GROQ_API_KEY`; later Vercel and GitHub secrets | In the Groq console switch on **zero data retention** (Data Controls) and note the model names and limits |
| 4 | **Adzuna** | Job search API for India | Free key | 6 | `api/.env`: `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | Free tier is for evaluation; check the quota and terms |
| 5 | **Cerebras** | Optional backup (off, D-024) | Trial credit needs a card | not planned | `api/.env`: `CEREBRAS_API_KEY` (leave empty) | Only if you decide to enable it later |
| 6 | **VAPID keys** (web push) | Phone alerts | Free (generated on your laptop) | 8 | `api/.env`: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`; `web/.env.local`: `NEXT_PUBLIC_VAPID_PUBLIC_KEY` | A command generates the pair; the private key never leaves secrets |
| 7 | **App secrets** (generated on your laptop) | JWT signing; data encryption later | Free | 4 (done by `setup-local`) | `api/.env`: `JWT_SECRET`; `APP_ENCRYPTION_KEY` from Phase 12 | Long random values; different for local and production |
| 8 | **Google Cloud project** with an OAuth client (testing mode) | Calendar connection (D-023, D-031) | Free | 12 | `api/.env`: `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI` | Add yourself as the test user; scope `calendar.events.owned` only |
| 9 | **Google Apps Script** (in your own account) | Gmail script (D-019) | Free | 12 | The script holds the key id and secret that NxtRole shows you once | Created from Settings > Connections |
| 10 | **Sentry** | Error reports | Free, optional | 12 | `api/.env`: `SENTRY_DSN`; `web/.env.local`: `NEXT_PUBLIC_SENTRY_DSN` | Off until set; scrubbing rules first |
| 11 | **Langfuse** | AI call tracing | Free, optional | 12 | `api/.env`: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | Off until set; redacted data only |
| 12 | **Supabase** | Production PostgreSQL + Storage | Free | 15 | Vercel and GitHub secrets: `DATABASE_URL` (app, pooled), `MIGRATION_DATABASE_URL` (migrations, direct), `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | Region near India; Data API **off**; private bucket; free project pauses when unused |
| 13 | **Upstash** | Production Redis | Free | 15 | `REDIS_URL` | 500K commands a month |
| 14 | **Vercel** | Hosting for web and API | Free (non-commercial) | 15 | Project environment variables (same names as `.env`) | Region choice; check function limits live |
| 15 | **GitHub token for burst runs** | API starts a worker run (`repository_dispatch`) | Free | 15 | Vercel: `GITHUB_DISPATCH_TOKEN` (fine-grained, this repository, Actions write only) | Expires; set a reminder |
| 16 | **GitHub secrets** | Scheduled workflows | Free | 15 | Repository secrets with the same names as production `.env` | Never visible to fork builds |

## 3. Environment variables

Every setting comes from environment variables through **one module** (`api/app/config.py`); a missing variable stops start-up with a message naming it (`check-config` lists them all). `.env.example` files (root, `api/`, `web/`) list **names only**.

| Group | Variables (names only) |
|---|---|
| Core | `APP_ENV` (`local`, `production`), `APP_BASE_URL`, `ALLOWED_ORIGINS`, `LOG_LEVEL` |
| Database | `DATABASE_URL` (the limited user `nxtrole_app`), `MIGRATION_DATABASE_URL` (the owner: migrations and account commands), `DB_POOL_SIZE` |
| Redis | `REDIS_URL` |
| Auth | `JWT_SECRET` (32 characters or more), `LOGIN_RATE_PER_MINUTE` (default 5), `TRUSTED_PROXY_COUNT` (default 0), `APP_ENCRYPTION_KEY` (Phase 12) |
| Storage | `STORAGE_BACKEND` (`local`, `supabase`), `STORAGE_BUCKET`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `UPLOAD_MAX_BYTES` |
| AI | `GROQ_API_KEY`, `AI_MODEL_CHAIN`, `AI_DAILY_TOKEN_BUDGET`, `AI_TOP_N`, `CEREBRAS_API_KEY` (empty) |
| Sources | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` |
| Push | `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` |
| Google | `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI` |
| Scheduling | `GITHUB_DISPATCH_TOKEN`, `GITHUB_REPOSITORY`, `SCHEDULE_QUIET_START`, `SCHEDULE_QUIET_END` |
| Observability | `SENTRY_DSN`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` |
| Web (public, safe in a browser) | `NEXT_PUBLIC_API_BASE`, `NEXT_PUBLIC_VAPID_PUBLIC_KEY`, `NEXT_PUBLIC_SENTRY_DSN` |

## 4. Deployment pipeline (to build in Phase 15)

1. Pull request: lint, types, tests, migrations check, audits, secret scan (`docs/TESTING.md` section 5).
2. Merge to `main`: Vercel builds web and API; a migration job runs `alembic upgrade head` with `MIGRATION_DATABASE_URL` **before** the new code takes traffic (expand then contract, `docs/DATABASE_SCHEMA.md` section 7).
3. Smoke test against the production address: sign-in, Today, one job, health details.
4. Scheduled workflows start using the new code on their next run.

**Rollback:** redeploy the previous Vercel build; because migrations are expand-then-contract, the old code still works with the new schema. If a migration must be undone, restore from the latest backup (steps tested in Phase 15).

## 5. Operations (to complete in Phases 15 and 16)

| Topic | Plan |
|---|---|
| Backups | Daily `backup.yml` dump to the private bucket, encrypted; monthly restore drill |
| Health | `GET /api/health` for uptime; `GET /api/health/details` shows last runs, backup age, queue size, Actions minutes used |
| Free-tier limits | Supabase 500 MB and 7-day pause; Upstash 500K commands a month; GitHub 2,000 minutes; Groq daily tokens; each has a counter in Settings or health |
| Key rotation | See section 6 |
| Runbook | One page per failure: morning run failed, source paused, AI limits used, database paused, push not arriving, Gmail script stopped, Calendar needs reconnect |
| Monitoring | Sentry and Langfuse if keys exist; otherwise `run_logs` and the in-app agent log |
| Privacy tools | "Export my data" and "Delete my account and data" tested before launch (E-35, E-36) |

## 6. Rotating a secret (the order matters)

| Secret | Steps |
|---|---|
| Groq key | Create a new key in the Groq console; update `.env`, Vercel and GitHub secrets; delete the old key |
| JWT secret | Set a new value everywhere; everyone is signed out (acceptable for one user) |
| `APP_ENCRYPTION_KEY` | Needs a re-encryption script (decrypt with old, encrypt with new); do not change it without the script |
| Gmail script key | Settings > Connections > "New key"; paste the new script in Apps Script; the old key stops working |
| MCP token | Revoke and create a new one in Settings > Connections |
| Database password | Change in Supabase; update `DATABASE_URL` and `MIGRATION_DATABASE_URL` everywhere |
| GitHub dispatch token | Create a new fine-grained token; replace in Vercel; delete the old one |
| Google OAuth client secret | Create a new secret in Google Cloud; update; reconnect Calendar |

## 7. Launch checklist (Phase 16; mirrors ROADMAP H)

- [ ] All phase acceptance criteria accepted
- [ ] Full tests, evals and accessibility checks green
- [ ] Security review done; no critical or high issue open
- [ ] Production accounts created; `check-config` passes every line
- [ ] `nxtrole_app` given a password; `DATABASE_URL` uses it, not the owner
- [ ] Visitor address measured on the host and `TRUSTED_PROXY_COUNT` set (KI-014); password hashing time re-measured
- [ ] Migrations run; pgvector enabled; Data API off
- [ ] Secrets only in Vercel and GitHub; nothing in git
- [ ] HTTPS and security headers confirmed
- [ ] Sentry and Langfuse receiving events (if enabled)
- [ ] Daily backup runs; one restore tested
- [ ] Runbook and rollback tried once
- [ ] Smoke test of every core journey on desktop and phone
- [ ] Privacy notice live; export and delete work
