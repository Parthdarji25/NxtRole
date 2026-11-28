# Technology stack

Status: **Phase 1, verified 27 Nov 2026.** Starting point: `docs/ROADMAP.md` section C (accepted in D-001). This file records what was checked,
the exact current versions, what changed from the roadmap and why. Decisions are in `docs/DECISIONS.md` (D-024 to D-038).

**How versions were checked.** Version numbers and Python/Node requirements below come **straight from the official package registries**
(PyPI and npm) on 27 Nov 2026. Behaviour and limits come from the vendors' own documentation pages listed under "Sources". Where a source was
a third-party summary, or documents disagreed, the line says **to verify** and names the phase that must confirm it. Versions are pinned in
lockfiles in Phase 2 (D-036); a release younger than 7 days is not adopted unless it fixes a security issue.

---

## 1. Changes from the roadmap

| Roadmap said | Now | Why | Record |
|---|---|---|---|
| LiteLLM for AI access | **Our own gateway** on Groq's official client + Instructor | LiteLLM had two supply-chain compromises of PyPI releases in 2026 | D-025 |
| Groq main + Cerebras backup | **Groq only**, a chain of Groq models; Cerebras adapter optional and off | Cerebras free tier is now a one-time $5 credit that needs a card and expires in 30 days | D-024 |
| Redis + arq for the queue | **Jobs table in PostgreSQL + small worker**; Redis only for locks and rate limits | arq is in maintenance-only mode | D-026 |
| Docker Desktop for local services | **Docker Engine inside Ubuntu on WSL 2** | Docker Desktop does not list Windows 10 Home as supported | D-041 |
| Morning run at 07:00 IST (01:30 UTC) | Starts **05:30 IST (00:00 UTC)**, push at or after 07:00 IST | A run that starts at 07:00 cannot be ready by 07:00 | D-030 |
| Vercel runs web and API | Same, but **API requests assumed to be under 10 s**, uploads go straight to storage, and Vercel Cron is not used | 4.5 MB body limit; unclear and small function time limits; Hobby cron is once a day | D-029, D-030, D-038 |
| 5 MB resume sent through the API | Signed upload URL to private storage | 4.5 MB request limit | D-029 |

Everything else in ROADMAP C is kept.

---

## 2. Runtime requirements

| Tool | Needed | On the founder's laptop (27 Nov 2026) | Action |
|---|---|---|---|
| Python | 3.13 (supported by Vercel and by every pinned package; the newest packages need 3.10 to 3.11 or newer) | 3.12.4 system install; **3.13.18 installed by `uv`** | Use 3.13 via `uv`; pin it in `.python-version` |
| `uv` (Python packages and virtual environments) | current | 0.13.6 | none |
| Node.js | 22.12 or newer (several tools require it: Vitest 5, axe Playwright, Sentry) | 22.14.0 | none; pin in `.nvmrc` |
| Git | any recent | 2.56 | none |
| Ubuntu on WSL 2 + Docker Engine | current | Ubuntu 26.04.1, Docker 29.10.1, Compose 5.8.0 | Installed in Phase 2 (D-041) |

---

## 3. Backend (Python) and its parts

