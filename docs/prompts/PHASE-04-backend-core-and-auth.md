# Phase 4 — Backend core and authentication

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-04-backend-core-and-auth.md and follow it.`
> Follow `CLAUDE.md`. No commits.

## 1. Phase name and objective
**Backend core and authentication.** Build the API conventions every feature will reuse, secure
sign-in with our own JWT, user-scoped data access, and the shared "proposal → approve → history → undo"
engine. Connect the login screen so I can sign in, stay signed in, and sign out.

## 2. Context and dependencies
- Requires Phase 3 approved (login UI and app shell exist).
- Follow `docs/DATABASE_SCHEMA.md`, `docs/API_DOCUMENTATION.md`, `docs/SECURITY.md` and the login
  decision (M1). Single user at launch unless `docs/DECISIONS.md` says otherwise.

## 3. Detailed implementation tasks
1. **API conventions:** routers → services → repositories; one error shape with stable codes; request
   id on every response; cursor pagination helper; `Idempotency-Key` support for create actions (stored
   in Redis for 24 h); optimistic concurrency helper (version column, 409 `version_conflict`).
2. **Tables + migrations:** `users`, `refresh_tokens`, `proposals`, `events` (history). Emails stored
   lower-case and unique.
3. **Accounts by CLI only:** `uv run python -m app.cli create-user` (asks for email and password in the
   terminal, password at least 12 characters, refuses if a user exists unless invites were decided),
   `reset-password`, `list-sessions`, `revoke-sessions`. No public sign-up endpoint.
4. **Login** `POST /api/auth/login`: rate limit 5 per minute per IP (Redis); Argon2 verify (pwdlib),
   with a dummy hash check for unknown emails so timing does not reveal accounts; failed-attempt counter
   updated atomically in SQL; 5 failures → locked 15 minutes (423 with minutes left); on success reset
   counters, upgrade the hash if needed, issue tokens.
5. **Tokens:** access JWT HS256, 15 minutes, claims `sub, exp, iat, jti, type`, algorithm pinned on
   decode, 30-second leeway, returned in JSON and kept in memory by the browser. Refresh token: 32 random
   bytes, 7 days, stored only as a SHA-256 hash, sent as cookie `nr_refresh` (HttpOnly, Secure,
   SameSite=Strict, Path=`/api/auth`).
6. **Refresh** `POST /api/auth/refresh` (requires header `X-NxtRole: 1`): lock the token row; expired →
   401; valid → mark used, issue a new token in the same family; already used **within 10 seconds**
   (two tabs racing) → return a new access token without rotating again; used earlier or revoked → reuse
   detected → revoke the whole family, clear the cookie, 401 `session_reused`.
7. **Logout** `POST /api/auth/logout` (header required): revoke the family, clear the cookie, 204.
   `POST /api/auth/logout-all` revokes every session. `GET /api/auth/me`. `POST /api/account/password`
   (current password required; revokes other sessions).
8. **Authorization:** a `current_user` dependency on every route except health, login, refresh and
   logout; every repository method takes `user_id` and filters by it; asking for another user's record
   returns 404 (never 403, to avoid revealing it exists).
9. **Proposals and history engine:** create proposal (kind, target, payload, base_version); approve →
   apply in one transaction with a version check (409 on conflict), write an `events` row with before and
   after; reject; undo → applies the inverse of an event if the record has not changed since (else 409
   with a clear message). Generic endpoints `GET /api/proposals`, `POST /api/proposals/{id}/approve`,
   `POST /api/proposals/{id}/reject`, `POST /api/history/{event_id}/undo`, `GET /api/history`.
10. **Frontend auth:** `web/lib/api.ts` (fetch wrapper: adds the bearer token, parses the error shape,
    on 401 `token_expired` runs one shared refresh and retries once); `AuthProvider` (on load: refresh →
    me; states loading / signed-in / signed-out); `(app)` layout guard (redirect to `/login`);
    `BroadcastChannel` so logout in one tab signs out all tabs; login form wired with messages for wrong
    details, locked (minutes), too many attempts (seconds), and network down; double-submit prevented;
    Settings › Accounts shows email, "Change password", "Sign out everywhere".

## 4. UI mock references
`Login`, `MLogin` (as changed by decision M1), `Settings` / `MSettings` (Accounts section), `Nav`
(sign-out entry if present), Toast with Undo (from Phase 3) for the history engine.

## 5. Recommended technologies
FastAPI dependencies, SQLAlchemy 2 async, Alembic, PyJWT, pwdlib[argon2], redis-py, pydantic
`EmailStr`; React context, React Hook Form + zod, TanStack Query (set up its provider now).

## 6. Files and modules to create or modify
`api/app/auth/{router,service,tokens,passwords}.py`, `api/app/core/{deps,errors,pagination,idempotency,
concurrency,rate_limit}.py`, `api/app/history/{models,service,router}.py`,
`api/app/users/models.py`, `api/alembic/versions/*_auth_and_history.py`, `api/app/cli.py`,
`api/tests/auth/*`, `api/tests/history/*`, `web/lib/api.ts`, `web/lib/auth.tsx`,
`web/app/(public)/login/*`, `web/app/(app)/layout.tsx`, `web/app/(app)/settings/*` (Accounts),
`web/tests/*`.

## 7. Database and API requirements
Tables: `users`, `refresh_tokens`, `proposals`, `events`. Endpoints: login, refresh, logout, logout-all,
me, account password, proposals list/approve/reject, history list/undo. Document each in
`docs/API_DOCUMENTATION.md` with examples and error codes.

## 8. Implementation sequence
Conventions → tables and migration → CLI create-user → passwords and tokens → login → refresh with
rotation, race window and reuse detection → logout → me and account → authorization dependency →
proposals and history engine → frontend client and provider → login wiring → settings account → tests.

## 9. Testing requirements
pytest (real Postgres and Redis): login success sets the correct cookie flags; wrong password and
unknown email give the same message; lockout after 5 and unlock after the time; rate limit 429 with
`Retry-After`; parallel wrong attempts counted correctly; expired, tampered and `alg=none` tokens
rejected; refresh rotation; two-tab race within 10 s works; reuse after 10 s revokes the family;
refresh without the header → 403; logout and logout-all; another user's ids → 404; proposal approve with
stale version → 409; undo after a later change → 409. Vitest: one refresh for many parallel 401s; form
validation and error messages. Playwright: sign in, reload stays signed in, sign out, second tab signed
out too.

## 10. Edge-case checklist
- [ ] Login lockout; unlock after 15 minutes.
- [ ] Expired access token in the middle of using the app (silent refresh).
- [ ] Two tabs refreshing at the same time.
- [ ] Stolen refresh token reused.
- [ ] Redis down: login still works (rate limit skipped and logged; lockout in the database still protects).
- [ ] Double-click on "Sign in".
- [ ] Password with spaces or Unicode; email with capitals.
- [ ] Very long inputs (limits enforced before hashing).
- [ ] Clock difference between server and browser (leeway).

## 11. Security considerations
Argon2 hashing; constant-time comparisons; no account enumeration; tokens never logged; cookie scoped
to `/api/auth` with SameSite=Strict plus the custom header (CSRF); algorithm pinned; secret length
checked at startup; IDOR tests; generic error messages; sessions revoked on password change.

## 12. Acceptance criteria
- [ ] I can create my account by CLI, sign in, reload, use two tabs, and sign out everywhere.
- [ ] All tests in section 9 pass; lint, types and build pass.
- [ ] Every non-public route rejects missing or invalid tokens; cross-user access returns 404.
- [ ] Proposals, history and undo work end to end with a toast showing Undo.
- [ ] Login screen matches the approved design.

## 13. Documentation updates
`docs/API_DOCUMENTATION.md`, `docs/DATABASE_SCHEMA.md`, `docs/SECURITY.md` (auth section final),
`docs/TESTING.md` (edge-case register rows with test names), `README.md` (create your user),
`docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format. Explain: hashing vs encryption, JWT, access vs refresh tokens, cookies,
CSRF, authorization vs authentication, optimistic locking.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 5." Do not commit.
