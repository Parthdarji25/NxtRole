# Known issues

Every defect or limitation that is known and not yet fixed. Add a row when you find one, and update its status when it is fixed.
A phase may not be marked done while a **critical** or **high** issue is open (see the Definition of Done in `CLAUDE.md`).

**Severity:** *critical* = data loss, security hole or app unusable · *high* = a main journey is broken or unsafe ·
*medium* = a feature is wrong but there is a workaround · *low* = cosmetic or rare.
**Status:** open · in progress · fixed (name the phase) · accepted (the founder decided to live with it).

| ID | Date found | Area | Description | Severity | Status | Phase to fix |
|---|---|---|---|---|---|---|
| KI-001 | 2026-11-27 | Laptop | The Windows system PATH is missing `C:\Windows\System32` and related folders. `cmd`, `powershell` and `taskkill` are not found by name: the web pre-commit check fails and `pnpm e2e` does not exit | medium | open (founder: README Troubleshooting, last row) | Phase 2 |
| KI-002 | 2026-11-27 | Laptop | Windows 10 is past Microsoft's normal support period | medium | open (founder: check the Windows 11 upgrade or extended security updates) | before launch |
| KI-003 | 2026-11-27 | Laptop, tools | Node 22.14.0 is old: it blocks jsdom 31 and misses later fixes. Updating to the current 22.x is recommended | low | open | any time |
| KI-004 | 2026-11-27 | Web tools | TypeScript 7 and ESLint 10 cannot be used yet (lint tooling support) | low | accepted (D-044) | when supported |
| KI-005 | 2026-11-27 | Local containers | WSL sometimes prints "Failed to start the systemd user session". Docker and the containers work | low | open, watching | - |
| KI-006 | 2026-11-27 | CI | The commits up to `bd78534` are on GitHub, but nobody has checked whether the CI workflow passed there (the GitHub command-line tool is not installed) | medium | open (founder: look at the repository's Actions tab) | now |
| KI-007 | 2026-11-27 | Local containers | The Linux user is in the `docker` group, which has root-level power inside Ubuntu | low | accepted (personal development laptop) | - |
| KI-008 | 2026-11-27 | Containers | Container images use moving tags (`pg17`, `7-alpine`), so the 7-day rule does not cover them | low | open | Phase 14 |
| KI-009 | 2026-11-27 | Landing | The 3D view of the "how it works" tour is not built; the picture area shows the step number (D-018 made it the last, optional task) | low | accepted for now: build later (D-049) | before launch |
| KI-010 | 2026-11-27 | Landing, design | The Landing mocks show two blue buttons (header and tour), against "one primary button per screen" | low | accepted (D-049) | - |
| KI-011 | 2026-11-27 | Visual tests | The approved screen pictures are for Windows only and are not compared in CI (D-046) | low | accepted (D-046) | - |
| KI-012 | 2026-11-27 | Legal pages | The founder approved the Terms, Privacy notice and About text (D-049); they have had no legal review, and must be checked against the finished features | medium | open | before launch |
| KI-013 | 2026-11-27 | Rendering | Every page is rendered on each request, because the security policy needs a new nonce each time. Check speed when pages have data | low | open, watching | 13 |
| KI-014 | 2026-11-28 | Sign-in, production | The visitor's address as the API sees it is not yet reliable behind a forwarding server: the local web server passes a visitor-written `X-Forwarded-For` through unchanged. Locally all visitors look like one address, which is harmless. On the host this must be measured and `TRUSTED_PROXY_COUNT` set, or a stranger could lock the owner out | medium | open | 15 |
| KI-015 | 2026-11-28 | Sign-in | Password hashing settings were timed on the laptop only | low | open | 15 |
| KI-016 | 2026-11-28 | Sign-in | While Redis is down, an email without an account never locks, so a patient attacker could tell which email exists during that outage | low | accepted | - |
| KI-017 | 2026-11-28 | Database | Expired sign-in rows are removed only at the next sign-in; unused request keys only when reused. A clean-up job is planned | low | open | 8 |
| KI-018 | 2026-11-28 | AI | The real Groq service has not been used yet: no key in `api/.env`, so `check-ai` and the recorded-answer tests have not run. Resume reading is proved only with stand-ins | high | open (founder: add the key and the Zero Data Retention date; then check, record and try) | 5 |
| KI-019 | 2026-11-28 | AI | The free-plan limits are NxtRole's defaults, not read from the founder's account | low | open (founder: send the numbers from Groq's Limits page) | 5 |
| KI-020 | 2026-11-28 | AI, terms | Groq's Services Agreement, section 2, says the services are not for consumer use. The founder has to read it and decide | medium | open | before launch |
| KI-021 | 2026-11-28 | Profile | Saved answers (FR-024) are not built. Notice period and expected pay are stored in preferences; there is no `saved_answers` table | medium | open (founder decides the phase; recommended: 10, where packs use them) | 10 |
| KI-022 | 2026-11-28 | Onboarding | Setup records how far it got but does not reopen there, and there is no finished screen or finishing rule (FR-020, FR-021): steps 3 to 5 do not exist yet | medium | open (founder decides; recommended: 8, with the last setup step it depends on) | 8 |
| KI-023 | 2026-11-28 | Profile | No screen to delete a resume file or to see and restore older profile versions (the API can) | low | open | 14 |
| KI-024 | 2026-11-28 | Profile | A resume is read inside the API process: a restart interrupts it and it must be started again | low | open | 8 |
| KI-025 | 2026-11-28 | Files, production | Uploads go through the API to a local folder. The host allows requests of about 4.5 MB, so production needs the direct-to-storage upload of D-029 | medium | open | 15 |
| KI-026 | 2026-11-28 | Files | A file reader that runs past 30 seconds is abandoned but keeps running, and has no memory limit | low | open | 8 |
| KI-027 | 2026-11-28 | Onboarding | After a failed reading, the failure shows again on each visit to step 1 until a new upload (it can be put aside each time) | low | open | 8 |
| KI-028 | 2026-11-28 | Preferences | A resume that says an old city name (for example Bangalore) is offered beside the saved name (Bengaluru) in setup step 2 | low | open | 8 |

Mock conflicts are tracked in `docs/mocks/MOCK_INVENTORY.md` (M1 to M22) and their decisions in `docs/DECISIONS.md`, not here.
