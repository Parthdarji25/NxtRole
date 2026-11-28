# Security

Status: **Phase 1 design, 27 Nov 2026.** Inputs: PRD Appendix B (data classes), NFR-SEC, NFR-PRIV, decisions D-010, D-012, D-019 to D-039, `docs/ARCHITECTURE.md`, `docs/API_DOCUMENTATION.md`.
This is the plan. A full review (OWASP Top 10 and OWASP Top 10 for LLM applications) is done in Phase 14; controls are built and tested in the phase noted beside each one.

**What a threat model is.** A written list of who might attack the system, what they want, how they could get it, and what stops them. We write it before building so that each control is a deliberate answer to a named threat, and each threat has a test.

## 1. What we protect

| Asset | Class (PRD Appendix B) | Why it matters |
|---|---|---|
| Passwords (hashed), recovery code (hashed), access and refresh tokens | Secret | Anyone with them can act as the owner |
| MCP tokens, Gmail script key (HMAC), VAPID private key, Google refresh token, provider keys, database URL, encryption key | Secret | Control of data and accounts |
| Resume, profile facts, applications, notes, offers, interview logs, drafts | Personal | Privacy harm and career harm if leaked |
| Contacts (from the LinkedIn export), email metadata | Personal (about others) | Other people's data, never to AI |
| Jobs, companies, trust checks, scores, run logs | Internal | Low sensitivity; integrity matters |

**Who may see what.** Only the signed-in owner sees personal data, and only the owner's own rows (queries and row-level security). The AI provider sees redacted text only (identity removed), never contacts or email text. Tracing and error services see redacted data only.

## 2. Actors and trust boundaries

| Actor | Trust |
|---|---|
| The owner (signed in) | Trusted for their own data |
| An outsider on the internet | Untrusted; can reach public endpoints and the webhook and MCP endpoints with guesses |
| Authors of job posts, emails, web pages | Untrusted **content**; they can plant text that tries to steer the AI or break the page |
| AI models | Useful but **not trusted**: output is validated, never executed, and cannot write data except as a proposal |
| Third-party services (Groq, Google, Vercel, Supabase, Upstash, GitHub) | Trusted for their job; we limit what they receive |
| Another user (after invites, Later) | Untrusted for the owner's data |
| Dependencies | Untrusted until locked and audited (D-036) |

Boundaries: browser ⇄ proxy ⇄ API ⇄ database; API ⇄ AI gateway ⇄ Groq; worker ⇄ public web; Google script ⇄ webhook; MCP client ⇄ MCP server.

## 3. Decisions on the mechanics (PHASE-01 section 11)

| Topic | Decision |
|---|---|
| Password hashing | Argon2id via `argon2-cffi`: 64 MiB memory, 3 passes, 1 lane (about 0.3 s on the development laptop; re-measured on the host in Phase 15). Hashes carry their settings and are upgraded at the next sign-in. 12 to 128 characters, NFKC-normalised, no symbol rules; refused if on the NCSC common-password list (`api/app/auth/data/`), equal to the email, or made of fewer than 5 different characters. |
| Access token | Signed JWT (HS256 with a secret from the environment, `exp` 15 minutes, `sub` = user id, `jti`). Held **in memory only**, never in local or session storage, never in a cookie. |
| Refresh token | 256-bit random opaque value, **stored hashed** (SHA-256), 7-day expiry, **rotated on every use**, grouped in a family; reuse of a used token revokes the whole family (E-24). |
| Cookie | `__Secure-nr_refresh`: `HttpOnly; Secure; SameSite=Strict; Path=/api/auth; Max-Age=604800`. Browsers accept it on `127.0.0.1` for local development (checked by a browser test). |
| CSRF | The cookie is sent only to `/api/auth/*`, is `SameSite=Strict`, and refresh and logout also need the custom header `X-NxtRole-CSRF` set by our script (a cross-site form cannot add a custom header; a cross-origin script request would need CORS, which is not enabled). Every other endpoint uses the `Authorization` header, so there is no ambient credential for another site to ride. |
| Lockout | 5 wrong attempts for one email from one address lock that pair for 15 minutes; 20 for one email lock the email (D-050). Counted in Redis, with a database copy on the user row that locks at 5 if Redis is down. Unknown emails get the same answers and similar timing. Also at most 5 sign-in attempts a minute per address (`LOGIN_RATE_PER_MINUTE`). |
| Recovery | One-time recovery code (D-027), hashed, rate limited like sign-in, revokes all sessions, issues a new code. |
| Transport | HTTPS only; HSTS with a long max-age; no mixed content. |
| Encryption at rest | The host encrypts the database and storage. In addition, `refresh_token_encrypted`, `secret_encrypted` and `auth_secret` (push) use application-level AES-GCM with a key from the environment, kept separate from the database URL. |
| Secrets | Only in `.env` (local) and Vercel/GitHub secrets (production), filled in by the owner, never in git, chat or logs. CI scans for committed secrets (see 8). |
| Security headers | `Strict-Transport-Security`, `Content-Security-Policy` (default-src 'self'; no inline script except a nonce for the theme script; `frame-ancestors 'none'`; `connect-src` limited to our origin), `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` (camera, microphone, geolocation off), `Cross-Origin-Opener-Policy: same-origin`. Set in `proxy.ts` and the API. |

