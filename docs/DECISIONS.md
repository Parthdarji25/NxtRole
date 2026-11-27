# Decisions

A short record of every real product or technical choice. Each record has an ID, a date, the decision,
the reason and the alternatives that were considered. A decision is only changed by a **new** record that
says which earlier one it replaces. Questions come from `docs/ROADMAP.md` section I (Q1 to Q13) and from
the conflicts M1 to M21 in `docs/mocks/MOCK_INVENTORY.md`.

Status values: **Accepted** (agreed by the founder) · **Superseded by D-xxx**.

## Index

| ID | Decision | Answers |
|---|---|---|
| D-001 | Roadmap and stack are the baseline | Phase 0 baseline |
| D-002 | Start from a clean repository | ROADMAP Q11, Q12 |
| D-003 | One user at launch, built ready for invited users | Q1 |
| D-004 | Gmail may auto-move clear cases (rejection, interview invite) with undo; the rest are proposals | Q13 |
| D-005 | Job sources: official APIs, Gmail-script alert emails, manual add; no scraping | M12 |
| D-006 | Jobs abroad and visa filters are later; v1 is India and Remote (India) | M15 |
| D-007 | Adding a job: paste a public link, by hand, or Gmail; extension and share sheet later | M13, M14 |
| D-008 | Voice is later; mock interview and Ask are text only in v1 | Q9, M7, M17 |
| D-009 | Resume exports: `.tex` and PDF (from HTML); `.docx` later; ATS score counted by code | Q8, M6, M18 |
| D-010 | Sign-in is email + password with our own tokens | Q2, M1 |
| D-011 | Alerts by web push; Telegram later; no email alerts in v1 | Q4, M2 |
| D-012 | AI providers: Groq and Cerebras only; Llama 3.3 70B is judge and reviewer | Q5, M3 |
| D-013 | Default schedules and alert rules (hourly search, 7:00 AM brief, 80+ and High trust, max 5/day, quiet 10 PM to 7 AM) | M16 |
| D-014 | Layout: phone below 768 px, desktop from 768 px, icon-only side menu below 1024 px | Q6, M8 |
| D-015 | Missing states are designed in the mock style and approved first | Q7, M9 |
| D-016 | Fresh jobs on desktop are a block at the top of Today | Q10, M10 |
| D-017 | One Settings menu (9 sections), a Prepare list, notes inside Pipeline | M19 |
| D-018 | v1 keeps the landing page and adds legal, data and error pages | M21 |
| D-019 | Keep the Gmail script; rename every "morrow" leftover | M4, M20 |
| D-020 | Accounts and keys are created only when a phase needs them | Q3 |
| D-021 | Company radar uses hiring signals; no funding news | M5 |
| D-022 | NxtRole never says "Send": copy-and-mark-sent or open-in-the-other-app (also "Approve & send", "Schedule for") | M11 |
| D-023 | Google Calendar connection (OAuth) is in v1, as in the mock | M22 |
| D-024 | Groq only; Cerebras optional and off (amends D-012) | Phase 1 |
| D-025 | Our own thin AI gateway; no LiteLLM | Phase 1 |
| D-026 | `background_jobs` table + worker; Redis for locks and limits; no arq | Phase 1 |
| D-027 | Owner created from the command line; recovery code (completes D-010) | Phase 1 |
| D-028 | Repo layout, layering, global vs per-user data | Phase 1 |
| D-029 | Resume upload straight to storage (4.5 MB limit) | Phase 1 |
| D-030 | GitHub Actions schedules; morning run 05:30 IST | Phase 1 |
| D-031 | Calendar scope `calendar.events.owned` | Phase 1 |
| D-032 | Auth, cookie and CSRF rules | Phase 1 |
| D-033 | Groq free-tier AI budget and model chain | Phase 1 |
| D-034 | Embeddings and search | Phase 1 |
| D-035 | Webhook and MCP security rules | Phase 1 |
| D-036 | Supply-chain policy | Phase 1 |
| D-037 | Docker Desktop (WSL2) for local development | Phase 1 |
| D-038 | Short API requests; long work in the worker | Phase 1 |
| D-039 | Row-level security on every per-user table | Phase 1 |
| D-040 | Discovery hourly 07:00 to 21:00 IST; AI retries hourly (refines D-013, D-030) | Phase 1 |
| D-041 | Docker Engine inside Ubuntu on WSL 2; no Docker Desktop (replaces D-037) | Phase 2 |
| D-042 | pnpm for the web app (amends D-036) | Phase 2 |
| D-043 | Foundation layout details | Phase 2 |
| D-044 | Foundation versions and test location | Phase 2 |
| D-045 | All commits go on `main` | Phase 3 |
| D-046 | Mock viewer, truthful landing copy, "Check first" badge | Phase 3 |
| D-047 | Screen states and wording approved | Phase 3 |
| D-048 | Phase 3 build choices | Phase 3 |
| D-049 | Phase 3 approved: wording, 3D tour later, two blue buttons on landing, screen pictures | Phase 3 |

All 13 questions in ROADMAP section I and all conflicts M1 to M22 are covered. Q1 = D-003, Q2 = D-010, Q3 = D-020,
Q4 = D-011, Q5 = D-012, Q6 = D-014, Q7 = D-015, Q8 = D-009, Q9 = D-008, Q10 = D-016, Q11 and Q12 = D-002, Q13 = D-004.
M1 = D-010, M2 = D-011, M3 = D-012, M4 = D-019, M5 = D-021, M6 = D-009, M7 = D-008, M8 = D-014, M9 = D-015,
M10 = D-016, M11 = D-022, M12 = D-005, M13 and M14 = D-007, M15 = D-006, M16 = D-013, M17 = D-008, M18 = D-009 and D-012,
M19 = D-017, M20 = D-019, M21 = D-018, M22 = D-023.

---

## D-001 · Roadmap and stack are the baseline
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 0 baseline question
- **Decision:** `docs/ROADMAP.md` (17 phases, 0 to 16, and the technology stack in its section C) is the
  starting plan for NxtRole. Phase 1 checks the current version and changes of every tool before anything is built.
  Any later change to a phase or a major tool needs a new decision record.
- **Why:** It was designed for free hosting for one user, strong AI tooling and privacy, and it gives a clear order
  of work. Phase 1 still protects against outdated versions.
- **Alternatives:** Review the stack line by line before accepting (slower start); change the plan first (phase
  prompts would need edits).

## D-002 · Start from a clean repository
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I, Q11 and Q12
- **Decision:** The repository contains no application code (no `web/`, `api/`, README, `.env.example`, config or
  commits) and no `BUILD-PROMPT.md`, so we start clean. Nothing is kept or reviewed, and no `docs/archive/` folder is
  created now. If an old `BUILD-PROMPT.md` turns up, the founder moves it into `docs/archive/`; files there are history
  only and are never followed.
