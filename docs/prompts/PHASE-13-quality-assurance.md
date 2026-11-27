# Phase 13 — Quality assurance

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-13-quality-assurance.md and follow it.`
> Follow `CLAUDE.md`. No commits. Do not add features in this phase; fix defects only.

## 1. Phase name and objective
**Quality assurance.** Prove the whole product works the way the PRD and mocks say: complete end-to-end
journeys, cross-browser and responsive checks, visual comparison with the mocks, accessibility, AI evals
in CI, performance budgets, and a regression suite. Fix every critical and high defect found.

## 2. Context and dependencies
- Requires Phases 0–12 complete. Use `docs/PRD.md` (journeys and FRs), `docs/TESTING.md` (edge-case
  register), `docs/mocks/MOCK_INVENTORY.md`.

## 3. Detailed implementation tasks
1. **Traceability audit:** for every FR and every edge-case register row, find the test that covers it;
   list gaps; write the missing tests.
2. **End-to-end suite (Playwright):** one spec per journey in the PRD (set up, morning, apply, track,
   follow up, prepare, decide, improve, ask) using a seeded **test** database built only from recorded
   fixtures in `tests/fixtures` (never the app's real data); run against a production build.
3. **Browsers and sizes:** Chromium, Firefox and WebKit; widths 390, 768, 1024 and 1440; light and dark.
4. **Visual regression:** screenshot baselines for every route and main state; review differences
   against the mocks with me before updating any baseline.
5. **Accessibility:** axe on every route (no serious or critical issues); keyboard-only run of each
   journey; focus order and visible focus; screen-reader spot check with NVDA on Windows for login, Today,
   job detail and application pack; colour contrast in both themes; 44 px touch targets on phone.
6. **AI quality in CI:** scoring, tailoring, Q&A and tool-choice evals run on recorded responses in CI and
   fail the build below target; a separate manual workflow runs them live against the providers.
7. **Performance:** Lighthouse (mobile) on landing, Today, Jobs and job detail: LCP under 2.5 s, CLS under
   0.1, total JS budget agreed with me; API timing for the main reads (p95 under 300 ms locally with
   realistic data volumes: 5,000 jobs, 300 applications); fix slow queries with `EXPLAIN ANALYZE`.
8. **Regression and bug bash:** run the full suite; give me a 30-minute manual test script for desktop
   and phone; triage findings (critical/high/medium/low) into `docs/KNOWN_ISSUES.md`; fix critical and
   high; re-run everything.
9. **Coverage report:** backend services ≥ 80% lines; key frontend components covered; report gaps that
   matter rather than chasing numbers.

## 4. UI mock references
Every screen in `docs/mocks/MOCK_INVENTORY.md`, desktop and phone, light and dark.

## 5. Recommended technologies
Playwright (multi-browser, screenshots, axe-core), Vitest, pytest + coverage, Lighthouse CI, NVDA,
GitHub Actions (CI matrix).

## 6. Files and modules to create or modify
`web/tests/e2e/*.spec.ts` (per journey), `web/tests/visual/*`, `web/tests/a11y/*`, `lighthouserc.json`,
`api/tests/**` (gap tests), `.github/workflows/ci.yml` (matrix, evals, Lighthouse), `docs/TESTING.md`,
`docs/KNOWN_ISSUES.md`, `docs/qa/manual-test-script.md`, `docs/qa/report-<date>.md`.

## 7. Database and API requirements
A test-only seed script that loads recorded fixtures into the test database; never used in production.
No schema changes unless fixing a defect (then with a migration and a test).

## 8. Implementation sequence
Traceability audit → missing unit/integration tests → journey E2E → browsers and sizes → visual baselines
with my review → accessibility → evals in CI → performance → bug bash → fixes → full re-run → report.

## 9. Testing requirements
This whole phase is testing. Report every suite with the command, the number of tests, passes, failures
and duration. Never mark a suite green that was not run.

## 10. Edge-case checklist
Re-run every row in the edge-case register; additionally: browser back/forward and refresh in the middle
of each flow; offline then online on phone; session expiry in the middle of a long form; slow 3G
throttling; very large data sets (5,000 jobs, long histories); time-zone change on the device.

## 11. Security considerations
Include auth and authorization tests in E2E (signed-out access, another user's ids); confirm no personal
data in logs, screenshots or test artifacts committed to the repo.

## 12. Acceptance criteria
- [ ] Every FR and edge case has a passing test (traceability table in `docs/TESTING.md`).
- [ ] All journeys pass on three browsers and four widths, light and dark.
- [ ] No serious accessibility issues; keyboard-only journeys pass.
- [ ] Evals meet targets in CI; performance budgets met.
- [ ] No open critical or high defects; QA report written.

## 13. Documentation updates
`docs/TESTING.md` (final strategy, traceability, how to run each suite), `docs/KNOWN_ISSUES.md`,
`docs/qa/*`, `README.md` (test commands), `docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format, plus the QA report link. Explain: regression, flaky tests, visual
regression, accessibility testing, performance budgets.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 14." Do not commit.
