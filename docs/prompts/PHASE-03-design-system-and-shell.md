# Phase 3 — Design system and app shell

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-03-design-system-and-shell.md and follow it.`
> Follow `CLAUDE.md`. No commits.

## 1. Phase name and objective
**Design system and app shell.** Turn the mocks into reusable components and layouts: tokens, fonts,
light/dark theme, navigation on desktop and phone, the public landing page, and every product route
with its real empty, loading and error states (no fake data). After this phase NxtRole looks right
everywhere; later phases fill the screens with real data.

## 2. Context and dependencies
- Requires Phase 2 approved. Use `docs/DESIGN_SYSTEM.md`, `docs/mocks/MOCK_INVENTORY.md` and the
  decisions on tablet layout (M8), missing states (M9), login (M1) and desktop fresh jobs (M10).
- The temporary health page from Phase 2 is replaced.

## 3. Detailed implementation tasks
1. **Tokens and theme:** import `docs/mocks/design-tokens.css` into `web/app/globals.css`; map tokens
   to Tailwind with `@theme inline` (`bg-paper`, `bg-card`, `text-ink`, `text-ink-2`, `text-ink-3`,
   `border-rule`, `bg-blue`, `text-red`, `text-green`, `text-amber` and the soft variants); dark mode via
   `data-theme="dark"` on `<html>`, chosen from saved preference or the system setting, without a
   flash on load; Geist and Geist Mono through `next/font`.
2. **Components** (shadcn/ui where it fits, restyled to the mocks; others hand-built): Button (primary
   blue, ink, outline, text; loading state; never more than one primary per screen), Input, Textarea,
   Label, Select, Switch (the toggle in Sources and memory), Segmented control (Light/Dark, PF basis),
   Tabs, Dialog, Sheet (drawers such as "Add a job"), DropdownMenu, Tooltip, Toast with Undo, Chip,
   Badge (trust: High / Check first / Risky; status tags), Panel/Card, PageHeader (mono kicker + heading
   + lead), Stat tile, Progress bar, Skeleton, EmptyState, ErrorState, Kicker (mono label).
3. **Layouts:** desktop `AppShell` = left navigation (from `Nav.dc.html`: logo, items with counts,
   Settings, agent status line, theme switch) + `TopBar` (search box and agent log button from
   `TopBar.dc.html`; search and log are wired in later phases, show their empty states now) + content
   area (max 1180 px, padding 32/40/64). Phone layout = content + bottom `MTabs` (Today, Jobs, Pipeline,
   Prepare, More) + the More page (`MMore.dc.html`). Breakpoints as decided (M8).
4. **Routes** (from the inventory) with loading (skeleton), empty and error states:
   `/today`, `/today/fresh`, `/jobs`, `/jobs/[id]`, `/ask`, `/pipeline`, `/pipeline/offers/[id]`,
   `/follow-ups`, `/prepare/[applicationId]`, `/companies/[id]`, `/studio`, `/studio/packs/[id]`,
   `/resume`, `/progress`, `/progress/coach`, `/network`, `/settings`, `/settings/sources`, `/more`,
   `/onboarding` (step layout only). Empty states say what to do next, for example "No jobs yet. Add the
   companies you want to watch." with a link to the right place. Never show sample data.
5. **Public pages:** the landing page `/` built fully from `Landing.dc.html` / `MLanding.dc.html`
   (static content; check every number on it is true for NxtRole, otherwise ask me), and the sign-in
   page UI `/login` per decision M1 (form validation only; wired to the API in Phase 4).
6. **Design review page:** a development-only route `/design` showing every component in every state,
   light and dark (not built for production).
7. **Visual checks:** Playwright screenshots of each route at 1440×900 and 390×844, light and dark, saved
   as baselines; a side-by-side review page in `docs/visual-review/` comparing each built screen with its
   mock PNG (or a note to compare with the `.dc.html` source when no PNG exists). Show me the empty-state
   designs before applying the pattern everywhere (M9).

## 4. UI mock references
`Foundations`, `Nav`, `TopBar`, `MTabs`, `MMore`, `Landing`, `MLanding`, `Login`, `MLogin`, and every
screen in the inventory for page headers, spacing and layout. Exact values come from the `.dc.html`
inline styles (for example the header: mono 12 px kicker with .1em letter spacing, 48–56 px heading,
18 px lead, 2 px ink rule below).

## 5. Recommended technologies
Next.js 16 App Router, Tailwind v4, shadcn/ui (Radix), `next/font`, sonner (toasts), lucide or inline
stroke icons matching the mocks, Playwright (screenshots, axe), Vitest + Testing Library.

## 6. Files and modules to create or modify
`web/app/globals.css`, `web/app/layout.tsx`, `web/app/(public)/page.tsx` (landing),
`web/app/(public)/login/page.tsx`, `web/app/(app)/layout.tsx` and one folder per route above,
`web/components/ui/*` (primitives), `web/components/layout/{app-shell,side-nav,top-bar,tab-bar}.tsx`,
`web/components/states/{empty-state,error-state,skeletons}.tsx`, `web/lib/theme.ts`,
`web/app/design/page.tsx` (dev only), `web/tests/visual/*.spec.ts`, `docs/visual-review/`.

## 7. Database and API requirements
None. Routes must not call the API yet except the login form's client-side validation.

## 8. Implementation sequence
Tokens + theme → primitives → page header and state components → desktop shell → phone shell and More →
show me the empty-state pattern → all routes with states → landing page → login UI → design page →
screenshots and visual review → accessibility pass.

## 9. Testing requirements
- Vitest: each primitive's variants and states; theme switch persists; nav marks the current page.
- Playwright: every route renders on desktop and phone sizes, light and dark; keyboard can reach every
  control; axe reports no serious violations; screenshots saved.
- Manual: side-by-side review page shows each screen next to its mock.

## 10. Edge-case checklist
- [ ] Dark mode on first visit follows the system; no flash of the wrong theme.
- [ ] Long names and long headings wrap without breaking layout (test with a 60-character title).
- [ ] 200% browser zoom and 390 px width still usable.
- [ ] Reduced-motion users get no animations.
- [ ] Very slow network shows skeletons, not blank screens.
- [ ] Unknown route shows a friendly 404 in the same style.

## 11. Security considerations
No data yet. Do not render any HTML strings; set security headers already added in Phase 2;
`/design` must not exist in production builds.

## 12. Acceptance criteria
- [ ] Every route in the inventory exists with loading, empty and error states, desktop and phone.
- [ ] Landing and login UI match their mocks; side-by-side review shows no large differences.
- [ ] Light and dark themes both match the tokens.
- [ ] One primary (blue) button per screen; red used only for errors or due-today items.
- [ ] Accessibility checks pass; all tests, lint, types and build pass.
- [ ] No sample or fake data anywhere.

## 13. Documentation updates
`docs/DESIGN_SYSTEM.md` (final components and usage), `docs/mocks/MOCK_INVENTORY.md` (status per
screen: UI done), `docs/TESTING.md` (visual and accessibility tests), `docs/KNOWN_ISSUES.md`,
`docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format, plus screenshots (desktop and phone) of three screens next to their mocks.
Explain: components, props, design tokens, responsive layout, accessibility basics.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 4." Do not commit.
