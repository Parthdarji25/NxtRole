# Phase 10 — Agents: application pack, company research, Studio, resume and interview prep

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-10-agents-studio-resume-prepare.md and follow it.`
> Follow `CLAUDE.md`. No commits. If this phase is too big for one go, propose parts 10a–10d with a
> clean stopping point after each and wait for my OK.

## 1. Phase name and objective
**Agents and writing tools.** Add multi-step AI agents that do real work but always stop for my
approval: the application pack (research → pick facts → write → check → I approve), the company research
agent, the job-page finder, the Studio review queue, the resume builder with ATS and keyword checks and
exports, and interview preparation with a mock interview.

## 2. Context and dependencies
- Requires Phases 5 (gateway, facts), 7 (scores), 8 (worker, runs), 9 (applications, rounds, notes).
- Decisions: resume export (M6), voice (M7). Read the current LangGraph docs (checkpointer, interrupt,
  resume) before coding.

## 3. Detailed implementation tasks
1. **Agent framework:** LangGraph with the Postgres checkpointer; every run recorded in `agent_runs`
   (tool calls, tokens, status); budgets per agent (max 6 tool calls, recursion limit, timeout, token
   cap); tool allow-list per agent; untrusted text (web pages, job posts) in tags; progress streamed to
   the browser with server-sent events read through `fetch` (because `EventSource` cannot send the
   bearer token); a run survives a restart and resumes from its checkpoint; side effects only after the
   approval step or made idempotent.
2. **Application pack agent:** nodes `research` (company brief, reuse cache) → `pick_facts` (from the
   approved profile only) → `write` (tailored resume bullets, a short note, screening answers; tone
   Warm / Formal / Brief as in Studio) → `check` (code fact-check: no new skills, numbers or employers
   versus my facts; then the judge model from a different family checks each bullet; up to 2 rewrites)
   → `approve` (interrupt; the UI shows the pack). Unknown values become `[1]`, `[2]` blanks that block
   approval and export until I fill them. Approving saves a `documents` version; "Open the company's page"
   and "Copy all answers"; "I applied" moves the card to Applied.
3. **Company research agent:** read-only tools: fetch the company careers page, its own job posts, its
   blog/news page if linked, GitHub organisation (public API), Hacker News search (public API). SSRF
   guard (https only, public IPs only, no redirects into private ranges, 2 MB and 10 s limits). Output:
   what they build, stack counted from their job posts, recent items with dates, hiring now, "not found
   in any source" list, questions worth asking — every item with a source and date. Cache 7 days; match
   companies by domain, not just name.
4. **Job-page finder agent** (Sources and memory → "Add a company"): from a name or URL, find the careers
   page, detect the board, test the feed, then ask me before adding (upgrade of the Phase 6 detection).
5. **Overnight packs:** in the morning run, pre-draft packs for the top 3 High-trust matches (as drafts in
   Studio, never approved automatically).
6. **Studio:** review queue of drafts needing me (packs, follow-ups, interview feedback), with context,
   tone switch and the same approve/edit flow.
7. **Resume builder:** resume variants built only from my facts; templates Classic / Compact / Modern;
   tabs Keywords (matched vs missing for a chosen job; missing ones can go to my learning plan, never
   added as fake skills), ATS check (rules: standard headings, no tables/columns in the export, contact
   details present, dates consistent, file type), Edit content, Export: PDF (print-ready A4 page from
   HTML), `.tex` (LaTeX with special characters escaped: `& % $ # _ { } ~ ^ \`), `.docx`. One-page
   overflow warning. Export blocked while blanks remain.
8. **Prepare:** per application with a round: sections The company, The process, Behavioural,
   Questions (filter: "Asked by them" from my own interview logs at that company; "Predicted for you"
   from the job post and my facts), Salary (from real salary ranges in jobs I have seen for similar roles,
   with counts), Sources; mock interview in text with rubric feedback and "how you sounded"; voice as an
   optional mode using the browser's speech recognition where available (M7).

