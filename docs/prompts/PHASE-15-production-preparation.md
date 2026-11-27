# Phase 15 — Production preparation

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-15-production-preparation.md and follow it.`
> Follow `CLAUDE.md`. No commits or pushes without my explicit OK. This phase is done **together, step by
> step**: you explain each step, I create accounts and paste keys into the right place myself.

## 1. Phase name and objective
**Production preparation.** Create the production environment on free tiers, configure it safely, set up
deployment, monitoring, backups and recovery, and write the runbook, so launch day is calm and reversible.

## 2. Context and dependencies
- Requires Phase 14 (secure, tested). Use `docs/DEPLOYMENT.md` (accounts and keys checklist).
- No domain purchase: the app uses its `vercel.app` address with automatic HTTPS.
- Read the current docs for Vercel (Next.js and FastAPI deployment, function limits, regions),
  Supabase (pgvector, pooler, Data API, storage), Upstash Redis and GitHub Actions secrets before acting.

## 3. Detailed implementation tasks
1. **Accounts, one at a time with me** (what it is for, free-tier limits, where the key goes):
   Supabase (Postgres + storage, region close to India), Upstash Redis, Vercel, Groq
   (production key; Cerebras stays off, D-024), Adzuna, Sentry, Langfuse, GitHub repository secrets. I enter every value myself in
   Vercel, GitHub secrets or my local `.env.production` (git-ignored).
2. **Environments:** development (Docker), preview (Vercel previews: no production data; separate small
   database or features that need data disabled), production. Settings per environment documented.
3. **Database:** enable pgvector; turn the Data API off; enable Row Level Security on all tables with no
   policies (defence in depth); use the pooler connection string with prepared statements disabled for
   the async driver as Supabase's docs require; run Alembic migrations against production from a manual
   step I trigger (local command or a `workflow_dispatch` workflow with a protected environment); create my
   user with the CLI against production.
4. **Storage:** private Supabase bucket behind the storage interface from Phase 5; signed, short-lived
   download links; delete works.
5. **Redis:** Upstash connection (TLS URL) for cache, locks, rate limits (the queue is a PostgreSQL table, D-026); verify locks.
6. **Deploy:** `web/` and `api/` as Vercel projects (or the structure Vercel's current docs recommend),
   functions in a region close to India; Next.js rewrites to the production API; environment variables
   set; build commands; long work never inside web requests (worker runs in GitHub Actions on schedule).
7. **Schedules:** production workflows (`morning.yml` 05:30 IST, `discovery.yml` hourly 07:00 to 21:00 IST, D-030, D-040) with secrets; manual
   `workflow_dispatch` for an on-demand run; run failures notify me by push.
8. **Monitoring:** Sentry alerts (new issue, error spike); Langfuse dashboard; a scheduled health check
   (`/api/health/ready`) that alerts me if it fails twice; AI quota warnings.
9. **Backups and recovery:** nightly `pg_dump` in GitHub Actions, encrypted with my public key before it
   is stored (private artifact, retention 30 days), plus storage file list; a written restore procedure;
   **one real restore test** into a scratch database.
10. **Runbook and rollback:** `docs/DEPLOYMENT.md` final: deploy steps, rollback (Vercel instant
    rollback; database "expand then contract" so rollback never needs a down-migration), common
    incidents (AI limits, source down, database paused, Redis down, push failing, schedule not running)
    with exact steps.
11. **Final `check-config` in production mode:** every line passes.

## 4. UI mock references
None new. Verify production screens still match the mocks after deploy (spot check).

## 5. Recommended technologies
Vercel, Supabase (Postgres + pgvector + Storage), Upstash Redis, GitHub Actions (secrets, environments,
schedules), Sentry, Langfuse, `pg_dump` + `age` or GPG for encryption.

## 6. Files and modules to create or modify
`.github/workflows/{deploy-migrations,schedule,backup,healthcheck}.yml`, `vercel.json` files if needed,
`api/app/config.py` (production settings), `api/app/files/storage_supabase.py`, `docs/DEPLOYMENT.md`
(final), `docs/runbook/*.md`, `README.md` (deploy section), `.env.production.example`.

## 7. Database and API requirements
Production migrations applied; RLS on; Data API off; extensions verified; no API changes except
configuration.

## 8. Implementation sequence
Explain the plan → accounts one by one → database → storage → Redis → deploy preview → deploy production
→ schedules → monitoring → backups + restore test → runbook → production `check-config` → spot checks.

## 9. Testing requirements
Smoke tests against preview then production (sign in, Today, Jobs, job detail, pipeline move + undo, pack
approval, push alert, export my data); scheduled run once manually; backup restore test; health-check
alert test (simulate a failure); rollback drill on preview.

## 10. Edge-case checklist
- [ ] Wrong or missing production variable (check-config catches it).
- [ ] Database paused after inactivity (schedule keeps it active; alert if it fails).
- [ ] Function time limits (no long work in requests).
- [ ] Preview deployments never touching production data.
- [ ] Secret accidentally printed in a log (scrubbing verified).
- [ ] Schedule delayed or skipped by GitHub (alert after a missed run).

## 11. Security considerations
Least-privilege keys; secrets only in Vercel and GitHub secrets; protected environment for production
migrations; RLS and Data API off; encrypted backups; HTTPS everywhere; security headers verified on the
live site; key rotation steps tested once.

## 12. Acceptance criteria
- [ ] Production is live at the `vercel.app` address over HTTPS and every smoke test passes.
- [ ] Scheduled runs work in production; failures alert me.
- [ ] A backup was restored successfully into a scratch database.
- [ ] Runbook and rollback steps are written and the rollback drill worked.
- [ ] `check-config` passes in production mode.

## 13. Documentation updates
`docs/DEPLOYMENT.md` (final), `docs/runbook/*`, `docs/SECURITY.md` (production settings),
`docs/KNOWN_ISSUES.md`, `README.md`, `docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format. Explain: environments, deployment, serverless limits, backups vs restores,
rollback, monitoring and alerting.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 16." Do not commit or push without my OK.