## 4. Threat model by area

Each row: **threat → control → test and phase**. IDs are used in `docs/TESTING.md`.

### 4.1 Authentication and sessions (STRIDE: spoofing, elevation)

| ID | Threat | Controls | Test, phase |
|---|---|---|---|
| T-AUTH-1 | Password guessing, credential stuffing | Argon2id, rate limits, lockout, same message for every failure, common-password check | Integration: lockout and message sameness, 4 |
| T-AUTH-2 | Stolen refresh token | Rotation, family revocation on reuse, httpOnly cookie, short life, sessions list with "sign out everywhere" | Reuse test, 4 |
| T-AUTH-3 | Stolen access token (for example from a script on the page) | 15-minute life, memory only, strict CSP, no HTML rendering of outside text | CSP and XSS tests, 3 and 14 |
| T-AUTH-4 | Cross-site request forgery on refresh or logout | `SameSite=Strict`, path-scoped cookie, custom header, no CORS | Cross-site request test, 4 |
| T-AUTH-5 | Account takeover through recovery | Code is 128 bits, hashed, rate limited, single use, rotated; no email channel to hijack; a new code after every use | Recovery tests, 4 |
| T-AUTH-6 | Forged or `alg: none` JWT | Fixed algorithm, key from environment, `exp` and `sub` required | Unit tests, 4 |
| T-AUTH-7 | A second public sign-up creating users | No sign-up route exists; `create-owner` only from the command line | Route list test, 4 |

### 4.2 Data access between users (IDOR, elevation)

| ID | Threat | Controls | Test, phase |
|---|---|---|---|
| T-IDOR-1 | A user reads or edits another user's record by guessing an id | `user_id` from the token only; repository filter; **row-level security** (D-039); 404 for foreign ids; UUIDs | Cross-user test on **every** endpoint and table, 4 onward |
| T-IDOR-2 | A job added by user A appears to user B | `added_by_user_id` rule in the job query | Two-user test, 6 |
| T-IDOR-3 | An export or file URL is shared | Private bucket, signed URLs of 5 minutes, bound to the file id | URL expiry test, 5 and 14 |
| T-IDOR-4 | The data tool in Ask reads other users' rows or writes | Separate database role, allow-listed views with row-level security, statement timeout, row limit, one read-only statement | Security tests, 11 and 14 |

### 4.3 Input, XSS and injection

| ID | Threat | Controls | Test, phase |
|---|---|---|---|
| T-XSS-1 | Script or markup in a job post, email, note or AI answer | All outside text stored and shown as plain text; React escapes by default; no `dangerouslySetInnerHTML`; links get `rel="noopener noreferrer"` and only `https` links are made clickable; CSP | Hostile fixtures with `<script>`, `javascript:` links, 3, 6 |
| T-INJ-1 | SQL injection | SQLAlchemy parameters only; no string-built SQL; the Ask data tool uses a read-only role | Lint rule against raw string SQL; tests, 4 |
| T-INJ-2 | Oversized or malformed input exhausting memory | Body-size limit in the proxy and API, field length limits, pagination limits, timeouts | Limit tests, 4 |
| T-INJ-3 | CSV or LaTeX injection through names (`=cmd`, `\input{}`) | CSV import reads values as text and never writes CSV back with formulas; the `.tex` export escapes every special character and never allows commands from data | E-52 tests, 10, 11 |

### 4.4 Files and uploads (D-029)

