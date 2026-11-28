# Testing

Status: **Phase 1 design, 27 Nov 2026.** Inputs: `docs/ROADMAP.md` G, `docs/PRD.md` (Appendix A edge cases, NFRs), `docs/SECURITY.md` (threat tests), `docs/TECH_STACK.md`.
Phase 2 builds the test tooling; every phase adds its tests; Phase 13 runs the full suite.

**What a test is.** A small program that runs part of NxtRole with known input and checks the result. "A feature that compiles is not done" (CLAUDE.md section 6): a feature is done when its tests ran and passed.

## 1. Test layers

| Layer | Tool | What it proves | Real services? | When it runs |
|---|---|---|---|---|
| Unit (Python) | pytest | One function: salary parsing, trust rules, token rotation, quote check, redaction, stage order, tax maths | No | Every task, every push |
| Integration (API + database) | pytest + pytest-asyncio, real PostgreSQL (with pgvector) and Redis in Docker | Router + service + repository + migrations, row-level security, locks, queue | **Yes**, never mocks of the database | Every API task, every push |
| Contract | pytest (checks real responses against `docs/API_DOCUMENTATION.md` shapes and the OpenAPI file) | The API still matches its documented contract | Yes | Every push |
| Component (web) | Vitest + Testing Library | Each screen part: states (loading, empty, error, success), keyboard, labels | No | Every UI task |
| End to end | Playwright (Chromium, Firefox, WebKit; desktop 1440 and phone 390 sizes) | Whole journeys as a user (UJ-1 to UJ-9) | Yes (app, API, database) | End of each feature phase; full suite in Phase 13 |
| Visual | Playwright full-page screenshots compared with approved pictures of the app (checked against the mocks by eye) | Screens do not change by accident | Yes | From Phase 3, on the founder's laptop only (D-046) |
| Accessibility | `@axe-core/playwright` + keyboard-only runs + contrast script | WCAG 2.2 AA basics (NFR-A11Y) | Yes | Every UI phase |
| AI evaluation | pytest evaluation sets built from the owner's labelled jobs and recorded model answers | Scores agree with labels at least 85%, 0 invented facts, Ask answers at least 90%, tool choice at least 18 of 20 | Recorded answers by default; live model on demand | Phases 7, 10, 11; in CI from 13 |
| Security | pytest + Playwright (cross-user, SSRF table, injection set, CSP, headers, webhook replay) | Controls in `docs/SECURITY.md` | Yes | From Phase 4; full in Phase 14 |
| Performance | Lighthouse (mobile profile), a small load test, query-plan checks | NFR-PERF targets | Yes | Phases 13 and 14 |
| Migration | CI job: apply all migrations to an empty database, `alembic check`, run the row-level-security test | The schema and models agree | Yes | Every push |
| Restore drill | Script: restore the latest backup into an empty database and compare row counts | FR-216 | Yes | Phase 15, then monthly |

## 1a. How to run the tests (Windows PowerShell)

Start the containers first (`wsl docker compose up -d`) for anything marked "needs containers".

| From | Command | Runs | Needs containers |
|---|---|---|---|
| `api/` | `uv run pytest tests/unit` | Unit tests | no |
| `api/` | `uv run pytest` | Unit and integration tests (uses `nxtrole_test` and Redis database 1; tests empty them) | yes |
| `api/` | `uv run ruff check .` · `uv run ruff format --check .` · `uv run mypy app tests migrations` | Lint, format, types | no |
| `web/` | `pnpm test` | Component tests | no |
| `web/` | `pnpm lint` · `pnpm typecheck` · `pnpm build` | Lint, types, build | no |
| `web/` | `pnpm e2e` | All browser tests. Builds the web app (port 3100) and starts an API (port 8100) on a **throw-away database** named `…_e2e_test`, so your account is never touched; `pnpm dev` can keep running | yes |
| `web/` | `pnpm e2e:update-pictures` | Replaces the approved screen pictures after an intended change; look at them before committing | yes |
| root | `node scripts/mock-viewer/screenshots.mjs` then `node scripts/mock-viewer/review.mjs` | Builds `docs/visual-review/index.html`: every mock beside the app | no |

