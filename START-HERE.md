# Start here

This pack contains the NxtRole roadmap and one Claude Code prompt for every phase.

## What is inside

| File | What it is |
|---|---|
| `CLAUDE.md` | Permanent rules. Claude Code reads it automatically in every session (git control, teaching, mocks as source of truth, Definition of Done, report format). |
| `docs/ROADMAP.md` | Sections A–J: product understanding, mock analysis, tech stack, architecture, phases, testing and security strategy, production checklist, risks and open questions, execution order. |
| `docs/prompts/PHASE-00…16-*.md` | 17 copy-paste prompts, one per phase. |
| `docs/mocks/source/` | The latest mocks (24 Nov 2026), 46 screens as `.dc.html` design files + `canvas.json`. |
| `docs/mocks/MOCK_INVENTORY.md` | Every screen → route → phase, plus 11 known conflicts to decide. |
| `docs/mocks/design-tokens.css` | Colours, fonts, radius (light and dark). Same as the copy already in your repo. |

## How to add it to your repository (Windows PowerShell)

1. Unzip `nxtrole-roadmap.zip` somewhere, for example your Downloads folder.
2. Copy everything inside the `nxtrole-roadmap` folder into the root of your NxtRole repository, so that
   `CLAUDE.md` sits next to your `docs` folder. Keep your existing `docs/mocks/desktop` and
   `docs/mocks/phone` PNGs; they stay as older references.
3. Move the old build prompt out of the way, so Claude Code does not follow two plans:
   ```powershell
   New-Item -ItemType Directory -Force docs\archive
   Move-Item BUILD-PROMPT.md docs\archive\BUILD-PROMPT.md
   ```
4. Do not commit yet unless you want to. Committing is always your call.

## How to run a phase

1. Open the repository in VS Code and start Claude Code.
2. Paste the whole prompt file, or type:
   `Read docs/prompts/PHASE-00-discovery.md and follow it.`
3. Answer its questions (one at a time). Read its plan and type "go".
4. At the end it gives a completion report and stops. Check the acceptance criteria yourself, then say
   "approved", ask for fixes, or ask it to show the proposed commit.
5. Move to the next phase only after you approve.

Start with Phase 0. It reviews your repository, asks the 13 open questions from `docs/ROADMAP.md`
section I, and writes the PRD. No code is written in Phases 0 and 1.
