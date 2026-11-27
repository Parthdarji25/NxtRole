# Phase 0 — Product discovery and PRD

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-00-discovery.md and follow it.`
> Follow `CLAUDE.md` at all times. **Do not write or change application code in this phase.**

## 1. Phase name and objective
**Product discovery and PRD.** Understand NxtRole completely, check what already exists in the
repository, settle the open product questions with me, and write the Product Requirements Document
that every later phase builds from.

## 2. Context and dependencies
- No earlier phase. Inputs: `CLAUDE.md`, `docs/ROADMAP.md` (sections A to J), `docs/mocks/MOCK_INVENTORY.md`,
  `docs/mocks/source/*.dc.html`, `docs/mocks/design-tokens.css`, `docs/LEARNING-GUIDE.md` if present,
  and anything else already in the repository.
- `docs/archive/` (for example the old `BUILD-PROMPT.md`) is history: read it for background, do not follow it.

## 3. Detailed implementation tasks
1. **Inspect the repository** without changing it: full file tree, `git status`, `git log --oneline -20`,
   every README and doc, any existing `web/` or `api/` code, config files, `.env.example` files.
   For existing code, list what it does, its quality, whether it matches `CLAUDE.md` and the roadmap,
   and what must be preserved. Do not run code that changes anything.
2. **Inspect every mock** in `docs/mocks/source/` (desktop and phone) and the older PNGs. For each
   screen, note: purpose, main components, user actions, data it needs, and states shown. Confirm or
   correct `docs/mocks/MOCK_INVENTORY.md` (routes, phases, conflicts M1 to M11).
3. **Resolve open questions with me, one at a time.** Use the list in `docs/ROADMAP.md` section I
   (questions 1 to 13) plus any new ones you find. For each: explain it in simple words, give options
   with pros and cons, give your recommendation, wait for my answer, then record it in
   `docs/DECISIONS.md` as a short decision record (ID, date, decision, why, alternatives).
4. **Write `docs/PRD.md`** with these sections:
   1. Vision and one-line pitch
   2. Users and personas (me first; invited users later if decided)
   3. Problems and goals
   4. User journeys (the 9 in `docs/ROADMAP.md` A), each as numbered steps naming the screens used
   5. Features by module (Auth, Profile, Sources, Jobs, Trust, Matching, Memory, Today, Alerts,
      Pipeline, Follow-ups, Offers, Coach, Agents/Studio, Resume, Prepare, Ask, Notes, Network, MCP,
      Gmail integration, Settings), each with priority (MVP / later) and the mock it appears in
   6. Functional requirements, numbered `FR-001`… each testable ("Given/When/Then" where useful)
   7. Non-functional requirements: performance, security, privacy, accessibility (WCAG 2.2 AA),
      reliability, cost (free tiers), maintainability, observability
   8. MVP scope, out of scope, and "never" list (auto-apply, sending for me, scraping logged-in sites)
   9. Success metrics (from ROADMAP A)
   10. Assumptions, risks, dependencies on third parties (job APIs, AI providers, hosting)
5. **Start the documentation set**: create `docs/DECISIONS.md` (with the records from task 3),
   `docs/KNOWN_ISSUES.md` (empty table), `docs/LEARNING_LOG.md` (first entry: what a PRD is).
   Update `docs/ROADMAP.md` only if a decision changes a phase (say what changed).

## 4. UI mock references
All screens in `docs/mocks/MOCK_INVENTORY.md`. Pay special attention to conflicts M1 (login),
M2 (alerts), M3 (AI providers), M4 (Gmail script), M8 (tablet), M9 (missing states), and open
question 13 in `docs/ROADMAP.md` (Gmail moving pipeline cards automatically).

## 5. Recommended technologies
None to install. Use reading tools, `git status/log/diff`, and Markdown. Diagrams in Mermaid.

## 6. Files and modules to create or modify
Create: `docs/PRD.md`, `docs/DECISIONS.md`, `docs/KNOWN_ISSUES.md`, `docs/LEARNING_LOG.md`.
Modify if needed: `docs/mocks/MOCK_INVENTORY.md`, `docs/ROADMAP.md`. Nothing else.

## 7. Database and API requirements
None in this phase. Capture data needs per screen inside the PRD feature list (they feed Phase 1).

## 8. Implementation sequence
1 inspect repo → 2 inspect mocks → 3 summarise findings to me (what exists, what conflicts) →
4 ask questions one at a time and record decisions → 5 write PRD → 6 create the other docs →
7 self-review: every mock screen appears in the PRD, every FR maps to a screen or a background job.

## 9. Testing requirements
No code tests. Do a documentation check instead: list every screen in the inventory and the FRs that
cover it; list every FR and the screen or job that delivers it; report any gaps.

## 10. Edge-case checklist
Capture, in the PRD, the product edge cases each module must handle (later phases test them):
first run with no data; no approved profile; no sources; all AI limits used; the same job on several
sites; scams; reposted and closed jobs; offline phone; two tabs; undo after later changes; data export
and deletion.

## 11. Security considerations
Classify data in the PRD: secret (passwords, tokens, keys), personal (resume, contacts, emails, offers),
internal (jobs, scores). State who may see each and where it may go (for example: personal data never
to providers that train on prompts).

## 12. Acceptance criteria
- [ ] I received a clear summary of the repository, existing code and what must be preserved.
- [ ] Every open question is answered by me and recorded in `docs/DECISIONS.md`.
- [ ] `docs/PRD.md` has all 10 sections; every mock screen is referenced; FRs are numbered and testable.
- [ ] `docs/mocks/MOCK_INVENTORY.md` is verified or corrected.
- [ ] No application code was created or changed (`git diff` shows only docs).

## 13. Documentation updates
PRD, DECISIONS, KNOWN_ISSUES, LEARNING_LOG, MOCK_INVENTORY (and ROADMAP if a decision changes it).

## 14. Completion report
Use the 12-point format in `CLAUDE.md` section 9. Under "What I learned", explain what a PRD, a user
journey, MVP scope and a non-functional requirement are.

## 15. Approval
Stop after the report. Write "Waiting for your approval before Phase 1." Do not commit.