| Part | Choice | Version checked (PyPI) | Needs | Why this one | Rejected |
|---|---|---|---|---|---|
| Language | Python | 3.13 | | Best AI libraries; typed with hints and Pydantic | Node API (weaker AI tooling) |
| Web framework | FastAPI | 0.165.0 (18 Nov 2026) | Python 3.11+ | Types check every request; writes API docs; Vercel runs it with zero config | Flask (no validation), Django (heavy) |
| Server (local) | uvicorn | 0.54.0 | 3.10+ | Standard FastAPI server | |
| Validation and config | Pydantic, pydantic-settings | 2.14.4, 2.16.3 | 3.10+, 3.11+ | One config module; clear errors when a variable is missing | |
| ORM | SQLAlchemy | 2.1.9 | 3.11+ | Typed queries; async | Raw SQL (more mistakes) |
| Migrations | Alembic | 1.20.1 | 3.10+ | Every database change is a versioned file | |
| Database driver | psycopg 3 | 3.3.9 | 3.10+ | One driver for the app **and** the LangGraph checkpointer | asyncpg (a second driver) |
| Vector support | pgvector (Python helper) | 0.5.1 | 3.10+ | Stores and searches vectors in PostgreSQL | A vector database (another service) |
| Password hashing | argon2-cffi | 25.1.0 | 3.8+ | Argon2id, the current recommendation | bcrypt (older design) |
| Tokens | PyJWT | 2.15.1 | 3.9+ | Signs and checks the 15-minute access token | |
| AI client | Groq official client | 1.7.0 | 3.10+ | Official, small, no routing layer | LiteLLM (D-025) |
| Typed AI answers | Instructor | 1.18.0 (26 Nov 2026) | 3.10+ | Validates model output against a Pydantic type and retries | Hand parsing |
| Agents | LangGraph + Postgres checkpointer | 1.2.24, langgraph-checkpoint-postgres 3.2.1 | 3.10+ | Agents that pause for approval and resume; state stored in our database | Hand-written loops |
| MCP server | `mcp` (official Python SDK) | 2.3.0 | 3.10+ | Streamable HTTP, can run stateless (suits serverless) | |
| Embeddings | fastembed (`BAAI/bge-small-en-v1.5`, 384 dimensions) | 0.9.1 | 3.10+ | Runs on the server, free, resume text stays private | Paid embedding APIs |
| HTTP client | httpx | 0.29.0 | 3.10+ | Async, timeouts, used for every outgoing call | requests (sync) |
| Redis client | redis-py | 8.2.0 | 3.11+ | Locks and rate limits | |
| Web push | pywebpush | 2.5.0 | 3.10+ | VAPID web push | |
| PDF text | pypdf, pdfplumber | 7.2.0, 0.11.11 | 3.10+, 3.8+ | Read resume text; "Parse my PDF" check; our own ATS rules | Resume-parser packages (mostly unmaintained) |
| PDF export from HTML | WeasyPrint | **to verify in Phase 10** | | Makes the PDF in the worker; no browser needed | A headless browser (heavy) |
| Logging | structlog | 26.1.0 | 3.10+ | Structured logs, easy to redact | |
| Errors | sentry-sdk | 3.0.1 | | Optional; off until a key exists | |
| AI tracing | langfuse | 5.2.0 | 3.11+ | Optional; off until keys exist; receives redacted data only | |
| Tests | pytest, pytest-asyncio | 9.2.0, 1.5.0 | | | |
| Lint, types | ruff, mypy | 0.17.6, 2.4.1 | | | |
| Browser tests | Playwright (Python not used; JS version below) | | | | |

Notes:
- **psycopg for everything.** LangGraph's PostgreSQL checkpointer uses psycopg, so using it for the app avoids two drivers.
- `fastembed` 0.9.1 runs on Python 3.13; the model is downloaded once and cached. Confirm the model name is still supported in Phase 7.
- `groq` 1.7.0 is 3 months old: fine under the 7-day rule. `argon2-cffi` 25.1.0 is older but stable.

## 4. Frontend (TypeScript)

| Part | Choice | Version checked (npm) | Why | Rejected |
|---|---|---|---|---|
| Framework | Next.js | 16.4.6 | Pages, routing, a safe proxy to the API. In Next 16 `middleware.ts` is renamed `proxy.ts` (verified in the official docs) | Plain React |
| UI library | React, react-dom | 19.3.1 | Required by Next 16 | |
| Language | TypeScript | 7.0.2 | Strict mode. **7 is a new major release: Phase 2 confirms Next 16.4, ESLint and Vitest work with it; if not, pin the newest 5.x** | |
| Styling | Tailwind CSS v4 (+ `@tailwindcss/postcss`) | 4.3.5 | Turns the mock tokens into classes; light and dark from one file | Plain CSS |
| UI parts | shadcn/ui CLI (Radix based, code lives in our repo) | 4.23.1 | Accessible dialogs, menus, tabs we restyle to match the mocks | Hand-built (accessibility risk) |
| Icons | lucide-react | 1.82.0 | The mocks use simple line icons; Phase 3 matches them exactly, so it may use inline SVG instead | |
| Forms | React Hook Form, zod, resolvers | 7.92.0, 4.6.7, 7.0.9 | Fast forms with clear messages | Formik |
| Server data | TanStack Query | 5.108.4 | Caching, loading and error states, optimistic undo | Hand fetching |
| Fonts | `geist` (Geist and Geist Mono) | 1.9.2 | The mocks' fonts; self-hosted by Next | |
| Landing 3D tour | three.js (**only on the landing page, loaded lazily**) | 0.187.0 | The mock's 3D view; step cards remain the fallback (D-018) | |
| Unit and component tests | Vitest, Testing Library | 5.1.2, 16.3.3 | | Jest |
| End-to-end and visual | Playwright | 1.65.1 | Chromium, Firefox, WebKit; desktop and phone sizes | |
| Accessibility tests | @axe-core/playwright | 4.14.1 | WCAG checks inside browser tests | |
| Lint | ESLint | 10.15.0 | | |
| Errors | @sentry/nextjs | 11.19.0 | Optional; off until a key exists | |