| ID | Threat | Controls | Test, phase |
|---|---|---|---|
| T-FILE-1 | A disguised or malicious file | Check the **content** (PDF signature, structure, page count), not the name; declared and real size compared; parsers run with timeouts and memory limits in the worker; no macro or embedded-file execution; file stored privately | `test_resume_text.py`, `test_files.py` (Phase 5). Memory limits arrive with the worker (KI-026) |
| T-FILE-2 | A signed upload URL reused or used for another kind | One-use URL tied to file id, content type and max size, expiring in 10 minutes | `test_an_upload_address_works_once_and_only_for_its_file` (Phase 5) |
| T-FILE-3 | PDF parser denial of service ("zip bomb" text) | Page and text limits, time limit, fail closed with a clear message | `test_resume_text.py` (Phase 5; KI-026) |
| T-FILE-4 | Leftover files after deletion | `delete_account` removes storage objects; expired exports are cleaned | Delete test, 14 |

### 4.5 AI and prompt injection (OWASP LLM Top 10)

| ID | Threat | Controls | Test, phase |
|---|---|---|---|
| T-LLM-1 | **Prompt injection** in a job post, email, web page or note ("ignore previous instructions…") | Outside text is placed in a delimited **data block**; the system part says it is data; outputs are schema-validated (Instructor); scores need **verified quotes**; the model has **no tools that write** (only proposals); least-privilege tools per agent | Injection test set run in CI, 7, 10, 11 |
| T-LLM-2 | **Data leakage to the provider** (identity, contacts, email text) | The gateway redacts name, phone, email and links; purposes forbid contacts and email text; only providers that do not train on prompts (Groq with zero data retention on); trace data redacted | Redaction tests with seeded identity, 5 |
| T-LLM-3 | **Excessive agency**: the AI changes data or sends messages | Proposal mechanism only; no send tool exists; deletes and settings are not tools; D-004 exception is code rules, not AI | Tool-list tests, 10, 11 |
| T-LLM-4 | **Insecure output handling**: AI text becomes HTML, SQL or a shell command | Never rendered as HTML, never executed; typed schema; LaTeX escaped | Tests, 10 |
| T-LLM-5 | **Invented facts** | Every claim checked against approved profile facts by a judge model and code; failures removed or flagged; pack not approvable while unchecked | Eval set, 10 |
| T-LLM-6 | **Runaway cost or loops** (agent tool loops, denial of wallet) | Step limits per agent (the finder stops after 6), token budgets per day, rate limits, timeouts | Loop tests, 10, 11 |
| T-LLM-7 | **Supply chain** of AI libraries | Own gateway, exact pins, 7-day rule, audits (D-025, D-036) | CI audit, 2 and each upgrade |
| T-LLM-8 | **Model denial** (providers down or limited) | Chain, queue as "Drafts pending", non-AI work continues | Provider-down test, 5 |

### 4.6 Fetching outside content (SSRF) (FR-046, company finder, research)

Rules every outgoing fetch of a **user- or job-supplied URL** must pass (NFR-SEC-05):

1. Scheme must be `https`. Ports 443 only (and 80 redirecting to https on the same host).
2. Resolve the name ourselves, then connect to the **resolved address**. Reject private (10/8, 172.16/12, 192.168/16), loopback, link-local (169.254/16, includes cloud metadata), carrier-grade (100.64/10), multicast, unspecified and IPv6 equivalents (`::1`, `fc00::/7`, `fe80::/10`), and IPv4-mapped IPv6.
3. Re-check **after every redirect** (maximum 3) and on the final address, to defeat DNS rebinding.
4. Limit response size (2 MB), time (8 seconds total), and content types (`text/html`, `application/json`, `application/ld+json`).
5. No cookies, no credentials, a fixed honest `User-Agent`, no forwarding of the owner's data.
6. Never log in; a login wall or block ends in "fill it in by hand" with the link kept.
7. Domains known to forbid automated reading (LinkedIn, Naukri, Indeed) are not fetched at all (D-007).
8. The same module is used by every fetcher, so there is one place to test.

Test: a table of hostile URLs (`http://169.254.169.254/`, `https://localhost`, a name that resolves to 127.0.0.1, a redirect to a private address, a 5 GB response) must all be refused. Phase 6, repeated in 10 and 14.

### 4.7 Webhook (Gmail script), MCP and other token endpoints

