# API documentation

Status: **Phase 1 design, 27 Nov 2026.** The API is a FastAPI program (`api/`) that the web app calls through the Next.js proxy (`/api/*`).
Inputs: `docs/PRD.md` (FR-001 to FR-220), `docs/DATABASE_SCHEMA.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, decisions D-025 to D-040.
FastAPI also publishes a live, machine-written description at `/api/docs` in development (switched off in production). This document is the **design contract**: Phase 4 onwards
builds to it, and the contract tests (`api/tests/contract/`) check the real API against it.

**What an API is, in one paragraph.** An API is a menu of requests one program can make to another. The web app does not touch the database; it asks the API "give me today's brief"
or "move this card to Interview", and the API checks who is asking, applies the rules, talks to the database and answers in a fixed shape.

## 1. Overview

- Base path `/api`. The MCP server is the single exception: `/mcp`.
- JSON in, JSON out (`Content-Type: application/json`). Uploads do not pass through the API; they go to storage with a signed URL (D-029).
- Every endpoint belongs to one **module**; modules match the domain packages in `docs/ARCHITECTURE.md` section 3.
- Slow work returns **202 Accepted** with a `run_id`; the browser reads progress from `GET /api/agent-runs/{id}` (short polling) (D-038).

## 2. Conventions

| Topic | Rule |
|---|---|
| Authentication | `Authorization: Bearer <access token>` (15 minutes). The refresh cookie is sent only to `/api/auth/*` (D-032). |
| Request ids | Every response carries `X-Request-Id`; it appears in logs (without personal data). |
| Naming | Plural nouns, lower-case with hyphens in paths, `snake_case` in JSON. IDs are UUID strings. |
| Time | ISO 8601 in UTC (`2026-11-27T01:30:00Z`). Round times also carry a `tz` field (IANA name). Screens convert to IST. |
| Money | Integer rupees per year (`fixed_inr`). Original wording is kept in `*_text` fields. |
| Pagination | Cursor based: `?limit=` (default 25, max 100) and `?cursor=`. Reply: `{items: [...], next_cursor: "..." \| null}`. |
| Idempotency | Create endpoints marked "Idempotency-Key" accept the `Idempotency-Key` header. The same key and body within 24 hours returns the first answer; the same key with a different body returns `idempotency_conflict` 409 (FR-218). |
| Concurrency | Updatable records carry `version`. Send it in the body or as `If-Match: "<version>"`. A mismatch returns `conflict` 409 with the current record (E-27). |
| Undo | Changes that the owner may reverse return an `event_id`; `POST /api/events/{id}/undo` reverses it or explains what blocks it. |
| Rate limits | Responses carry `RateLimit-Limit`, `RateLimit-Remaining` and `RateLimit-Reset`. Over the limit returns `rate_limited` 429 with `Retry-After`. |
| Validation | Pydantic models reject unknown fields and wrong types with `validation_error` 422 and a `fields` list. |
| Content | Text from outside (jobs, emails, AI) is returned as plain text. Clients never render it as HTML (NFR-SEC-04). |
| Versioning | There is no `/v1` prefix while the only client is our own web app. A breaking change ships web and API together. |
| Caching | `Cache-Control: no-store` on every authenticated response. |
| CORS | Not enabled; the browser talks to the same origin through the proxy. |
| Large lists inside a record | Embedded lists are capped (for example 50 notes) with a link to the paged endpoint. |

## 3. Errors

One shape for every error (NFR-SEC-01):

```json
{ "detail": { "code": "invalid_move", "message": "A card can only move forward, one stage at a time. Move it to Applied first.", "fields": [] } }
```

`message` is written for a beginner and says what to do next. `fields` is present for 422 errors (`[{ "field": "min_salary", "message": "Enter a number of lakhs, for example 14." }]`).

| HTTP | Meaning | Typical codes |
|---|---|---|
| 400 | The request cannot be understood | `invalid_state` (OAuth), `scope_denied` |
| 401 | Not signed in, or a bad token or signature | `unauthorized`, `invalid_credentials`, `invalid_refresh`, `invalid_recovery`, `invalid_signature`, `stale_timestamp` |
| 403 | Signed in but not allowed | `csrf_missing`, `forbidden_scope` |
| 404 | Not found **or belongs to someone else** (never reveals which) | `not_found` |
| 409 | The request conflicts with the current state | `conflict`, `invalid_move`, `undo_blocked`, `already_undone`, `stale_proposal`, `duplicate_found`, `profile_not_approved`, `risky_job`, `blocked_placeholders`, `claims_unchecked`, `idempotency_conflict`, `file_not_ready` |
| 413 / 415 | Too large / wrong type | `file_too_large`, `too_large`, `unsupported_type` |
| 422 | Input failed validation | `validation_error`, `weak_password`, `invalid_url`, `blocked_url`, `bad_csv`, `not_pdf`, `no_text`, `protected_pdf`, `too_many_pages`, `confirm_required` |
| 429 | Rate limited | `rate_limited`, `account_locked` |
| 502 / 503 | A dependency failed | `fetch_failed`, `ai_unavailable` (the work is queued as "Drafts pending", FR-139) |
| 202 | Accepted, still working | body `{run_id}` or `{status: "brief_pending"}` |

## 4. Security rules that apply to every endpoint

1. **No endpoint lacks an auth rule.** Each row in the catalogue names one: public, user, refresh, webhook or mcp. The only public endpoints are the health routes (`/health`, `/api/health`, `/api/health/ready`), `POST /api/auth/login` and `POST /api/auth/recover`.
2. **User scope.** `user_id` is taken from the token, never from the request. The repository filters by it, and PostgreSQL row-level security enforces it again (D-039). Asking for another user's record returns `not_found`.
3. **Input.** Server-side validation of every field (length, range, allowed values). Strings are trimmed; HTML is never accepted or returned as HTML.
4. **Outgoing fetches** (`/api/jobs/from-link`, the company finder, research) follow the SSRF rules in `docs/SECURITY.md` section 6.
5. **Webhook** (`/api/webhooks/gmail`): HMAC-SHA256 over timestamp and body with the founder's key, 5-minute window, size limit, rate limit, idempotent by message id (D-035).
6. **MCP** (`/mcp`): bearer token starting `nxr_live_`, scopes per tool, rate limited, every call logged without payload text (D-035).
7. **Logs** never contain passwords, tokens, resume text, email text, phone numbers or request bodies of sensitive endpoints.
8. **Sign-in** is rate limited per account and per IP: 5 failures in 15 minutes lock for 15 minutes, with the same message for every failure (D-032).
9. **AI** is called only by services through the gateway; no endpoint passes raw user text to a model without redaction (D-025).
10. **Undo and history.** Every change an agent or a rule makes is a proposal or an event row with before and after values (`docs/ARCHITECTURE.md` section 12.2).

## 4a. Long-running work and progress

```
POST /api/studio/packs        -> 202 {"run_id": "…"}
GET  /api/agent-runs/{run_id} -> {"status": "running", "steps": [{"name": "Researched company", "ok": true}], "waiting_for": null}
GET  /api/agent-runs/{run_id} -> {"status": "waiting_approval", "waiting_for": "proposal", "proposal_id": "…"}
POST /api/proposals/{id}/approve
```

`status` is one of `queued`, `running`, `waiting_approval`, `done`, `failed`, `cancelled`. Steps carry names and results only, never personal text. For chat and long runs the browser may use
Server-Sent Events where the host allows it; polling every 1 to 2 seconds is the supported default.

## 5. Endpoint catalogue

Auth levels: **public** (no sign-in; rate limited where noted), **user** (`Authorization: Bearer` access token), **refresh** (httpOnly cookie plus the `X-NxtRole-CSRF` header), **webhook** (HMAC signature and timestamp), **mcp** (MCP token with a scope). Every **user** endpoint is also bound by row-level security (D-039).
The "Tables" column is the set the endpoint reads or writes; every one exists in `docs/DATABASE_SCHEMA.md` (checked).

### Health (Phase 4)

Used by the scheduler, the hosting platform and the owner.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| HEALTH-1 | `GET /health` and `GET /api/health` | public | none | `{status: "ok"}`; touches no service | - | none | Phase 2 (built) |
| HEALTH-3 | `GET /api/health/ready` | public | none | `{database: "ok", redis: "ok"}` | `not_ready` 503 with `checks` naming the failed part | none | Phase 2 (built) |
| HEALTH-2 | `GET /api/health/details` | user | none | Database, cache, last run times by kind, last backup age, queue size, estimated Actions minutes | `unauthorized` | run_logs, background_jobs | Phase 8 |

### Auth (Phase 4)

No sign-up route exists (D-027). Login answers are identical for every kind of failure.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| AUTH-1 | `POST /api/auth/login` | public (rate limited) | `{email, password}` | `{access_token, expires_in, user}` + refresh cookie | `invalid_credentials` 401, `rate_limited` 429, `account_locked` 429 | users, refresh_tokens | Phase 4 |
| AUTH-2 | `POST /api/auth/refresh` | refresh (cookie + `X-NxtRole-CSRF`) | none | New access token + new cookie | `invalid_refresh` 401, `csrf_missing` 403 | refresh_tokens | Phase 4 |
| AUTH-3 | `POST /api/auth/logout` | refresh | none | 204; cookie cleared; family revoked | `invalid_refresh` 401 | refresh_tokens | Phase 4 |
| AUTH-4 | `POST /api/auth/recover` | public (rate limited) | `{email, recovery_code, new_password}` | `{recovery_code}` (the new one, shown once) | `invalid_recovery` 401 (same for every wrong input), `rate_limited` 429, `weak_password` 422 | users, refresh_tokens | Phase 4 |

### Account and settings (Phase 4 (settings grow in later phases))

Everything under Settings > Accounts, Notifications and Privacy.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| ACCT-1 | `GET /api/me` | user | none | User, settings summary, onboarding state | `unauthorized` 401 | users, user_settings, search_preferences | Phase 4 (settings grow in later phases) |
| ACCT-2 | `GET /api/me/counts` | user | none | Badge counts for navigation (Today, Jobs, Follow-ups, Prepare, Studio, Network) | `unauthorized` | briefs, follow_ups, documents, rounds, contacts, user_job_states | Phase 8 |
| ACCT-3 | `POST /api/account/password` | user | `{current_password, new_password}` | 204; other sessions revoked | `invalid_credentials` 401, `weak_password` 422 | users, refresh_tokens | Phase 4 (settings grow in later phases) |
| ACCT-4 | `GET /api/account/sessions` | user | none | List of `{family_id, user_agent, created_at, current}` | - | refresh_tokens | Phase 4 (settings grow in later phases) |
| ACCT-5 | `DELETE /api/account/sessions/{family_id}` | user | none | 204 | `not_found` 404 | refresh_tokens | Phase 4 (settings grow in later phases) |
| ACCT-6 | `DELETE /api/account/sessions` | user | none | 204 (all other sessions) | - | refresh_tokens | Phase 4 (settings grow in later phases) |
| ACCT-7 | `POST /api/account/export` | user (Idempotency-Key) | none | 202 `{job_id}` | `rate_limited` 429 | background_jobs, files | Phase 14 |
| ACCT-8 | `GET /api/account/exports/{id}` | user | none | `{status, download_url?, expires_at}` (signed, private) | `not_found` 404 | files | Phase 14 |
| ACCT-9 | `POST /api/account/delete` | user (re-enter password) | `{password, confirm: "DELETE"}` | 202; account deleted by a job, then signed out | `invalid_credentials` 401, `confirm_required` 422 | users, background_jobs | Phase 14 |
| ACCT-10 | `GET /api/settings` | user | none | Settings: brief time, quiet hours, alert score and cap, agent switches, safety rules, template, top-N | - | user_settings | Phase 4 (settings grow in later phases) |
| ACCT-11 | `PATCH /api/settings` | user | `{fields…}` + `If-Match` version | Updated settings | `validation_error` 422, `conflict` 409 | user_settings | Phase 4 (settings grow in later phases) |
| ACCT-12 | `GET /api/settings/ai` | user | none | Provider status, model chain, allowance and reset time, 7-day usage, test-set status, "what keeps working" text data | - | ai_usage | Phase 5 |
| ACCT-13 | `GET /api/settings/privacy` | user | none | What is stored and for how long; zero-data-retention status (only if verified) | - | user_settings | Phase 14 |

### Files (Phase 5)

Uploads go straight to storage (D-029); the API issues the URL and verifies the result.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| FILES-1 | `POST /api/files/uploads` | user (Idempotency-Key) | `{kind, content_type, size}` (resume up to 5 MB; csv/offer up to 4 MB) | `{file_id, upload_url, expires_at, headers}` | `file_too_large` 413, `unsupported_type` 415 | files | Phase 5 |
| FILES-2 | `POST /api/files/{id}/complete` | user | none | `{status: "ready"}` or `{status: "rejected", reason}` | `not_pdf` 422, `no_text` 422, `protected_pdf` 422, `too_many_pages` 422, `not_found` 404 | files | Phase 5 |
| FILES-3 | `GET /api/files/{id}/download` | user | none | `{url, expires_at}` (signed, 5 minutes) | `not_found` 404 | files | Phase 5 |
| FILES-4 | `DELETE /api/files/{id}` | user | none | 204; storage object removed | `not_found` 404 | files | Phase 5 |

### Profile and preferences (Phase 5)

Facts are proposed by AI and used only after the owner approves them.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| PROF-1 | `POST /api/profile/parse` | user (Idempotency-Key) | `{file_id}` | 202 `{run_id}`; a proposed profile version is created | `profile_not_ready` 409, `file_not_ready` 409 | files, profile_versions, background_jobs | Phase 5 |
| PROF-2 | `GET /api/profile` | user | none | `{approved, proposed, diff?}` | - | profile_versions | Phase 5 |
| PROF-3 | `PATCH /api/profile/proposed` | user | `{facts: add/edit/remove}` + version | Updated proposed version | `conflict` 409, `validation_error` 422 | profile_versions, events | Phase 5 |
| PROF-4 | `POST /api/profile/approve` | user | `{version_id}` | New approved version; older one superseded; history row | `nothing_to_approve` 409 | profile_versions, events | Phase 5 |
| PROF-5 | `GET /api/profile/versions` | user | none | List of versions | - | profile_versions | Phase 5 |
| PROF-6 | `POST /api/profile/versions/{id}/restore` | user | none | New proposed version copied from an old one | `not_found` 404 | profile_versions, events | Phase 5 |
| PROF-7 | `GET /api/preferences` | user | none | Titles, places, minimum salary (rupees per year), remote preference, notice, onboarding step | - | search_preferences | Phase 5 |
| PROF-8 | `PUT /api/preferences` | user | Same fields, validated | Saved preferences | `validation_error` 422 | search_preferences, events | Phase 5 |
| PROF-9 | `GET /api/saved-answers` | user | none | List of saved answers | - | saved_answers | Phase 5 |
| PROF-10 | `PUT /api/saved-answers/{key}` | user | `{value}` | Saved answer | `validation_error` 422 | saved_answers | Phase 5 |
| PROF-11 | `POST /api/onboarding/finish` | user | none | Onboarding marked done; first brief time stated | `profile_not_approved` 409, `no_titles` 422, `no_places` 422 | search_preferences, profile_versions | Phase 5 |

### Sources and watched companies (Phase 6)

Sources are configuration rows; the owner sees health, not secrets.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| SRC-1 | `GET /api/sources` | user | none | Sources with status, last run, last error text, next retry | - | sources, run_logs | Phase 6 |
| SRC-2 | `POST /api/sources/{id}/retry` | user | none | 202; a discovery job for that source is queued | `not_found` 404, `rate_limited` 429 | background_jobs, sources | Phase 6 |
| SRC-3 | `GET /api/company-watches` | user | none | Watched companies: feed, last check, new today, latest signal, alert switch | - | company_watches, companies | Phase 6 |
| SRC-4 | `POST /api/company-watches/find` | user (Idempotency-Key) | `{name_or_url}` | 202 `{run_id}`; finder agent (public https pages only, max 6 steps) | `invalid_url` 422, `blocked_url` 422 | background_jobs, agent_runs | Phase 6 |
| SRC-5 | `POST /api/company-watches` | user | `{company_id}` (after the finder result is confirmed) | New watch; first check time | `already_watching` 409 | company_watches, companies, events | Phase 6 |
| SRC-6 | `PATCH /api/company-watches/{id}` | user | `{alerts_on?, paused?}` | Updated watch | `not_found` 404 | company_watches | Phase 6 |
| SRC-7 | `DELETE /api/company-watches/{id}` | user | none | 204 | `not_found` 404 | company_watches, events | Phase 6 |

### Jobs and trust (Phases 6 and 7)

Lists are cursor-paginated: `?cursor=&limit=` returns `{items, next_cursor}`.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| JOBS-1 | `GET /api/jobs` | user | `segment` (matches, saved, companies), `sort`, `min_score`, `posted_within`, `remote`, `q`, `cursor` | `{items, next_cursor, hidden_count, hidden_by_rules}` | `validation_error` 422 | jobs, job_scores, trust_checks, user_job_states, rules, companies | Phases 6 and 7 |
| JOBS-2 | `GET /api/jobs/{id}` | user | none | Job (plain text), fit reasons with quotes, missing skills, trust check, sightings, repost count, days open | `not_found` 404 | jobs, job_scores, trust_checks, job_sightings, companies | Phases 6 and 7 |
| JOBS-3 | `GET /api/jobs/{id}/people` | user | none | Contacts at the company (names, titles; no emails exist) | `not_found` 404 | contacts, jobs | Phase 11 |
| JOBS-4 | `POST /api/jobs` | user (Idempotency-Key) | `{title, company, location?, pay?, experience?, link?, status}` | Created job; possible duplicate offered; with `status: applied` also an application | `validation_error` 422, `duplicate_found` 409 | jobs, companies, job_sightings, applications, user_job_states | Phases 6 and 7 |
| JOBS-5 | `POST /api/jobs/from-link` | user (rate limited) | `{url}` | `{fields, filled_from}` or `{fallback: "by_hand", link_kept: true}` | `invalid_url` 422, `blocked_url` 422 (private address, login-only site), `fetch_failed` 502 | jobs | Phases 6 and 7 |
| JOBS-6 | `PUT /api/jobs/{id}/state` | user | `{saved?, skipped?, skip_reason?, hidden?}` | Updated state; history row for skip and hide (undoable) | `not_found` 404 | user_job_states, events | Phases 6 and 7 |
| JOBS-7 | `POST /api/jobs/{id}/hide-similar` | user | none | `{hidden_count}` (this job and posts sharing a contact) | `not_found` 404 | user_job_states, job_contact_keys, events | Phases 6 and 7 |
| JOBS-8 | `POST /api/jobs/{id}/keep` | user | none | Risky job kept; history row | `not_found` 404 | user_job_states, events | Phases 6 and 7 |
| JOBS-9 | `PUT /api/jobs/{id}/label` | user | `{label: good \| not_for_me}` | Saved evaluation label | `not_found` 404 | eval_labels | Phase 7 |
| JOBS-10 | `POST /api/jobs/{id}/trust-report` | user | `{rule, note?}` | 201 report | `not_found` 404 | trust_reports | Phases 6 and 7 |
| JOBS-11 | `GET /api/search` | user | `q`, `types` (jobs, companies, notes, questions) | Grouped results; "Nothing found" is an empty list | `validation_error` 422 | jobs, companies, notes, interview_logs | Phase 11 |

### Rules and memory (Phase 7)

Rules run before any AI. Suggested rules wait for the owner.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| RULES-1 | `GET /api/rules` | user | `status` (active, suggested, dismissed) | Rules with source and effect counts | - | rules | Phase 7 |
| RULES-2 | `POST /api/rules` | user | `{kind, value}` | Created rule; history row | `validation_error` 422 | rules, events | Phase 7 |
| RULES-3 | `PATCH /api/rules/{id}` | user | `{value?, status?}` (confirm, dismiss, edit) + version | Updated rule; a dismissed suggestion sets `dismissed_until` (30 days) | `conflict` 409, `not_found` 404 | rules, events | Phase 7 |
| RULES-4 | `DELETE /api/rules/{id}` | user | none | 204; history row (undoable) | `not_found` 404 | rules, events | Phase 7 |

### Today and alerts (Phase 8)

The brief is a stored row built before the owner opens the app.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| TODAY-1 | `GET /api/today` | user | none | Greeting data, top matches (up to 5), "This week", "Needs you", AI state, stale flag, hidden counts, fresh block | - | briefs, job_scores, jobs, trust_checks, rounds, applications, follow_ups, documents, user_job_states | Phase 8 |
| TODAY-2 | `GET /api/today/fresh` | user | none | Jobs posted within the last hour that meet the alert rule | - | jobs, job_scores, trust_checks, user_job_states | Phase 8 |
| TODAY-3 | `GET /api/briefs` | user | `date` | An earlier brief | `not_found` 404 | briefs | Phase 8 |
| TODAY-4 | `POST /api/today/jobs/{id}/not-today` | user | `{reason?}` | Hidden for the day; undo token | `not_found` 404 | user_job_states, events | Phase 8 |
| TODAY-5 | `GET /api/week` | user | `filter` (interview, deadline, todo) | Items for "This week" | - | rounds, applications, offers, follow_ups | Phase 8 |
| TODAY-6 | `GET /api/push/vapid-key` | user | none | Public key for web push | - | push_subscriptions | Phase 8 |
| TODAY-7 | `POST /api/push/subscriptions` | user | `{endpoint, keys}` | 201 | `validation_error` 422 | push_subscriptions | Phase 8 |
| TODAY-8 | `DELETE /api/push/subscriptions/{id}` | user | none | 204 | `not_found` 404 | push_subscriptions | Phase 8 |
| TODAY-9 | `GET /api/notifications` | user | `cursor` | Recent notifications and their status (sent, held for quiet hours, capped) | - | notifications | Phase 8 |

### Pipeline, rounds, notes and history (Phase 9)

Updates send `version`; a mismatch returns `conflict` 409 (E-27).

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| PIPE-1 | `GET /api/applications` | user | `stage`, `cursor` | Cards with next step, moved-by tag, round counts | - | applications, rounds | Phase 9 |
| PIPE-2 | `POST /api/applications` | user (Idempotency-Key) | `{job_id? or company, role, stage}` | Created card ("I applied" uses this); history row | `validation_error` 422 | applications, jobs, companies, events | Phase 9 |
| PIPE-3 | `GET /api/applications/{id}` | user | none | Card with rounds, notes, offers, history | `not_found` 404 | applications, rounds, notes, offers, events | Phase 9 |
| PIPE-4 | `PATCH /api/applications/{id}` | user | Editable fields + version | Updated card | `conflict` 409, `validation_error` 422 | applications, events | Phase 9 |
| PIPE-5 | `POST /api/applications/{id}/move` | user | `{to_stage, close_reason?}` + version | Moved card; history row; undo token | `invalid_move` 422 (not in order, no round, no offer), `conflict` 409 | applications, rounds, offers, events | Phase 9 |
| PIPE-6 | `POST /api/applications/{id}/reapply` | user | none | New linked application | `not_closed` 409 | applications, events | Phase 9 |
| PIPE-7 | `POST /api/applications/{id}/rounds` | user (Idempotency-Key) | `{kind, date, time, tz}` | Created round; calendar sync job if connected | `validation_error` 422 | rounds, events, background_jobs | Phase 9 |
| PIPE-8 | `PATCH /api/rounds/{id}` | user | `{date?, time?, tz?, status?}` + version | Updated round (reschedule, done, cancel); calendar sync job | `conflict` 409 | rounds, events, background_jobs | Phase 9 |
| PIPE-9 | `GET /api/applications/{id}/notes` | user | none | Notes list | - | notes | Phase 11 |
| PIPE-10 | `POST /api/applications/{id}/notes` | user | `{body}` (max 10,000 characters) | Created note; embedding job queued | `validation_error` 422 | notes, events, background_jobs | Phase 11 |
| PIPE-11 | `PATCH /api/notes/{id}` | user | `{body}` + version | Updated note | `conflict` 409 | notes, events | Phase 11 |
| PIPE-12 | `DELETE /api/notes/{id}` | user | none | 204; history row | `not_found` 404 | notes, events | Phase 11 |
| PIPE-13 | `GET /api/history` | user | `target_type?`, `target_id?`, `cursor` | Events newest first, with actor and note | - | events | Phase 9 |
| PIPE-14 | `POST /api/events/{id}/undo` | user | none | Inverse event applied, or `{blocked_by: [...]}` explaining what prevents it | `undo_blocked` 409, `already_undone` 409 | events, applications | Phase 9 |
| PIPE-15 | `GET /api/proposals` | user | `status` | Pending proposals with payload preview | - | proposals | Phase 9 |
| PIPE-16 | `POST /api/proposals/{id}/approve` | user | `{edited_payload?}` | Applied in one transaction with a history row | `stale_proposal` 409 (base version changed), `not_found` 404 | proposals, events, applications, rounds | Phase 9 |
| PIPE-17 | `POST /api/proposals/{id}/reject` | user | none | Rejected; nothing changed | `not_found` 404 | proposals | Phase 9 |

### Follow-ups (Phase 9)

NxtRole never sends; "mark sent" records that the owner did.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| FU-1 | `GET /api/follow-ups` | user | none | Counts and list with day, reply-time history and draft | - | follow_ups, applications, documents | Phase 9 |
| FU-2 | `POST /api/follow-ups/{id}/mark-sent` | user | none | Marked sent; next check in 7 days | `not_found` 404 | follow_ups, events | Phase 9 |
| FU-3 | `POST /api/follow-ups/{id}/replied` | user | none | Marked replied; history row | `not_found` 404 | follow_ups, applications, events | Phase 9 |
| FU-4 | `POST /api/follow-ups/{id}/snooze` | user | `{days: 3}` | Snoozed | `not_found` 404 | follow_ups | Phase 9 |
| FU-5 | `POST /api/follow-ups/{id}/close` | user | none | Application closed with reason | `not_found` 404 | follow_ups, applications, events | Phase 9 |

### Offers (Phase 9)

Pay maths runs in code from `tax_tables`, never in the AI.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| OFFER-1 | `POST /api/applications/{id}/offers` | user (Idempotency-Key) | `{fixed, variable?, bonus?, joining_bonus?, reply_by, …}` | Created offer; application moves to Offer | `validation_error` 422 | offers, applications, events | Phase 9 |
| OFFER-2 | `GET /api/offers/{id}` | user | `pf_full_basic?` | Offer, CTC parts, monthly in-hand estimate with assumptions and table year, clauses, HR questions | `not_found` 404, `tax_table_missing` 409 | offers, tax_tables | Phase 9 |
| OFFER-3 | `PATCH /api/offers/{id}` | user | Fields + version | Updated offer | `conflict` 409 | offers, events | Phase 9 |
| OFFER-4 | `POST /api/offers/{id}/letter` | user | `{file_id}` or `{text}` | 202; identity removed, clauses and HR questions drafted | `file_not_ready` 409 | offers, files, background_jobs | Phase 9 |
| OFFER-5 | `GET /api/offers/compare` | user | `ids` (2 or more) | Side-by-side comparison | `validation_error` 422 | offers, tax_tables | Phase 9 |

### Progress, coach and learning (Phases 9 and 10)

Counting is code; AI only words the advice.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| COACH-1 | `GET /api/progress/overview` | user | `days` (30 or 90) | Funnel, what is working, going cold | - | applications, events, follow_ups | Phases 9 and 10 |
| COACH-2 | `GET /api/progress/coach` | user | `week_start?` | Weekly report: groups, reply rates, "too few", one change, suggested rule | - | coach_reports, rules | Phases 9 and 10 |
| COACH-3 | `GET /api/interview-logs` | user | `improve_only?`, `company?` | Logs with questions and drafted answers | - | interview_logs | Phase 10 |
| COACH-4 | `POST /api/interview-logs` | user (Idempotency-Key) | `{company, role, date, round, outcome, questions[], said?}` | 201; draft-answers job queued | `validation_error` 422 | interview_logs, background_jobs | Phase 10 |
| COACH-5 | `PATCH /api/interview-logs/{id}` | user | Fields | Updated log | `not_found` 404 | interview_logs | Phase 10 |
| COACH-6 | `GET /api/progress/learn` | user | none | Skills missing most often, share of matches, resources, plan | - | job_scores, learning_items | Phase 10 |
| COACH-7 | `PUT /api/learning-items/{skill}` | user | `{status}` | Plan item | `validation_error` 422 | learning_items | Phase 10 |
| COACH-8 | `GET /api/progress/market` | user | none | Postings, typical pay, median for the owner's target; above or below the median | - | jobs, search_preferences | Phase 10 |

### Studio, packs and agents (Phase 10)

Slow work returns 202 and a run id; the browser polls `GET /api/agent-runs/{id}` (D-038).

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| STUDIO-1 | `GET /api/documents` | user | `status`, `kind` | Drafts needing review | - | documents, document_versions | Phase 10 |
| STUDIO-2 | `GET /api/documents/{id}` | user | none | Document with versions, checks, placeholders | `not_found` 404 | documents, document_versions | Phase 10 |
| STUDIO-3 | `PATCH /api/documents/{id}` | user | `{body parts}` + version | New version by `you` | `conflict` 409 | documents, document_versions, events | Phase 10 |
| STUDIO-4 | `POST /api/documents/{id}/rewrite` | user (Idempotency-Key) | `{tone? or part?}` | 202 `{run_id}`; result returns as a pending version the owner accepts or keeps their own | `ai_unavailable` 503 (queued as Drafts pending) | documents, background_jobs, agent_runs | Phase 10 |
| STUDIO-5 | `POST /api/documents/{id}/approve` | user | none | Approved version saved; history row | `blocked_placeholders` 409, `claims_unchecked` 409 | documents, document_versions, events | Phase 10 |
| STUDIO-6 | `POST /api/documents/{id}/mark-sent` | user | none | Marked sent (the owner sent it) | `not_approved` 409 | documents, events | Phase 10 |
| STUDIO-7 | `POST /api/documents/{id}/remind` | user | `{at}` | A reminder is queued (not a scheduled send) | `validation_error` 422 | notifications, documents | Phase 10 |
| STUDIO-8 | `POST /api/studio/packs` | user (Idempotency-Key) | `{job_id}` | 202 `{run_id, document_id}` | `risky_job` 409, `profile_not_approved` 409, `ai_unavailable` 503 | documents, agent_runs, background_jobs, jobs, trust_checks, profile_versions | Phase 10 |
| STUDIO-9 | `GET /api/agent-runs/{id}` | user | none | Status, steps so far, tool-call count, rewrites, blanks, waiting-for-approval | `not_found` 404 | agent_runs | Phase 10 |
| STUDIO-10 | `POST /api/agent-runs/{id}/cancel` | user | none | Cancelled | `not_found` 404 | agent_runs | Phase 10 |
| STUDIO-11 | `GET /api/agent-log` | user | `cursor` | What ran while the owner was away, with results, links and undo | - | agent_runs, events, run_logs | Phase 10 |

### Resume (Phase 10)

Scores and checks are code; wording help is AI through the gateway.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| RES-1 | `GET /api/resume` | user | none | Master resume from approved facts, templates, named versions | `profile_not_approved` 409 | profile_versions, documents, user_settings | Phase 10 |
| RES-2 | `POST /api/resume/tailor` | user (Idempotency-Key) | `{job_id}` | 202; tailored version with only confirmed facts | `profile_not_approved` 409 | documents, document_versions, jobs, background_jobs | Phase 10 |
| RES-3 | `GET /api/resume/keywords` | user | `job_id` | In resume, missing, suggestions | `not_found` 404 | jobs, documents, learning_items | Phase 10 |
| RES-4 | `GET /api/resume/ats` | user | `job_id?` | Score out of 100, "fix these first" list | - | documents | Phase 10 |
| RES-5 | `POST /api/resume/skills` | user | `{skill}` | A proposal to add the skill to the profile | `validation_error` 422 | proposals | Phase 10 |
| RES-6 | `POST /api/resume/export` | user (Idempotency-Key) | `{format: tex \| pdf, version_id}` | 202; file ready later (private, signed) | `blocked_placeholders` 409 | documents, files, background_jobs | Phase 10 |
| RES-7 | `POST /api/resume/parse-pdf` | user | `{file_id}` | 202; what an ATS reads | `file_not_ready` 409 | files, background_jobs | Phase 10 |

### Prepare and company briefs (Phase 10)

Every claim carries a source link and date; gaps say "Not found in any source".

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| PREP-1 | `GET /api/prepare` | user | none | Upcoming interviews from Pipeline | - | applications, rounds | Phase 10 |
| PREP-2 | `GET /api/prepare/{application_id}` | user | none | Six-section brief, plan checklist, sources, age | `not_found` 404, `brief_pending` 202 | research_briefs, applications | Phase 10 |
| PREP-3 | `POST /api/prepare/{application_id}/refresh` | user | none | 202; research job queued | `rate_limited` 429 | background_jobs, agent_runs | Phase 10 |
| PREP-4 | `GET /api/companies/{id}/brief` | user | none | Company brief and owner history | `not_found` 404 | research_briefs, companies, applications, contacts | Phase 10 |
| PREP-5 | `POST /api/companies/{id}/brief/refresh` | user | none | 202 | `rate_limited` 429 | background_jobs, agent_runs | Phase 10 |
| PREP-6 | `POST /api/mock-interviews` | user | `{application_id?, from_question?}` | Started session with 10 questions (text only) | `brief_pending` 409 | mock_interviews, research_briefs | Phase 10 |
| PREP-7 | `POST /api/mock-interviews/{id}/answer` | user | `{index, answer}` | Feedback on how it sounded and what to improve | `ai_unavailable` 503 | mock_interviews, background_jobs | Phase 10 |

### Ask NxtRole (Phase 11)

The assistant works through the proposals mechanism for any change.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| ASK-1 | `GET /api/chats` | user | none | Chats (kept 30 days) | - | chats | Phase 11 |
| ASK-2 | `POST /api/chats` | user | `{title?}` | New chat | - | chats | Phase 11 |
| ASK-3 | `GET /api/chats/{id}` | user | none | Messages with tool calls, sources, quotes and approval cards | `not_found` 404 | chats, chat_messages | Phase 11 |
| ASK-4 | `POST /api/chats/{id}/messages` | user (Idempotency-Key) | `{text}` | 202 `{run_id}` | `empty_message` 422, `ai_unavailable` 503 | chat_messages, agent_runs, background_jobs | Phase 11 |
| ASK-5 | `GET /api/chats/{id}/stream` | user | `after` message part | Server-Sent Events where supported; otherwise the same data by polling `GET /api/chats/{id}` | `not_found` 404 | chat_messages, agent_runs | Phase 11 |
| ASK-6 | `POST /api/chats/{id}/stop` | user | none | Run cancelled, partial answer kept | `not_found` 404 | agent_runs, chat_messages | Phase 11 |
| ASK-7 | `DELETE /api/chats/{id}` | user | none | 204 | `not_found` 404 | chats | Phase 11 |

### Network (Phase 11)

Contacts are never sent to AI; drafts use a `{name}` placeholder.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| NET-1 | `POST /api/contacts/import` | user | `{file_id}` (the LinkedIn CSV) | `{imported, skipped, dropped_emails}` | `bad_csv` 422, `file_not_ready` 409 | contacts, files | Phase 11 |
| NET-2 | `GET /api/contacts/matches` | user | none | Top matches that have contacts, closest closing date first | - | contacts, job_scores, jobs, companies | Phase 11 |
| NET-3 | `POST /api/contacts/{id}/referral-draft` | user | none | Draft with the name added by NxtRole, not by the AI | `ai_unavailable` 503 | documents, contacts, background_jobs | Phase 11 |
| NET-4 | `POST /api/contacts/{id}/asked` | user | `{note?}` | Asked date saved | `not_found` 404 | contacts | Phase 11 |
| NET-5 | `DELETE /api/contacts` | user | `{confirm: true}` | 204; all contacts removed | `confirm_required` 422 | contacts | Phase 11 |

### MCP tokens and server (Phase 11)

The MCP server is one endpoint (`/mcp`, Streamable HTTP, stateless). Tokens start `nxr_live_` and carry scopes (D-035).

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| MCP-1 | `GET /api/mcp/tokens` | user | none | Tokens (prefix, name, scopes, last used) | - | mcp_tokens | Phase 11 |
| MCP-2 | `POST /api/mcp/tokens` | user | `{name, scopes[]}` | The token, **shown once**; only its hash is stored | `validation_error` 422 | mcp_tokens | Phase 11 |
| MCP-3 | `DELETE /api/mcp/tokens/{id}` | user | none | 204; stops working at once | `not_found` 404 | mcp_tokens | Phase 11 |
| MCP-4 | `GET /api/mcp/calls` | user | none | Recent calls (tool, time, status; no payload) | - | mcp_calls | Phase 11 |
| MCP-5 | `GET /api/mcp/tools` | user | none | Tools shared, and the list of what is never shared | - | mcp_tokens | Phase 11 |
| MCP-6 | `POST /mcp` | mcp (bearer token + scope) | MCP messages; tools `list_jobs`, `get_job`, `get_brief`, `list_applications`, `get_prep_brief`, `search_notes`, `get_interview_log`, `save_draft_note` | MCP responses | `unauthorized` 401, `forbidden_scope` 403, `rate_limited` 429 | mcp_tokens, mcp_calls, jobs, applications, notes, interview_logs, research_briefs, briefs, documents | Phase 11 |

### Gmail script and Google Calendar (Phase 12)

The webhook is signed; no sign-in token is involved.

| ID | Method and path | Auth | Request | Response | Errors | Tables | Phase |
|---|---|---|---|---|---|---|---|
| INTEG-1 | `GET /api/integrations/gmail` | user | none | Script text (with key id, never the secret after creation), status, last run, count | - | integration_keys, inbound_emails | Phase 12 |
| INTEG-2 | `POST /api/integrations/gmail/key` | user | none | New key shown once; the old one is revoked | - | integration_keys | Phase 12 |
| INTEG-3 | `POST /api/webhooks/gmail` | webhook (HMAC-SHA256 + timestamp) | Signed JSON with `message_id`, sender domain, subject, received time, class hint | 202 | `invalid_signature` 401, `stale_timestamp` 401, `too_large` 413, `rate_limited` 429 | integration_keys, inbound_emails, background_jobs | Phase 12 |
| INTEG-4 | `GET /api/integrations/calendar` | user | none | Connection status (`connected`, `needs_reconnect`, `disconnected`) | - | oauth_connections | Phase 12 |
| INTEG-5 | `POST /api/integrations/calendar/connect` | user | none | `{authorization_url}` with a one-time `state` | - | oauth_connections | Phase 12 |
| INTEG-6 | `GET /api/integrations/calendar/callback` | user (state check) | `code`, `state` | Connection saved (refresh token encrypted); redirect to Settings | `invalid_state` 400, `scope_denied` 400 | oauth_connections, events | Phase 12 |
| INTEG-7 | `DELETE /api/integrations/calendar` | user | none | 204; tokens deleted | - | oauth_connections, events | Phase 12 |

### Background jobs and commands (no HTTP route)

| ID | Job | Detail | Tables | Phase |
|---|---|---|---|---|
| JOB-MORNING | Morning run (J1) | Section 6 of `docs/ARCHITECTURE.md` | jobs, job_sightings, trust_checks, job_scores, briefs, rules, run_logs, ai_usage, documents, notifications | Phase 8 |
| JOB-DISCOVERY | Hourly discovery and fresh-job radar (J2) | Fetch, clean, de-duplicate, trust, fresh alerts, retry Drafts pending | sources, companies, jobs, job_sightings, trust_checks, job_scores, notifications, run_logs, background_jobs | Phase 6, 8 |
| JOB-TRUST | Trust check engine (J3) | Runs on every new or changed job | trust_checks, job_contact_keys, jobs | Phase 6 |
| JOB-FOLLOWUP | Follow-up check (J4) | Day 7, 14, 21 | follow_ups, applications, documents, notifications | Phase 9 |
| JOB-RADAR | Company radar, hiring signals (J5) | Daily | company_watches, companies | Phase 8 |
| JOB-RESEARCH | Interview research agent (J6) | When a round is booked | research_briefs, agent_runs, rounds | Phase 10 |
| JOB-PACK | Application pack agent (J7) | On request and pre-draft for the top 3 High-trust jobs | documents, document_versions, agent_runs, proposals, job_scores | Phase 10 |
| JOB-EMAIL | Gmail email processing (J8) | Classify and move or propose | inbound_emails, applications, rounds, proposals, events, jobs | Phase 12 |
| JOB-NOTIFY | Notification dispatcher (J9) | Quiet hours, caps, de-duplication | notifications, push_subscriptions, user_settings | Phase 8 |
| JOB-CLEANUP | Retention clean-up (J10) | Chats, emails, exports, old text | chats, inbound_emails, files, jobs, idempotency_keys, mcp_calls, run_logs | Phase 14 |
| JOB-BACKUP | Daily backup (J11) | Dump, store, check | run_logs | Phase 15 |
| JOB-AIRETRY | AI retry queue (J12) | Drafts pending, retried at every discovery run (D-040) | background_jobs, documents, ai_usage | Phase 5, 8 |
| JOB-CALENDAR | Google Calendar sync (J13) | Create, move or remove events | rounds, oauth_connections, events | Phase 12 |
| JOB-EMBED | Embedding and index jobs | Jobs and notes | jobs, notes | Phase 7 |
| JOB-ACCOUNT | Export and delete account jobs | Whole-account export and cascade delete | files, users, background_jobs | Phase 14 |
| CLI-OWNER | Owner setup and reset commands (D-027) | `create-owner`, `reset-password`, `check-config` run on the founder's laptop | users, refresh_tokens | Phase 4 |

## 6. Traceability: every functional requirement to tables, endpoints or jobs, screens and phase

Generated from `docs/PRD.md` section 6 and the catalogue above. "Screens" uses the keys in PRD section 6.2. **212 of 220** requirements map to at least one table and one endpoint or job. **8** are front-end only (listed with the reason) and have no table or endpoint of their own.

| FR | Priority | Tables | Endpoints / jobs | Screens | Phase |
|---|---|---|---|---|---|
| FR-001 | MVP | refresh_tokens, users | AUTH-1 | S02 | Phase 4 |
| FR-002 | MVP | refresh_tokens, users | AUTH-1 | S02 | Phase 4 |
| FR-003 | MVP | refresh_tokens, users | AUTH-1, AUTH-4 | S02 | Phase 4 |
| FR-004 | MVP | refresh_tokens, users | AUTH-1, AUTH-2 | S02 | Phase 4 |
| FR-005 | MVP | refresh_tokens | AUTH-2 | S02, S04 | Phase 4 |
| FR-006 | MVP | refresh_tokens, search_preferences, user_settings, users | AUTH-1, ACCT-1 | S02 | Phase 4 |
| FR-007 | MVP | refresh_tokens, users | CLI-OWNER | S02 | Phase 4 |
| FR-008 | MVP | refresh_tokens, users | AUTH-4, CLI-OWNER | S02 | Phase 4 |
| FR-009 | MVP | refresh_tokens, users | ACCT-3, ACCT-4, ACCT-5, ACCT-6 | S20 | Phase 4 |
| FR-010 | MVP | refresh_tokens | AUTH-3 | S20, S22 | Phase 4 |
| FR-011 | MVP | refresh_tokens, search_preferences, user_settings, users | ACCT-1, AUTH-1 | S02, S04, S06, S09, S14 | Phase 4 |
| FR-012 | Later | refresh_tokens, users | AUTH-1 | S02, S20 | Phase 4 |
| FR-013 | MVP | files | FILES-1, FILES-2 | S03 | Phase 5 |
| FR-014 | MVP | background_jobs, files, profile_versions | PROF-1 | S03 | Phase 5 |
| FR-015 | MVP | background_jobs, files, profile_versions | PROF-1 | S03 | Phase 5 |
| FR-016 | MVP | events, profile_versions | PROF-2, PROF-4 | S03, S04 | Phase 5 |
| FR-017 | MVP | events, profile_versions | PROF-3, PROF-4, PROF-5, PROF-6 | S03, S20 | Phase 5 |
| FR-018 | MVP | background_jobs, files, profile_versions | PROF-1, PROF-2 | S03, S20 | Phase 5 |
| FR-019 | MVP | events, search_preferences | PROF-7, PROF-8 | S03, S20 | Phase 5 |
| FR-020 | MVP | events, search_preferences | PROF-7, PROF-8 | S03 | Phase 5 |
| FR-021 | MVP | profile_versions, search_preferences | PROF-11 | S03 | Phase 5 |
| FR-022 | MVP | events, search_preferences | PROF-7, PROF-8 | S03 | Phase 5 |
| FR-023 | MVP | background_jobs, files, users | FILES-1, FILES-4, ACCT-9 | S03, N4 | Phase 5 |
| FR-024 | MVP | saved_answers | PROF-9, PROF-10 | S15, S14 | Phase 5 |
| FR-025 | MVP | background_jobs, companies, job_scores, job_sightings, jobs, notifications, run_logs, sources, trust_checks | SRC-1, JOB-DISCOVERY | S21, S03, J2 | Phase 6 |
| FR-026 | MVP | run_logs, sources | SRC-1 | S21 | Phase 6 |
| FR-027 | MVP | run_logs, sources | SRC-1 | S03 | Phase 6 |
| FR-028 | MVP | agent_runs, background_jobs, companies, company_watches, events | SRC-4, SRC-5 | S21 | Phase 6 |
| FR-029 | MVP | companies, company_watches, events | SRC-3, SRC-7 | S21 | Phase 6 |
| FR-030 | MVP | background_jobs, companies, job_scores, job_sightings, jobs, notifications, run_logs, sources, trust_checks | JOB-DISCOVERY | J2, J1 | Phase 6 |
| FR-031 | MVP | background_jobs, run_logs, sources | SRC-1, SRC-2 | S06 | Phase 6 |
| FR-032 | MVP | run_logs, sources | SRC-1 | S21, S20 | Phase 6 |
| FR-033 | MVP | background_jobs, companies, job_scores, job_sightings, jobs, notifications, run_logs, sources, trust_checks | JOB-DISCOVERY | J2 | Phase 6 |
| FR-034 | MVP | companies, company_watches | JOB-RADAR, SRC-3 | J5, S06, S21, SH2 | Phase 6 |
| FR-035 | Later | companies, job_scores, jobs, rules, trust_checks, user_job_states | JOBS-1 | S06 | Phase 6 |
| FR-036 | MVP | companies, job_scores, jobs, rules, trust_checks, user_job_states | JOBS-1 | S06 | Phases 6 and 7 |
| FR-037 | MVP | companies, job_scores, jobs, rules, trust_checks, user_job_states | JOBS-1 | S06 | Phases 6 and 7 |
| FR-038 | MVP | companies, job_scores, jobs, rules, trust_checks, user_job_states | JOBS-1 | S06 | Phases 6 and 7 |
| FR-039 | MVP | companies, job_scores, job_sightings, jobs, trust_checks | JOBS-2 | S06, S07 | Phases 6 and 7 |
| FR-040 | MVP | companies, company_watches, job_scores, job_sightings, jobs, trust_checks | JOBS-2, SRC-6 | S06, S13 | Phases 6 and 7 |
| FR-041 | MVP | contacts, jobs | JOBS-3 | S06, S19 | Phases 6 and 7 |
| FR-042 | MVP | background_jobs, companies, job_scores, job_sightings, jobs, notifications, run_logs, sources, trust_checks | JOB-DISCOVERY, JOBS-2 | S06, S07 | Phases 6 and 7 |
| FR-043 | MVP | background_jobs, companies, job_scores, job_sightings, jobs, notifications, run_logs, sources, trust_checks | JOB-DISCOVERY, JOBS-2 | S06, J2 | Phases 6 and 7 |
| FR-044 | MVP | background_jobs, companies, job_scores, job_sightings, jobs, notifications, run_logs, sources, trust_checks | JOB-DISCOVERY, JOBS-2 | S07, J2 | Phases 6 and 7 |
| FR-045 | MVP | applications, companies, job_sightings, jobs, user_job_states | JOBS-4 | S06 | Phases 6 and 7 |
| FR-046 | MVP | jobs | JOBS-5 | S06 | Phases 6 and 7 |
| FR-047 | MVP | applications, companies, job_sightings, jobs, user_job_states | JOBS-4, JOBS-5 | S06, S09 | Phases 6 and 7 |
| FR-048 | MVP | events, user_job_states | JOBS-6 | S06, S07, S04 | Phases 6 and 7 |
| FR-049 | MVP | companies, job_scores, job_sightings, jobs, trust_checks | JOBS-2 | S06, S07 | Phases 6 and 7 |
| FR-050 | MVP | companies, job_scores, jobs, rules, trust_checks, user_job_states | JOBS-1 | S06 | Phases 6 and 7 |
| FR-051 | Later | applications, companies, job_sightings, jobs, user_job_states | JOBS-4 | S06 | Phases 6 and 7 |
| FR-052 | MVP | companies, job_contact_keys, job_scores, job_sightings, jobs, rules, trust_checks, user_job_states | JOB-TRUST, JOBS-1, JOBS-2 | S07, S06, S04, S05, J3 | Phase 6 |
| FR-053 | MVP | job_contact_keys, jobs, trust_checks | JOB-TRUST | J3, S07 | Phase 6 |
| FR-054 | MVP | job_contact_keys, jobs, trust_checks | JOB-TRUST | J3 | Phase 6 |
| FR-055 | MVP | companies, job_scores, job_sightings, jobs, trust_checks | JOBS-2 | S07 | Phase 6 |
| FR-056 | MVP | agent_runs, ai_usage, background_jobs, briefs, documents, job_scores, job_sightings, jobs, notifications, profile_versions, rules, run_logs, trust_checks | JOB-MORNING, STUDIO-8 | S07, J3, J7 | Phase 6 |
| FR-057 | MVP | events, job_contact_keys, user_job_states | JOBS-7 | S07 | Phase 6 |
| FR-058 | MVP | events, user_job_states | JOBS-8 | S07 | Phase 6 |
| FR-059 | MVP | trust_reports | JOBS-10 | S07 | Phase 6 |
| FR-060 | MVP | user_settings | ACCT-10, ACCT-11 | S20 | Phase 6 |
| FR-061 | MVP | companies, job_scores, job_sightings, jobs, trust_checks | JOBS-2 | S07 | Phase 6 |
| FR-062 | MVP | ai_usage, briefs, documents, job_contact_keys, job_scores, job_sightings, jobs, notifications, rules, run_logs, trust_checks | JOB-TRUST, JOB-MORNING | J3, J1 | Phase 6 |
| FR-063 | MVP | ai_usage, briefs, documents, job_scores, job_sightings, jobs, notifications, rules, run_logs, trust_checks | JOB-MORNING, RULES-1 | J1, S06 | Phase 7 |
| FR-064 | MVP | ai_usage, briefs, documents, job_scores, job_sightings, jobs, notes, notifications, rules, run_logs, trust_checks | JOB-MORNING, JOB-EMBED | J1 | Phase 7 |
| FR-065 | MVP | ai_usage, briefs, documents, job_scores, job_sightings, jobs, notifications, rules, run_logs, trust_checks | JOB-MORNING | J1, S07 | Phase 7 |
| FR-066 | MVP | companies, job_scores, job_sightings, jobs, trust_checks | JOBS-2 | S07 | Phase 7 |
| FR-067 | MVP | companies, job_scores, job_sightings, jobs, rules, trust_checks, user_job_states | JOBS-1, JOBS-2 | S06, S07 | Phase 7 |
| FR-068 | MVP | ai_usage, background_jobs, briefs, documents, job_scores, job_sightings, jobs, notifications, rules, run_logs, trust_checks | JOB-MORNING, JOB-AIRETRY | J1, J12, S06 | Phase 7 |
| FR-069 | MVP | eval_labels | JOBS-9 | S06, S07, J1 | Phase 7 |
| FR-070 | MVP | ai_usage, briefs, documents, job_scores, job_sightings, jobs, notifications, rules, run_logs, trust_checks | JOB-MORNING | J1, J7 | Phase 7 |
| FR-071 | MVP | rules | RULES-1 | S21 | Phase 7 |
| FR-072 | MVP | events, rules | RULES-1, RULES-3 | S21, S18 | Phase 7 |
| FR-073 | MVP | events, rules | RULES-3 | S21 | Phase 7 |
| FR-074 | MVP | applications, events, rules | RULES-2, RULES-3, RULES-4, PIPE-14 | S21 | Phase 7 |
| FR-075 | MVP | ai_usage, briefs, companies, documents, job_scores, job_sightings, jobs, notifications, rules, run_logs, trust_checks, user_job_states | JOB-MORNING, JOBS-1 | S21, S06 | Phase 7 |
| FR-076 | MVP | applications, briefs, documents, follow_ups, job_scores, jobs, rounds, trust_checks, user_job_states | TODAY-1 | S04 | Phase 8 |
| FR-077 | MVP | ai_usage, applications, briefs, documents, follow_ups, job_scores, job_sightings, jobs, notifications, rounds, rules, run_logs, trust_checks, user_job_states | JOB-MORNING, TODAY-1 | J1, S04 | Phase 8 |
| FR-078 | MVP | applications, follow_ups, offers, rounds | TODAY-5 | S04 | Phase 8 |
| FR-079 | MVP | applications, briefs, documents, follow_ups, job_scores, jobs, rounds, trust_checks, user_job_states | TODAY-1 | S04, S10, S19, S14 | Phase 8 |
| FR-080 | MVP | agent_runs, applications, background_jobs, companies, documents, events, jobs, profile_versions, trust_checks | PIPE-2, STUDIO-8 | S04, S15, S09 | Phase 8 |
| FR-081 | MVP | events, user_job_states | TODAY-4 | S04 | Phase 8 |
| FR-082 | MVP | ai_usage, applications, briefs, documents, follow_ups, job_scores, jobs, rounds, trust_checks, user_job_states | TODAY-1, ACCT-12 | S04, S20 | Phase 8 |
| FR-083 | MVP | applications, briefs, documents, follow_ups, job_scores, jobs, rounds, trust_checks, user_job_states | TODAY-2, TODAY-1 | S04 | Phase 8 |
| FR-084 | MVP | job_scores, jobs, trust_checks, user_job_states | TODAY-2 | S05 | Phase 8 |
| FR-085 | MVP | applications, briefs, documents, follow_ups, job_scores, jobs, rounds, trust_checks, user_job_states | TODAY-1 | S04 | Phase 8 |
| FR-086 | MVP | applications, briefs, documents, follow_ups, job_scores, jobs, rounds, trust_checks, user_job_states | TODAY-1 | S04 | Phase 8 |
| FR-087 | MVP | briefs | TODAY-3 | J1 | Phase 8 |
| FR-088 | MVP | push_subscriptions | TODAY-6, TODAY-7 | S21, S20 | Phase 8 |
| FR-089 | MVP | background_jobs, companies, job_scores, job_sightings, jobs, notifications, push_subscriptions, run_logs, sources, trust_checks, user_settings | JOB-DISCOVERY, JOB-NOTIFY | J9, J2 | Phase 8 |
| FR-090 | MVP | applications, documents, follow_ups, notifications, push_subscriptions, user_settings | JOB-NOTIFY, JOB-FOLLOWUP | J9, J4 | Phase 8 |
| FR-091 | MVP | user_settings | ACCT-10, ACCT-11 | S20, S21 | Phase 8 |
| FR-092 | MVP | notifications, push_subscriptions, user_settings | JOB-NOTIFY | J9 | Phase 8 |
| FR-093 | MVP | notifications | TODAY-9 | S05, S10, S09 | Phase 8 |
| FR-094 | MVP | company_watches | SRC-6 | S06, S21 | Phase 8 |
| FR-095 | MVP | push_subscriptions | TODAY-7, TODAY-8 | J9, N4 | Phase 8 |
| FR-096 | Later | notifications, push_subscriptions, user_settings | JOB-NOTIFY | S20 | Phase 8 |
| FR-097 | MVP | applications, rounds | PIPE-1 | S09 | Phase 9 |
| FR-098 | MVP | applications, events, offers, rounds | PIPE-5 | S09 | Phase 9 |
| FR-099 | MVP | applications, events | PIPE-14, PIPE-13 | S09 | Phase 9 |
| FR-100 | MVP | applications, events | PIPE-6 | S09 | Phase 9 |
| FR-101 | MVP | background_jobs, events, rounds | PIPE-7, PIPE-8 | S09 | Phase 9 |
| FR-102 | MVP | applications, events, notes, offers, rounds | PIPE-3, PIPE-13 | S09 | Phase 9 |
| FR-103 | MVP | applications, events, inbound_emails, jobs, proposals, rounds | PIPE-1, JOB-EMAIL | S09, J8 | Phase 9 |
| FR-104 | MVP | applications, events, offers, rounds | PIPE-4, PIPE-5 | S09 | Phase 9 |
| FR-105 | MVP | applications, events, offers | OFFER-1 | S09, S11 | Phase 9 |
| FR-106 | MVP | applications, events, notes, offers, rounds | PIPE-1, PIPE-3 | S09 | Phase 9 |
| FR-107 | MVP | applications, events, notes, offers, rounds | PIPE-1, PIPE-3 | S09 | Phase 9 |
| FR-108 | MVP | applications, documents, follow_ups | FU-1 | S10 | Phase 9 |
| FR-109 | MVP | applications, documents, follow_ups, notifications | JOB-FOLLOWUP | J4, S10 | Phase 9 |
| FR-110 | MVP | applications, documents, follow_ups, notifications | JOB-FOLLOWUP, FU-1 | S10, J4 | Phase 9 |
| FR-111 | MVP | applications, events, follow_ups | FU-2, FU-3, FU-4, FU-5 | S10 | Phase 9 |
| FR-112 | MVP | applications, documents, follow_ups | FU-1 | S10 | Phase 9 |
| FR-113 | MVP | ai_usage, applications, background_jobs, documents, follow_ups | FU-1, JOB-AIRETRY | S10, J12 | Phase 9 |
| FR-114 | MVP | applications, events, offers | OFFER-1, OFFER-3 | S09, S11 | Phase 9 |
| FR-115 | MVP | offers, tax_tables | OFFER-2 | S11 | Phase 9 |
| FR-116 | MVP | offers, tax_tables | OFFER-2 | S11 | Phase 9 |
| FR-117 | MVP | background_jobs, files, offers | OFFER-4 | S11 | Phase 9 |
| FR-118 | MVP | background_jobs, files, offers, tax_tables | OFFER-2, OFFER-4 | S11 | Phase 9 |
| FR-119 | MVP | offers, tax_tables | OFFER-5 | S09, S11, S14 | Phase 9 |
| FR-120 | MVP | applications, follow_ups, notifications, offers, push_subscriptions, rounds, user_settings | TODAY-5, JOB-NOTIFY | S04, J9 | Phase 9 |
| FR-121 | MVP | applications, events, follow_ups | COACH-1 | S17 | Phases 9 and 10 |
| FR-122 | MVP | coach_reports, rules | COACH-2 | S18 | Phases 9 and 10 |
| FR-123 | MVP | coach_reports, events, rules | COACH-2, RULES-2 | S18, S21 | Phases 9 and 10 |
| FR-124 | MVP | background_jobs, interview_logs | COACH-3, COACH-4, COACH-5 | S17 | Phases 9 and 10 |
| FR-125 | MVP | job_scores, learning_items | COACH-6, COACH-7 | S17, S16 | Phases 9 and 10 |
| FR-126 | MVP | jobs, search_preferences | COACH-8 | S17 | Phases 9 and 10 |
| FR-127 | MVP | interview_logs | COACH-3 | S17, S12 | Phases 9 and 10 |
| FR-128 | MVP | document_versions, documents | STUDIO-1, STUDIO-2 | S14 | Phase 10 |
| FR-129 | MVP | agent_runs, background_jobs, document_versions, documents, events | STUDIO-3, STUDIO-4 | S14 | Phase 10 |
| FR-130 | MVP | document_versions, documents, events, notifications | STUDIO-5, STUDIO-6, STUDIO-7 | S14, S15 | Phase 10 |
| FR-131 | MVP | agent_runs, background_jobs, document_versions, documents, job_scores, jobs, profile_versions, proposals, trust_checks | STUDIO-8, JOB-PACK | S15, J7 | Phase 10 |
| FR-132 | MVP | agent_runs, background_jobs, document_versions, documents, jobs, profile_versions, trust_checks | STUDIO-2, STUDIO-8 | S15 | Phase 10 |
| FR-133 | MVP | agent_runs | STUDIO-9 | S15 | Phase 10 |
| FR-134 | MVP | applications, companies, document_versions, documents, events, jobs | STUDIO-5, PIPE-2 | S15, S09 | Phase 10 |
| FR-135 | MVP | agent_runs, ai_usage, briefs, document_versions, documents, job_scores, job_sightings, jobs, notifications, proposals, rules, run_logs, trust_checks | JOB-PACK, JOB-MORNING | J7, J1 | Phase 10 |
| FR-136 | MVP | agent_runs, document_versions, documents, job_scores, proposals | STUDIO-9, STUDIO-10, JOB-PACK | J7, J6, S15 | Phase 10 |
| FR-137 | MVP | agent_runs, events, run_logs | STUDIO-11 | SH2, S20 | Phase 10 |
| FR-138 | MVP | applications, events, proposals, rounds | PIPE-15, PIPE-16, PIPE-17 | S04, S09, S14, S15, S08 | Phase 10 |
| FR-139 | MVP | ai_usage, background_jobs, documents | JOB-AIRETRY | J12, S14, S04 | Phase 10 |
| FR-140 | MVP | documents, profile_versions, user_settings | RES-1 | S16 | Phase 10 |
| FR-141 | MVP | background_jobs, document_versions, documents, jobs | RES-2 | S16 | Phase 10 |
| FR-142 | MVP | documents, jobs, learning_items, proposals | RES-3, RES-5 | S16, S17 | Phase 10 |
| FR-143 | MVP | documents | RES-4 | S16 | Phase 10 |
| FR-144 | MVP | background_jobs, files | RES-7 | S16 | Phase 10 |
| FR-145 | MVP | background_jobs, documents, files | RES-6 | S16, S14 | Phase 10 |
| FR-146 | MVP | documents, profile_versions, user_settings | RES-1 | S16 | Phase 10 |
| FR-147 | Later | background_jobs, documents, files | RES-6 | S16 | Phase 10 |
| FR-148 | MVP | applications, rounds | PREP-1 | N1, SH1, SH3 | Phase 10 |
| FR-149 | MVP | agent_runs, research_briefs, rounds | JOB-RESEARCH | J6, S12 | Phase 10 |
| FR-150 | MVP | applications, research_briefs | PREP-2 | S12 | Phase 10 |
| FR-151 | MVP | applications, research_briefs | PREP-2 | S12, S13 | Phase 10 |
| FR-152 | MVP | applications, research_briefs | PREP-2 | S12 | Phase 10 |
| FR-153 | MVP | applications, companies, contacts, research_briefs | PREP-4 | S13 | Phase 10 |
| FR-154 | MVP | agent_runs, background_jobs | PREP-3, PREP-5 | S13, J6 | Phase 10 |
| FR-155 | MVP | background_jobs, mock_interviews, research_briefs | PREP-6, PREP-7 | S12 | Phase 10 |
| FR-156 | MVP | background_jobs, mock_interviews, research_briefs | PREP-6, PREP-7 | S12 | Phase 10 |
| FR-157 | MVP | agent_runs, research_briefs, rounds | JOB-RESEARCH | J6, S13 | Phase 10 |
| FR-158 | Later | background_jobs, mock_interviews, research_briefs | PREP-6, PREP-7 | S12 | Phase 10 |
| FR-159 | MVP | agent_runs, background_jobs, chat_messages, chats | ASK-3, ASK-4, ASK-5 | S08 | Phase 11 |
| FR-160 | MVP | applications, chat_messages, chats, events, proposals, rounds | PIPE-16, ASK-3 | S08 | Phase 11 |
| FR-161 | MVP | agent_runs, background_jobs, chat_messages | ASK-4 | S08 | Phase 11 |
| FR-162 | MVP | chat_messages, chats, files, idempotency_keys, inbound_emails, jobs, mcp_calls, run_logs | ASK-1, ASK-2, ASK-3, ASK-7, JOB-CLEANUP | S08, J10 | Phase 11 |
| FR-163 | MVP | agent_runs, background_jobs, chat_messages | ASK-4, ASK-6 | S08 | Phase 11 |
| FR-164 | MVP | agent_runs, background_jobs, chat_messages | ASK-4 | S08 | Phase 11 |
| FR-165 | MVP | agent_runs, background_jobs, chat_messages | ASK-4 | S08 | Phase 11 |
| FR-166 | MVP | agent_runs, background_jobs, chat_messages | ASK-4 | S08 | Phase 11 |
| FR-167 | MVP | background_jobs, events, notes | PIPE-9, PIPE-10, PIPE-11, PIPE-12 | S09 | Phase 11 |
| FR-168 | MVP | companies, interview_logs, jobs, notes | JOBS-11 | SH2, S09 | Phase 11 |
| FR-169 | MVP | agent_runs, applications, background_jobs, briefs, chat_messages, documents, interview_logs, jobs, mcp_calls, mcp_tokens, notes, research_briefs | MCP-6, ASK-4 | S08, S20 | Phase 11 |
| FR-170 | MVP | events | PIPE-13 | S09 | Phase 11 |
| FR-171 | MVP | contacts, files | NET-1 | S19 | Phase 11 |
| FR-172 | MVP | contacts, files | NET-1 | S19 | Phase 11 |
| FR-173 | MVP | companies, contacts, job_scores, jobs | NET-2 | S19, S06 | Phase 11 |
| FR-174 | MVP | background_jobs, contacts, documents | NET-3 | S19 | Phase 11 |
| FR-175 | MVP | companies, contacts, job_scores, jobs | NET-2, NET-4 | S19, S13 | Phase 11 |
| FR-176 | MVP | contacts, files | NET-1, NET-5 | S19, N4 | Phase 11 |
| FR-177 | MVP | background_jobs, contacts, documents | NET-3 | S19 | Phase 11 |
| FR-178 | MVP | mcp_tokens | MCP-1, MCP-2, MCP-3 | S20 | Phase 11 |
| FR-179 | MVP | applications, briefs, documents, interview_logs, jobs, mcp_calls, mcp_tokens, notes, research_briefs | MCP-6 | S20 | Phase 11 |
| FR-180 | MVP | mcp_tokens | MCP-5 | S20 | Phase 11 |
| FR-181 | MVP | mcp_calls | MCP-4 | S20 | Phase 11 |
| FR-182 | MVP | mcp_tokens | MCP-5 | S20 | Phase 11 |
| FR-183 | MVP | applications, briefs, documents, interview_logs, jobs, mcp_calls, mcp_tokens, notes, research_briefs | MCP-3, MCP-6 | S20 | Phase 11 |
| FR-184 | MVP | inbound_emails, integration_keys | INTEG-1 | S03, S20 | Phase 12 |
| FR-185 | MVP | inbound_emails, integration_keys | INTEG-1 | S03, S20 | Phase 12 |
| FR-186 | MVP | inbound_emails, integration_keys | INTEG-1, INTEG-2 | S20 | Phase 12 |
| FR-187 | MVP | background_jobs, inbound_emails, integration_keys | INTEG-3 | J8 | Phase 12 |
| FR-188 | MVP | applications, background_jobs, events, inbound_emails, integration_keys, jobs, proposals, rounds | INTEG-3, JOB-EMAIL | J8 | Phase 12 |
| FR-189 | MVP | applications, events, inbound_emails, jobs, proposals, rounds | JOB-EMAIL | J8, S09 | Phase 12 |
| FR-190 | MVP | applications, events, inbound_emails, jobs, proposals, rounds | JOB-EMAIL | J8, S09 | Phase 12 |
| FR-191 | MVP | applications, events, inbound_emails, jobs, proposals, rounds | JOB-EMAIL | J8, S07 | Phase 12 |
| FR-192 | MVP | events, oauth_connections, rounds | INTEG-4, INTEG-5, INTEG-6, INTEG-7, JOB-CALENDAR | S20, J13, S09 | Phase 12 |
| FR-193 | MVP | events, oauth_connections, rounds | JOB-CALENDAR, INTEG-6 | J13, S20 | Phase 12 |
| FR-194 | MVP | user_settings | ACCT-10 | S20, S21, S22 | Phases 4 to 14 |
| FR-195 | MVP | search_preferences, user_settings | ACCT-10, ACCT-11, PROF-7 | S20 | Phases 4 to 14 |
| FR-196 | MVP | user_settings | ACCT-10 | S20 | Phases 4 to 14 |
| FR-197 | MVP | ai_usage | ACCT-12 | S20, S04 | Phases 4 to 14 |
| FR-198 | MVP | ai_usage | ACCT-12 | S20 | Phases 4 to 14 |
| FR-199 | MVP | user_settings | ACCT-13 | S20, N2 | Phases 4 to 14 |
| FR-200 | MVP | user_settings | ACCT-10, ACCT-11 | S20 | Phases 4 to 14 |
| FR-201 | MVP | refresh_tokens, search_preferences, user_settings, users | ACCT-1, ACCT-3, ACCT-4 | S20, N4 | Phases 4 to 14 |
| FR-202 | MVP | background_jobs, files, users | ACCT-7, ACCT-8, FILES-3, JOB-ACCOUNT | N4 | Phases 4 to 14 |
| FR-203 | MVP | background_jobs, files, users | ACCT-9, JOB-ACCOUNT | N4 | Phases 4 to 14 |
| FR-204 | MVP | chats, files, idempotency_keys, inbound_emails, jobs, mcp_calls, run_logs | JOB-CLEANUP | J10, S20 | Phases 4 to 14 |
| FR-205 | MVP | (none) | UI only: Theme is remembered on the device (`nxtrole-theme`); no server data | SH1, S22 | Phases 4 to 14 |
| FR-206 | MVP | user_settings | ACCT-10, ACCT-11 | S20, S21 | Phases 4 to 14 |
| FR-207 | MVP | ai_usage | ACCT-12 | S20, S02, S01 | Phases 4 to 14 |
| FR-208 | MVP | briefs, contacts, documents, follow_ups, rounds, user_job_states | ACCT-2 | S22 | Phases 4 to 14 |
| FR-209 | MVP | briefs, contacts, documents, follow_ups, rounds, user_job_states | ACCT-2 | SH1, SH3 | Phases 3, 4 and 8 |
| FR-210 | MVP | briefs, contacts, documents, follow_ups, rounds, user_job_states | ACCT-2 | SH3 | Phases 3, 4 and 8 |
| FR-211 | MVP | companies, interview_logs, jobs, notes | JOBS-11 | SH2 | Phases 3, 4 and 8 |
| FR-212 | MVP | (none) | UI only: Public landing page; no data | S01 | Phases 3, 4 and 8 |
| FR-213 | MVP | (none) | UI only: Public legal pages; no data | N2, S01, S02 | Phases 3, 4 and 8 |
| FR-214 | MVP | (none) | UI only: Service worker and offline page; reads cached screens only | N3 | Phases 3, 4 and 8 |
| FR-215 | MVP | (none) | UI only: Web app manifest; no data | SH3, S21 | Phases 3, 4 and 8 |
| FR-216 | MVP | run_logs | JOB-BACKUP | J11 | Phases 3, 4 and 8 |
| FR-217 | MVP | (none) | UI only: Front-end states (loading, empty, error); no data of their own | SH4, S04, S06, S09 | Phases 3, 4 and 8 |
| FR-218 | MVP | applications, companies, events, idempotency_keys, jobs | PIPE-2 | S06, S09 | Phases 3, 4 and 8 |
| FR-219 | MVP | (none) | UI only: Display rules (IST, rupees, LPA); data is stored in UTC and rupees everywhere | S04, S09, S11 | Phases 3, 4 and 8 |
| FR-220 | MVP | (none) | UI only: Front-end accessibility; no data | SH4, SH1, SH3 | Phases 3, 4 and 8 |

## 7. Traceability check results

| Check | Result |
|---|---|
| Endpoints in the catalogue | 151 (+ 16 background jobs and commands) |
| Every endpoint has an auth rule | Yes (151 of 151) |
| Every table named by an endpoint or job exists in `docs/DATABASE_SCHEMA.md` | Yes (50 tables in the schema) |
| Every FR maps to a table and an endpoint or job | 212 of 220; the other 8 are front-end only (reason given) |
| Every endpoint is used by at least one FR (health excepted) | Yes |
| Every table is used by an endpoint or job | Yes |
| Every screen has FRs (PRD Appendix C) | Yes |
