# Mock inventory

Every screen in the latest mocks, the route it becomes, and the phase that builds it.
Latest source: `docs/mocks/source/*.dc.html` (exported 24 Nov 2026 from the canvas
"NxtRole UI Mocks · End product"). Older PNGs: `docs/mocks/desktop`, `docs/mocks/phone` (5 Nov 2026).
If a PNG and a source file differ, the source file wins. If a decision in `docs/DECISIONS.md` changes a mock,
the decision wins (see PRD Appendix D for the list of changes).

**Verified in Phase 0 (27 Nov 2026).** All 46 `.dc.html` files and `canvas.json` were read: text, actions, state and data keys.
The 22 screens, their routes and the shared parts below are correct, with these corrections to the first version of this file:
1. Onboarding has **5 steps plus a "You're set" screen**, not 6 steps (desktop labels: Resume, Profile, Sources, Inbox, Alerts).
2. The older PNG folders (`docs/mocks/desktop`, `docs/mocks/phone`) are **not in the repository**, so the "Older PNG" column
   could not be checked. It lists the names from the pack and is for reference only.
3. Overlays and sub-views (drawers, panels, tours) were not listed. They are now in "Sub-views and overlays".
4. Conflicts M12 to M22 are new; M3 and M4 were widened. Every conflict now has a decision.
5. Four screens needed by the decisions do not exist as mocks: they are in "New screens".

Phase numbers refer to `docs/ROADMAP.md`. "UI" = the shell and states are built in Phase 3;
"data" = the phase that connects real data and behaviour.

## Screens

| # | Screen | Route | Desktop source | Phone source | Older PNG | UI | Data |
|---|---|---|---|---|---|---|---|
| 1 | Landing page (public) | `/` | Landing | MLanding | 01-Landing, 01-MLanding | 3 | 3 |
| 2 | Sign in | `/login` | Login | MLogin | 02-Login, 02-MLogin | 3 | 4 |
| 3 | Onboarding (5 steps + done screen) | `/onboarding` | Onboarding | MOnboarding | 03-Onboarding, 03-MOnboarding | 3 | 5, 6, 8, 12 |
| 4 | Today brief | `/today` | Brief | MToday | 04-Brief, 04-MToday | 3 | 8 |
| 5 | Fresh jobs (from an alert) | `/today/fresh` | none (desktop: a block on Today, D-016) | MFresh | none | 3 | 8 |
| 6 | Jobs list + add a job | `/jobs` | Jobs | MJobs | 06-Jobs, 06-MJobs | 3 | 6, 7 |
| 7 | Job detail: fit, trust, duplicates | `/jobs/[id]` | JobCheck | MJobCheck | none | 3 | 6, 7 |
| 8 | Ask NxtRole | `/ask` | Ask | MAsk | 05-Ask, 05-MAsk | 3 | 11 |
| 9 | Pipeline: rounds, offers, history | `/pipeline` | Pipeline | MPipeline | 07-Pipeline, 07-MPipeline | 3 | 9 |
| 10 | Follow-ups | `/follow-ups` | Nudges | MNudges | none | 3 | 9 |
| 11 | Offer check | `/pipeline/offers/[id]` | OfferCheck | MOfferCheck | none | 3 | 9 |
| 12 | Prepare (interview prep, text mock interview) | `/prepare/[applicationId]` | Prepare | MPrepare | 08-Prepare, 08-MPrepare | 3 | 10 |
| 13 | Company brief | `/companies/[id]` | CompanyBrief | MCompany | none | 3 | 10 |
| 14 | Studio (drafts to review) | `/studio` | Studio | MStudio | 09-Studio, 09-MStudio | 3 | 10 |
| 15 | Application pack | `/studio/packs/[id]` | ApplyPack | MApplyPack | none | 3 | 10 |
| 16 | Resume builder: LaTeX, ATS, keywords | `/resume` | ResumeBuilder | MResume | 10-ResumeBuilder, 10-MResume | 3 | 10 |
| 17 | Progress: overview, interview log, learn | `/progress` | Progress | MProgress | 11-Progress, 11-MProgress | 3 | 9, 10 |
| 18 | Weekly coach | `/progress/coach` | Coach | MCoach | none | 3 | 9 |
| 19 | Network (referral finder) | `/network` | Network | MNetwork | none | 3 | 11 |
| 20 | Settings: nine sections (search, agents, AI models, sources and memory, privacy, safety rules, notifications, accounts, connections, D-017) | `/settings` | Settings | MSettings | 12-Settings, 13-MSettings | 3 | 4-8, 11, 12, 14 |
| 21 | Settings: sources, alerts and memory | `/settings/sources` | Memory | MMemory | none | 3 | 6, 7, 8 |
| 22 | More (phone menu) | `/more` | none | MMore | 12-MMore | 3 | 3 |

*The "Older PNG" names are from the pack. The PNG folders are not in the repository (see correction 2).*

## New screens (decisions, no mock yet)