Integration tests refuse to run unless the test database name ends in `_test`.

## 1b. Screen tests added in Phase 3

| File | What it checks |
|---|---|
| `web/e2e/smoke.spec.ts` | Landing leads to sign-in; the API answers through `/api`; security headers; no console errors |
| `web/e2e/accessibility.spec.ts` | Every route, at 1440 and 390 px, light and dark: axe (WCAG 2.2 AA rules), one visible `h1`, correct theme, no sideways scrolling |
| `web/e2e/shell.spec.ts` | 320 px and 200% zoom, long headings, icon-only side menu, phone tabs, keyboard reach, theme without a flash, reduced motion, slow network, one primary button, 404, no showroom in production |
| `web/e2e/visual/routes.spec.ts` | 28 routes × 2 sizes × 2 themes = 112 pictures. Today's date is replaced with fixed words |
| `web/src/styles/tokens.test.ts` | The tokens equal the mock file; every text colour pair reaches 4.5:1 in both themes |

Automated checks do not replace a person: a screen-reader pass (NFR-A11Y-05) is still to be done in Phase 13.

## 1c. Sign-in and history tests added in Phase 4

| File | What it checks |
|---|---|
| `api/tests/unit/test_passwords_and_tokens.py`, `test_api_rules.py`, `test_setup_local.py` | Hashing, token forgery, password rules, pages, rate limits, body size, settings |
| `api/tests/integration/test_login.py`, `test_sessions.py`, `test_account.py` | Sign-in, lockout, refresh rotation and reuse, sign-out, recovery, password change, devices |
| `api/tests/integration/test_history.py`, `test_idempotency.py` | History, undo, proposals, repeated requests |
| `api/tests/integration/test_row_level_security.py`, `test_every_route_is_protected.py` | Users cannot see each other's rows; no address works without sign-in |
| `api/tests/integration/test_account_commands.py` | `create-owner`, `reset-password`, sessions commands |
| `web/src/lib/api.test.ts`, `safeNext.test.ts`, `features/auth/*.test.tsx`, `features/account/*.test.tsx` | One shared refresh, tabs, the sign-in guard, forms, Undo |
| `web/e2e/auth.spec.ts`, `account.spec.ts` | Sign in, reload, two tabs, sign out, lockout, expired token, passwords, devices, recovery, name and Undo |

The browser tests make new passwords for every run. `api/tests/e2e_server.py` builds their database.

## 2. Folder layout

```
api/tests/
  unit/<domain>/test_*.py
  integration/<domain>/test_*.py       (real Postgres + Redis)
  contract/test_contract_*.py
  security/test_*.py                   (cross-user, ssrf, injection, headers)
  ai_evals/                            (evaluation sets, runner, reports)
web/src/**/*.test.tsx                  (component tests next to the code)
web/e2e/<journey>.spec.ts              (Playwright, D-044)
web/e2e/routes.json                    (every route with its mock names; used by tests and the review page)
web/e2e/visual/                        (screenshot test; approved pictures in visual/pictures/)
tests/
  fixtures/                            (recorded real responses; see section 4)
```

## 3. Naming and style

- Python: `test_<area>_<behaviour>` for example `test_auth_reused_refresh_token_revokes_family`. One behaviour per test, arranged as Given / When / Then in comments when it helps.
- Web: `describe('<Component>')` + `it('shows the empty state with a next step')`.
- Playwright: one file per user journey, named after the PRD id (`uj-2-morning.spec.ts`).
- Every test that covers an edge case from the register carries its id in the name or a marker (`@E-24`), so the register can be checked automatically.
- Tests are independent: each makes its own rows, scoped to its own user, and cleans up. No test depends on another's order.
- A failing test is investigated and fixed; **a test is never weakened to pass**, and nobody claims a test passed unless it was run and seen to pass.

## 4. Fixtures policy (golden rule 1)

- **No invented data in the app.** Test data lives only in `tests/fixtures/` (and inside test code for tiny inputs).
- Fixtures are **recorded real responses** (a real job board JSON, a real Groq answer, a real email subject line with identifiers removed). The file name carries source and date:
  `greenhouse_2026-12-01_board-jobs.json`, `groq_2026-12-04_score-job.json`.
