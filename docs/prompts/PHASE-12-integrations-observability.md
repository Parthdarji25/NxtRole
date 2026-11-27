# Phase 12 — Integrations and observability

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-12-integrations-observability.md and follow it.`
> Follow `CLAUDE.md`. No commits.

## 1. Phase name and objective
**Integrations and observability.** Connect job emails from my Gmail safely through a script that runs
in my own Google account, turn alert emails into jobs and recruiter replies into pipeline updates, and
add error tracking and AI tracing so problems are visible. Make every external service fail gracefully.

## 2. Context and dependencies
- Requires Phases 6 (jobs), 9 (pipeline), 11 (all features in place).
- Decisions: Gmail script design (M4), auto-move vs proposal (open question 13).
- **Optional free accounts now:** Sentry and Langfuse (both do nothing when their keys are empty).
  I put the keys in `.env` myself.

## 3. Detailed implementation tasks
1. **Gmail script (`nxtrole-gmail.gs`):** generated per user from Onboarding step 4 with a personal
   webhook key; a Google Apps Script I paste into my own Google account; every 15 minutes it searches
   Gmail for job-alert emails (Naukri, LinkedIn, Instahyre — sender list in settings) and replies to my
   applications; sends minimal data (message id, date, sender domain, subject, plain-text body capped in
   size) to `POST /api/webhooks/gmail` signed with HMAC-SHA256 over timestamp + body. Step-by-step
   install guide in the UI (with screenshots) and a "Test connection" button.
2. **Webhook endpoint:** verify signature with a constant-time compare; reject timestamps older than 5
   minutes; dedupe by message id (replay protection); rate limit; size limit; store only what is needed
   in `inbound_emails` and delete bodies after processing (retention: 30 days for metadata).
3. **Alert emails → jobs:** one parser per sender format with recorded real emails (my own, with personal
   details removed) as fixtures; extracted jobs go through cleaning, dedupe and trust like any source.
4. **Replies → pipeline:** the small model classifies replies (interview invite, rejection, offer,
   other) with a quoted line as evidence; matched to an application by company and role; per decision 13:
   clear cases move the card with "Moved by Gmail · Undo" and a note, everything else becomes a proposal.
5. **Error tracking:** Sentry for web and API (environment, release, no personal data, scrubbing rules,
   source maps for the web build); off when no DSN.
6. **AI tracing:** Langfuse traces for every AI call and agent step (task, prompt id and version, model,
   tokens, latency, cost, eval scores linked), with message text redacted; off when no keys.
7. **Resilience review:** every external call (job APIs, AI providers, GitHub/HN/web fetch, push, Gmail
   webhook) has timeouts, retries where safe, a circuit breaker for repeated failures, and a visible
   health status (Settings › Search "source health", AI status banners).
8. **`check-config` complete:** reports every setting and tests every connection (database, Redis,
   storage, Groq, Adzuna, push keys, Sentry, Langfuse, webhook secret) with clear fixes.

## 4. UI mock references
`Onboarding` / `MOnboarding` step 4 ("Let replies update your pipeline", Gmail script, "Optional",
"Recommended · no domain needed"), `Pipeline` / `MPipeline` ("From Gmail", "Moved by Gmail · undo inside"),
`Settings` / `MSettings` (Agents → Inbox, Connections), `Jobs` (source health).

## 5. Recommended technologies
Google Apps Script (GmailApp, UrlFetchApp, time-driven trigger), HMAC-SHA256, FastAPI, Sentry SDKs
(Python, Next.js), Langfuse SDK, a small circuit-breaker helper.

## 6. Files and modules to create or modify
`api/app/integrations/gmail/{script_template.gs,router,verify,parse_alerts,classify}.py`,
`api/app/integrations/gmail/parsers/{naukri,linkedin,instahyre}.py`, `api/app/observability/{sentry,
langfuse,breaker}.py`, `api/app/cli.py` (check-config), migration for `inbound_emails`;
`web/sentry.*.config.ts`, onboarding step 4 UI, pipeline "moved by Gmail" UI.

## 7. Database and API requirements
Table `inbound_emails` (minimal, with retention). Endpoints: `POST /api/webhooks/gmail` (signed, no user
token), `POST /api/integrations/gmail/script` (generate), `POST /api/integrations/gmail/test`,
`DELETE /api/integrations/gmail` (rotate/revoke key).

## 8. Implementation sequence
Webhook verify + dedupe + limits → script generator + install guide → test connection → alert parsers →
reply classifier + pipeline moves/proposals → Sentry → Langfuse → resilience review → check-config → tests.

## 9. Testing requirements
Webhook: valid signature accepted; wrong signature, old timestamp, replayed message id, oversize body all
rejected. Parsers: recorded real alert emails for each sender. Classifier: recorded responses; low
confidence → proposal. Pipeline: auto-move writes history and can be undone. Sentry/Langfuse: disabled
when keys are empty; scrubbing removes emails and phone numbers (test the scrubber). Circuit breaker opens
after repeated failures and recovers.

## 10. Edge-case checklist
- [ ] Gmail script key leaked → rotate; old key rejected.
- [ ] Same email delivered twice; emails out of order.
- [ ] An alert format changes (parser fails safely, source health shows it).
- [ ] Reply that matches two applications (proposal asks me to choose).
- [ ] Sentry or Langfuse down (app unaffected).
- [ ] AI provider down for hours (breaker + pending states).

## 11. Security considerations
HMAC signatures, timestamp window, replay protection, minimal data, retention limits, no tokens in URLs,
personal data scrubbed from Sentry and Langfuse, webhook key rotatable, the script only reads Gmail and
sends to NxtRole (document its permissions in plain words).

## 12. Acceptance criteria
- [ ] With the script installed in my Google account, job-alert emails create jobs and a real reply moves
      the right card (or creates a proposal), with undo.
- [ ] Sentry shows a test error from web and API without personal data; Langfuse shows a redacted trace.
- [ ] `check-config` passes for every configured service and explains any missing one.
- [ ] All tests, lint, types and build pass.

## 13. Documentation updates
`docs/ARCHITECTURE.md` (Gmail flow), `docs/API_DOCUMENTATION.md`, `docs/SECURITY.md` (webhook, scrubbing,
retention), `docs/DEPLOYMENT.md` (Sentry, Langfuse, webhook secret rows), `docs/TESTING.md`,
`docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format. Explain: webhooks, HMAC signatures, replay attacks, observability, circuit
breakers.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 13." Do not commit.