## 4. UI mock references
`ApplyPack` / `MApplyPack`, `CompanyBrief` / `MCompany`, `Studio` / `MStudio`, `ResumeBuilder` / `MResume`,
`Prepare` / `MPrepare`, `Memory` (Add a company), `JobCheck` ("Make application pack", "Research the
company"), `Brief` (drafts ready).

## 5. Recommended technologies
LangGraph (+ Postgres checkpointer), the Phase 5 gateway + Instructor, httpx with an SSRF-safe transport, SSE
(FastAPI `StreamingResponse`), python-docx, a LaTeX escaping helper, print CSS for PDF, Web Speech API
(optional).

## 6. Files and modules to create or modify
`api/app/agents/{framework,budget,stream,ssrf}.py`, `api/app/agents/pack/{graph,nodes,checks}.py`,
`api/app/agents/research/{graph,tools}.py`, `api/app/agents/finder/*`, `api/app/documents/*`,
`api/app/resume/{variants,ats,keywords,export_pdf,export_tex,export_docx}.py`, `api/app/prepare/*`,
prompts for each node (versioned); migrations for `documents`, research cache; web routes `/studio`,
`/studio/packs/[id]`, `/companies/[id]`, `/resume`, `/prepare/[applicationId]`, `web/lib/sse.ts`.

## 7. Database and API requirements
Tables: `documents` (kind, version, status, blanks), research cache, LangGraph checkpoint tables (created
by the library through a migration), `agent_runs` (existing). Endpoints: `POST /api/agents/pack`
(start), `GET /api/agents/runs/{id}/events` (SSE), `POST /api/agents/runs/{id}/approve`,
`POST /api/agents/runs/{id}/reject`, `POST /api/companies/{id}/research`, documents CRUD and export,
resume variants and checks, prepare sections, mock interview turns.

## 8. Implementation sequence
Framework (budgets, checkpoints, SSE) → research agent → pack agent with checks and interrupt → pack
screen → overnight packs → Studio → finder agent → resume builder (variants → keywords → ATS → exports)
→ Prepare sections → mock interview → tests and evals.

## 9. Testing requirements
Graph tests with recorded AI responses: happy path to approval; fact-check catches an invented skill;
judge rejects a bullet; budget exceeded ends cleanly; crash and resume from checkpoint; approve twice is
safe. Research: SSRF attempts (private IP, `localhost`, redirect to a private range) refused; page too
big; no results → "not found". Tailoring eval: 0 invented facts on 20 real job posts (report the number).
Exports: LaTeX special characters, one-page overflow, blanks block export. Playwright: job → make pack →
fill blank → approve → open company page.

## 10. Edge-case checklist
- [ ] Agent loops or keeps calling tools (budget stops it).
- [ ] A tool fails or times out (agent explains, no crash).
- [ ] Job closes before I approve the pack (warn).
- [ ] I edit a draft, then ask to regenerate (keep my edits unless I confirm).
- [ ] Two companies with the same name (match by domain).
- [ ] Research finds nothing; a page is not HTML; a huge page.
- [ ] `[N]` blanks; LaTeX special characters; resume longer than one page.
- [ ] Voice not supported in the browser (text mode).

## 11. Security considerations
Agents never send or submit anything; approval required before saving; least-privilege tools; SSRF guard
tested; prompt injection from web pages treated as data; identity stripped; research cache contains public
data only; exports generated server-side from my facts only.

## 12. Acceptance criteria
- [ ] I can make, review, fill blanks in and approve an application pack; nothing is saved before approval.
- [ ] Company briefs show sources and dates and say what was not found.
- [ ] Tailoring eval reports 0 invented facts on the test set.
- [ ] Resume exports work (PDF, .tex, .docx) and pass the ATS checks.
- [ ] Prepare and the mock interview work for a real upcoming round.
- [ ] Screens match the mocks; all tests, lint, types and build pass.

## 13. Documentation updates
`docs/ARCHITECTURE.md` (agents, graphs with Mermaid), `docs/API_DOCUMENTATION.md`,
`docs/DATABASE_SCHEMA.md`, `docs/SECURITY.md` (agents, SSRF), `docs/TESTING.md` (agent tests, tailoring
eval), `docs/DECISIONS.md` (export choice), `docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format, including the tailoring eval result. Explain: agent vs single AI call,
graphs and checkpoints, human-in-the-loop approval, LLM-as-judge, SSRF.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 11." Do not commit.
