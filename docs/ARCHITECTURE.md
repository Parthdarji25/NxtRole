# Architecture

Status: **Phase 1 design, 27 Nov 2026.** Inputs: `docs/PRD.md`, `docs/DECISIONS.md` (D-001 to D-040), `docs/TECH_STACK.md`, `docs/DATABASE_SCHEMA.md`.
Nothing here is built yet. Phase 2 creates the repository structure in section 3; later phases fill it in.

## 1. Overview and principles

NxtRole is two programs and a set of scheduled jobs that share one database:

- **`web/`** is the screens (Next.js, TypeScript). It is installed on the phone as a web app.
- **`api/`** is the brain and the data gate (FastAPI, Python). It checks every request, talks to the database, and calls AI only through one gateway.
- **The worker** is the same Python code run in the background (locally in a terminal, in production by GitHub Actions). It does slow work: searching jobs, scoring, drafting, researching.

Principles that every design choice follows:

1. **The database is the memory.** Slow work is a row in `background_jobs`; progress and results are rows. A closed tab or a restarted server loses nothing (D-026, D-038).
2. **AI never writes to the database directly.** It creates a **proposal**. The owner approves it. One transaction applies it, writes a history row, and can be undone (section 12.2).
3. **One door for AI.** Every model call goes through `api/app/ai/gateway.py`, which removes identity first (D-025).
4. **Every query is scoped to the owner** in code *and* by PostgreSQL row-level security (D-028, D-039).
5. **Short requests.** The API assumes it has 10 seconds per request (D-038).
6. **Free tiers.** Nothing that costs money; every limit is a design input (`docs/TECH_STACK.md` section 5).

## 2. System diagram and components

```mermaid
flowchart LR
  subgraph Device["Owner's phone or laptop"]
    PWA["Installed web app (Next.js pages)"]
    SW["Service worker: offline shell and web push"]
  end
  subgraph Vercel["Vercel (free)"]
    NX["Next.js server: pages and /api rewrite (proxy.ts)"]
    API["FastAPI (Python 3.13)"]
  end
  subgraph Supabase["Supabase (free)"]
    PG[("PostgreSQL + pgvector")]
    ST[("Private file storage")]
  end
  RD[("Redis (Upstash): locks, rate limits")]
  subgraph GH["GitHub Actions (free)"]
    WK["Worker: morning run, hourly discovery, burst jobs, backup"]
  end
  GQ["Groq (AI models)"]
  SRC["Job sources: Greenhouse, Lever, Ashby, Adzuna, Arbeitnow"]
  GM["Gmail script in the owner's Google account"]
  GC["Google Calendar API"]
  PUSH["Browser push service"]
  MCP["Other AI apps (Claude Code, Cursor, VS Code)"]

  PWA -->|"access token in memory"| NX
  NX -->|"rewrite /api/*"| API
  PWA -->|"signed upload URL, then direct upload"| ST
  API --> PG
  API --> RD
  API --> ST
  API -->|"through the gateway only"| GQ
  API -->|"repository_dispatch for burst jobs"| WK
  WK --> PG
  WK --> RD
  WK --> ST
  WK -->|"through the gateway only"| GQ
  WK --> SRC
  WK --> PUSH
  WK --> GC
  GM -->|"HMAC-signed webhook"| API
  MCP -->|"token with scopes"| API
  PUSH --> SW
```

| Component | Responsibility | Does **not** do | Built in |
|---|---|---|---|
| Next.js pages | Screens, forms, loading and error states, holds the access token in memory | Talk to the database or to AI; hold secrets | 3 and each phase |
| Next.js `proxy.ts` | Rewrites `/api/*` to FastAPI so the browser sees one origin; sets security headers | Decide who is signed in (the API does; the proxy is not the only guard) | 3 |
| FastAPI routers | Validate input (Pydantic), check auth, call a service, shape the answer and errors | Contain business rules or SQL | 4 and each phase |
| Services | Business rules: stage order, approval, scoring, trust, estimates | Know about HTTP | each phase |
| Repositories | All SQL, always scoped to the user, optimistic-lock checks | Business decisions | each phase |
| AI gateway | Removes identity, walks the model chain, retries, counts usage, validates answers, restores identity | Decide anything about the owner's data | 5 |
| Worker | Takes `background_jobs`, runs handlers, schedules the daily work | Serve web requests | 8 |
| Agents (LangGraph) | Multi-step tasks (pack, research, ask) that pause for approval; state saved in PostgreSQL | Write data except as proposals | 10 and 11 |
| MCP server | Read tools for other AI apps, one draft-note tool, token scopes | Send, delete, change settings, read email text | 11 |
| Gmail script | Posts job emails to the webhook with an HMAC signature | Run anywhere but the owner's Google account | 12 |
| Service worker | Caches the shell for offline reading, receives web push | Queue changes silently (E-33) | 8 |

