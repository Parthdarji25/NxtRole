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
| KI-006 | 2026-11-27 | CI | The CI workflow and Dependabot have never run: nothing is pushed. The workflow passes actionlint | medium | open | first push |
| KI-007 | 2026-11-27 | Local containers | The Linux user is in the `docker` group, which has root-level power inside Ubuntu | low | accepted (personal development laptop) | - |
| KI-008 | 2026-11-27 | Containers | Container images use moving tags (`pg17`, `7-alpine`), so the 7-day rule does not cover them | low | open | Phase 14 |

Mock conflicts are tracked in `docs/mocks/MOCK_INVENTORY.md` (M1 to M22) and their decisions in `docs/DECISIONS.md`, not here.