## 5. Data, hosting and services

| Part | Choice | What was verified | Notes and limits to design for |
|---|---|---|---|
| Database | PostgreSQL + pgvector (Supabase free plan) | Free plan: 500 MB per project; a free project is **paused after about a week of low activity**; 2 active projects | Embeddings count toward 500 MB; the daily run keeps it active (E-21); backups are our own job (FR-216). **Data API off.** pgvector support on Supabase: confirm in Phase 15 |
| Private files | Supabase Storage | About 1 GB free (secondary source: **to verify**) | Private bucket only; signed URLs (D-029) |
| Cache and locks | Redis (Upstash free) | 500K commands per month, one free database, about 250 MB | Design: locks and rate limits only (D-026); no polling loops |
| Web and API hosting | Vercel Hobby | **4.5 MB body limit confirmed**; Python 3.13 supported; FastAPI supported; function time limit documents **conflict (10 to 300 s)**; Hobby is **non-commercial only**; cron once a day only | See D-029, D-030, D-038. Revisit before charging anyone |
| Schedules and the worker | GitHub Actions | 2,000 free minutes a month for private repositories (Linux); scheduled runs can be **delayed under load** | Budget in `docs/ARCHITECTURE.md` section 9 |
| AI | Groq free plan | gpt-oss-120b: 30 requests per minute, 1,000 a day, 8,000 tokens per minute, **200,000 tokens a day** (official table). Zero data retention can be enabled on any account | D-033. Exact models and limits re-read from the console in Phase 5. Whether the free plan trains on data: terms say no, **founder confirms in the console and Data Controls** |
| Job sources | Greenhouse, Lever, Ashby feeds; Adzuna; Arbeitnow | Ashby: public, unauthenticated posting API (official docs). Adzuna: free key, "for evaluation", quota **to verify** on the portal. Greenhouse and Lever: public per-company endpoints, **to verify in Phase 6** against official docs. Arbeitnow: **to verify** | One adapter per source; recorded fixtures; terms re-read in Phase 6 |
| Calendar | Google Calendar API, scope `calendar.events.owned` | Scope exists and is the narrowest that can write events (official docs) | D-031; testing-mode tokens may expire (E-32) |
| Push | Web Push (VAPID) | Works on Android and iOS 16.4+ for installed web apps | Install help in the app (FR-088) |
| Errors, tracing | Sentry, Langfuse | Both have free plans | Optional; redacted data only |

## 6. Why two languages

TypeScript for the screens and Python for the AI and data work. The AI libraries are far stronger in Python and both languages appear on most
AI-engineer job posts. The cost is more to learn; `docs/LEARNING_LOG.md` carries a note per task.

## 7. Open items for later phases

| Item | Phase | What to confirm |
|---|---|---|
| Exact Groq model names, limits and zero-data-retention switch | 5 | Read from the console; record |
| Greenhouse, Lever, Arbeitnow official terms and limits; Adzuna quota | 6 | Record in `docs/API_DOCUMENTATION.md` source notes |
| `fastembed` model name still supported; HNSW index settings | 7 | |
| PDF-from-HTML tool and the ATS "parse my PDF" method | 10 | |
| Supabase pgvector and storage limits; Vercel function limits | 15 | Re-read the live pages |
| Google OAuth testing-mode token lifetime | 12 | |

## 8. Installed versions (Phase 2, 27 Nov 2026)

These are the versions in the lockfiles (`api/uv.lock`, `web/pnpm-lock.yaml`). The tables above show what was current in Phase 1; where they differ, **this section is what runs**.
The differences come from the 7-day rule (D-036) and from tool compatibility (D-044).