## 3. Repository structure

Created in Phase 2: everything below marked with its phase already exists only if the phase is 2; the rest is added by the phase that needs it.

```
NxtRole/
├── web/                         Next.js app (TypeScript strict)                              (Phase 2)
│   ├── src/app/                 Routes: (public) landing, login, legal; (app) today, jobs, ...
│   ├── src/components/ui/       Radix-based parts styled to the mocks (D-048)               (Phase 3)
│   ├── src/features/<domain>/   Screen parts, hooks and zod schemas per domain (health: Phase 2)
│   ├── src/lib/                 api client, auth (token in memory), config, format (IST, LPA)
│   ├── src/styles/tokens.css    Copy of docs/mocks/design-tokens.css                         (Phase 2)
│   ├── public/                  Icons, manifest, service worker
│   ├── e2e/                     Playwright journeys, visual and accessibility checks         (Phase 2, D-044)
│   ├── next.config.ts           /api forwarding and basic security headers                   (Phase 2)
│   └── src/proxy.ts             Nonce-based content security policy                          (Phase 3, D-043)
├── api/
│   ├── app/
│   │   ├── main.py, serve.py    Creates the app; starts it locally                           (Phase 2)
│   │   ├── config.py            The one configuration module (environment variables only)    (Phase 2)
│   │   ├── core/                errors, logging (redaction), middleware, redis, event loop   (Phase 2);
│   │   │                        security (Argon2, JWT), idempotency, time (IST), rate limits
│   │   ├── db/                  engine, sessions, base model (Phase 2); RLS setup, models/
│   │   ├── ai/                  gateway, privacy, prompts/, budget, usage, transport, cassettes (Phase 5); evals later
│   │   ├── <domain>/            router.py, service.py, repository.py, schemas.py (health: Phase 2)
│   │   ├── worker/              loop.py, schedules.py, handlers/<kind>.py
│   │   └── cli.py               check-config (Phase 2); create-owner, reset-password, run-job
│   ├── migrations/              Alembic versions (0001: the vector extension)                (Phase 2)
│   └── tests/                   unit/, integration/ (real Postgres and Redis), contract/
├── tests/fixtures/              Recorded real responses, name = source_YYYY-MM-DD_what.json
├── docker-compose.yml           Local Postgres+pgvector and Redis                            (Phase 2)
├── docker/postgres/init/        Creates the separate test database                           (Phase 2)
├── .github/                     workflows/ci.yml, dependabot.yml (Phase 2); morning, discovery, burst, backup
├── scripts/                     new-local-env.ps1, install-docker-ubuntu.sh                  (Phase 2)
├── docs/                        This documentation set
├── CLAUDE.md  README.md  .env.example (root, api, web)  .gitignore  .pre-commit-config.yaml  .nvmrc
```

**Domains (one package each under `api/app/`)**: `auth`, `accounts`, `files`, `profile`, `preferences`, `sources`, `companies`, `jobs`, `trust`, `matching`, `rules`, `today`
(brief), `alerts`, `pipeline` (applications, rounds, notes), `followups`, `offers`, `coach`, `studio` (documents, packs), `agents`, `resume`, `prepare`, `ask`, `network`,
`mcp`, `integrations` (gmail, calendar), `settings`, `proposals`, `history`, `health`.

## 4. Request layers