- **Why:** Phase 0 inspection found only documents. There is nothing to preserve and nothing that can conflict with the
  new plan.
- **Alternatives:** Bring older code or an older plan in from somewhere else (would need a review first and add work).

## D-003 · One user at launch, built ready for invited users
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I, Q1
- **Decision:** NxtRole launches for the founder only. The design is ready for invited users later: every per-user
  table has a `user_id` with a foreign key, and every database query is scoped to the logged-in user. No public sign-up,
  billing, roles or invites are built in the MVP. How the first account is created is decided in Phases 1 and 4.
  Before anyone else is invited, a privacy notice, consent, and "export my data" / "delete my data" must exist
  (India's DPDP Act applies once other people's data is stored).
- **Why:** It is the simplest and cheapest path. The free AI limits stay with one person, and no legal duties for other
  people's data exist yet. Keeping `user_id` everywhere makes inviting people later a small extra phase, not a rewrite.
- **Alternatives:** Invited users from the start (shared free AI quota, bigger Phase 4, consent work first);
  a public product (billing, abuse protection, legal pages, paid hosting).

## D-004 · Gmail may auto-move clear cases, with undo; everything else is a proposal
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I, Q13 (Phase 0 focus item)
- **Decision:** For job emails that arrive through the Gmail script, **rules in code (not AI judgement)** may move a
  Pipeline card on their own for two clear cases only: a **rejection** and an **interview invite** (for example a
  calendar invite). Every such move writes a History row, shows "Moved by Gmail, undo inside" on the card, and can be
  undone in one tap. Every other change from an email (new round time, offer, unclear wording, anything the rules do
  not recognise) is a **proposal** that waits for the founder's approval. Exact rules are defined in Phase 12 and
  must be tested.
- **Why:** It keeps Pipeline current without effort, as the mock shows, while staying close to "AI suggests, I approve":
  code rules for unmistakable cases only, with a full history and undo.
- **Needs a written exception:** Golden rule 2 in `CLAUDE.md` says AI never changes data directly. Proposed one-line
  addition, **not yet applied** (Phase 0 may not edit `CLAUDE.md`; the founder decides): *"Exception: a code rule (not AI)
  may move a Pipeline card for a clear rejection or interview-invite email, with a history row and one-tap undo."*
- **Alternatives:** Never auto-move (strictest, but approve on every email); auto-move the same two cases plus a
  Settings switch to turn it off (one more setting to build and test).

## D-005 · Job sources: official APIs, forwarded alert emails and manual add only (M12)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Mock conflict M12
- **Decision:** Jobs come from (1) official job APIs and public ATS job feeds (Greenhouse, Lever, Ashby, Adzuna,
  Arbeitnow), (2) job alert and recruiter emails that arrive in the founder's own Gmail and are read by the
  Gmail script (for example Naukri, LinkedIn, Instahyre alerts; clarified in D-019: v1 has no inbound email address), and
  (3) jobs the founder adds by hand. NxtRole does **not** search, read or scrape LinkedIn, Naukri,
  Indeed or any site that needs a login. The mock copy that says these sites are read "through public search" and the
  "LinkedIn blocked this morning's search" banner are changed: onboarding, Jobs and Settings list only the real source
  types, and a paused API source shows a generic "Source paused" state.
- **Why:** Golden rule 5 (official sources only), the site terms, and the newest Sources and memory mock all agree.
  Scraping those sites is unreliable and gets blocked.
- **Alternatives:** Read public search pages of those sites (more jobs, but against their terms, fragile, and would
  require changing golden rule 5); official-only now with a later review if a proper partner API appears.

