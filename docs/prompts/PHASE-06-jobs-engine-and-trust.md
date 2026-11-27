# Phase 6 — Jobs engine and trust check

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-06-jobs-engine-and-trust.md and follow it.`
> Follow `CLAUDE.md`. No commits.

## 1. Phase name and objective
**Jobs engine and trust check.** Bring in real jobs from official sources, clean them for India, merge
duplicates, notice reposts and closed jobs, check each one for scam and ghost-job signals, and show them
on the Jobs screen and the job detail page. Let me watch companies and add a job by hand.

## 2. Context and dependencies
- Requires Phase 5 (AI gateway for the one AI trust signal; rules for filtering).
- **Key needed now:** free Adzuna API credentials (developer.adzuna.com). I put `ADZUNA_APP_ID` and
  `ADZUNA_APP_KEY` in `api/.env` myself. Confirm India's country code and the attribution rules in
  Adzuna's docs. Greenhouse, Lever, Ashby and Arbeitnow need no keys; read each one's public API docs.

## 3. Detailed implementation tasks
1. **Source adapters** (one class per source, same interface `fetch()` → raw items, `normalize()` →
   `JobIn`): Greenhouse job board API, Lever postings API, Ashby job board API (for watched companies),
   Adzuna search (India), Arbeitnow. httpx with timeouts; tenacity retries with backoff on timeouts, 429
   and 5xx; at most 1 request per second per host; respect `Retry-After`; pagination with a page cap.
   A generic User-Agent naming NxtRole (no personal email).
2. **Cleaning for India:** salary to a yearly INR range from "12–18 LPA", "₹1.5L/month", "$120k",
   "CTC"; cities and aliases; "Pan India", remote (India-only vs global), hybrid; experience ranges
   ("0–2 yrs", "fresher", "5+"); notice requirements ("immediate joiners only"); job description HTML
   converted to safe plain text (no HTML kept); text length cap.
3. **Saving:** upsert on `(source, external_id)`; `content_hash` to skip unchanged jobs; `fingerprint`
   (normalised company + title + city) to merge the same job from several sources into one, recording
   each sighting; repost detection (same fingerprint, new id within 60 days → `repost_count`); closed
   detection (missing from its board for 2 runs → `closed_at`); `first_seen_at` used when a source has no
   posted date; future posted dates corrected.
4. **Watched companies:** add by name or careers-page URL; detect the board from URL patterns (Greenhouse,
   Lever, Ashby); test the feed (open job count) before saving; "no public feed" status for others;
   per-company health (last check, errors). The AI job-page finder comes in Phase 10; this phase is
   code-only detection.
5. **Trust check:** a rules engine with ids and a version: asks for money (fee, deposit, bond with
   certificates kept), contact only on WhatsApp/Telegram, free email domain for a company recruiter,
   pay far above normal for the experience, not on any company careers page, reposted 2+ times in
   60 days, open 30+ days, very wide salary range, offer without interview; one AI signal (small model)
   for "vague description". Output level High / Check first / Risky with reasons and which were rules
   vs AI. Risky jobs are never sent to the AI for scoring (Phase 7). My safety toggles in Settings
   (hide vs warn) from the mock.
6. **Add a job by hand:** paste a URL (if it is a known board, fetch through its API) or paste the text;
   same cleaning and trust check.
7. **Screens:** Jobs list (filters, sort, source chips, "source paused" banner, add-a-job drawer, empty
   and error states); Job detail `/jobs/[id]` with header, trust check section, duplicates and history
   section, "Not for me" reasons (saved; used in Phase 7), and the fit section showing "Not scored yet";
   Settings › Sources and memory: watched companies table and "Add a company"; Settings › Safety rules;
   Onboarding step 3 ("Where should we look?").
8. **Manual run:** `uv run python -m app.cli fetch-jobs [--source X]` with a summary (fetched, new,
   updated, merged, closed, errors per source). Scheduling comes in Phase 8.

## 4. UI mock references
`Jobs` / `MJobs` (list, filters, "Add a job" drawer, "Source paused", "Other ways to add"),
`JobCheck` / `MJobCheck` (trust check, duplicates and history, Not for me), `Memory` / `MMemory`
(watched companies, add a company), `Settings` (Safety rules switches), `Onboarding` step 3.

## 5. Recommended technologies
httpx, tenacity, nh3 (or an HTML-to-text converter), rapidfuzz (company name matching), Pydantic,
SQLAlchemy, TanStack Query.

## 6. Files and modules to create or modify
`api/app/sources/{base,greenhouse,lever,ashby,adzuna,arbeitnow,detect}.py`,
`api/app/jobs/{models,normalize,salary,cities,dedupe,service,router}.py`,
`api/app/trust/{rules,service,models}.py`, `api/app/companies/{models,service,router}.py`,
migrations for `sources`, `companies`, `company_watches`, `jobs`, `job_sightings`, `trust_checks`,
`user_job_states`; `api/tests/fixtures/sources/<source>_<date>.json` (recorded real responses);
`web/app/(app)/jobs/*`, `web/app/(app)/settings/sources/*`, onboarding step 3.

## 7. Database and API requirements
Tables as listed. Endpoints: `GET /api/jobs` (filters, cursor), `GET /api/jobs/{id}`,
`POST /api/jobs/manual`, `POST /api/jobs/{id}/state` (seen, saved, skipped + reason, hidden),
`GET/POST/DELETE /api/companies/watches`, `POST /api/companies/detect`, `GET /api/sources/health`,
`PUT /api/settings/safety`.

## 8. Implementation sequence
Adapter interface → one adapter end to end (Greenhouse) with recorded fixture → cleaning functions with
unit tests → save, dedupe, reposts, closed → other adapters → trust rules → AI vague-description signal →
watched companies + detection → manual add → CLI fetch → screens → tests.

## 9. Testing requirements
Unit tests for every parser (salary, city, experience, notice) with real-world strings; trust rules
(each rule true and false); dedupe and repost logic. Integration with recorded responses: each adapter;
a source timing out while others succeed; 429 with `Retry-After`; wrong board token (404) message.
Frontend: list states, filters, drawer validation, trust badge rendering. Playwright: add a company →
fetch → job appears → open detail → trust section.

## 10. Edge-case checklist
- [ ] Source timeout, 429, 5xx, malformed JSON — others continue; health shows "paused".
- [ ] Wrong board token or company with no public feed.
- [ ] Same job on three sources → one card with three sightings.
- [ ] Reposted job; job closed; job reopened.
- [ ] Missing or future posted date.
- [ ] Salary in LPA, monthly, USD, "not disclosed".
- [ ] Bangalore vs Bengaluru; Gurgaon vs Gurugram; "Pan India"; remote outside India.
- [ ] HTML, scripts or prompt-injection text in a description (stored as plain text, never followed).
- [ ] Very long descriptions; emoji and ₹ symbols.
- [ ] Manual URL pointing to a private or local address (refused).

## 11. Security considerations
Outbound fetches only to allowed source hosts (manual URLs: https only, public IPs only, size and time
limits, no redirects to private ranges); no HTML rendered; adapter errors never expose keys; Adzuna keys
only in env; respect terms and attribution.

## 12. Acceptance criteria
- [ ] With my watched companies and Adzuna, `fetch-jobs` brings in real jobs with a clear summary.
- [ ] Duplicates merge, reposts and closed jobs are marked, every job has a trust level with reasons.
- [ ] Jobs list and job detail match the mocks on desktop and phone with real data.
- [ ] I can add a company (detected board, tested feed) and add a job by hand.
- [ ] All tests pass with recorded responses only; lint, types and build pass.

## 13. Documentation updates
`docs/ARCHITECTURE.md` (sources), `docs/API_DOCUMENTATION.md`, `docs/DATABASE_SCHEMA.md`,
`docs/TESTING.md` (edge-case rows), `docs/DEPLOYMENT.md` (Adzuna key row), `docs/KNOWN_ISSUES.md`,
`docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format. Explain: what an API adapter is, rate limits and backoff, deduplication,
why rules run in code and only one signal uses AI.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 7." Do not commit.