```mermaid
flowchart LR
  R["HTTP request"] --> M["Middleware: request id, CORS, security headers, body-size limit"]
  M --> A["Auth dependency: verify access token, load user, set app.user_id for RLS"]
  A --> RT["Router: Pydantic validation, idempotency key"]
  RT --> SV["Service: rules, stage order, approval, calls AI gateway if needed"]
  SV --> RP["Repository: SQL scoped by user_id, version check"]
  RP --> DB[("PostgreSQL")]
  SV --> EV["Events and proposals (history, undo)"]
  RT --> ER["One error shape: {detail: {code, message}}"]
```

Rules: routers never run SQL; repositories never apply business rules; services never read the HTTP request; every error becomes
`{"detail": {"code": "...", "message": "..."}}` with a message in plain words (NFR-SEC-01).

## 5. Sign-in, token refresh and logout

```mermaid
sequenceDiagram
  participant B as Browser
  participant N as Next.js proxy
  participant A as FastAPI
  participant D as PostgreSQL
  participant R as Redis
  B->>N: POST /api/auth/login (email, password)
  N->>A: forward
  A->>R: check lockout counters
  A->>D: load user, verify Argon2 hash
  A->>D: create refresh token (hash), new family
  A-->>B: access token (15 min, JSON) + refresh cookie (HttpOnly, Secure, SameSite=Strict, Path=/api/auth)
  Note over B: access token kept in memory only
  B->>A: GET /api/today (Authorization: Bearer access)
  A-->>B: data
  Note over B: access token expires
  B->>A: POST /api/auth/refresh (cookie + X-NxtRole-CSRF header)
  A->>D: mark old token used, issue new one in the same family
  A-->>B: new access token + new cookie
  Note over B,A: if an already-used refresh token arrives, the whole family is revoked
  B->>A: POST /api/auth/logout
  A->>D: revoke the family
  A-->>B: cookie cleared
```

Two tabs: the browser takes the **Web Locks** lock so that one tab refreshes at a time, and the server also accepts a just-used token for 10 seconds without issuing another (D-050). A **BroadcastChannel** tells the other tabs about signing in and out. Every request checks that its sign-in is still alive, so signing out a device works at once. Recovery by code (`/login/recover`, D-027) revokes all sessions.

In the web app: `lib/session.ts` (the token, in memory), `lib/api.ts` (adds it, refreshes once, retries), `features/auth/RequireSignIn.tsx` (the screen guard).

## 6. The morning run

Starts at **00:00 UTC (05:30 IST)** (D-030) and must finish before 07:00 IST. Push is sent at or after 07:00 IST.

```mermaid
flowchart TD
  S["GitHub Actions starts the worker"] --> L{"Redis lock free?"}
  L -- no --> X["Exit: another run is active (E-21)"]
  L -- yes --> F["Fetch all sources in parallel (timeouts, retries, rate limits)"]
  F --> C["Clean: salary to rupees per year, city aliases, plain text"]
  C --> DD["De-duplicate by fingerprint; record sightings; mark closed jobs"]
  DD --> T["Trust check in code (AI only for 'specific description')"]
  T --> RU["Apply the owner's confirmed rules (hidden jobs are counted)"]
  RU --> E["Embeddings (fastembed) and keyword search rank the rest"]
  E --> TOP["Take the top N (default 30), skipping Risky jobs"]
  TOP --> SC["AI scores each job twice with three quoted reasons (budget-paced, section 10)"]
  SC --> Q["Code checks every quote appears in the post; drop bad reasons"]
  Q --> PK["Queue pack drafts for the top 3 High-trust jobs (Phase 10)"]
  PK --> BR["Save the brief; if AI limits were hit, mark 'drafts pending'"]
  BR --> FU["Follow-up check (day 7, 14, 21)"]
  FU --> CL["Clean-up: expired data, retention"]
  CL --> PU["Notification: held until 07:00 IST, then one push"]
  PU --> UL["Release lock, write run_log stats"]
```

If the run fails, Today shows the previous brief with a "stale" label and one push says so (E-22).

## 7. Application pack agent (pause, approve, resume)

