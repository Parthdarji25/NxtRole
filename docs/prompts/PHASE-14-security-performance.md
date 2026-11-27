# Phase 14 — Security and performance hardening

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-14-security-performance.md and follow it.`
> Follow `CLAUDE.md`. No commits. No new features: harden what exists.

## 1. Phase name and objective
**Security and performance hardening.** Review NxtRole like an attacker and like a busy user: close
security gaps, protect personal data, give me control over my data (export and delete), and make the app
fast under realistic load.

## 2. Context and dependencies
- Requires Phase 13 (full test suite green). Use `docs/SECURITY.md` (threat model) and the QA report.

## 3. Detailed implementation tasks
1. **OWASP Top 10 review** with evidence (file, test) for each: broken access control (IDOR tests for
   every endpoint), cryptographic failures, injection (SQL parameters only; no shell calls with input),
   insecure design, misconfiguration (debug off, docs exposure decision, CORS closed), vulnerable
   components, authentication failures, integrity (dependency pinning, lockfiles), logging and monitoring,
   SSRF.
2. **OWASP Top 10 for LLM apps:** prompt injection (job posts, notes, web pages, emails), sensitive data
   disclosure (identity stripping, contacts never sent), excessive agency (agents propose only), output
   handling (no AI HTML rendered), model denial of service (budgets, quotas), supply chain (model ids
   pinned in config).
3. **Web security headers:** Content-Security-Policy (with nonces if needed for Next.js), HSTS,
   X-Content-Type-Options, Referrer-Policy, Permissions-Policy, frame-ancestors none; cookies re-checked.
4. **Rate limits** on every mutating and expensive endpoint (AI, uploads, exports, webhooks, MCP), with
   clear 429 messages and `Retry-After`.
5. **Secrets and dependencies:** gitleaks across the full git history; `pip-audit` and `pnpm audit`;
   update vulnerable packages (with tests); confirm `.env` never tracked; key rotation steps documented.
6. **Files:** upload hardening re-check (type sniffing, size, storage paths, private access, deletion).
7. **Privacy controls:** "Export my data" (a zip of JSON + my files), "Delete my data" (confirm by typing,
   cascades across tables and storage, revokes sessions and MCP tokens), retention rules (raw email bodies
   deleted after processing; metadata 30 days; AI traces redacted), a privacy notice page in the app.
   If invites were decided: consent and India DPDP Act basics (notice, purpose, deletion on request).
8. **Performance:** database indexes from real query plans; N+1 checks; Redis caching for hot reads (brief,
   job detail) with correct invalidation; pagination everywhere; frontend bundle analysis, code-splitting
   for heavy screens (resume builder, ask), font loading; image and icon sizes.
9. **Load test:** k6 or Locust script for the main reads and a morning run at 5,000 jobs; record results
   and fixes.
10. **Penetration checklist:** try the top 15 attacks yourself (documented steps and results), including
    token tampering, cookie theft scenarios, CSRF on refresh/logout, webhook forgery, SSRF via manual job
    URL and research agent, XSS via job text and notes, path traversal in file ids.

## 4. UI mock references
`Settings` / `MSettings` (Privacy section) for export/delete and the privacy notice link; error and 429
states from the design system.

## 5. Recommended technologies
OWASP checklists, gitleaks, pip-audit, pnpm audit, Playwright (security E2E), k6 or Locust, Lighthouse,
`EXPLAIN ANALYZE`.

## 6. Files and modules to create or modify
`web/next.config.ts` (headers/CSP), `api/app/core/rate_limit.py` (coverage), `api/app/privacy/{export,
delete,retention,router}.py`, `web/app/(app)/settings/privacy/*`, `web/app/(public)/privacy/page.tsx`,
`load/` scripts, `docs/SECURITY.md`, `docs/security/pentest-<date>.md`.

## 7. Database and API requirements
Endpoints: `POST /api/privacy/export` (async, download link valid 24 h), `POST /api/privacy/delete`
(confirmation token), retention worker task. Indexes added via migrations with before/after timings.

## 8. Implementation sequence
Automated scans → OWASP and LLM reviews → fixes with tests → headers/CSP → rate limits → privacy export,
delete, retention → performance profiling → indexes and caching → load test → pentest checklist → re-run
the full suite.

## 9. Testing requirements
A test for every fixed issue; IDOR suite over all endpoints; CSP does not break any page (E2E); export
contains everything and nothing of anyone else; delete leaves no rows or files (verified by queries);
load-test thresholds recorded; full suite re-run green.

## 10. Edge-case checklist
- [ ] Delete my data while a background run is active (run stops safely).
- [ ] Export of a large account (async, size limits).
- [ ] CSP blocking a needed script (fixed with nonce, not `unsafe-inline` everywhere).
- [ ] Rate limit hit during normal use (limits tuned to real usage).
- [ ] A dependency update that breaks a feature (caught by tests).

## 11. Security considerations
This phase is the security review. Record residual risks and their owner in `docs/SECURITY.md`.

## 12. Acceptance criteria
- [ ] OWASP and LLM checklists complete with evidence; no open critical/high findings.
- [ ] No secrets in git history; dependencies audited and updated.
- [ ] Export and delete my data work and are tested.
- [ ] Performance budgets from Phase 13 still met under the load test.
- [ ] Full test suite green.

## 13. Documentation updates
`docs/SECURITY.md` (final), `docs/security/pentest-<date>.md`, `docs/TESTING.md`, `docs/KNOWN_ISSUES.md`,
`docs/DEPLOYMENT.md` (key rotation), `docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format. Explain: IDOR, XSS, CSRF, SSRF, CSP, prompt injection, why data deletion
matters.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 15." Do not commit.