Designed in the mock style in the stated phase and **shown to the founder before they are built** (D-015).

| Key | Screen | Route | Decision | UI | Data |
|---|---|---|---|---|---|
| N1 | Prepare list: upcoming interviews | `/prepare` | D-017 | 3 | 10 |
| N2 | Terms, Privacy notice, About | `/terms`, `/privacy`, `/about` | D-018 | 3 | 3 |
| N3 | 404 page and offline page | not-found, offline | D-018 | 3 | 3 |
| N4 | Export my data and Delete my account and data (inside Settings > Accounts) | `/settings` (Accounts) | D-018 | 3 | 14 |
| N5 | Desktop "Fresh" block at the top of Today (part of screen 4) | `/today` | D-016 | 3 | 8 |
| N6 | Loading, empty, error and offline states for every screen | all | D-015 | 3 | each phase |

## Shared parts

| Part | Source | Notes |
|---|---|---|
| Desktop side navigation | Nav | 10 items (Today, Ask NxtRole, Jobs, Pipeline, Follow-ups, Prepare, Studio, Resume, Network, Progress) + Settings, theme switch, agent status. Collapses to icons below 1024 px (D-014). |
| Desktop top bar: search + agent log | TopBar | Search across jobs, companies, notes and questions (Ctrl K); agent log drawer. The same drawers appear in MToday on phone. |
| Phone tab bar | MTabs | Today, Jobs, Pipeline, Prepare, More. Phone layout below 768 px (D-014). |
| Design foundations | Foundations | Type scale, components, spacing, radius, motion. The sample "Send" button is renamed (D-022). |
| Canvas layout | canvas.json | Board titles and positions (reference only) |

## Sub-views and overlays

These live inside the screens above. They are built with their screen.

| Screen | Sub-view or overlay |
|---|---|
| Today | AI-state banner (backup, drafts pending, all limits used); "This week" filters; "Needs you" list; desktop Fresh block (D-016) |
| Jobs | Add a job drawer (link or by hand, status); job panel tabs Why it fits, People, Company, Description; company alert bell; source-paused banner. The country picker and the visa filter are hidden in v1 (D-006) |
| Job detail | Trust check list; Duplicates and history; "Not for me, because..." reasons; Hide similar posts |
| Ask | Chat list drawer; tool-call chips with sources; approval cards (Approve, Edit, Reject); "Tools it can use" and "How it works" panel. The microphone is hidden in v1 (D-008) |
| Pipeline | Card panel with notes and History; Add or reschedule round form; Record offer form; Compare offers panel; "Moved by Gmail" banner; undo toast |
| Prepare | Contents list; six sections one at a time; text mock interview overlay (the Type/Speak toggle and recording steps are hidden in v1, D-008) |
| Progress | Tabs Overview, Interview log, What to learn; period filter (30 or 90 days); Log an interview drawer |
| Sources and memory | Rules list with a suggestion card; Add a company (finder) flow; Alerts panel |
| Settings | Nine sections; MCP token create, copy once, revoke; client set-up commands; AI models list with usage chart |
| Resume | Panels Keywords, ATS, Preview (phone tabs); Add a skill; Parse my PDF; `.tex` view |
| Onboarding | Five steps and a finished screen on both desktop and phone |
| Landing | Six-step "how it works" tour (3D view with a step-card fallback when WebGL is off); "Is it safe?" numbers |
| Offer check | PF basis switch; clauses list; questions for HR |
| Studio | Draft list; tone selector; rewrite by part; keyword coverage |
| Application pack | Agent steps; "Needs your answer" field; approve and undo |
| Company brief | Refresh brief |
| Network | Referral message editor; asked tracking |

## Mock-only controls and data (never build these)

- The "MOCK PREVIEW" state picker in Settings and MSettings (it only lets a designer see states; the real banner is driven by real provider status).
- "Demo code: 123456" and "In this mock, use 123456" on Login and MLogin.
- The "Mock data" footer on Landing and MLanding.
- The example person, companies, salaries, dates and numbers (see `CLAUDE.md` section 4).
- The mock runtime (`support.js`, `dc-import`, `sc-for`, `renderVals`) and the sample data arrays in each file's script.

## Known conflicts and gaps, with decisions

Phase 0 decided every one of these with the founder. `D-xxx` is the record in `docs/DECISIONS.md`.