```mermaid
sequenceDiagram
  participant U as Owner
  participant W as Web app
  participant A as FastAPI
  participant Q as background_jobs
  participant K as Worker (agent)
  participant G as AI gateway
  participant D as PostgreSQL
  U->>W: Make application pack (job)
  W->>A: POST /api/studio/packs (Idempotency-Key)
  A->>A: refuse if job is Risky or profile not approved
  A->>Q: insert job 'build_pack' (dedupe key)
  A-->>W: 202 + run id
  K->>Q: take the job
  K->>D: read job text, approved profile facts
  K->>G: research company (public pages only) and pick facts
  K->>G: write bullets, note, answers
  K->>G: judge: check every claim against the profile facts
  K->>D: save draft document version - run state 'waiting_approval'
  W->>A: GET /api/agent-runs/{id} (short polling)
  A-->>W: steps so far, draft, blanks (for example expected CTC)
  U->>W: fill blank, tap Approve pack
  W->>A: POST /api/proposals/{id}/approve
  A->>D: one transaction: mark approved, new version, history row
  A-->>W: approved - open the company page - Undo available
```

The agent's graph state is saved in the PostgreSQL checkpointer after every step, so a closed tab or a restart resumes the same run (E-44). Only tools allowed for
that agent are given to it; text from the web or the job post is passed as data (NFR-SEC-06).

## 8. Gmail webhook

```mermaid
sequenceDiagram
  participant S as Gmail script (owner's Google account)
  participant A as FastAPI webhook
  participant D as PostgreSQL
  participant K as Worker
  S->>A: POST /api/webhooks/gmail (body, timestamp, key id, HMAC-SHA256 signature)
  A->>A: reject if older than 5 min, wrong signature, too large, or rate limited
  A->>D: insert inbound_emails by message id (a replay does nothing)
  A->>D: enqueue background_job 'classify_email'
  A-->>S: 202
  K->>D: take job - rules in code classify the email (no AI sees email text in v1 rules)
  alt clear rejection or interview invite on a known application
    K->>D: one transaction: move the card, history row 'Moved by Gmail', undo available
  else anything else
    K->>D: create a proposal for the owner
  end
  K->>D: notification for the owner
```

The script sends only emails that match the job filter, and the server stores only the minimal fields (D-019, D-035). The email text is processed in memory and not stored or logged.

## 9. Background work and the free scheduler budget

**Queue.** `background_jobs` rows, taken with `select … for update skip locked`, with `run_after` for backoff, a dedupe key, and stale-lock reclaim (D-026).
**Locks and limits.** Redis keys with expiry: `lock:morning:{user}`, `lock:discovery`, per-provider rate counters. Redis down → the worker refuses to run scheduled work
(safe) and the API falls back to database-based rate limits for sign-in only (E: Redis down).
**Where the worker runs.** Locally: a terminal command. Production: GitHub Actions. Burst work started by the owner (a pack, research, an export) is launched by the API
with a `repository_dispatch` call (a fine-grained GitHub token limited to this repository's Actions, kept in Vercel's environment). Phase 15 measures whether Vercel
functions can run short steps inline; if so the burst start-up cost disappears (D-038).

| Workflow | Schedule (UTC) | IST | Notes |
|---|---|---|---|
| `morning.yml` | `0 0 * * *` | 05:30 | Section 6. Up to 15 minutes |
| `discovery.yml` | `30 1-15 * * *` | 07:00 to 21:00 hourly | 15 runs; the 07:00 run sends the morning push; also retries "Drafts pending"; light, cached dependencies |
| `burst.yml` | `repository_dispatch` | on demand | Packs, research, export, delete, calendar sync |
| `backup.yml` | `30 20 * * *` | 02:00 | Dump, upload to private storage, check |
| `security.yml` | weekly | Sunday | Dependency audit and secret scan |

**Estimated budget (private repository, 2,000 free Linux minutes a month, billed in whole minutes per job).** These are **estimates to be measured in Phases 8 and 15** (D-040).