- A fixture is recorded by a script (`scripts/record_fixture.py`) that strips identifiers and secrets, and the commit message says where and when it came from.
- A **hostile fixture** (a job post with a script tag, an injection sentence, a private-address link) is hand-written because the real world rarely provides one; it lives in `tests/fixtures/hostile/` and is labelled "synthetic hostile input" in its name.
- Resume and offer test files are **the founder's own documents with identity removed**, or a clearly synthetic file labelled as such; they are never committed if they contain real personal data.
- The mocks' example people and companies are never copied into fixtures or code.

## 5. CI gates (every push and pull request)

1. Lint and type checks: `ruff`, `mypy` (strict on `app/`), `eslint`, `tsc --noEmit`.
2. Unit, integration, contract and component tests.
3. Migrations apply to an empty database; `alembic check`; row-level-security test.
4. Dependency audits (`pip-audit`, `pnpm audit`) and the secret scan (D-036).
5. Security tests (cross-user matrix on every endpoint, SSRF table, header test).
6. End-to-end smoke journey (UJ-1 sign-in and Today) on Chromium; the full browser matrix runs nightly and in Phase 13.
7. Accessibility checks on built screens.
A failing gate blocks the phase. Coverage is reported but is **not** the goal; the register and the journeys are.

## 6. AI evaluation sets (D-033)

| Set | Built from | Pass mark | Phase |
|---|---|---|---|
| Scoring agreement | Jobs the owner labelled Good or Not for me (FR-069), with recorded model scores | At least 85% agreement | 7 |
| Quote integrity | Model answers with deliberately wrong quotes | 100% of wrong quotes detected and dropped | 7 |
| Claim checking | Pack drafts with planted invented facts | 0 invented facts pass | 10 |
| Injection | Hostile posts and notes (T-LLM-1) | 0 behaviour changes | 7, 10, 11 |
| Ask answers | 30 questions on the owner's own data | At least 90% correct with sources | 11 |
| Ask tool choice | 20 questions with a known right tool | At least 18 of 20 | 11 |
| Redaction | Seeded identity in resume, notes and offers | 0 leaks in gateway requests, logs and traces | 5 |
Evaluations run on **recorded** answers in CI (free, repeatable); a live run against Groq is a manual command that stays inside the daily token budget (D-033).

## 7. Performance targets (NFR-PERF)

Today under 2 s on a mid-range phone (Lighthouse mobile); API reads under 500 ms at the 95th percentile; the hourly run under 10 minutes; the morning run before 7:00 AM IST; search under 500 ms. Query plans are checked for the jobs list, today and search (indexes in `docs/DATABASE_SCHEMA.md`).

## 8. Definition of done for a test task

The test exists; it fails first when the behaviour is removed (checked once); it passes; it is named with its register id; the register row below is updated with the real test name and status.

---

## 9. Edge-case register

Seeded from PRD Appendix A (E-01 to E-55), the Phase 1 checklist (E-56 to E-70), the Phase 2 checklist (E-71 to E-75) and Phase 3 (E-76 to E-79) and Phase 4 (E-80 to E-83). **Status:** `planned` until the owning phase writes the test; then `written`, then `passing`. The "Planned test" column is the intended name (the phase may refine it).