| ID | Threat | Controls | Test, phase |
|---|---|---|---|
| T-HOOK-1 | Forged webhook call | HMAC-SHA256 over `timestamp + "." + body` with the founder's key (encrypted at rest); constant-time compare; key id in header | Signature tests, 12 |
| T-HOOK-2 | Replay of a captured request | 5-minute timestamp window; message id uniqueness makes a repeat a no-op | Replay test (E-31), 12 |
| T-HOOK-3 | Flooding | Size limit, rate limit per key, cheap rejection before any parsing | Load test, 12, 14 |
| T-HOOK-4 | Malicious email content | Email text never stored or logged, never sent to AI in v1; rules read subject and sender domain only; the class decides the action; auto-move limited to two clear classes (D-004) | Fixture tests, 12 |
| T-MCP-1 | Stolen or leaked MCP token | Prefix `nxr_live_` so secret scanners recognise it; shown once; stored as SHA-256 hash; scopes; instant revoke; rate limit; call log; expiry optional | Token tests, 11 |
| T-MCP-2 | A tool does more than intended | Read tools only plus `save_draft_note`; never send, delete, settings or email text; schema validated | Tool allow-list test, 11 |
| T-MCP-3 | Prompt injection through MCP results | Results are data; the client's model is outside our control, so tools return **plain text fields only** and no instructions | Review, 11 |

### 4.8 Third-party integrations

| ID | Threat | Controls | Test, phase |
|---|---|---|---|
| T-OAUTH-1 | OAuth state forgery or code interception on the Calendar connection | One-time `state` bound to the session, PKCE, exact redirect URI, scope `calendar.events.owned` only, refresh token encrypted | State test, 12 |
| T-OAUTH-2 | Calendar writes to the wrong place or invites others | Events on the owner's primary calendar, **no attendees** (so no invitations), every change in History with undo | Test, 12 |
| T-PUSH-1 | Push to a stolen subscription or leak of content | Payloads carry a title and a link only; subscriptions per device, removed on sign-out, pruned when invalid | Test, 8 |
| T-SRC-1 | A job source returns hostile or huge data | Parsers validate with Pydantic, caps on size and counts, timeouts | Fixture tests, 6 |

### 4.9 Operations, secrets and supply chain

| ID | Threat | Controls | Test, phase |
|---|---|---|---|
| T-OPS-1 | Secrets committed to git | `.gitignore` for `.env*` (not `.env.example`), pre-commit and CI secret scan, `.env.example` has names only, no values anywhere in docs | CI scan, 2 |
| T-OPS-2 | A key leaks (log, screenshot, chat) | Never paste keys in chat; logs redact keys and tokens; rotation steps documented in `docs/DEPLOYMENT.md` | Log scan test, 4 |
| T-OPS-3 | Compromised dependency | Lockfiles, exact versions, `uv sync --frozen`, `pnpm install --frozen-lockfile`, 7-day rule, `pip-audit` and `pnpm audit` in CI, review install scripts, no secrets for fork builds (D-036) | CI jobs, 2 |
| T-OPS-4 | CI workflow abuse | Least-privilege `permissions:` in workflows, pinned action versions (by commit hash), no `pull_request_target` with secrets | Workflow review, 2 and 15 |
| T-OPS-5 | The database is exposed | Supabase **Data API off**; database reachable only with the owner-held URL; row-level security; the API uses a limited role; migrations use a separate role | Config check, 15 |
| T-OPS-6 | Backups leak or are lost | Backups in a private bucket, encrypted with the app key, restore tested (FR-216) | Restore drill, 15 |
| T-OPS-7 | Denial of service | Rate limits, body limits, short requests (D-038), free-tier limits as a natural cap, paged lists | Load test, 14 |
| T-OPS-8 | Sensitive data in logs and traces | Redaction filter; allow-list of logged fields; tests that grep logs for seeded identity | Log tests, 4, 14 |
| T-OPS-9 | Repudiation: "who changed this?" | `events` table with actor, before and after, never edited (only `undone_by`) | History tests, 4 |

### 4.10 Privacy (DPDP-ready)

| Control | Where |
|---|---|
| Data minimisation: no email bodies, no LinkedIn emails, no audio | Schema, FR-171, FR-188 |
| Purpose limitation and notice: privacy page lists every third party that receives data (Groq, Google, hosting) | FR-213, Phase 14 |
| Export and deletion that cover every Personal table | FR-202, FR-203 |
| Retention and clean-up | Appendix B, FR-204 |
| Consent and invite flow before other users | Later (D-003) |

