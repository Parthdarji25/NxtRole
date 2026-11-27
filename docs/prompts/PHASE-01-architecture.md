# Phase 1 — Technical architecture

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-01-architecture.md and follow it.`
> Follow `CLAUDE.md`. **Documents only: no application code in this phase.**

## 1. Phase name and objective
**Technical architecture.** Turn the PRD into a buildable design: stack with verified versions,
system architecture, full database schema, API catalogue, design system spec, security threat model
and test strategy. Every later phase follows these documents.

## 2. Context and dependencies
- Requires Phase 0 approved: `docs/PRD.md`, `docs/DECISIONS.md`, `docs/mocks/MOCK_INVENTORY.md`.
- Proposed stack: `docs/ROADMAP.md` section C. Keep it unless you find a strong reason not to;
  if so, explain the trade-off and ask me before changing it.

## 3. Detailed implementation tasks
1. **Verify the stack.** For each tool in ROADMAP C, check the official docs for the current stable
   version and anything that changed (for example Next.js 16 renamed `middleware.ts` to `proxy.ts`;
   check LangGraph, LiteLLM, Instructor, MCP SDK, fastembed, pgvector, Tailwind v4, shadcn/ui).
   Record versions, reasons and rejected alternatives in `docs/TECH_STACK.md`.
2. **`docs/ARCHITECTURE.md`:** components and responsibilities; Mermaid diagrams for (a) the system,
   (b) sign-in and token refresh, (c) the morning run, (d) the application pack agent with approval,
   (e) the Gmail webhook, (f) local versus production deployment. Folder structure for `web/` and `api/`
   (routers → services → repositories; one module per domain). How background work runs (arq worker
   locally; GitHub Actions burst runs in production). How AI calls flow through one gateway.
3. **`docs/DATABASE_SCHEMA.md`:** every table with columns, types, nullability, defaults, constraints,
   indexes and a Mermaid ER diagram. Start from this list; refine it, and ask before removing anything:
   - Global (shared by all users): `sources`, `companies`, `jobs` (normalised fields, INR salary range,
     city, remote type, experience range, notice requirement, sanitised text, url, posted/first/last
     seen, closed_at, content_hash, fingerprint, repost_count, `embedding vector(384)`, `search tsvector`),
     `job_sightings` (same job seen on other sources), `trust_checks` (level, signals, rules_version).
   - Per user: `users`, `refresh_tokens` (family_id, token_hash, expires/used/revoked), `files`,
     `profile_versions` (facts JSON with fact ids, status), `rules` (kind, value, source you/learned,
     status active/suggested/dismissed, evidence), `company_watches`, `job_scores` (profile_version,
     prompt_version, model, two scores, unsure, reasons with quotes), `user_job_states` (seen, saved,
     skipped + reason, hidden), `eval_labels`, `briefs`, `applications` (stage, version for 409),
     `rounds`, `notes` (with embedding), `offers`, `follow_ups`, `documents` (packs, resume variants,
     drafts), `proposals` (kind, target, payload, base_version, status), `events` (history: before,
     after, actor, proposal_id, undone_by), `agent_runs`, `contacts` (from the LinkedIn CSV; never sent
     to AI), `notifications` (dedupe_key), `push_subscriptions`, `mcp_tokens`, `mcp_calls`,
     `inbound_emails` (minimal fields), `ai_usage` (per day/provider/model).
   - Every per-user table has `user_id` with a foreign key and an index. Explain the global vs per-user
     split (it keeps the app ready for invited users later). Migration strategy: Alembic, one migration
     per change, "expand then contract" for risky changes.
4. **`docs/API_DOCUMENTATION.md`:** conventions (base path `/api`, JSON, error shape
   `{"detail":{"code","message"}}`, cursor pagination, `Idempotency-Key` header on create actions,
   `If-Match`/version field for updates → 409 on conflict, rate-limit headers) and a catalogue table per
   module: method, path, auth, request, response, errors. Modules: health, auth, account, files, profile,
   rules, sources and companies, jobs (list, search, detail, add), trust, scores and labels, brief,
   alerts and push, applications and rounds, notes, offers, follow-ups, documents and packs, agent runs
   (SSE progress), company research, chat (SSE), network, coach and stats, proposals (approve, reject,
   undo), history, settings (AI usage, evals), MCP tokens, webhooks (Gmail).
5. **`docs/DESIGN_SYSTEM.md`:** tokens (from `design-tokens.css`, light and dark), type scale and
   fonts, spacing, radius, motion, breakpoints (as decided for tablet), and a component inventory taken
   from the mocks (`docs/mocks/source/Foundations.dc.html` first): each component, its variants and
   states, and which screens use it. Rules: one blue primary button per screen; red only for due
   today/tomorrow and errors.
6. **`docs/SECURITY.md`:** data classification (from the PRD), threat model per area (auth, files,
   AI prompt injection, SSRF from URL fetching, webhooks, MCP tokens, XSS from job HTML, IDOR between
   users), controls planned for each, and secrets handling.
7. **`docs/TESTING.md`:** test layers and tools (ROADMAP G), folder layout, naming, fixtures policy
   (recorded real responses only, with source and date), and the **edge-case register**: a table with
   ID, edge case, phase, expected behaviour, test name (filled as phases build them).
8. **`docs/DEPLOYMENT.md` (skeleton):** local vs production, and the accounts and keys checklist
   (Groq, Cerebras, Adzuna, Sentry, Langfuse, Supabase, Upstash, Vercel, GitHub secrets): what each is
   for, which phase needs it, where the value goes. No values.
9. Add decision records to `docs/DECISIONS.md` for every real choice (stack, auth, global vs per-user
   data, hosting, background work, AI gateway).

## 4. UI mock references
All screens (for data needs and components). Component inventory from `Foundations.dc.html`, `Nav`,
`TopBar`, `MTabs`, and repeated patterns across screens (page header with mono kicker + heading + lead,
chips, trust badges, toggles, drawers).

## 5. Recommended technologies
As in ROADMAP C. Mermaid for diagrams.

## 6. Files and modules to create or modify
Create: `docs/ARCHITECTURE.md`, `docs/TECH_STACK.md`, `docs/DATABASE_SCHEMA.md`,
`docs/API_DOCUMENTATION.md`, `docs/DESIGN_SYSTEM.md`, `docs/SECURITY.md`, `docs/TESTING.md`,
`docs/DEPLOYMENT.md`. Modify: `docs/DECISIONS.md`, `docs/ROADMAP.md` (only if the plan changes).

## 7. Database and API requirements
As in tasks 3 and 4. Every FR in the PRD must map to at least one table and one endpoint or job;
include that mapping table at the end of `docs/API_DOCUMENTATION.md`.

## 8. Implementation sequence
Verify stack → architecture → schema → API → design system → security → testing → deployment skeleton
→ decisions → traceability check (FR → table → endpoint → screen → phase).

## 9. Testing requirements
Documentation checks: every FR is traceable; every mock component is in the inventory; every table
used by an endpoint exists; no endpoint lacks auth rules.

## 10. Edge-case checklist
Seed the edge-case register with at least: login lockout, expired token mid-use, two tabs refreshing,
reused refresh token, scanned or protected PDF, file over 5 MB, source timeout/429, wrong board token,
same job on several sites, reposts, closed jobs, salary formats (LPA, monthly, USD), missing posted
date, city aliases, prompt injection in job text, all AI providers limited, malformed AI output,
quote not found, no approved profile, `[N]` placeholders, LaTeX special characters, two tabs editing
one card (409), double clicks, undo after later changes, agent tool loops, Redis down, overlapping
runs, cron in UTC (07:00 IST = 01:30 UTC), hosting time limits, free database pausing, push
subscription expired, webhook replay.

## 11. Security considerations
Threat model as in task 6. Decide token lifetimes, cookie flags, CSRF approach (SameSite=Strict on a
cookie scoped to `/api/auth` plus a custom request header), password hashing (Argon2), SSRF rules for
any URL the server fetches, webhook signatures (HMAC + timestamp), MCP token scopes.

## 12. Acceptance criteria
- [ ] All eight documents exist, are consistent with each other and with the PRD and decisions.
- [ ] Stack versions were checked against official docs (sources listed in TECH_STACK.md).
- [ ] Every FR traces to tables, endpoints, screens and a phase.
- [ ] Edge-case register seeded; threat model complete.
- [ ] No application code created (`git diff` shows docs only).

## 13. Documentation updates
The eight documents above, DECISIONS, LEARNING_LOG (entries for: architecture, schema, API, threat
model), ROADMAP if changed.

## 14. Completion report
`CLAUDE.md` section 9 format. Explain in "What I learned": what an API is, what a database schema and
a migration are, what a token is, what a threat model is.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 2." Do not commit.