| ID | Edge case | Phase | Expected behaviour | Planned test | Status |
|---|---|---|---|---|---|
| E-01 | First run with no data | 3, 8 | Every screen shows a "what to do next" empty state; no example data | `@E-01 empty-state wording` (component); `e2e: uj-1_first_run_empty_states` (Phase 8) | wording passing; journey planned |
| E-02 | No approved profile | 5 | Scoring, packs, drafts, tailoring blocked with "Approve your profile" | `test_profile_unapproved_blocks_scoring_and_packs` | planned |
| E-03 | No sources and no watched companies | 6 | Today and Jobs say how to add one | `component: jobs_empty_no_sources` | planned |
| E-04 | No rules yet | 7 | Nothing hidden; Memory invites a first rule | `component: rules_empty` | planned |
| E-05 | Push not allowed or app not installed | 8 | Settings explain why and how; app still works | `e2e: alerts_permission_denied` | planned |
| E-06 | All AI limits used | 5, 8 | Banner "All limits used"; non-AI work continues; drafts "pending", retried at discovery runs; one push | `test_ai_all_limits_queue_and_banner` | planned |
| E-07 | One AI model in the chain fails or is slow | 5 | Next model answers; banner "Using backup" | `test_gateway_falls_back_down_chain` | planned |
| E-08 | AI returns invalid or unparseable output | 5, 7 | Schema validation, 2 retries, then "unsure" or "pending" | `test_gateway_malformed_output_retries_then_pending` | planned |
| E-09 | AI quotes text not in the post | 7 | Reason dropped; with none left the job is "unsure" | `test_scoring_drops_unverified_quotes` | planned |
| E-10 | The same job on several sites | 6 | One job with sightings and "also found on" | `test_ingest_dedupes_same_job_across_sources` | planned |
| E-11 | Scam posts (fee, WhatsApp only, no company contact) | 6 | Risky; not scored; no pack; can be hidden with similar posts | `test_trust_fee_post_is_risky_and_unscored` | planned |
| E-12 | Reposted jobs | 6 | Repost count; level at most Check | `test_trust_repost_count_and_level` | planned |
| E-13 | Closed or removed jobs | 6 | Marked Closed; snapshot kept; link may say it closed | `test_ingest_marks_closed_and_keeps_snapshot` | planned |
| E-14 | Salary in LPA, monthly, ranges, USD or missing | 6 | Normalised to rupees per year or "Not stated" | `test_salary_parser_formats` (table of recorded real strings) | planned |
| E-15 | City aliases, hybrid, several locations | 6 | One normalised place; hybrid and remote flags kept | `test_city_normalisation_aliases` | planned |
| E-16 | Job text with markup, scripts or huge text | 6 | Plain text; long text cut with "show more" | `component: job_text_plain_text` + `test_ingest_text_caps` | planned |
| E-17 | Prompt-injection text in a post, email or note | 7, 10, 11, 12 | Treated as data; no change in scores or behaviour | `ai_evals: injection_set` | planned |
| E-18 | Pasted link: invalid, http, private, redirect, huge, timeout, login wall | 6 | Clear message; by-hand form opens with the link kept | `test_fetcher_ssrf_and_limits_table` | planned |
| E-19 | A job added by hand already exists | 6 | Duplicate found; owner offered the existing job | `test_add_job_duplicate_offered` | planned |
| E-20 | A source changes format or hits a rate limit (429) | 6 | That source "paused"; others continue; error logged | `test_discovery_source_429_does_not_stop_run` | planned |
| E-21 | Two runs overlap, or the free database is paused | 8, 15 | Lock stops overlap; health alert says what failed | `test_run_lock_prevents_overlap`; `test_health_reports_paused_db` | planned |
| E-22 | The morning run fails | 8 | Today shows the last brief with "stale" and one push | `e2e: today_stale_after_failed_run` | planned |
| E-23 | Two tabs refresh the session together | 4 | One refresh succeeds; both tabs continue | `test_two_tabs_racing_both_continue`, `test_simultaneous_refreshes_create_one_new_token`, `@E-23 two tabs` (browser) | passing |
| E-24 | A used refresh token is presented again | 4 | Whole family revoked; sign-in needed | `test_auth_reused_refresh_token_revokes_family` | passing |
| E-25 | Forgotten password | 4 | Recovery code works; no email needed; new code issued | `test_recover_with_code_rotates_code`, `@E-25` (browser) | passing |
| E-26 | Too many failed sign-ins (lockout) | 4 | Rate-limit message; same wording for every failure | `test_auth_lockout_after_five_failures`, `wrong details … five tries lock` (browser) | passing |
| E-27 | Two tabs edit the same card | 9 | Second save rejected with 409 and "this card changed, reload" | `test_a_change_based_on_an_old_version_is_a_conflict` (profile, Phase 4); `test_pipeline_stale_version_returns_409` (Phase 9) | profile passing; cards planned |
| E-28 | Undo after later changes | 4, 9 | Safe revert, or explains what blocks it | `test_undo_blocked_explains_dependency` (profile); pipeline cases in Phase 9 | engine passing; pipeline planned |
| E-29 | A move out of order, or Interview without a round | 9 | Refused with a plain message | `test_pipeline_invalid_moves_refused` | planned |
| E-30 | Interview times in other time zones or unclear | 9, 12 | Zone shown; unclear times become proposals | `test_round_timezone_and_unclear_time_proposal` | planned |
| E-31 | Gmail: same email twice, unclear email, unknown company, burst, script stopped | 12 | Idempotent; proposals; status shows last run | `test_webhook_replay_is_noop`; `test_email_unclear_makes_proposal` | planned |
| E-32 | Calendar: token expired or revoked, event deleted outside, round cancelled | 12 | "Reconnect" state; no crash; event removed on cancel | `test_calendar_needs_reconnect_state` | planned |
| E-33 | Offline phone | 8 | Read-only last screens with an offline notice; nothing queued silently | `e2e: offline_readonly_shell` | planned |
| E-34 | Slow network and repeated taps | 3, 4 | Loading states; retry; a repeated create makes one record | `@E-34` slow screen and double click (browser), `test_idempotency_key_replays_response` | passing; used by create actions from Phase 9 |
| E-35 | Data export | 14 | Contains every module's records and nobody else's | `test_export_contains_all_user_tables_only` | planned |
| E-36 | Delete my account and data | 14 | Rows, files, tokens, subscriptions removed; confirmation; resumable; verified | `test_delete_account_leaves_no_rows_or_files` | planned |
| E-37 | Delete all contacts; replace the resume | 5, 11 | Confirmation; old data removed or versioned as specified | `test_contacts_delete_all`; `test_resume_replace_makes_new_version` | planned |
| E-38 | Fewer than 5 applications in a coach group | 9 | "too few"; no percentage | `test_coach_too_few_group` | planned |
| E-39 | A dismissed rule suggestion | 7 | Not suggested again for 30 days | `test_rule_dismissal_30_days` | planned |
| E-40 | Offer without variable pay; new financial year; no tax table | 9 | Estimate works or says "Tax table not available for this year" | `test_offer_estimate_cases` | planned |
| E-41 | Offer letter text with personal data | 9 | Identity removed before AI | `test_offer_letter_redaction` | planned |
| E-42 | LinkedIn CSV: other columns, odd encoding, duplicates, huge | 11 | Clear errors; bad rows skipped and counted; limits | `test_contacts_csv_variants` | planned |
| E-43 | Pack with thin job text, missing answer, claim failing twice | 10 | Blanks flagged; failed claims removed or flagged; pack not approved | `test_pack_blank_and_failed_claims` | planned |
| E-44 | An agent run is interrupted (tab closed, restart) | 10 | Run survives and resumes on approval | `test_agent_resumes_after_restart` | planned |
| E-45 | A pack requested twice (double tap) | 10 | One pack | `test_pack_request_dedupe` | planned |
| E-46 | Asking for another user's data or something destructive | 11 | Refused; attempt logged | `test_ask_cross_user_and_destructive_refused` | planned |
| E-47 | A streaming answer is cut off | 11 | Partial answer kept with retry | `e2e: ask_stream_interrupted` | planned |
| E-48 | A chat older than 30 days | 11, 14 | Deleted by clean-up | `test_cleanup_deletes_old_chats` | planned |
| E-49 | A revoked or leaked MCP token | 11 | Stops at once; calls limited and logged | `test_mcp_revoked_token_rejected` | planned |
| E-50 | Quiet hours cross midnight; IST and UTC; the daily cap | 8 | Honoured across midnight; cap resets at midnight IST | `test_alert_quiet_hours_and_cap` | planned |
| E-51 | Reduced motion, 200% zoom, dark theme, keyboard, screen reader | 3 to 13 | All journeys still work | `accessibility.spec.ts` and `@E-51` tests in `shell.spec.ts` and `tokens.test.ts` | passing for Phase 3 screens; repeat each phase |
| E-52 | Resume placeholders `[N]`, over one page, LaTeX special characters | 10 | Export blocked until filled; page warning; characters escaped | `test_resume_export_blocks_placeholders`; `test_tex_escaping` | planned |
| E-53 | A small company with almost no public information | 10 | "Not found in any source"; nothing invented | `test_brief_not_found_fields` | planned |
| E-54 | A company brief older than 7 days | 10 | Marked old; refreshed on request | `test_brief_expiry_flag` | planned |
| E-55 | A browser without WebGL | 3 | Step cards and the tour message | `e2e: landing_no_webgl` (when the 3D view is built) | planned (3D view not built) |
| E-56 | **Access token expires in the middle of use** | 4 | One refresh, then the original request is retried once | `@E-56` in `api.test.ts` and `auth.spec.ts` | passing |
| E-57 | **Scanned (image-only) or password-protected PDF** | 5 | Rejected with a clear reason; nothing stored | `test_upload_scanned_and_protected_pdf` | planned |
| E-58 | **File over 5 MB** (and the 4.5 MB request limit) | 5 | Rejected before upload completes; direct-to-storage path works for 5 MB | `test_upload_size_limits` | planned |
| E-59 | **Wrong or changed board token** for a company feed | 6 | Source marked paused with a plain message; finder asks again | `test_feed_wrong_board_token` | planned |
| E-60 | **Missing posted date** | 6 | `posted_at` null; shown as "Posted date not stated"; excluded from "posted within" filters only when asked | `test_job_without_posted_date` | planned |
| E-61 | **Agent tool loop or step overrun** | 10, 11 | Step limit stops the run; clear message; no repeated charges | `test_agent_step_limit` | planned |
| E-62 | **Redis down** | 4, 8 | Sign-in falls back to database-based limits; scheduled work refuses to start; health shows it | `test_redis_down_behaviour_still_signs_in_and_still_locks` (sign-in); scheduled work in Phase 8 | sign-in passing; schedules planned |
| E-63 | **Cron in UTC** (07:00 IST = 01:30 UTC; morning run 00:00 UTC) | 8 | Times shown in IST; push after 07:00 IST; no run on the wrong day near midnight | `test_schedule_utc_to_ist` | planned |
| E-64 | **Hosting time limit hit mid-request** | 4, 10 | Request ends cleanly; slow work already a job; no half-written data | `test_long_work_is_a_job` | planned |
| E-65 | **Push subscription expired** | 8 | Marked expired and pruned; no repeated failures | `test_push_expired_subscription_pruned` | planned |
| E-66 | **Free database paused after inactivity** | 15 | Hourly run keeps it active; health alert and runbook step if paused | `drill: db_pause_runbook` | planned |
| E-67 | **Webhook replay with a changed body** | 12 | Signature fails; same id with the same body is a no-op | `test_webhook_tamper_and_replay` | planned |
| E-68 | **SSRF hostile URL table** | 6, 14 | All refused (private, loopback, metadata, rebinding, redirects, huge) | `test_fetcher_ssrf_and_limits_table` (shared with E-18) | planned |
| E-69 | **Groq daily token budget crossed mid-run** (D-033) | 5, 7 | Gateway moves down the chain or queues; scores marked pending; no 429 storms | `test_gateway_token_budget_pacing` | planned |
| E-70 | **Cross-user access on every endpoint and table** | 4 onward | Always `not_found`; row-level security returns no rows with the wrong user | `test_rls_wrong_user_sees_nothing`, `test_cross_user_ids_are_not_found`, `test_every_route_refuses_a_visitor_without_a_valid_token` | passing for Phase 4 tables; repeat each phase |
| E-71 | **Docker or the containers not running** | 2 | README and `check-config` say how to start them; non-zero exit; no crash | `test_check_config_explains_unreachable_services`; checked by stopping the containers | passing |
| E-72 | **Port 5432, 6379, 8000 or 3000 already in use** | 2 | Documented fix: another port in `.env` | README Troubleshooting; compose renders the override (manual check, not an automated test) | checked by hand |
| E-73 | **Missing or invalid environment variable** | 2 | One readable error naming the variable, never its value | `test_config_missing_variables_are_all_named`, `test_config_invalid_value_names_variable_without_showing_it` | passing |
| E-74 | **Database or Redis not ready when the API starts** | 2 | API starts; `/api/health/ready` returns 503 naming the part; recovers by itself | `test_ready_reports_503_and_which_parts_failed`; checked by stopping and restarting containers | passing |
| E-75 | **Windows line endings, paths and event loop** | 2 | LF enforced by `.gitattributes`; commands work in PowerShell; psycopg gets the Selector loop | integration tests run on Windows; fresh-copy run | passing |
| E-76 | **A 60-character heading with no spaces** | 3 | Wraps; no sideways scrolling at 320 px | `@E-76 a 60-character heading wraps` | passing |
| E-77 | **First visit on a dark system** | 3 | Dark from the first paint; the owner's choice is kept | `@E-77 follows a dark system on the first visit` | passing |
| E-78 | **Unknown address** | 3 | A 404 page in the same style with a way back | `@E-78 an unknown address shows the 404 page` | passing |
| E-79 | **Development showroom in production** | 3 | `/design` does not exist | `@E-79 the showroom does not exist` | passing |
| E-80 | **Password with spaces or other alphabets; email with capitals** | 4 | Works; the same password typed differently matches; capitals ignored | `test_spaces_unicode_and_composed_characters_work`, `test_email_capitals_do_not_matter` | passing |
| E-81 | **Very long sign-in input** | 4 | Refused before any hashing | `test_bad_input_is_refused_before_any_work_and_not_echoed` | passing |
| E-82 | **Clocks of server and browser differ** | 4 | 30 seconds allowed | `test_a_small_clock_difference_is_allowed` | passing |
| E-83 | **A link that tries to send the owner elsewhere after sign-in** | 4 | Today opens instead | `safeNext.test.ts`, `auth.spec.ts` | passing |