| Item | Runs a month | Minutes each | Minutes |
|---|---|---|---|
| Morning run | 30 | 15 | 450 |
| Discovery (hourly, 07:00 to 21:00 IST, 15 a day) | 450 | 2 | 900 |
| Backup | 30 | 3 | 90 |
| Burst runs (about 2 a day on demand) | 60 | 3 | 180 |
| Weekly security job | 4 | 5 | 20 |
| **Total** | | | **1,640 (82%)** |

Levers if usage nears the limit, in this order: discovery every 2 hours (about 450 minutes saved); fewer top-N jobs; run bursts inline (if Phase 15 allows); make the
repository public (code is not secret; secrets live only in encrypted settings) for unlimited standard-runner minutes. Settings > Agents shows the month's estimated minutes (from `run_logs`).
Scheduled runs can start late (GitHub documents delay under load), so every run is idempotent and `health` reports "last run too old" (NFR-REL-02).

**Keeping the free database awake.** The hourly run touches the database, so the 7-day pause rule never triggers while the schedule works (E-21).

## 10. AI gateway (D-025, D-033, D-053; built in Phase 5)

Every AI call goes through one function, `Gateway.run` in `api/app/ai/gateway.py`. Nothing else talks to a provider.

```mermaid
flowchart TD
  CALL["Caller gives: a purpose, a prompt id@version, the data, a Pydantic answer type, the owner's identity"] --> LOCK{"Key set and Zero Data Retention confirmed?"}
  LOCK -- no --> STOP["Refused: nothing is sent"]
  LOCK -- yes --> RED["Privacy guard: replace identity with markers; fence outside text"]
  RED --> LEAK{"Any personal value still there?"}
  LEAK -- yes --> STOP
  LEAK -- no --> BUD{"Free limits: room this minute and today?"}
  BUD -- "no" --> NXT["Next model in the chain"]
  BUD -- ok --> SND["Groq official client, strict JSON schema, timeout"]
  SND -- "429 or server error" --> NXT
  SND --> OK{"Answer fits the type?"}
  OK -- no --> RET["Ask again, at most 2 more times"]
  RET --> SND
  OK -- yes --> USE["Count requests and tokens; return the answer"]
  NXT -- "no model left" --> WAIT["Say when to try again; the job waits"]
```

