# Phase 5 — AI gateway, resume and profile

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-05-ai-gateway-and-profile.md and follow it.`
> Follow `CLAUDE.md`. No commits.

## 1. Phase name and objective
**AI gateway, resume and profile.** Build the one safe path every AI call goes through, then use it for
the first real feature: upload my resume, turn it into a list of facts I review and approve, and record
what I am looking for. Everything later (scoring, packs, chat) depends on an approved profile.

## 2. Context and dependencies
- Requires Phase 4 (auth, proposals, history).
- **Key needed now:** a free Groq API key. Guide me to create it (console.groq.com → API keys), put it
  in `api/.env` as `GROQ_API_KEY` myself, never in chat. Also check Groq's data controls (zero data
  retention option) and note what is available. Groq is the only active provider (D-024); a Cerebras adapter may exist but stays off.
- Decisions: AI providers (M3), privacy rules in `CLAUDE.md` section 3.

## 3. Detailed implementation tasks
1. **AI gateway** (`api/app/ai/gateway.py`, our own, no LiteLLM, D-025) on Groq's official client with a
   configurable **model chain**: `main` (gpt-oss-120b, reasoning effort high, temperature 0.2), then other
   free Groq models, `judge` (a different family on Groq), `small` (a small Llama). Read the current model ids,
   limits and the zero-data-retention switch from the Groq console. Add token budgeting and call pacing
   (200K tokens a day and 8K a minute on the large model, D-033). Instructor for typed
   output (Pydantic models, max 2 retries). Timeouts, retries with backoff, fallback on 429/5xx. Never
   route personal data to providers outside the allowed list.
2. **Prompt registry:** prompts stored as files with an id and version (for example
   `profile_extract@v1`); every result stores prompt id, version and model.
3. **Privacy guard:** before each call remove my name, email, phone (Indian formats like +91 98765 43210),
   address and profile links; replace with tokens; restore after. Untrusted text is wrapped in tags with
   an instruction to ignore instructions inside it.
4. **Usage tracking:** `ai_usage` per day, provider and model (requests, tokens, errors, rate-limit
   hits); a service that reports "normal / using backup / all limits used" for the UI banners later.
5. **Recorded responses for tests:** a cassette mechanism: "record" mode calls the real API and saves
   the response (with prompt id, model and date in the file name) under `api/tests/fixtures/ai/`;
   "replay" mode (default in tests and CI) never calls the network.
6. **File storage abstraction:** local private folder in development (`api/var/uploads`, git-ignored),
   Supabase Storage later behind the same interface; files referenced by id, never by public URL;
   upload limits: PDF or DOCX, max 5 MB, checked by content (magic bytes), not just the extension;
   SHA-256 to detect duplicates.
7. **Resume to text:** PDF with pypdf (or pdfplumber), DOCX with python-docx; detect scanned PDFs (no
   text) and password-protected files and explain what to do; cap very long text and warn.
8. **Profile facts:** the AI extracts facts (role, company, dates, skills, achievements with numbers,
   education, location, notice period if stated), each with an id and the exact source sentence; code
   checks each fact's source sentence exists in the resume text; the result is a **proposal**; I review,
   edit, remove, then approve → `profile_versions` v1 (re-upload creates v2; old versions kept).
9. **Preferences ("What are you looking for?")**: target roles, cities (with aliases: Bengaluru/Bangalore,
   Gurugram/Gurgaon, Mumbai/Bombay), remote/hybrid/on-site, minimum fixed pay in LPA, experience range,
   my notice period, company types to avoid. Saved as `rules` with source "you".
10. **Screens:** Onboarding steps 1 ("Start with your resume") and 2 ("What are you looking for?")
    wired; Settings › Search section wired; anywhere that needs a profile shows "Approve your profile
    first" with a link.

## 4. UI mock references
`Onboarding` / `MOnboarding` steps 1–2 (upload, "Experience", "Latest role", "Skills found", review),
`Settings` / `MSettings` (Search, Privacy: "Hide my identity from AI", "Zero data retention"),
`Memory` / `MMemory` (rules list shows the "You set" rules created here).

## 5. Recommended technologies
Groq official client, Instructor, Pydantic, pypdf or pdfplumber, python-docx, python-magic or a small magic-bytes
check, TanStack Query, React Hook Form + zod.

## 6. Files and modules to create or modify
`api/app/ai/{gateway,models,prompts,privacy,usage,cassettes}.py`, `api/app/ai/prompts/*.md`,
`api/app/files/{storage,router,service}.py`, `api/app/profile/{extract,service,router,models}.py`,
`api/app/rules/{models,service,router}.py`, migrations for `files`, `profile_versions`, `rules`,
`ai_usage`; `api/tests/ai/*`, `api/tests/profile/*`, `api/tests/fixtures/ai/*`;
`web/app/(app)/onboarding/*`, `web/app/(app)/settings/*` (Search, Privacy), `web/lib/queries/profile.ts`.

## 7. Database and API requirements
Tables: `files`, `profile_versions`, `rules`, `ai_usage`. Endpoints: `POST /api/files` (multipart),
`GET /api/files/{id}`, `POST /api/profile/extract` (creates a proposal; long work returns 202 + status
until the worker exists in Phase 8), `GET /api/profile`, `GET /api/profile/versions`,
`PUT /api/rules`, `GET /api/rules`, `GET /api/settings/ai-usage`.

## 8. Implementation sequence
Gateway + model roles → privacy guard → prompt registry → usage tracking → cassettes → storage →
text extraction → fact extraction + source-sentence check → proposal review UI → preferences →
settings wiring → tests.

## 9. Testing requirements
Unit: privacy guard removes and restores every contact format; fact source-sentence check; LPA parser;
city aliases. Integration (replayed recordings, no network): extraction proposal → approve → version 1;
re-upload → version 2; malformed AI output retried then clear error; provider 429 → backup used.
Frontend: upload states (progress, error, success); review list editing; preferences validation.
Playwright: upload a real resume of mine **only on my machine** (never commit it); fixtures in tests
use a resume text I approve for testing.

## 10. Edge-case checklist
- [ ] File over 5 MB; wrong type renamed to `.pdf`; empty file.
- [ ] Scanned PDF (no text) and password-protected PDF.
- [ ] Same file uploaded twice (duplicate detected).
- [ ] Very long resume; resume not in English.
- [ ] AI returns invalid JSON or invents a fact not in the resume (dropped by the check).
- [ ] All providers rate-limited (status "pending", retried later, nothing lost).
- [ ] No approved profile yet (other screens show what to do).
- [ ] Editing facts after approval creates a new version, history kept, undo works.

## 11. Security considerations
Files private, served only to the owner; content-type sniffing; no file paths from user input; identity
stripped before AI; no resume text in logs or Sentry; prompt-injection wrapper; provider allow-list
enforced in code (test it).

## 12. Acceptance criteria
- [ ] I can upload my resume, review the extracted facts with their source sentences, edit, approve,
      and see version 1; uploading again gives version 2.
- [ ] My preferences are saved as rules and visible in Sources and memory.
- [ ] No AI call contains my name, email or phone (proved by a test).
- [ ] Tests run without network using recordings; all checks pass.
- [ ] Screens match Onboarding steps 1–2 and Settings › Search.

## 13. Documentation updates
`docs/ARCHITECTURE.md` (AI gateway), `docs/API_DOCUMENTATION.md`, `docs/DATABASE_SCHEMA.md`,
`docs/SECURITY.md` (privacy guard, providers), `docs/DEPLOYMENT.md` (Groq key row),
`docs/TESTING.md` (cassettes, edge-case rows), `docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format. Explain: LLM, tokens, temperature, structured output, prompt injection,
why we strip identity, what a recorded response (cassette) is.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 6." Do not commit.
