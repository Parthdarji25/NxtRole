# Phase 16 — Launch and maintenance

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-16-launch-maintenance.md and follow it.`
> Follow `CLAUDE.md`. No commits, pushes or tags without my explicit OK.

## 1. Phase name and objective
**Launch and maintenance.** Launch NxtRole for real use, confirm every core journey with my real data,
watch it closely for the first week, fix launch issues, and set up a simple routine that keeps it healthy,
accurate and up to date.

## 2. Context and dependencies
- Requires Phase 15 (production ready, smoke tests passing, backups tested).

## 3. Detailed implementation tasks
1. **Launch checklist** (go/no-go with me): ROADMAP section H all ticked; open issues reviewed; rollback
   ready.
2. **Real data setup with me:** sign in on desktop and phone; install the app on my phone and allow
   alerts; upload my resume and approve my facts; set preferences; add the companies I want to watch;
   connect Adzuna; install the Gmail script (optional); import my LinkedIn CSV (optional).
3. **First runs:** trigger a morning run manually; check the brief, trust levels, scores and quotes on
   real jobs; trigger a radar run; confirm one push alert.
4. **Accuracy check:** I label 20 real jobs; run the scoring eval on production data (read-only); review
   results with me; adjust the rubric or thresholds only with my OK (new prompt version, eval again).
5. **Journey verification:** go through every PRD journey with real data on desktop and phone; record
   anything confusing or broken.
6. **First 7 days:** a daily 10-minute check you prepare for me (runs succeeded, errors in Sentry, AI
   usage, source health, alert delivery, slow pages); fix issues in order of severity, each with a test.
7. **Release v1.0:** CHANGELOG, release notes, screenshots for the README; propose the tag `v1.0.0`
   (create it only when I say so).
8. **Maintenance routine** written in `docs/MAINTENANCE.md`:
   - Weekly: review Dependabot updates (tests must pass), source health, AI quotas, scoring eval with new
     labels, weekly coach sanity check.
   - Monthly: restore test from backup, check model ids and provider terms, check job API changes,
     prune old data per retention rules, review `docs/KNOWN_ISSUES.md`.
   - Yearly: update the tax table for the new financial year (Offer check).
   - Any time: a source or provider breaks → runbook steps.
9. **Feedback loop:** `docs/FEEDBACK.md` for my notes; monthly prioritisation into `docs/ROADMAP.md`
   (later items: Telegram alerts, invites, browser extension, voice beyond Chrome).
10. **Inviting others (only if decided):** consent, privacy notice, DPDP basics, per-user quotas and
    cost review before the first invite.

## 4. UI mock references
All screens, checked against the mocks with real data on desktop and phone (spot check list in the
launch checklist).

## 5. Recommended technologies
Everything already in production; Sentry and Langfuse dashboards; GitHub Releases; Dependabot.

## 6. Files and modules to create or modify
`docs/launch/checklist.md`, `docs/launch/day-log-<date>.md`, `docs/MAINTENANCE.md`, `docs/FEEDBACK.md`,
`CHANGELOG.md`, `README.md` (screenshots, status), fixes with tests as needed.

## 7. Database and API requirements
No planned changes. Any fix that needs a migration follows "expand then contract" and is tested on
preview first.

## 8. Implementation sequence
Go/no-go → real data setup → first runs → accuracy check → journey verification → 7-day monitoring and
fixes → v1.0 release (with my OK) → maintenance routine → feedback loop.

## 9. Testing requirements
Production smoke test after every deploy; a regression test for every launch bug; eval re-run after any
prompt or model change; the full suite must stay green.

## 10. Edge-case checklist
- [ ] First real day with very few or very many jobs.
- [ ] A source or provider failing on launch day.
- [ ] Alerts not arriving on my phone (permissions, install, quiet hours).
- [ ] My resume producing odd facts (edit and re-approve flow).
- [ ] A real scam or ghost job slipping through (new rule + test).

## 11. Security considerations
Watch Sentry for auth errors; confirm no personal data in logs after real use; rotate any key that was
ever exposed; review access to all accounts (2FA on GitHub, Vercel, Supabase, Upstash, Google).

## 12. Acceptance criteria
- [ ] NxtRole runs every morning for 7 days in a row with my real data and no critical errors.
- [ ] Scoring eval on my labels is at or above target, or a plan to reach it is agreed.
- [ ] Every PRD journey works on desktop and phone with real data.
- [ ] v1.0 release notes and maintenance routine written; tag created only with my OK.

## 13. Documentation updates
`README.md`, `CHANGELOG.md`, `docs/MAINTENANCE.md`, `docs/FEEDBACK.md`, `docs/KNOWN_ISSUES.md`,
`docs/ROADMAP.md` (what comes next), `docs/LEARNING_LOG.md` (a final "skills I can put on my resume" list).

## 14. Completion report
`CLAUDE.md` section 9 format, plus a one-page launch summary and the list of resume-ready skills.

## 15. Approval
Stop. Write "NxtRole v1.0 is ready. Waiting for your decision on what comes next." Do not commit, push or
tag without my OK.
