# Phase 9 — Pipeline, follow-ups, offers and coach

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-09-pipeline-followups-offers-coach.md and follow it.`
> Follow `CLAUDE.md`. No commits.

## 1. Phase name and objective
**Pipeline, follow-ups, offers and coach.** Track every application from saved to closed with rounds,
notes, history and undo; draft follow-ups at the right time; turn offers into monthly in-hand pay and
explain risky clauses; and show what is working with a weekly coach built from my real numbers.

## 2. Context and dependencies
- Requires Phases 4 (history and undo engine), 5 (AI gateway, files), 8 (minimal applications, worker,
  Today). No new accounts.
- Golden rule: NxtRole never sends anything. All messages are drafts I copy.

## 3. Detailed implementation tasks
1. **Pipeline:** stages exactly as the mock (Saved, Applied, Interview, Offer, Closed with a reason);
   board on desktop, stage tabs on phone; move by drag and drop **and** by buttons/keyboard; optimistic
   update with rollback; `version` check → 409 shows "This changed in another tab. Reload?"; card drawer
   with interview rounds (add, reschedule — shows "moved", outcome), notes, history newest first,
   "reapplied · linked" for a second application to the same company; every change writes history and
   shows a toast with Undo; double clicks do nothing twice (idempotency key).
2. **Follow-ups:** rules — first nudge on day 7 after applying, second on day 14, "likely ghosted" on
   day 21 with no reply; company reply-time stats from my own history ("usually replies in N days, from
   M applications", or "no history yet"); drafts written by the small model from pipeline data only
   (no invented facts; placeholders where needed); actions: "Copy and mark sent", "Snooze 3 days",
   "They replied", "Mark closed"; daily worker task creates due follow-ups; Today "Needs you" lists them.
3. **Offers:** "Record the offer" form from the mock (fixed, variable, joining bonus, joining date,
   reply-by date, notice, location); "Compare offers" view; **Offer check** page: CTC breakdown table,
   monthly in-hand estimate calculated **in code** (new tax regime slabs stored per financial year in a
   config table with the source noted, standard deduction, cess, employee PF on full basic or the
   ₹15,000 cap, professional tax by state, editable assumptions; "estimate, not tax advice"); optional
   upload of the offer letter → text → AI extracts clauses with exact quotes (verified) and plain-language
   notes; drafted "questions for HR".
4. **Progress:** Overview (counts by stage, reply rate, interviews, offers), Interview log ("Log an
   interview": company, role, date, round, questions asked, my answers; AI suggests "a better answer"
   and "to improve" as a proposal I can keep), "What to learn" (skills missing across my top matches and
   interview gaps).
5. **Weekly coach:** SQL counts for the last 7 and 30 days and since start: reply rate by speed of
   applying (within 24 h vs later), by source, by resume version; groups under 5 applications shown as
   "too few"; one "change for next week" worded by the AI **only from the computed numbers**; rule
   suggestions shown with confirm/dismiss (from Phase 7); "Add to next week" creates a task on Today.
6. **Today wiring:** "This week" strip from rounds and deadlines (interview = blue, deadline = red,
   to-do = ink, done = green, as in the mock); "Needs you" now includes follow-ups and offers due.

## 4. UI mock references
`Pipeline` / `MPipeline` (board, drawer, rounds, notes, history, record offer, compare offers),
`Nudges` / `MNudges`, `OfferCheck` / `MOfferCheck`, `Progress` / `MProgress` (Overview, Interview log,
What to learn), `Coach` / `MCoach`, `Brief` / `MToday` ("This week", "Needs you").
Note: the Pipeline mock shows "From Gmail" moves; those arrive in Phase 12.

## 5. Recommended technologies
TanStack Query (optimistic updates), a drag-and-drop library with keyboard support (for example
dnd-kit), SQLAlchemy, the Phase 5 gateway + Instructor (small model for drafts, main model for interview feedback).

## 6. Files and modules to create or modify
`api/app/applications/{models,service,router}.py` (full), `api/app/rounds/*`, `api/app/notes/*` (basic,
embeddings later), `api/app/followups/{rules,drafts,service,router}.py`,
`api/app/offers/{models,tax,calc,clauses,router}.py`, `api/app/offers/tax_tables/*.json`,
`api/app/progress/{stats,coach,interviews,router}.py`, migrations for `rounds`, `notes`, `offers`,
`follow_ups`, `interview_logs` (if not in notes), `tasks`; web routes `/pipeline`, `/pipeline/offers/[id]`,
`/follow-ups`, `/progress`, `/progress/coach`; Today updates.

## 7. Database and API requirements
Tables: full `applications`, `rounds`, `notes`, `offers`, `follow_ups`, interview logs, tasks.
Endpoints: applications CRUD + move (version), rounds CRUD, notes CRUD, offers CRUD + `/check`,
`/compare`, clauses upload; follow-ups list + actions; progress overview; coach weekly; interview log CRUD.

## 8. Implementation sequence
Applications full model + move + history → board UI with keyboard alternative → rounds → notes →
follow-up rules + worker task + drafts → follow-ups UI → offers form + compare → tax tables + calculator
with tests → offer check page → clause extraction → progress overview → interview log → coach → Today wiring.

## 9. Testing requirements
Unit: stage transitions; follow-up day maths in IST; reply-time stats; tax calculator against worked
examples I can check by hand (include the calculation in the test name or comment); coach with small
samples; clause quote verification. Integration: move with stale version → 409; undo after a later change
→ blocked with a clear message; double-click move creates one event. Frontend: optimistic move rolls back
on error; keyboard move. Playwright: apply → follow-up due on day 7 (with a fixed clock) → copy and mark
sent; record offer → offer check shows in-hand; coach renders "too few" correctly.

## 10. Edge-case checklist
- [ ] Two tabs editing one card (409); double clicks.
- [ ] Undo after later changes.
- [ ] Deleting an application that has rounds, notes and an offer (confirm; history kept).
- [ ] Follow-up while I already got a reply (stops); snooze over a weekend.
- [ ] Offer reply-by date passed; missing or invalid salary inputs; tax table missing for the year (warn).
- [ ] Offer letter scanned or protected (same handling as Phase 5).
- [ ] Coach with zero applications; division by zero; groups under 5.
- [ ] Rounds in different time zones ("as in the invite").

## 11. Security considerations
Offer letters and notes are personal data: private storage, identity stripped before AI, no logging;
calculations in code (AI never computes money); every query user-scoped.

## 12. Acceptance criteria
- [ ] I can move applications through every stage on desktop and phone, with history and undo.
- [ ] Follow-ups appear on the right days with drafts I can copy; nothing is ever sent by NxtRole.
- [ ] Offer check gives an in-hand estimate matching a hand-checked example, and lists clauses with quotes.
- [ ] Progress and the weekly coach show my real numbers, with "too few" where samples are small.
- [ ] Screens match the mocks; all tests, lint, types and build pass.

## 13. Documentation updates
`docs/API_DOCUMENTATION.md`, `docs/DATABASE_SCHEMA.md`, `docs/DECISIONS.md` (tax table source and
yearly update process), `docs/TESTING.md`, `docs/KNOWN_ISSUES.md`, `docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format. Explain: optimistic UI, version conflicts, why money maths is never done by
the AI, how the coach avoids misleading small numbers.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 10." Do not commit.