## 5. Provider checklist (to complete in Phase 5; D-012, D-024)

| Item | Status |
|---|---|
| Groq: zero data retention switched on in the console (Data Controls) | **Founder to do.** Until `GROQ_ZDR_CONFIRMED_ON` is set, NxtRole sends no personal data (KI-018) |
| Groq: inputs and outputs not used for training | Read 28 Nov 2026: Services Agreement of June 2026, section 4.2, no training without permission; temporary logs up to 30 days unless zero data retention is on; processed in the United States. Section 2 says the services are not for consumer use: **founder to read** (KI-020). The data processing addendum has not been reviewed |
| Groq: free limits and model names | Models re-read from Groq's documents (D-053). The free-plan limit numbers were not visible there: defaults are used until the founder reads the Limits page (KI-019) |
| Cerebras: not used (D-024). If switched on later, terms verified first | n/a |
| Langfuse and Sentry: off until keys exist; scrubbing rules in place before enabling | Phase 12 |
| Supabase: Data API off, row-level security on, private bucket, region noted | Phase 15 |

## 6. Mapping to standard lists

**OWASP Top 10 (web).**

| Risk | Where handled |
|---|---|
| A01 Broken access control | 4.2, row-level security, cross-user tests |
| A02 Cryptographic failures | Section 3 (Argon2id, hashed tokens, AES-GCM, HTTPS) |
| A03 Injection | 4.3 |
| A04 Insecure design | This document and the PRD "never" list |
| A05 Security misconfiguration | Headers, Data API off, least privilege, config check |
| A06 Vulnerable and outdated components | 4.9 T-OPS-3, D-036 |
| A07 Identification and authentication failures | 4.1 |
| A08 Software and data integrity failures | Lockfiles, signed webhook, pinned actions |
| A09 Logging and monitoring failures | `events`, `run_logs`, redacted logs, Sentry |
| A10 Server-side request forgery | 4.6 |

**OWASP Top 10 for LLM applications.**

| Risk | Where handled |
|---|---|
| Prompt injection | T-LLM-1 |
| Sensitive information disclosure | T-LLM-2, Appendix B |
| Supply chain | T-LLM-7, D-025, D-036 |
| Data and model poisoning | Job text is treated as untrusted; evals use the owner's labels |
| Improper output handling | T-LLM-4 |
| Excessive agency | T-LLM-3 |
| System prompt leakage | Prompts hold no secrets; nothing sensitive is placed in prompts |
| Vector and embedding weaknesses | Local embeddings, per-user rows, no cross-user retrieval |
| Misinformation | T-LLM-5, claim checking, quotes |
| Unbounded consumption | T-LLM-6, budgets |

## 7. Incident basics

If a key or token may have leaked: revoke or rotate it first (MCP token revoke, Gmail key rotate, provider key regenerate, JWT secret rotate signs everyone out), then check `events`, `mcp_calls` and provider usage, then record what happened in `docs/KNOWN_ISSUES.md` with the fix. Steps per secret are in `docs/DEPLOYMENT.md`.

## 8. Controls checklist by phase

| Phase | Controls delivered |
|---|---|
| 2 | `.gitignore`, secret scan, lockfiles, pinned actions, audit jobs, config module with clear missing-variable errors |
| 3 | **Done:** content security policy with a per-request nonce (`web/src/proxy.ts`); other headers (`next.config.ts`); headers checked by a browser test (see the Phase 3 note below) |
| 4 | Auth (Argon2id, tokens, cookie, CSRF header, lockout, recovery), RLS and the cross-user test harness, error shape, idempotency, log redaction |
| 5 | **Done:** upload flow, file checks, gateway with redaction, provider checklist (founder items open: KI-018, KI-019, KI-020). See the Phase 5 note |
| 6 | SSRF-safe fetcher, source parsers with caps, trust engine |
| 7, 10, 11 | Prompt-injection test set, claim checking, proposal-only tools, Ask data role, MCP scopes |
| 8 | Push handling, notification dedupe |
| 12 | Webhook signing, Gmail rules, OAuth with PKCE |
| 13, 14 | Full security review, load test, dependency audit, export and delete verification |
| 15 | Production configuration check, backup and restore drill, rotation runbook |

## Phase 3 note: what the web app does today