| Part | File | What it does |
|---|---|---|
| Purposes and models | `ai/models.py` | Each purpose names a role (`main`, `small`, `judge`), whether it carries personal data, and its limits. The chain per role comes from configuration: `openai/gpt-oss-120b` → `openai/gpt-oss-20b`; judge `qwen/qwen3.8-27b` (preview) → `openai/gpt-oss-20b` (D-053) |
| Provider | `ai/transport.py` | The only code that calls Groq. Provider errors become ours: rate limited, unavailable, bad answer, not set up, too large. Retries are the gateway's, not the client's |
| Privacy guard | `ai/privacy.py` | Removes emails, Indian and international phones, government ID numbers and private lines (date of birth, parents' names) always; name, links, address and extra words as the owner confirmed. Checks again before sending |
| Prompts | `ai/prompts/*.md` | One file per `name@vN`; outside text goes between `<untrusted_data>` tags with an instruction to ignore instructions inside |
| Limits | `ai/budget.py` | Counts per model per minute and per IST day in Redis and paces calls. If Redis is down, calls go ahead and the provider's own limit still applies |
| Usage | `ai/usage.py`, table `ai_usage` | Requests, tokens, errors and rate-limit hits per day and model. Status: normal, using backup, limits used, not set up, privacy not confirmed |
| Recordings | `ai/cassettes.py` | Record real answers once; tests replay them without the network |

**Not built yet:** agent traces, evaluation sets and the in-app "All limits used" banner (their phases).

### 10.1 Reading a resume (Phase 5)

```mermaid
sequenceDiagram
  participant W as Web app
  participant A as API
  participant S as Private storage
  participant G as AI gateway
  W->>A: POST /api/files/uploads
  A-->>W: one-file upload address (10 minutes)
  W->>S: PUT the file (through the API in local development)
  W->>A: POST /api/files/{id}/complete
  A->>A: check contents, read the text, find identity
  A-->>W: what will be hidden
  W->>A: POST /api/profile/parse (the confirmed list)
  A->>A: save a background_jobs row, answer 202
  A->>G: after the answer is sent
  G-->>A: facts with quotes
  A->>A: drop facts whose words are not in the resume; save a proposal
  W->>A: GET /api/profile (every 2 seconds while reading)
  W->>A: approve (possibly edited): a profile version and a history row
```

- The job runs **inside the API process** until the Phase 8 worker. A job cut off by a restart (running for 10 minutes, or never started for 2) shows as interrupted and can be started again.
- Storage is a small interface (`files/storage.py`): a private local folder now, Supabase Storage in Phase 15 (D-029).
- A long resume is cut at 30,000 characters and read in parts that fit the per-minute limit.

## 11. Local and production

```mermaid
flowchart LR
  subgraph Local["Local (Docker Engine in Ubuntu on WSL 2)"]
    LW["web: next dev :3000"] --> LA["api: uvicorn :8000"]
    LA --> LP[("Postgres + pgvector (container)")]
    LA --> LR[("Redis (container)")]
    LK["worker: python -m app.worker"] --> LP
    LK --> LR
    LS["Storage: local folder with the same signed-URL interface"]
  end
  subgraph Prod["Production (free tiers)"]
    PW["Vercel: web + API"] --> PP[("Supabase Postgres + Storage")]
    PW --> PR[("Upstash Redis")]
    PG2["GitHub Actions: worker"] --> PP
    PG2 --> PR
  end
```

| Concern | Local | Production |
|---|---|---|
| Database | Container, same major version and `vector` extension | Supabase; Data API **off**; connection through the pooler for the API, direct for migrations |
| Files | Local folder behind the same storage interface | Supabase private bucket with signed URLs |
| Worker | `uv run python -m app.worker` | GitHub Actions workflows |
| Config | `.env` files filled in by the owner (templates in `.env.example`) | Vercel environment and GitHub secrets (D-020) |
| Secrets | Never committed; `check-config` lists what is missing | Same |
| Domain | `localhost` | `*.vercel.app` over HTTPS |

## 12. Cross-cutting design

### 12.1 Errors, validation and idempotency
One error shape; every input validated by Pydantic on the server and zod in forms; create endpoints accept an `Idempotency-Key` and store the response for 24 hours; updates send
`version` (or `If-Match`) and get `409 conflict` on mismatch (E-27).

### 12.2 Proposals, history and undo
```mermaid
flowchart LR
  AG["Agent, Ask, or Gmail rules"] --> PR["proposals: pending, with base_version"]
  PR --> OW{"Owner: Approve, Edit, Reject"}
  OW -- Reject --> RJ["status rejected; nothing changes"]
  OW -- Approve --> TX["One transaction: check base_version, apply change, insert events row with before and after"]
  TX --> UN["Undo: insert an inverse event if nothing blocks it; otherwise explain what blocks it (E-28)"]
```
The single exception (D-004): rules in code may apply a "clear rejection" or "clear interview invite" move directly, still through the same transaction, event row and undo.

### 12.3 Time, money and language
Stored in UTC and rupees; shown in IST with the zone named for other zones; LPA for yearly pay; English only in v1.

### 12.4 Observability
`structlog` JSON logs with a request id and a redaction filter; `run_logs` for scheduled runs; the in-app agent log reads `agent_runs` and `events`; Sentry and Langfuse are optional and receive redacted data only (NFR-OBS).

### 12.5 Configuration
One module `api/app/config.py` reads environment variables with Pydantic settings, fails at start-up with a clear message listing missing names, and exposes `check-config`.
`.env.example` lists every variable with no values. The web app reads only `NEXT_PUBLIC_*` values that are safe in a browser.

### 12.6 Offline and install
The service worker caches the shell and the last loaded read-only screens, shows an offline notice, disables actions, and never queues changes silently (E-33). A web manifest makes it installable; the same worker
receives web push (VAPID keys generated locally by the owner, D-020).

### 12.7 Performance
Today is built before the owner opens the app (the brief is a stored row), so the screen is one small read. Lists are cursor-paginated. Heavy pages (landing 3D, charts) load lazily. Target: Today under 2 seconds on a phone (NFR-PERF-01).