## 10. Threat tests (from `docs/SECURITY.md`)

| Threat id | Test file (planned) | Phase |
|---|---|---|
| T-AUTH-1 to T-AUTH-7 | `api/tests/security/test_auth_*.py` | 4 |
| T-IDOR-1 to T-IDOR-4 | `api/tests/security/test_cross_user.py`, `test_ask_data_role.py` | 4, 11 |
| T-XSS-1, T-INJ-1 to T-INJ-3 | `api/tests/security/test_output_and_input.py`; `web` component tests | 3, 4, 6, 10 |
| T-FILE-1 to T-FILE-4 | `api/tests/security/test_uploads.py` | 5 |
| T-LLM-1 to T-LLM-8 | `api/tests/ai_evals/` and `api/tests/security/test_gateway.py` | 5, 7, 10, 11 |
| T-HOOK-1 to T-HOOK-4, T-MCP-1 to T-MCP-3 | `api/tests/security/test_webhook.py`, `test_mcp.py` | 11, 12 |
| T-OAUTH-1, T-OAUTH-2, T-PUSH-1, T-SRC-1 | `api/tests/security/test_integrations.py` | 6, 8, 12 |
| T-OPS-1 to T-OPS-9 | CI jobs and `api/tests/security/test_logging.py` | 2 onward |

## 11. Register check (Phase 1 documentation check)

| Check | Result |
|---|---|
| The register contains every edge case named in `docs/prompts/PHASE-01-architecture.md` section 10 | Yes: login lockout E-26, expired token mid-use E-56, two tabs E-23, reused refresh token E-24, scanned or protected PDF E-57, file over 5 MB E-58, source timeout/429 E-20, wrong board token E-59, same job on several sites E-10, reposts E-12, closed jobs E-13, salary formats E-14, missing posted date E-60, city aliases E-15, prompt injection E-17, all AI providers limited E-06, malformed AI output E-08, quote not found E-09, no approved profile E-02, `[N]` placeholders and LaTeX characters E-52, two tabs editing one card E-27, double clicks E-34 and E-45, undo after later changes E-28, agent tool loops E-61, Redis down E-62, overlapping runs E-21, cron in UTC E-63, hosting time limits E-64, free database pausing E-66 and E-21, push subscription expired E-65, webhook replay E-31 and E-67 |
| Every PRD Appendix A row (E-01 to E-55) is present | Yes |
| Every row has a phase, expected behaviour and planned test | Yes |