| Area | Installed |
|---|---|
| Runtime | Python 3.13.18 (uv 0.13.6), Node 22.14.0, pnpm 12.16.1 |
| Containers | Docker 29.10.1, Compose 5.8.0, PostgreSQL 17.12 with pgvector 0.8.7 (`pgvector/pgvector:pg17`), `redis:7-alpine` |
| API | FastAPI 0.165.0, uvicorn 0.54.0, Pydantic 2.14.4, pydantic-settings 2.16.3, SQLAlchemy 2.1.9, Alembic 1.20.1, psycopg 3.3.9, redis 8.1.0 (8.2.0 was younger than 7 days), structlog 26.1.0; Phase 4: argon2-cffi 25.1.0, PyJWT 2.15.1, email-validator 2.4.0, python-dotenv |
| API tools | pytest 9.2.0, pytest-asyncio 1.5.0, httpx 0.28.1, ruff 0.17.6, mypy 2.4.1, pip-audit 2.10.1, pre-commit 4.7.0 |
| Web | Next.js 16.4.6, React 19.3.1, Tailwind CSS 4.3.5, geist 1.9.2, radix-ui 1.8.1, sonner, clsx, tailwind-merge, React Hook Form 7.92.0, zod 4.6.7, @hookform/resolvers 7.0.7 (Phase 3; D-048), @tanstack/react-query 5.108.2 (Phase 4) |
| Web tools | TypeScript **5.9.3** (typescript-eslint supports below 6.1), ESLint **9.39.5** (React, import and accessibility plugins do not support 10), Prettier 3.10.1, Vitest 5.1.1, jsdom **29.1.1** (31 needs Node 22.22.2), Testing Library 16.3.3, Playwright 1.65.1, @axe-core/playwright |
| CI actions and hooks | Pinned by commit hash in `.github/workflows/ci.yml` and `.pre-commit-config.yaml` (gitleaks 8.30.1) |

Libraries listed in sections 3 and 4 that are not here yet are added by the phase that first uses them.

## Sources

All read on 27 Nov 2026.

- Next.js 16 and the `proxy.ts` rename: https://nextjs.org/blog/next-16 · https://nextjs.org/docs/app/api-reference/file-conventions/proxy
- Vercel Functions limits (4.5 MB body): https://vercel.com/docs/functions/limitations · bypass guide: https://vercel.com/kb/guide/how-to-bypass-vercel-body-size-limit-serverless-functions
- Vercel Python runtime and FastAPI: https://vercel.com/docs/functions/runtimes/python · https://vercel.com/docs/frameworks/backend/fastapi · https://vercel.com/changelog/python-3-13-and-3-14-are-now-available
- Vercel Hobby and cron: https://vercel.com/docs/plans/hobby · https://vercel.com/docs/cron-jobs/usage-and-pricing
- GitHub Actions billing and minutes: https://docs.github.com/en/billing/concepts/product-billing/github-actions
- Groq rate limits: https://console.groq.com/docs/rate-limits · data controls: https://console.groq.com/docs/your-data
- Cerebras rate limits (trial tier): https://inference-docs.cerebras.ai/support/rate-limits
- Google Calendar scopes: https://developers.google.com/calendar/api/auth
- LiteLLM incident notices: https://docs.litellm.ai/blog/security-update-march-2026 · https://securitylabs.datadoghq.com/articles/litellm-compromised-pypi-docker/
- arq maintenance status: https://pypi.org/project/arq
- Ashby public job posting API: https://developers.ashbyhq.com/docs/public-job-posting-api
- Adzuna terms: https://developer.adzuna.com/docs/terms_of_service
- Supabase pricing and pausing: https://supabase.com/pricing · https://supabase.com/docs/guides/platform/free-project-pausing
- Upstash Redis billing: https://upstash.com/docs/redis/overall/billing
- LangGraph checkpointers and human-in-the-loop: https://docs.langchain.com/oss/python/langgraph/checkpointers · https://docs.langchain.com/oss/python/langgraph/human-in-the-loop
- MCP Python SDK: https://py.sdk.modelcontextprotocol.io
- Instructor with Groq: https://python.useinstructor.com/integrations/groq/
- Package versions: https://pypi.org (JSON API per package) and https://registry.npmjs.org (per package), queried 27 Nov 2026.