## D-006 · Jobs abroad and visa filters are later; v1 is India and Remote (India) (M15)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Mock conflict M15
- **Decision:** Version 1 searches India and Remote (India) only. The country picker, the visa filter ("sponsors or
  likely", "hide no sponsorship"), the "ABROAD" tag and the "abroad jobs searched every 2 hours" schedule are **later**
  (after v1.0) and are not built or shown in the MVP. The database keeps `country` and visa fields on jobs so the feature
  can be switched on later without a rewrite. The PRD lists them under "Later".
- **Why:** One market is easier to build, tune and test (scoring, trust rules, salary parsing in INR/LPA). Visa data is
  rarely provided by free APIs, and a second schedule uses more free-tier quota.
- **Alternatives:** Full abroad support as in the mocks (adds work to Phases 6, 7, 8); remote-for-India only (partial
  version of the mock).

## D-007 · Adding a job in v1: paste a public link, by hand, or Gmail (M13, M14)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Mock conflicts M13 and M14
- **Decision:** In v1 a job can be added in three ways: (1) **paste a link** to a public company careers or ATS page;
  NxtRole fetches only `https` pages, never private or internal addresses (SSRF protection), with size and time limits,
  and never logs in; (2) **fill the form by hand**; (3) **Gmail script** alert emails. Links on LinkedIn, Naukri, Indeed
  and other login-only or automated-reading-forbidden sites are **not fetched**: they go straight to the by-hand form with
  the link kept (the "Couldn't read that page" state in the mock). The desktop **browser extension** and the phone
  **share sheet** are **later** and are not shown in the MVP.
- **Why:** It keeps the convenience of auto-fill where it is allowed and safe, and follows golden rule 5. The share
  sheet only works for an installed Android web app, so it is not worth the work in v1.
- **Alternatives:** Add the phone share sheet in v1 (Android only, extra work); no link reading at all (safest, but you
  type everything).

## D-008 · Voice is later; the mock interview and Ask are text only in v1 (M7, M17, ROADMAP Q9)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I Q9, mock conflicts M7 and M17
- **Decision:** No voice in v1. The Prepare mock interview works by typing; the "Type / Speak" toggle, the recording
  steps ("Whisper on Groq") and the microphone button in Ask NxtRole are hidden in the MVP. Voice is **later**, and when
  it is added it needs a clear consent line, a verified data-retention statement from the speech provider, and a
  new decision record choosing the engine (Groq Whisper or the browser's own speech recognition). No audio leaves
  the device in v1.
- **Why:** Your voice is personal data and would go to a third party (Groq, or Google through Chrome). Text first keeps
  Phases 10 and 11 smaller and privacy simple.
- **Alternatives:** Voice in v1 with Groq Whisper (matches the mock; third party gets audio); Chrome speech recognition
  (no extra account; sends audio to Google, Chrome only).

## D-009 · Resume exports in v1: `.tex` and PDF (from HTML); `.docx` and in-browser LaTeX are later (Q8, M6, M18)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I Q8, mock conflicts M6 and M18
- **Decision:** The Resume builder exports a **`.tex`** file (to open in Overleaf) and a **PDF** made from a clean
  single-column ATS-safe HTML version. "Download .docx" and compiling LaTeX inside the app are **later** and are hidden
  in the MVP. The **ATS score** and the keyword match are **counted by code rules**, not by AI, so they are explainable
  and testable. How the "what an ATS reads from your PDF" check parses the exported PDF (which open-source parser) is
  chosen and verified in Phase 1/10. The model that "reviews" the resume text is decided with the AI-provider question
  (Q5/M3).
- **Why:** Two reliable formats that work on free hosting. A TeX engine is heavy to host, and a third template (`.docx`)
  adds work with little extra value in v1.
- **Alternatives:** Add `.docx` in v1 (matches the mock, more work in Phase 10); PDF only (smallest, loses Overleaf).

## D-010 · Sign-in is email + password with our own tokens; no Google, no email code (Q2, M1)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I Q2, mock conflict M1
- **Decision:** The Sign-in screens keep their layout and style, but "Continue with Google", the "or with email" divider,
  the 6-digit email-code step and the "Demo code: 123456" text are replaced by an **email + password** form. Passwords are
  stored only as Argon2 hashes. A 15-minute access token is kept in memory and a rotating 7-day refresh cookie (httpOnly,
  sent only to `/api/auth`) keeps the session. Settings > Accounts changes from "Signed in with Google" to account
  details (email, change password, active sessions, export my data, delete my account and data).
- **Open point for Phase 1/4:** with no email service there is no "forgot password by email". How the single owner
  recovers access (for example a one-time recovery code shown at setup, or an admin command on the server) is designed in
  Phase 1 and recorded then.
- **Why:** No third-party login, no email-sending account to set up, full control, and it matches the learning goal.
- **Alternatives:** Google sign-in only (depends on a Google app and consent rules); password now and Google later
  (button stays hidden until then).

## D-011 · Alerts go to the phone by web push; Telegram is later; no email alerts in v1 (Q4, M2)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I Q4, mock conflict M2
- **Decision:** v1 alerts (fresh high-trust matches, interview and follow-up reminders, "AI limits used" notice, source
  problems) are sent as **web push** to the installed NxtRole web app. On iPhone this needs the app added to the home
  screen (iOS 16.4 or later). **Telegram** is a possible later channel; **email alerts and the emailed brief are not in v1**.
  In the mocks: the Telegram and email switches, "Telegram + morning brief", "in the app and by email" and "you get one
  Telegram message" are replaced by push wording ("one push, then nothing more until it is sorted"), and an in-app banner
  carries the same message. Quiet hours and caps are a separate decision (M16).
- **Why:** No extra accounts or services, free, and your job data stays between NxtRole and your own device.
- **Alternatives:** Push + Telegram in v1 (needs a bot and more tests); push, Telegram and email as in the mocks (needs a
  mail-sending service, more places data can leak to).

## D-012 · AI providers: Groq and Cerebras only; Llama 3.3 70B is the judge and resume reviewer (Q5, M3, M18)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I Q5, mock conflict M3 (and the Mistral reviewer from M18)
- **Decision:** NxtRole sends AI work only to **Groq** (main: gpt-oss-120b, small tasks on a small Llama model, and the
  Llama 3.3 70B "judge" that checks another model's work) and **Cerebras** (backup). **Mistral, Google Gemini and
  OpenRouter are removed** from the Settings > AI models screen, the Today banner and everywhere else. The switch "Let
  Gemini and OpenRouter see my resume text" is removed. "If all five run out" becomes "if both run out" (job search,
  clean-up, rules and match scores that do not need AI keep running; AI drafts wait as "Drafts pending", and NxtRole
  retries every 15 minutes). The Resume builder's "reviewed by Mistral Large" becomes the Llama 3.3 70B judge
  (as the Application pack mock already says). Identity (name, phone, email) is removed before every AI call.
- **To verify in Phase 1:** each provider's current free limits and data-retention/training terms, and the mock claim
  "Groq keeps no copy of prompts or replies" (a zero-data-retention setting must exist and be on, or the wording changes).
- **Why:** Golden rule 4 forbids sending personal data to providers that may train on or keep prompts. One short,
  clear fallback chain is easier to build and test.
- **Alternatives:** Keep the other three for public job text only (needs strict code guarantees and more settings);
  keep all five with the resume-text switch off by default (relies on a switch for privacy).

## D-013 · Default schedules and alert rules (M16)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Mock conflict M16
- **Decision:** Defaults, all editable in Settings and defined in one place in the code (one source of truth for every
  screen that shows them):
  - Job discovery from official sources: **hourly** (the Settings text "every 30 min" changes).
  - Morning brief: **7:00 AM IST** (01:30 UTC). Follow-up check: daily (Phase 9 fixes the exact time).
  - Fresh-job alerts: only for score **80 or more** and **High trust**, at most **5 a day**.
  - Quiet hours: **10 PM to 7 AM**, no alerts (the phone Fresh-jobs text "11 PM" changes). Alert wording that says
    "90%+" changes to match; interview and follow-up reminders are separate from the 80+ job-match rule.
  - The abroad schedule ("every 2 hours") is removed with jobs abroad (D-006).
- **To verify in Phase 1:** GitHub Actions scheduled runs are best-effort (they can start late) and the free private-repo
  minutes budget must cover the schedule; the numbers are checked then.
- **Why:** It fits the free scheduler budget, matches the roadmap and the Fresh-jobs screen, and removes the
  contradictions between mocks.
- **Alternatives:** Search every 30 minutes (faster, doubles scheduled runs); only 90%+ matches and interview invites
  (fewer alerts, may miss a good early job).

## D-014 · Layout between phone and desktop (Q6, M8)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I Q6, mock conflict M8
- **Decision:** Below **768 px** wide the **phone layout** is used (bottom tab bar). From **768 px** the **desktop layout**
  is used. Below **1024 px** (down to 768 px) the 260 px side navigation collapses to **icons only**. No separate tablet
  mocks are made. Phase 3 tests every screen at 390, 768, 1024 and 1440 px and shows any screen that looks bad before
  it is fixed.
- **Why:** No new designs are needed, and every screen works at every width. These breakpoints are the starting values for
  `docs/DESIGN_SYSTEM.md` in Phase 1.
- **Alternatives:** Phone layout up to 1024 px (wastes tablet space); separate tablet design (needs new mocks first).

## D-015 · Missing states are designed in the mock style and approved before use (Q7, M9)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I Q7, mock conflict M9
- **Decision:** Where a mock does not show a loading, empty, error, offline or success state, Phase 3 designs it in the
  same style (tokens, type, spacing from `docs/mocks/design-tokens.css`) and shows the founder a sample sheet of these
  states **before** they are built on every screen. Empty states say what to do next and never show fake data. The sheet is
  approved first; then the states are used everywhere.
- **Why:** One consistent look, approved once, instead of changes that touch every screen later. It also follows
  `CLAUDE.md` section 4.
- **Alternatives:** Design and build directly, review afterwards (faster, riskier); founder provides new mocks (blocks Phase 3).

## D-016 · Fresh jobs on desktop appear at the top of Today (Q10, M10)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I Q10, mock conflict M10
- **Decision:** On desktop, fresh jobs are shown as a **"Fresh" block at the top of Today** with a "Posted N min ago"
  label, using the same row pattern as the other matches. The phone keeps its own Fresh jobs screen at `/today/fresh`
  (opened from the alert). The desktop block is designed in the mock style in Phase 3 and shown to the founder first
  (it is a new element, so D-015 applies). The block is empty and hidden when there is nothing fresh.
- **Why:** No new page; you already open Today every morning.
- **Alternatives:** A separate desktop screen at `/today/fresh` (one more screen to design); no fresh section on desktop
  (loses the "be among the first" nudge).

## D-017 · Navigation: one Settings menu, a Prepare list, and notes inside Pipeline (M19)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Mock conflict M19
- **Decision:**
  1. **Settings** has one menu of **9 sections**: Search, Agents, AI models, **Sources and memory**, Privacy, Safety
     rules, Notifications, Accounts, Connections. "Sources and memory" stays at `/settings/sources` and appears in this
     menu on desktop and in the phone More list. The 4-item menu drawn on the Sources and memory mock is replaced by this
     one. "Sources and memory" does not get its own item in the side navigation.
  2. **Prepare** opens a **list of upcoming interviews** (cards from Pipeline that have a booked round), at `/prepare`;
     each opens `/prepare/[applicationId]`. The list is a new screen designed in the mock style and shown to the founder
     first (D-015).
  3. **Notes** have **no separate screen**. Notes live inside Pipeline cards, are searchable from the top-bar search, and are
     available to Ask NxtRole and the MCP tools. The PRD keeps Notes as a feature, not a screen.
- **Why:** Every screen becomes reachable and consistent, with only one small new screen (the Prepare list).
- **Alternatives:** "Sources and memory" as an 11th side-menu item (longer menu than the mock); a dedicated Notes
  screen (new design, more scope in Phase 11).

## D-018 · v1 includes the landing page and the legal, data and error pages (M21)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Mock conflict M21
- **Decision:** v1 keeps the public **landing page** (`/`), with the 3D "how it works" tour as an **enhancement** over the
  plain step cards (the mock already shows the no-WebGL fallback); the 3D tour is the last, optional item of Phase 3. The
  footer text "Mock data" is replaced with real wording. v1 also includes simple pages in the mock style, designed in Phase 3
  and shown to the founder first (D-015): **Terms**, **Privacy notice**, **About NxtRole**, **Export my data**,
  **Delete my account and data** (with confirmation), a **404** page and an **offline** page.
- **Why:** The production checklist requires a privacy notice and working export and delete. The landing page is also a
  portfolio piece.
- **Alternatives:** Step cards only, no 3D (lighter); no public landing, `/` goes to sign-in (least work).

## D-019 · Keep the Gmail script; rename everything "morrow" to NxtRole names (M4, M20)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Mock conflicts M4 and M20
- **Decision:** Job emails reach NxtRole through a **Google Apps Script in the founder's own Google account** that checks
  Gmail every 15 minutes, picks only emails matching a job filter, and posts them to a NxtRole webhook with a personal
  key. It needs no domain and no Google review. It is the **only** email channel in v1 (there is no inbound email address
  or mail service). It is built in Phase 12. Only minimal fields of an email are stored; email text is never logged and
  never shared over MCP. The Onboarding "Inbox" step stays optional ("Skip for now"). All old-name leftovers change:
  `morrow-gmail.gs` → `nxtrole-gmail.gs`, `morrow-theme` → `nxtrole-theme`, the search-history key `morrow-q` →
  `nxtrole-q`, `MORROW_TOKEN` → `NXTROLE_TOKEN`, the MCP token prefix `mrw_live_` → `nxr_live_`, and the stray
  `jp2-theme` event name. The product name is NxtRole everywhere ("Nxt" in ink, "Role" in blue).
- **Why:** Automatic Pipeline updates and job emails without a domain or mail server, and the privacy rules (filter first,
  minimal fields, no logs) keep the email access narrow. One consistent product name.
- **Alternatives:** Drop the script from v1 (most private, but no auto-moving cards or alert emails); keep the "morrow"
  names for now (creates a rename task later).

## D-020 · Accounts and keys are created only when a phase needs them (Q3)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** ROADMAP I Q3
- **Decision:** Free accounts and keys are created **just in time**: Groq in Phase 5, Adzuna in Phase 6, Cerebras when the
  AI fallback is wired (confirmed in the Phase 5 prompt), Sentry and Langfuse (optional) and a Google Cloud project with an OAuth client for Calendar (D-023) in Phase 12, and the production
  accounts (Supabase, Upstash, Vercel, GitHub secrets) in Phase 15. Each phase tells the founder exactly what to create
  and which `.env` variable to fill. Secrets only ever go in `.env` files filled in by the founder, never in chat and
  never in git. `docs/DEPLOYMENT.md` keeps the accounts and keys checklist.
- **Why:** No unused keys sitting around, nothing to rotate early, and free limits or rules cannot change before use.
- **Alternatives:** Create everything now (keys idle for weeks); no external accounts until Phase 15 (Phases 5 to 12 could
  not be tried with real AI and real jobs).

## D-021 · Company radar uses hiring signals from public sources; no funding news (M5)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Mock conflict M5
- **Decision:** The "Company radar" agent in Settings > Agents watches **hiring signals** for the companies you watch,
  using only sources the company brief already uses: the careers page and its changes, new job posts, the company blog,
  public GitHub activity and Hacker News mentions. **Funding news is not included** (no free, reliable, allowed source).
  The Settings text "funding news and hiring posts" changes to "hiring signals". The agent reads public https pages only,
  never logs in, and stops after a fixed number of steps.
- **Why:** Free, reliable and within golden rule 5.
- **Alternatives:** Keep "funding news" and look for a source (likely a dead feature); remove the radar agent from v1.

## D-022 · NxtRole never says "Send": copy-and-mark-sent or open-in-the-other-app (M11)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Mock conflict M11 (golden rule 3)
- **Decision:** No button or message may say or imply that NxtRole sends something for you. In the mocks, "Send follow-up",
  "Send message" and "Send reply" (the "Needs you" cards on phone Today), the confirmations "Sent. Next check in 5 days.",
  "Sent to …" and "Reply sent.", and the sample "Send" button on the Design foundations sheet change to the safe wording
  used by the newer screens: **"Copy and mark sent"** (drafts you paste into your own email or LinkedIn),
  **"Open … ↗"** (opens the company page, LinkedIn profile or your own email app outside NxtRole), and **"Marked sent"**
  as the confirmation. The "Send" button in the Ask NxtRole chat stays: it sends your question to the assistant, not to
  anyone else. Studio's "Approve & attach" stays (it approves a draft inside NxtRole). No "email app link" option is
  added in v1.
- **Amendment, same day (found later in Phase 0, same principle):** the Studio mocks also say **"Approve & send"** (recruiter
  reply) and **"Schedule for 10:00 AM"** under "Best time to send" (follow-up). NxtRole cannot send or schedule a send,
  so they change to **"Approve"** (saves the draft in NxtRole, then "Copy and mark sent") and **"Remind me at 10:00 AM"**
  (a push reminder, not a scheduled send). The founder is told about this change in the Phase 0 report and can reverse it.
- **Why:** The words must always be true, so the founder can trust every button. It also matches the newer Follow-ups,
  Network and Studio screens.
- **Alternatives:** Also offer "Open in my email app" with a ready draft (quicker on phone, but puts recipient and text in
  a mail link and adds test cases); keep "Send" where the user only confirms their own message (misleading, breaks rule 3).

## D-023 · Google Calendar connection (OAuth) is in v1, as in the mock (M22)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Mock conflict M22 (found in Phase 0, not in the roadmap)
- **Decision:** v1 includes a **Google Calendar connection using Google OAuth**, as shown in Settings > Connections ("Adds
  interview events") and in the agent log ("Added round 2 to Google Calendar"). The founder connects it once from
  Settings, can disconnect at any time (tokens are deleted), and NxtRole only asks for the smallest Google permission
  that can create and edit its own events (the exact scope is chosen and verified in Phase 1). It is built in Phase 12
  (Integrations). The Google OAuth client is a private "testing" app for the one owner, so no Google review is needed
  while the founder is the only user.
- **Defaults to confirm in Phase 1 and Phase 12 (not yet decided):** an event is created only for an interview round that is saved in
  Pipeline (by the founder, or by the clear-case rules of D-004); it has **no attendees, so no invitation is sent**
  (golden rule 3); creating, moving or removing an event writes a History row and can be undone; rescheduling or
  cancelling a round updates or removes the event.
- **Security notes (carried into `docs/SECURITY.md`):** the Google refresh token is a **secret**; it is stored encrypted
  and is never logged or shown to AI.
- **Why:** The founder wants the integration shown in the mock. It keeps interview times in the calendar they already use.
- **Recommended alternative that was not chosen:** no calendar connection in v1 (fewer permissions and parts);
  adding events through the Gmail script (no Google app to register, but one more script permission).
- **Effect on other decisions:** D-020 gains one item: a Google Cloud project and OAuth client in Phase 12.

---

# Phase 1 decisions (architecture)

Verification sources for these records are listed in `docs/TECH_STACK.md`.

## D-024 · Groq is the only active AI provider; Cerebras is an optional adapter that stays off (amends D-012)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 verification
- **Decision:** Phase 1 found that Cerebras no longer has a standing free tier: it offers a one-time $5 credit that needs a
  payment method and expires after 30 days. NxtRole therefore uses **Groq only** in v1, with a **chain of Groq models**
  (each model has its own free allowance) defined in configuration. A Cerebras adapter may be written later but is **off by
  default** and is switched on only if the founder adds a payment method. If Groq is unavailable or its limits are used,
  AI work waits as "Drafts pending" (D-012 behaviour, FR on AI state). The Settings AI models screen lists the providers that
  are configured (one in v1), not a fixed list of two. D-012's rule still holds: no provider that may train on or keep
  prompts receives personal data.
- **Why:** Zero cost and no card (NFR-COST-01). Groq's own docs say zero data retention can be enabled for all accounts,
  which the founder must switch on and verify in the Groq console in Phase 5.
- **Alternatives:** Keep Cerebras with a card (against free-only); find another free no-training provider (more research, may find none).

## D-025 · Our own thin AI gateway; no LiteLLM
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 verification (changes ROADMAP C)
- **Decision:** All AI calls go through **one module we write** (`api/app/ai/gateway.py`) on top of Groq's official Python
  client, with **Instructor** for typed, validated answers. The gateway removes identity before a call and restores it after,
  walks the model chain, retries with backoff, counts usage per day and model, and traces calls. **LiteLLM is not used.**
- **Why:** LiteLLM had two supply-chain compromises of its PyPI releases in 2026 (March and October). It would sit next to
  your API keys and personal data. A small gateway is easier to understand, test and secure.
- **Alternatives:** LiteLLM pinned to an audited version (large dependency, constant watching).

## D-026 · Background jobs: a PostgreSQL `background_jobs` table and a small worker; Redis only for locks and rate limits; no arq
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 verification (changes ROADMAP C)
- **Decision:** Background work is rows in a `background_jobs` table (kind, payload, state, run-after, attempts, lock owner). A small worker
  takes one at a time with `FOR UPDATE SKIP LOCKED`, applies timeouts, retries with backoff, and records the result.
  **Redis** (Upstash in production) is used only for run locks, rate limits and short-lived counters, so the free
  500K commands per month are enough. **arq is not used** (it is in maintenance-only mode).
- **Why:** Fewer dependencies; jobs survive restarts and are visible in the database; agent runs that wait for approval need
  state in the database anyway.
- **Alternatives:** Keep arq; another Redis queue library (smaller, newer project).

## D-027 · Owner account is created from the command line; a one-time recovery code; CLI reset as last resort (completes D-010)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 (open point in D-010)
- **Decision:** (1) The owner account is created by running a command on the founder's laptop (`create-owner`), which asks for
  an email and a password typed locally. (2) At that moment a **one-time recovery code** is printed once; only its Argon2
  hash is stored. (3) A recovery page (`/login/recover`, not linked anywhere) accepts the code, sets a new password, revokes
  every session and issues a new code. (4) As a last resort the same command can reset the password directly in the database
  using the founder's own `.env`. There is no public sign-up route and no email service. The recovery endpoint is rate limited
  and fails with the same message for every wrong input.
- **Why:** No email service or sign-up surface to attack, and it works on free hosting.
- **Alternatives:** CLI only (no recovery page); an email service for password reset (new third party, domain set-up).

## D-028 · Repository layout, layering and global versus per-user data
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1
- **Decision:** One repository with two apps: `web/` (Next.js) and `api/` (FastAPI), plus `docs/`, `tests/`, `scripts/`, `infra/`.
  The API is layered **routers → services → repositories**, one module per domain; routers never touch the database,
  repositories never contain business rules. Data is split: **global** tables (sources, companies, jobs, job sightings, trust
  checks) are shared and contain nothing personal; **per-user** tables all carry `user_id` with a foreign key, an index and a
  repository that always filters by it. Full design in `docs/ARCHITECTURE.md` and `docs/DATABASE_SCHEMA.md`.
- **Why:** The global/per-user split keeps jobs from being stored once per user and keeps personal data in tables that can
  be exported and deleted in one pass. It makes inviting users later a small step (D-003).
- **Alternatives:** Everything per-user (duplicates jobs, wastes the 500 MB free database); a monolith without layers (harder to test).

## D-029 · Resume upload goes straight to storage with a signed URL (4.5 MB request limit)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 verification (PRD risk R-4)
- **Decision:** Vercel Functions reject request bodies over 4.5 MB, but resumes may be up to 5 MB (FR-013). The browser therefore
  asks the API for a **short-lived signed upload URL** (the API checks type and declared size), uploads the file **directly
  to private storage**, then tells the API it is done. The API reads the file from storage, verifies the real size and content
  (PDF signature, page count, extractable text), and deletes the file if it fails. Other uploads (LinkedIn CSV, offer text) are
  smaller than 4.5 MB and use the normal API, with a stated 4 MB limit.
- **Why:** The only way to keep the 5 MB limit on this host without paying.
- **Alternatives:** Lower the limit to 4 MB (simpler, but contradicts FR-013 and the mock); host the API elsewhere (paid).

## D-030 · Scheduling: GitHub Actions for all runs; morning run starts at 05:30 IST; Vercel cron is not used
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 verification (PRD risk R-16, D-013)
- **Decision:** Scheduled work runs as **GitHub Actions** workflows that call the worker. Vercel Cron is not used (the Hobby plan
  allows only one run per day with up to an hour of timing slack). **Morning run:** starts at **00:00 UTC (05:30 IST)** to leave time for
  late starts and AI limits, and must finish before 07:00 IST. The brief is "published" when the run finishes; the push goes at
  the first run at or after **07:00 IST** (01:30 UTC), or at once if the founder opens the app. **Hourly discovery:** every hour at
  :30 UTC from 01:30 to 15:30 UTC (07:00 to 21:00 IST, see D-040); the 07:00 IST run sends the morning push. Scheduled runs are best effort (GitHub documents delays under high load), so
  each run is idempotent, takes a lock, and a missed run is detected by a health check. The free allowance is 2,000 minutes a month
  for private repositories; the budget table in `docs/ARCHITECTURE.md` shows the plan fits (about 1,000 minutes).
- **Why:** The roadmap said the run starts at 07:00 IST and also that it finishes before 07:00 IST; both cannot be true.
- **Alternatives:** Start at 01:30 UTC (can finish late); a public repository for unlimited minutes (exposes code and history).

## D-031 · Google Calendar permission: `calendar.events.owned`
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 verification (D-023)
- **Decision:** The Calendar connection requests only `https://www.googleapis.com/auth/calendar.events.owned` (create, change and delete
  events on calendars the founder owns). Not the full `calendar` scope. Events have no attendees. The OAuth client stays in
  Google's "testing" mode for one test user. Google test-mode refresh tokens can expire after seven days, so "Reconnect" must be a
  normal, clearly shown state (edge case E-32). Needs re-checking against Google's current docs in Phase 12.
- **Why:** Narrowest scope that can write events (Google's guidance: smallest scope possible).
- **Alternatives:** The full calendar scope (can delete whole calendars); read-only scopes (cannot create events).

## D-032 · Authentication and request-safety rules
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 (PHASE-01 section 11)
- **Decision:** Passwords: Argon2id. Access token: signed JWT, 15 minutes, held in memory. Refresh token: opaque random value, 7 days,
  stored hashed, rotated on every use, grouped in a family so reuse revokes the family. Refresh cookie: `HttpOnly; Secure;
  SameSite=Strict; Path=/api/auth`. CSRF: the cookie is only sent to `/api/auth`, `SameSite=Strict`, and the refresh and logout calls also
  require a custom header (`X-NxtRole-CSRF`) that a cross-site form cannot set. All other calls use the `Authorization` header, not cookies.
  Sign-in lockout: 5 failures per account and per IP per 15 minutes, then a 15-minute wait, with the same message for every failure.
- **Why:** Standard practice for a single-page app with its own tokens. Details are in `docs/SECURITY.md`.
- **Alternatives:** Session cookies for everything (CSRF on every route); long-lived access tokens (bigger damage if stolen).

## D-033 · AI budget and model chain on Groq's free tier
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 verification
- **Decision:** Groq's documented free limits for gpt-oss-120b are 30 requests a minute, 1,000 requests a day, 8,000 tokens a minute and
  200,000 tokens a day. One scoring call of about 2,000 tokens means 30 jobs scored twice use about 120,000 tokens, which leaves little for drafts. So:
  (1) the model chain is configurable (large model first, then other free Groq models, each with its own allowance); (2) the two scoring
  passes use **different models** when possible; (3) the gateway tracks tokens per day and per minute, **spaces calls** to stay under the
  tokens-per-minute limit, and moves down the chain or queues work before a limit is hit; (4) the top-30 limit is a setting that can drop to
  fewer jobs; (5) usage is shown in Settings. The mock's "14,400 requests a day on the small model" is not relied on until the Groq console
  confirms it. Exact model names and limits are read from Groq's console in Phase 5, because they change.
- **Why:** Keeps NxtRole inside the free tier and makes the limit a design input, not a surprise.
- **Alternatives:** Score fewer jobs by default; use a paid plan (against NFR-COST-01).

## D-034 · Search and embeddings
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1
- **Decision:** Embeddings use `BAAI/bge-small-en-v1.5` (384 dimensions) through `fastembed`, run locally, so resume and job text
  never leave the server for this step. Stored in `pgvector` columns with an HNSW index; keyword search uses PostgreSQL full text
  (`tsvector`). Search blends both. The model files are downloaded once and cached.
- **Why:** Free, private and one database for everything.
- **Alternatives:** A paid embedding API (leaks text); a separate vector database (another service to run).

## D-035 · Webhook and MCP security rules
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 (PHASE-01 section 11)
- **Decision:** **Gmail webhook:** each request carries a timestamp and an HMAC-SHA256 signature of the body made with the founder's
  personal key; requests older than 5 minutes are rejected; the email id makes processing idempotent; size and rate are limited.
  **MCP:** personal access tokens start `nxr_live_`, are shown once and stored as a hash; each token has scopes
  (`read:jobs`, `read:pipeline`, `read:notes`, `read:brief`, `write:draft`); the server never exposes sending, deleting, settings or email text; every
  call is logged without payload text.
- **Why:** Replay and leak protection with small, testable rules.
- **Alternatives:** A static bearer key only (replayable, no scopes).

## D-036 · Supply-chain policy for dependencies
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 (LiteLLM incidents)
- **Decision:** Every dependency is pinned to an exact version in a lockfile (`uv.lock`, `package-lock.json`) and CI installs only from
  the lockfile (`uv sync --frozen`, `npm ci`). New releases are adopted only after they are at least **7 days old** unless they fix a
  published security issue. CI runs `pip-audit` and `npm audit`. Install scripts are reviewed for new packages. Secrets are never
  available to pull-request builds from forks.
- **Why:** Two compromised releases of a popular AI library in one year show the risk.
- **Alternatives:** Floating versions (fast, unsafe).

## D-037 · Local development uses Docker Desktop (WSL2)
- **Date:** 2026-11-27 · **Status:** Superseded by D-041 · **From:** Phase 1 environment check (changes ROADMAP assumption A-4)
- **Decision:** Docker Desktop is not installed on the founder's laptop. It will be installed (with WSL2) at the start of Phase 2, with exact steps given
  there. Local PostgreSQL with pgvector and Redis run as containers. Python 3.13 (via `uv`) and Node 22 are already available.
- **Why:** Same services as production; integration tests use real Postgres and Redis.
- **Alternatives:** Cloud databases for development (accounts needed early); native Windows installs (pgvector and Redis awkward).

## D-038 · API requests are short; long work runs in the worker
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 verification
- **Decision:** Vercel documentation gives conflicting function time limits for the free plan (10 to 60 seconds in some pages, up to 300 in newer
  ones), so the design assumes **10 seconds** for any API request. Anything slower (agent runs, scoring, research, PDF export, data export) is a
  **job** in the jobs table, run by the worker, with progress stored in the database and read by the browser (short polling, with Server-Sent
  Events only as a bonus where the host allows). The same code runs the worker locally and in GitHub Actions.
- **Why:** Free serverless hosting cannot hold long connections reliably.
- **Alternatives:** A paid always-on server (against NFR-COST-01).

## D-039 · Row-level security on every per-user table, as a second layer
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 (security design)
- **Decision:** Every per-user table has PostgreSQL row-level security with the policy `user_id = current_setting('app.user_id')`. The API runs as a
  normal (non-owner, non-superuser) role and sets `app.user_id` at the start of each transaction. Repositories also filter by `user_id`. The Ask
  NxtRole read-only data tool uses a separate role limited to allow-listed views. Details: `docs/DATABASE_SCHEMA.md` section 6.
- **Why:** A forgotten filter in code cannot leak another user's rows, and it makes the data tool safer (NFR-SEC-02, NFR-SEC-09).
- **Alternatives:** Application filters only (one mistake leaks data); a separate database per user (too heavy for the free tier).

## D-040 · Free scheduler budget: discovery runs hourly from 07:00 to 21:00 IST; AI retries ride on those runs
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 1 budget check (refines D-013 and D-030, FR-139)
- **Decision:** GitHub bills whole minutes per job, and 2,000 free minutes a month are shared by every run. An hourly all-day discovery plus the morning run,
  backup and on-demand runs would use about the whole allowance. So discovery is **hourly from 07:00 to 21:00 IST (15 runs a day)**, not 24. "Drafts
  pending" are retried **at every discovery run** (hourly) and on the owner's "Retry now", not every 15 minutes as the mocks and FR-139 say (the wording changes
  to "about every hour"). The estimated total is about 1,640 minutes (82%). It is an **estimate to measure in Phases 8 and 15**; the levers, in order: discovery every 2 hours,
  fewer jobs sent to AI, burst work inline if Vercel allows, and finally a public repository for unlimited minutes (secrets stay in encrypted settings). Settings shows the month's estimate.
- **Why:** Keeps the free plan. Alerts for fresh jobs still arrive within about an hour while the owner is awake.
- **Alternatives:** 24 runs a day (over budget with other work); every-15-minute retries (96 runs a day, far over budget).


## D-041 · Local containers run on Docker Engine inside Ubuntu on WSL 2; no Docker Desktop (replaces D-037)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 2 check of Docker's official Windows requirements
- **Decision:** PostgreSQL with pgvector and Redis run as containers with **Docker Engine installed inside an Ubuntu distribution on
  WSL 2**. Docker Desktop is not used. Commands run through WSL (for example `wsl docker compose up -d`). The compose file is the same one CI uses
  as its model. WSL's memory use is limited because the laptop has 8 GB.
- **Why:** Docker's requirements page lists Windows 10 only as Pro, Enterprise or Education (22H2) and only supports Windows versions that Microsoft
  still services. The founder's laptop is Windows 10 Home. D-037 did not check this.
- **Alternatives:** Try Docker Desktop anyway (unsupported edition); install PostgreSQL and a Redis-compatible server natively (pgvector and Redis awkward).

## D-042 · pnpm is the web package manager (amends D-036)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 2 plan
- **Decision:** The web app uses **pnpm** with `pnpm-lock.yaml`; CI installs with `pnpm install --frozen-lockfile` and audits with `pnpm audit`. Everywhere D-036
  says `package-lock.json`, `npm ci` or `npm audit`, read the pnpm equivalent. The 7-day rule is enforced by tool settings: `minimumReleaseAge` in
  `pnpm-workspace.yaml` and `exclude-newer` for `uv`.
- **Why:** It is already installed, the Phase 2 prompt names it, and it can enforce the 7-day rule by itself.
- **Alternatives:** npm (no install of anything extra, but the age rule would rely on care).

## D-043 · Foundation layout details (settles differences between the Phase 2 prompt and the Phase 1 documents)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 2 plan
- **Decision:** (1) Folders follow `docs/ARCHITECTURE.md` (`api/app/core`, `api/app/db`, `api/migrations`, one package per domain); `docker-compose.yml`
  stays at the repository root. (2) The API offers `GET /health` and `GET /api/health` (alive) and `GET /api/health/ready` (database and Redis). (3) The `/api`
  forwarding and basic security headers live in `next.config.ts` for now; `proxy.ts` arrives in Phase 3 with the nonce-based content security policy.
  (4) Dependabot uses its `uv` ecosystem with a 7-day cooldown if GitHub's current documentation supports it.
- **Why:** One consistent structure before the first line of code.
- **Alternatives:** Follow the prompt's flat file list (differs from the architecture); put forwarding in `proxy.ts` now (more work before it is needed).

## D-044 · Foundation versions and test location (found during Phase 2)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 2 build
- **Decision:** (1) **TypeScript 5.9.3** (the Phase 2 prompt: else pin the newest 5.x), because the lint tooling supports TypeScript below 6.1 only.
  (2) **ESLint 9.39.5**, because Next's React, import and accessibility lint plugins do not support ESLint 10. (3) **jsdom 29.1.1**, because 31 needs
  Node 22.22.2 or newer and the laptop has 22.14.0. (4) Playwright tests live in **`web/e2e/`**, not a root `tests/e2e/`, because they resolve their
  library from the web project. Recorded fixtures still go in the root `tests/fixtures/`. (5) Each is revisited when Dependabot offers a compatible upgrade.
- **Why:** Newest is not useful if the tools around it do not work with it.
- **Alternatives:** Upgrade Node now (the founder's choice, see the known issues); TypeScript 6.0 (works with the lint tooling, but the prompt asked for 5.x).

## D-045 · All commits go on `main`
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Founder instruction at the start of Phase 3
- **Decision:** Work is committed to `main` only. No new branches are created or proposed. The founder still decides when to commit and does every push
  (`CLAUDE.md` section 5). The Phase 2 commit made on `chore/phase-2-foundation` was brought into `main` by a fast-forward.
- **Why:** The founder wants one simple line of history.
- **Alternatives:** A branch per phase with a merge (more steps for a one-person project).

## D-046 · Phase 3 approach: mock viewer, truthful landing copy, badge wording
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 3 plan
- **Decision:**
  1. The mocks cannot open in a browser (their runtime file `support.js` is not in the repository). A small viewer in `scripts/mock-viewer/` renders
     them for screenshots and comparison. It is a development tool and never part of the app. Its screenshots are generated files, not committed.
  2. The landing page keeps the mock layout with truthful copy: official job feeds, careers pages, the owner's job-alert emails and pasted links (never "searches
     Naukri, Indeed and LinkedIn"); "before you wake, then hourly from 7 AM to 9 PM"; no invented numbers; "jobs you already applied to are hidden"; GitHub Actions and
     rules in NxtRole's own code; Groq's free AI; "your top 5 strong matches"; one phone alert (no Telegram); a clear rejection or interview invite moves a card with
     undo and anything else waits; a script in your own Google account reads job emails (read-only is verified in Phase 12); "A personal project" (no "Mock data").
     The 3D tour shows unnamed job cards, not the mock's example companies. Sign in drops "New here? The same steps create your account".
  3. The amber trust badge reads **"Check first"**, as the mock does (the PRD's "Check" is corrected).
  4. Code goes in `web/src/`; screenshot tests in `web/e2e/visual/` and run on the founder's laptop only, because Windows and Linux draw text differently.
  5. Phase 3 also builds the screens the phase prompt leaves out: the Prepare list, Terms, Privacy, About, 404, offline, Export and Delete (inside Settings),
     the desktop "Fresh" block and the nine-section Settings menu. New states are approved on a sample sheet before use (D-015).
- **Why:** Everything the page says must be true, and the screens need something to be compared against.
- **Alternatives:** The founder exports mock images from the design tool; keep the mock copy (false claims).

## D-047 · The screen states and their wording are approved (completes D-015)
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Phase 3 checkpoint (sample sheet at `/design/states`)
- **Decision:** The loading, empty, error, offline, waiting and not-found designs shown on the sample sheet, and the wording of the 18 empty screens in
  `web/src/content/emptyStates.ts`, are approved and may be used on every screen. A change to their look or wording needs the founder's approval.
- **Why:** One consistent set, approved once, as D-015 requires.
- **Alternatives:** Changes requested to the look or wording (none).


## D-048 · Phase 3 build choices
- **Date:** 2026-11-27 · **Status:** Accepted (D-049) · **From:** Phase 3 build
- **Decision:**
  1. Dialogs, drawers, menus, tabs, switches and tooltips are written by us on the `radix-ui` package, without the shadcn command-line tool. Radix still provides the keyboard and screen-reader behaviour.
  2. Icons are the mocks' own line drawings, kept in one file; `lucide-react` is not installed.
  3. `TanStack Query` is not installed yet; Phase 4 adds it with the first data.
  4. The security policy (proxy) lives at `web/src/proxy.ts` because the code is in `web/src/`.
  5. Browser tests run against the production build on port 3100.
  6. Phone landing page: the tour steps are pills, as the phone mock draws them (the design system otherwise uses underline tabs).
- **Why:** Fewer dependencies, and the screens match the mocks.
- **Alternatives:** The shadcn tool (more generated code to restyle); lucide icons (shapes differ from the mocks).

## D-049 · Phase 3 is approved
- **Date:** 2026-11-27 · **Status:** Accepted · **From:** Founder approval of the Phase 3 completion report
- **Decision:**
  1. The Terms, Privacy notice and About text, and the new wording listed in the report (landing, sign-in, setup steps, Settings, More, search, agent log, 404 and offline), are approved.
     The agent button reads "Agent log".
  2. The 3D landing tour is built later, before launch.
  3. The landing page keeps two blue buttons, as its mock draws them. Every other screen keeps one.
  4. D-048 is accepted.
  5. The approved screen pictures in `web/e2e/visual/pictures/` are committed and are the reference for later changes.
- **Why:** The screens match the mocks and say only true things.
- **Alternatives:** Build the 3D tour now; make the tour button outlined.

---

# Where earlier wording is superseded by Phase 1 decisions

Phase 1 may only change `DECISIONS.md` and `ROADMAP.md`, so the PRD and the phase prompts carried the old wording below. **Applied on 27 Nov 2026 after the founder approved Phase 1** (PRD amended in place; phase prompts 02, 05, 07, 08, 09, 10, 11, 12 and 15 edited). The tables are kept as a record of what changed.

## In `docs/PRD.md`

| Where | Old wording | Now | Decision |
|---|---|---|---|
| FR-139, NFR-REL-03, E-06 (Appendix A) | Drafts retried **every 15 minutes** | Retried at every hourly discovery run (and on "Retry now") | D-040 |
| FR-197, NFR-PRIV-02, D-012 text, Appendix D (Settings and Brief rows), section 7.3 | Providers are **Groq and Cerebras**; banner "2 of 2" | Only Groq is active; the screen lists the configured providers | D-024 |
| FR-033, FR-089, NFR-PERF-03 | Hourly run, no hours stated | Hourly from 07:00 to 21:00 IST | D-040 |
| FR-077, NFR-PERF-02, R-16 | Morning run timing left to Phase 1 | Starts 05:30 IST; push at 07:00 IST | D-030 |
| NFR-SEC-07, Appendix B | "Tokens and keys are stored hashed" | Also: the Gmail HMAC key and the Calendar token are **encrypted** (a hash cannot verify a signature) | D-035, D-031 |
| FR-008, R-17 | Recovery method to be designed | Recovery code and command-line reset | D-027 |
| R-4 | Upload limit risk | Direct-to-storage upload | D-029 |

## In the phase prompts (`docs/prompts/`)

| File | Old wording | Now | Decision |
|---|---|---|---|
| PHASE-02 | Docker assumed present | Install Docker Desktop first; adopt lockfile and 7-day policy | D-036, D-037 |
| PHASE-05, 07, 09, 10, 11 | "LiteLLM + Instructor"; "Cerebras optional now, required by Phase 15" | Own gateway on Groq's client + Instructor; Cerebras optional and off | D-024, D-025 |
| PHASE-08 | arq worker; cron `30 1 * * *` for the brief | Postgres queue worker; morning run `0 0 * * *`; discovery `30 1-15 * * *` | D-026, D-030, D-040 |
| PHASE-12, 15 | Cerebras in checklists; arq queue; "07:00 IST brief" | Groq only; Postgres queue; times from D-030 | D-024, D-026, D-030 |
