# Phase 8 — Background work, Today brief and alerts

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-08-worker-today-alerts.md and follow it.`
> Follow `CLAUDE.md`. No commits.

## 1. Phase name and objective
**Background work, Today brief and alerts.** Move all slow work out of web requests into a worker, run
it on a schedule (morning run 05:30 IST, push at 07:00 IST, hourly discovery 07:00 to 21:00 IST, D-030, D-040), make runs safe to repeat, build the Today
screen with real data, and send phone alerts for strong fresh jobs.

## 2. Context and dependencies
- Requires Phases 6 and 7 (fetching, trust, ranking, scoring).
- No accounts needed: push keys (VAPID) are generated locally by a CLI command and kept in `.env`.
- Decisions: alerts channel (M2, web push first), desktop fresh jobs (M10).

## 3. Detailed implementation tasks
1. **Worker:** our own loop over the `background_jobs` table (`for update skip locked`, D-026), Redis only for locks and rate limits; tasks: fetch sources, clean and dedupe, trust check, embed, rank, score,
   build brief, fresh-job radar, send notifications, extract profile (move the Phase 5 AI extraction
   here). Each task idempotent (dedupe keys), with retries and a final failure state.
2. **Runs:** `agent_runs` rows for every scheduled run (kind, status, counts, duration, error code);
   a Redis lock (`SET NX` with expiry) so two runs never overlap; a run that dies leaves a clear status
   and the next run continues safely.
3. **Schedules:** `.github/workflows/schedule.yml` with cron `0 0 * * *` (05:30 IST morning run) and
   `30 1-15 * * *` (hourly discovery, 07:00 to 21:00 IST; the 07:00 run sends the push and retries "Drafts pending") calling `uv run python -m app.cli run morning|radar` in burst mode; local
   development uses the same CLI. Document that GitHub may start scheduled runs late and
   that everything is safe to repeat.
4. **Morning brief:** fetch → clean → trust → rules → rank → score top 30 → build the brief for today in
   IST (top 5 shown, the rest behind "Show all"), with stats (jobs read, good matches, risky hidden).
   If AI limits are used up, the brief still appears with "AI score pending" and finishes later.
5. **Fresh-job radar (hourly):** check watched companies only; new jobs → trust → rules → score; a job
   with score ≥ 80 and High trust triggers an alert.
6. **Alerts (web push):** `generate-vapid` CLI; service worker and web app manifest (installable app);
   subscribe/unsubscribe in Onboarding step 5 and Sources and memory; settings: on/off per type, quiet
   hours (default 11 PM–7 AM IST), at most 5 a day; `notifications` with a unique `dedupe_key` so a job
   never alerts twice; expired subscriptions (404/410) removed.
7. **Minimal applications:** "I applied" from Today or job detail creates an `applications` row
   (stage "applied", date) so counts work now; the full Pipeline comes in Phase 9.
8. **Screens:** Today (`Brief` / `MToday`): greeting with IST date, lead sentence from real counts,
   "This week" strip (empty until rounds exist in Phase 9), strong matches with trust badges, score,
   reason, "Not today" with undo, "Apply" (opens the job's page in a new tab, then asks "Did you apply?"),
   "Needs you" (pending proposals for now), AI status banners (normal / using backup / all limits used);
   Fresh jobs (`MFresh`) and the desktop fresh section; top bar agent log (recent runs with status);
   nav agent status line ("next run …").

## 4. UI mock references
`Brief` / `MToday` (all sections and the three AI-limit banner states), `MFresh`, `TopBar` (agent log),
`Nav` (agent status), `Memory` / `MMemory` (Alerts section), `Onboarding` / `MOnboarding` step 5
("When should we tell you?") and step 6 ("Your agents are on it").

## 5. Recommended technologies
PostgreSQL queue table, Redis (locks and limits), GitHub Actions schedules, pywebpush (VAPID), service worker + Web App Manifest, TanStack Query
(polling or SSE for run progress).

## 6. Files and modules to create or modify
`api/app/worker/{settings,tasks,locks,runs}.py`, `api/app/brief/{build,service,router,models}.py`,
`api/app/notify/{push,service,router,models}.py`, `api/app/applications/models.py` (minimal),
migrations for `agent_runs`, `briefs`, `notifications`, `push_subscriptions`, `applications` (minimal);
`.github/workflows/schedule.yml`; `web/public/sw.js`, `web/app/manifest.ts`,
`web/app/(app)/today/*`, `web/app/(app)/today/fresh/*`, top bar agent log, settings alerts.

## 7. Database and API requirements
Tables: `agent_runs`, `briefs`, `notifications`, `push_subscriptions`, minimal `applications`.
Endpoints: `GET /api/brief/today`, `POST /api/jobs/{id}/applied`, `GET /api/runs`, `GET /api/runs/{id}`,
`POST /api/push/subscribe`, `DELETE /api/push/subscribe`, `PUT /api/settings/alerts`,
`GET /api/settings/ai-status`.

## 8. Implementation sequence
Worker and task wrappers → locks and run records → morning pipeline end to end via CLI → schedule
workflow → radar → push keys, service worker, subscribe → notification rules and dedupe → Today screen →
fresh screens → agent log → tests.

## 9. Testing requirements
Integration: morning run end to end with recorded sources and AI; second run at the same time is skipped
by the lock; a crashed run then a clean run; idempotent re-run creates no duplicates; "AI pending"
path; radar alert sent once only; quiet hours respected; 5-per-day cap; expired subscription removed.
Unit: IST date boundaries (a run at 01:30 UTC belongs to today in IST). Frontend: Today states (empty
first day, normal, pending AI, all limits used), "Not today" undo. Playwright: brief renders after a run.

## 10. Edge-case checklist
- [ ] Overlapping scheduled runs; GitHub starting a run late.
- [ ] Worker crash in the middle of a run.
- [ ] Redis unavailable (run fails safely and reports; web app still works).
- [ ] Free database paused or slow to wake (retry, then a clear failure alert).
- [ ] No new jobs today (friendly message, not an empty page).
- [ ] All AI limits used.
- [ ] Push permission denied; iPhone requires the app installed first; subscription expired.
- [ ] Duplicate alerts for the same job; alerts during quiet hours.
- [ ] Hosting time limits: no long work inside web requests.

## 11. Security considerations
Schedule secrets only in GitHub secrets; VAPID private key only in env; push payloads contain no personal
data beyond job title and company; run logs contain no personal text; the CLI refuses to run against
production without an explicit flag.

## 12. Acceptance criteria
- [ ] Running `run morning` produces today's brief with real matches; Today matches the mock.
- [ ] Two runs at once never overlap; re-running causes no duplicates.
- [ ] A strong fresh job sends exactly one push alert to my phone (outside quiet hours).
- [ ] The agent log shows each run with counts and status.
- [ ] All tests, lint, types and build pass.

## 13. Documentation updates
`docs/ARCHITECTURE.md` (worker, schedules), `docs/API_DOCUMENTATION.md`, `docs/DATABASE_SCHEMA.md`,
`docs/DEPLOYMENT.md` (schedules, VAPID keys, GitHub secrets list), `docs/TESTING.md`,
`docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format. Explain: background jobs and queues, cron and UTC vs IST, locks and
idempotency, push notifications and service workers.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 9." Do not commit.