| # | Where | Conflict or gap | Decision | What changes in the mock |
|---|---|---|---|---|
| M1 | Login, MLogin | Mock shows "Continue with Google" and a 6-digit email code. Agreed plan: email + password with our own tokens. | D-010: email + password, no Google, no email code. | Remove the Google button, divider, code step and "Demo code"; add a password field; "Signed in with Google" in Settings becomes account details. |
| M2 | Settings, Onboarding, Landing | Alerts shown by Telegram and email. The newer Sources and memory screen says phone (web push). | D-011: web push only in v1; Telegram later; no email alerts. | Remove Telegram and email switches and wording; "one Telegram message" becomes one push plus an in-app banner. |
| M3 | Settings (AI models), Brief banner, Resume | Mistral, Google Gemini and OpenRouter as fallbacks; a switch "Let Gemini and OpenRouter see my resume text"; "reviewed by Mistral Large". Breaks the privacy rule. | D-012: Groq and Cerebras only; Llama 3.3 70B is judge and reviewer. | Remove the other three providers, the resume-text switch and the Mistral reviewer; "all five" becomes "both". |
| M4 | Onboarding, Pipeline, Settings | Gmail script `morrow-gmail.gs`, old name "morrow". | D-019: keep the design; rename to `nxtrole-gmail.gs`. | Rename. The script is the only email channel in v1. |
| M5 | Settings (agents) | "Company radar: funding news" has no free, reliable source. | D-021: hiring signals only. | Change the text from "funding news" to "hiring signals". |
| M6 | ResumeBuilder | LaTeX resume with live A4 preview; compiling LaTeX is heavy to host. | D-009: `.tex` and PDF from HTML in v1; in-browser LaTeX later. | Keep "Open in Overleaf" and PDF; hide the compile step. |
| M7 | Prepare, Ask | Voice mock interview and a microphone (Whisper on Groq). | D-008: text only in v1; voice later. | Hide Type/Speak, recording steps and the microphone. |
| M8 | All screens | No tablet mocks. | D-014: phone layout below 768 px, desktop from 768 px, icon-only side menu below 1024 px. | No mock change; tested at 390, 768, 1024 and 1440 px. |
| M9 | Most screens | Empty, loading and error states are not mocked. | D-015: designed in the mock style, shown to the founder first. | New states sheet in Phase 3. |
| M10 | Fresh jobs | Phone only; no desktop version. | D-016: a "Fresh" block at the top of Today on desktop. | New element on Brief; shown first. |
| M11 | Today (phone), Studio, Foundations | Buttons "Send follow-up", "Send message", "Send reply", "Approve & send", "Schedule for 10:00 AM", a sample "Send" button, and "Sent" confirmations imply NxtRole sends. | D-022: "Copy and mark sent", "Open ... ↗", "Marked sent", "Approve", "Remind me at 10:00 AM". The Ask chat "Send" stays. | Change the wording. |
| M12 | Onboarding, Jobs, Settings | LinkedIn, Naukri and Indeed shown as read "through public search"; "LinkedIn blocked this morning's search". Conflicts with golden rule 5 and with the Sources and memory screen. | D-005: official APIs, Gmail-script alert emails and manual add only. | Remove those source claims and the LinkedIn banner; show a generic "Source paused". |
| M13 | Jobs (Add a job) | Pasting a link reads any page. SSRF and site-terms risk. | D-007: only public https careers or ATS pages; login-only sites go to the by-hand form. | Reword "Any site works". |
| M14 | Jobs, MJobs | "Browser extension" (desktop) and "Share sheet" (phone) as ways to add a job. | D-007: both later. | Remove those lines. |
| M15 | Jobs, MJobs | Country picker, visa filter, ABROAD tag, "searched every 2 hours". | D-006: later; v1 is India and Remote (India). | Hide them. |
| M16 | Settings, Memory, MFresh, MOnboarding | Discovery "every 30 min" vs hourly; quiet hours 10 PM vs 11 PM; alerts at 80+ vs 90%+. | D-013: hourly; quiet 10 PM to 7 AM; alerts at 80+ and High trust, max 5 a day. | Align the wording. |
| M17 | Prepare, MPrepare, Ask, MAsk | Whisper on Groq sends the owner's voice to a provider. | D-008. | See M7. |
| M18 | ResumeBuilder, MResume | Mistral reviewer, `.docx` download, ATS score, PDF parser. | D-009 and D-012: reviewer is Llama 3.3 70B; `.docx` later; ATS score computed by code. | Remove "Download .docx" and the Mistral text. |
| M19 | Settings, Memory, Nav, Prepare | Two different Settings menus; "Sources and memory" has no desktop nav entry; Prepare has no list screen; no Notes screen. | D-017: one nine-section Settings menu; a Prepare list; notes stay inside Pipeline cards. | New Prepare list (N1); update the Memory menu. |
| M20 | Nav, TopBar, Settings, Onboarding | Old name "morrow": `morrow-theme`, `morrow-q`, `MORROW_TOKEN`, token prefix `mrw_live_`, `morrow-gmail.gs`, `jp2-theme`. | D-019: rename to NxtRole names. | Rename (token prefix `nxr_live_`). |
| M21 | Landing, MLanding | Footer "Mock data"; 3D tour; no mocks for Terms, Privacy, About, export, delete, 404 and offline. | D-018: keep the landing page; add the simple pages (N2 to N4). | Replace the footer; add the new pages. |
| M22 | Settings (Connections), TopBar | "Google Calendar: adds interview events, Connected" is not in the roadmap. | D-023: Google Calendar connection (OAuth) in v1. | None; built in Phase 12. |