- Scripts run only with the nonce of the current request. Styles allow `unsafe-inline` (the animation and toast libraries set style attributes); no outside style host is allowed.
- `upgrade-insecure-requests` is sent on HTTPS only; `unsafe-eval` in development only.
- The only `dangerouslySetInnerHTML` is the theme script in the root layout. It is a constant written by us, with no input from anyone.
- The sign-in form uses `method="post"`, so a password cannot appear in the address bar if the page script has not loaded. It sends nothing yet.
- The development showroom (`/design`) is not part of production builds.
- The search box and agent log hold nothing and call nothing.

## Phase 4 note: sign-in as built

| Control | How it works | Test |
|---|---|---|
| Access token | HS256 JWT with `sub`, `sid` (the sign-in), `type`, `jti`, `iat`, `exp`; 15 minutes; 30 seconds clock allowance; the algorithm is fixed when reading. Kept in memory in the browser | `test_passwords_and_tokens.py`, `auth.spec.ts` |
| Signing out takes effect at once | Every request checks that the token's sign-in is still alive | `test_sessions.py`, `test_account.py` |
| Refresh token | 32 random bytes, stored as SHA-256, replaced on each use. A used token is tolerated for 10 seconds (two tabs); later it ends the whole sign-in. The browser also lets one tab refresh at a time | `test_sessions.py` |
| Cross-site requests | `SameSite=Strict`, cookie path `/api/auth`, and the `X-NxtRole-CSRF` header on refresh and sign-out; no CORS | `test_sessions.py`, `test_every_route_is_protected.py` |
| One user's data | The token names the user; queries filter by it; row-level security enforces it again; other ids answer `not_found` | `test_row_level_security.py`, `test_history.py` |
| Every route protected | A test walks the API's own list of addresses | `test_every_route_is_protected.py` |
| Sign-in page | Only a path inside this site is followed after sign-in | `safeNext.test.ts`, `auth.spec.ts` |
| Screen guard | The web app hides screens from signed-out visitors for convenience; **the API is the lock** | `RequireSignIn.test.tsx` |
| Logs | No password, token, cookie or email | `test_login.py` |
| Request size | 1 MB | `test_api_rules.py` |

**Open for production (KI-014):** the local web server forwards a visitor's `X-Forwarded-For` header unchanged and adds nothing, so `TRUSTED_PROXY_COUNT` must stay 0 locally. On the hosting platform, measure what the API receives and set the value so that it is the platform's record of the visitor, never the visitor's own words.

## Phase 5 note: resumes and AI as built

| Control | How it works | Test |
|---|---|---|
| Locks before any AI call | No call without a key; no personal text without the recorded Zero Data Retention date; a personal call without an identity is a programming error | `test_gateway.py`, `test_profile.py` |
| What is hidden | Emails, phone numbers, government ID numbers and lines such as date of birth are always removed. Name, links, address and extra words as the owner confirmed on screen. A final check stops the call if anything is left | `test_privacy.py`, `test_no_ai_request_contains_name_email_or_phone`, `test_nothing_personal_is_in_any_ai_request` |
| Owner sees it first | Nothing is sent until the owner presses "Hide these and read my resume" | `ResumeSetup.test.tsx` |
| Prompt injection | Resume text sits between data tags (it cannot close them), with an instruction to ignore instructions inside; the answer must fit a strict type; a fact is kept only if its words are in the resume; the answer only becomes a suggestion | `test_gateway.py`, `test_profile_facts.py` |
| Upload address | A signed pass for one file, 10 minutes, one use; it carries no sign-in | `test_files.py`, `test_every_route_is_protected.py` |
| Files | Contents checked, not names; 5 MB, 20 pages, zip limits, 30 seconds; private folder; paths made from ids | `test_files.py`, `test_resume_text.py` |
| Logs | No resume text, prompts, answers or upload passes. The `httpx`, `groq` and `pypdf` libraries are kept at warning level because they print requests at debug level | `test_no_resume_text_reaches_the_logs`, `test_nothing_sent_or_received_reaches_the_logs_even_in_debug` |
| Stored personal data | Resume file, its text, the hidden list and the facts, each under row-level security | `test_row_level_security.py` |
| In the browser | Facts and the hidden list are kept in memory only; all text is shown as text, never as HTML | component and browser tests |
| Browser tests | A stand-in answers for Groq; uploads go to a temporary folder; no request leaves the computer | `api/tests/e2e_server.py` |

**Remember for production (Phase 15):** the upload address carries its pass in the query. NxtRole does not log queries, but a hosting platform may. The pass is useless after the upload.
