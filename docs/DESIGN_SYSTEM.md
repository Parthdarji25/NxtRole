# Design system

Status: **specified in Phase 1, shared parts built in Phase 3 (27 Nov 2026); see section 8.** Source of truth: `docs/mocks/design-tokens.css`, `docs/mocks/source/Foundations.dc.html`, `Nav`, `TopBar`, `MTabs` and the repeated patterns across the 46 mock files.
Where a decision changes a mock (`docs/DECISIONS.md`, PRD Appendix D), the decision wins. Phase 3 builds this system; **no screen may invent a component that is not here** (CLAUDE.md section 4). New states are
designed in this style and approved first (D-015).

**What a design system is.** A small set of agreed building blocks (colours, type, spacing, components) so that every screen looks and behaves the same, and a change is made once. In code it becomes CSS variables
(tokens), Tailwind classes that read them, and a folder of components.

## 1. Principles (from the Foundations board, "The Brief")

1. **One action per screen.** Exactly one blue (`--blue`) primary button per screen; everything else is outlined or text.
2. **Agents stay backstage.** They appear as results, in the Agent log, or under "Needs you", never as chat-like noise.
3. **Rules, not boxes.** Hairlines (`--rule`) separate content; cards are rare.
4. **Details on demand.** Panels and drawers, not longer pages.
5. **Red means now.** `--red` only for things due today or tomorrow, things waiting on the owner, and errors.

## 2. Tokens

The file `web/src/styles/tokens.css` is a copy of `docs/mocks/design-tokens.css`. Light values are the default; dark values apply under `[data-theme="dark"]`. Tailwind v4 reads them with `@theme inline` (in `web/src/app/globals.css`) so classes such as `bg-paper`, `text-ink-2`, `border-rule` exist.

### 2.1 Colour (light / dark)

| Token | Light | Dark | Use |
|---|---|---|---|
| `--paper` | `#F4F1EA` | `#111214` | Page background |
| `--paper-2` | `#EBE6DB` | `#18191C` | Side navigation, tab bar, quiet areas |
| `--card` | `#FBF9F4` | `#1B1C20` | Panels, drawers, inputs |
| `--ink` | `#18181C` | `#ECE7DC` | Main text, dark buttons |
| `--ink-2` | `#45443F` | `#BEB9AE` | Body text, secondary |
| `--ink-3` | `#625F57` | `#8E8A80` | Meta, labels, placeholder text |
| `--rule` | `#DAD4C6` | `#2B2C31` | Hairlines |
| `--rule-2` | `#C4BCAA` | `#3C3D44` | Outlined button and input borders |
| `--blue` / `--blue-ink` / `--blue-soft` | `#2443E0` / `#1A33B8` / `#E4E8FB` | `#8EA2FF` / `#B1BEFF` / `#1C2342` | The one action colour; soft = selected background |
| `--on-blue` | `#FFFFFF` | `#0D1022` | Text on a blue button |
| `--red` / `--red-ink` / `--red-soft` | `#C23E2A` / `#A8321F` / `#F7E3DD` | `#FF8A73` / `#FF8A73` / `#3A1F19` | Due now, errors, Risky |
| `--green` / `--green-soft` | `#2F6B3A` / `#E2EDDF` | `#8DCB96` / `#16281A` | Done, High trust |
| `--amber` / `--amber-soft` | `#8A5B00` / `#F4E9CF` | `#E9C067` / `#2F2612` | Caution, Check, "not found" notices |
| `--shadow` | `0 1px 0 rgba(24,24,28,.04), 0 18px 40px -18px rgba(24,24,28,.22)` | `0 18px 40px -18px rgba(0,0,0,.7)` | Drawers and overlays only |

Contrast: the Foundations board states every text colour passes 4.5:1 on its paper in both themes. `web/src/styles/tokens.test.ts` checks every text/background pair the app uses and fails if one drops below 4.5:1 (NFR-A11Y-02). `--ink-3` on `--paper-2` and on `--card` is the pair to check first.
Colour is never the only signal: trust level and due dates always carry a word or icon too.

### 2.2 Typography

| Role | Font | Weight | Size (px) | Notes |
|---|---|---|---|---|
| Display | Geist | 600 | 44 to 64 (landing up to 88) | letter-spacing `-0.035em` for `h1`, `-0.025em` for other headings |
| Section and job titles | Geist | 600 | 20 to 28 | |
| Body | Geist | 400 / 500 | 15 to 17 | line-height 1.5 |
| Meta and helper | Geist | 400 | 13 | `--ink-2` or `--ink-3` |
| Labels, numbers | Geist Mono | 400 / 500 | 12 to 13 | letter-spacing `.05em`; the page "kicker" uses `.12em` uppercase |
| Match score numeral | Geist | 600 | 64 (large) / 13 mono in rows | `--blue` |

Loaded with `geist` (self-hosted by Next, no external font request). Mocks that use size 10 to 11 for mono labels are raised to 12 (the mock's own override rule) to meet legibility.

### 2.3 Spacing, radius, motion, layout

| Token | Values |
|---|---|
| Spacing scale | 4, 8, 12, 16, 24, 32, 48, 64 px |
| Radius | 6 inputs · 8 buttons · 12 panels · 16 hero cards · 999 pills and switches |
| Motion | 250 ms colour changes · 450 ms entrances · drawers slide 24 px · `prefers-reduced-motion: reduce` turns animation and transitions off |
| Page grid | content max width 1180 px, padding `32px 40px 64px` (desktop), side navigation 260 px |
| Phone | 390 px design width, 16 px side padding, bottom tab bar 84 px (52 px touch rows) |

### 2.4 Breakpoints (D-014)

| Width | Layout |
|---|---|
| below 768 px | Phone layout: bottom tab bar (Today, Jobs, Pipeline, Prepare, More), full-screen detail views |
| 768 to 1023 px | Desktop layout with the side navigation collapsed to **icons only** |
| 1024 px and above | Desktop layout with the 260 px side navigation |
| 1440 px | The mocks' design width; content stays at 1180 px and centres beyond it |

Phase 3 checks every screen at 390, 768, 1024 and 1440 px and shows the founder any screen that looks wrong.

## 3. Components

Component names are the code names in `web/src/components/ui/` (generic) and `web/src/features/*` (screen parts). "States" lists what must exist before a screen is done: **default, hover, focus (visible ring), pressed, disabled, loading, error** where they apply.

### 3.1 Primitives

| Component | Spec from the mocks | States and rules | Used by |
|---|---|---|---|
| **Button, primary** | 44 px high (40 px in list rows), padding `0 20px`, radius 8, `--blue` fill, `--on-blue` text, weight 600, 14 px. Label ends with an arrow for forward actions ("Apply →") | One per screen. Disabled, loading (label + spinner, width kept). Min hit area 44 px | Every screen |
| **Button, outline** | 44 px high, `1px solid --rule-2`, transparent, weight 600 | Same states | Save, Not today, Cancel |
| **Button, dark (small)** | 34 px high, `--ink` fill, radius 7, 13 px. **The sample on the board says "Send": renamed (D-022).** Mock height is below 44 px, so the hit area is padded to 44 px | Same states | Copy and mark sent, Approve |
| **Text button** | No border, `--ink-3`, 14 px, underline on hover | Focus ring | Not today, Undo, Dismiss |
| **Input, textarea, select** | Radius 6, `--card` fill, `1px --rule-2` border, 15 px; label above (never placeholder only) | Error: `--red` border + message with `aria-describedby`; disabled; loading | All forms |
| **Switch** | 44 × 24, thumb 16, `role="switch"`, `aria-checked`, label always present. On = `--ink` fill; off = outline `--ink-3`. **Hit area padded to 44 px** | Focus, disabled | Settings |
| **Chip (toggle)** | Pill, `aria-pressed`, selected uses `--blue-soft` with `--blue-ink` text | Focus, disabled | Titles, places, filters |
| **Tabs** | Underline tabs, **never pills**; selected = weight 600 + 2 px `--ink` underline; implemented as buttons with `aria-pressed` or `role="tablist"` | Keyboard arrow keys | Job panel, Progress, Settings sections |
| **Segmented control** | Underline style, same as tabs | | Jobs segments (Matches, Saved, Companies) |
| **Toast** | Bottom, `--ink` fill, message + action ("Undo") | Polite live region; stays 8 s; reduced motion | Undo, success |
| **Badge, count** | 16 px circle or pill, `--red` fill for items waiting on the owner | | Navigation |
| **Kicker** | Mono 12 px uppercase with `.12em` spacing, `--ink-3` ("TUESDAY, 20 OCTOBER · YOUR BRIEF") | | Every page header |
| **Page header** | Kicker + `h1` (display) + lead paragraph (`--ink-2`, 17 px) | | Every screen |
| **Divider** | `1px --rule` | | Everywhere (rules, not boxes) |
| **Skeleton** (new, D-015) | `--paper-2` blocks with a slow pulse (off for reduced motion), same sizes as the content | | Loading states |

### 3.2 Compound patterns (repeated across screens)

| Pattern | Anatomy | States | Screens |
|---|---|---|---|
| **List row (the core pattern)** | Large numeral (serif 32, `--ink-3`), bold title (serif 24), one line of meta, **one coloured reason** (red only when due now), mono score, one action button | Loading skeleton, empty, hover, selected (`--blue-soft`), saved, skipped (with Undo) | Today, Jobs, Fresh jobs |
| **Match score** | Large numeral in `--blue` with mono "% MATCH", or "92%" in rows; "AI score pending" text when null | Pending, unsure | Today, Jobs, Job detail |
| **Trust badge** | Small pill with word + icon: High trust (green), Check (amber), Risky (red) | Three levels | Today, Jobs, Fresh, Job detail |
| **Trust check list** | Rows with pass/fail icon, label, evidence quote (mono quote style) | Passed, failed, "not scored" | Job detail |
| **Quote** | Curly-quoted text with a verified tick ("checked word for word") | Verified, removed | Why it fits |
| **Drawer** | Right side, width `min(460px, 100vw)`, `--paper`, left border `--rule`, `--shadow`, slides 24 px, `role="dialog"`, `aria-modal`, focus trap, Esc closes, returns focus | Open, closing, loading, error | Add a job, Log an interview, Agent log, Chats, Search |
| **Side panel (job)** | Same drawer pattern on desktop; **full screen** on phone with a back link | | Jobs |
| **Banner** | `--card` or soft colour band with a sentence and one action; amber for "needs you", red for errors, green for success | Dismissible | Source paused, AI state, Moved by Gmail |
| **Approval card** | Proposed change with before/after, buttons Approve (primary), Edit, Reject; "The agent is paused until you decide" | Pending, approved, rejected, stale | Ask, Studio, Pipeline |
| **Stage board (Pipeline)** | Five columns Saved to Closed (phone: stage selector + list); card with company, role, next step, "Moved by Gmail" tag | Empty column text "Nothing in this stage yet." | Pipeline |
| **Round / History list** | Dated rows with actor (You, Gmail, agent) and "Undo this" | | Pipeline |
| **Stat strip** | Row of counts with mono labels | Loading, zero | Follow-ups, Progress, Coach |
| **Funnel / bar chart** | Rule-based bars in `--blue` / `--ink-3`; value labels; "too few" state | Too few, empty | Progress, Coach |
| **Section stepper** | "Section 2 of 6 · Next →" with a contents list | | Prepare |
| **Chat message** | User bubble (plain), assistant text streaming, tool-call chip with sources, approval card | Streaming, stopped, error | Ask |
| **Source link** | Mono 11 to 12 px, `--ink-3`, "SOURCE · DATE", opens in a new tab with `rel="noopener noreferrer"` | | Briefs |
| **Empty state** (new) | Heading, one sentence on what to do next, one action; **never fake data** | | Every list |
| **Error state** (new) | Plain sentence, what to try, "Retry" | | Every list |
| **Offline notice** (new) | Band "You are offline. Showing what was loaded." Actions disabled | | App shell |

### 3.3 Shell components

| Component | Spec | Source |
|---|---|---|
| **Side navigation (desktop)** | 260 px, `--paper-2`; logo "Nxt" in ink and "Role" in blue; 10 items (Today, Ask NxtRole, Jobs, Pipeline, Follow-ups, Prepare, Studio, Resume, Network, Progress), Settings, theme switch (Light / Dark), "Agents idle · next run …" status; count badges; icons only below 1024 px | Nav |
| **Top bar (desktop)** | Search field ("Search jobs, companies, notes, questions…", `Ctrl K`), "Ask NxtRole" shortcut, agent-log button; search overlay with grouped results and the text "Nothing found. Try a company, a skill or a word from a note." | TopBar |
| **Phone tab bar** | 84 px high, 5 tabs (Today, Jobs, Pipeline, Prepare, More), current tab in `--blue` weight 700, count badges, `aria-current` | MTabs |
| **More menu (phone)** | Profile line, list of destinations with sub-text and counts, appearance switch, agent status, About, Sign out | MMore |
| **Logo** | "Nxt" in `--ink` and "Role" in `--blue` everywhere (CLAUDE.md rule 6) | all |

### 3.4 Screen-specific parts (built inside their phase)

Landing tour (3D scene with step-card fallback, built last in Phase 3, D-018), onboarding stepper (5 steps + finished screen), keyword and ATS panels and the A4 preview (Resume), the CTC table and PF switch (Offer check),
the referral message editor (Network), the token box with "shown once" (Settings > Connections), the rules list with suggestion card (Sources and memory), the company finder flow (Sources and memory).

## 4. State coverage rule (D-015)

Every list and screen needs **loading, empty, error and success**; offline and "pending" where relevant. The mocks draw only a few. Phase 3 produces a **sample sheet** of the new states (skeleton, empty, error, offline, pending, stale brief) in this style and the founder approves it before the states are used on every screen. Empty states say what to do next and never show example data (golden rule 1).

## 5. Accessibility rules (WCAG 2.2 AA; NFR-A11Y)

- **Keyboard:** every control reachable and operable; logical order; drawers trap focus and return it; `Esc` closes overlays; `Ctrl K` opens search.
- **Focus:** a visible ring (2 px `--blue`, 2 px offset) on every focusable element; never `outline: none` without a replacement.
- **Targets:** at least 44 × 44 px (small visual controls such as the switch and the dark button get padded hit areas).
- **Labels:** every input has a visible label; icon-only buttons have `aria-label`; the theme switch and chips use `aria-pressed`.
- **Contrast:** 4.5:1 for text, 3:1 for non-text UI parts, in both themes (checked by script).
- **Motion:** `prefers-reduced-motion` disables animation and the 3D tour auto-play.
- **Live regions:** toasts and streaming text use `aria-live="polite"`; errors use `role="alert"` and are tied to their field.
- **Zoom and reflow:** works at 200% zoom and 320 px width without horizontal scrolling.
- **Language and landmarks:** `lang="en"`, one `main`, labelled `nav` regions.

## 6. Theme

Light by default; the choice is stored on the device as `nxtrole-theme` (`light` or `dark`) and follows the system on first visit. The theme switch sits in the side navigation (desktop) and More (phone). A small inline script sets `data-theme` before first paint to avoid a flash.

## 7. Component inventory check (Phase 1 documentation check)

| Source | Components found | In this document |
|---|---|---|
| `Foundations.dc.html` | Principles, 8 colour pairs, 5 type roles, primary / outline / dark / text buttons, switch, tabs, match score, list row, spacing, radius, motion | Sections 1 to 3 |
| `Nav.dc.html`, `TopBar.dc.html`, `MTabs.dc.html`, `MMore.dc.html` | Side navigation, top bar, search overlay, agent log, tab bar, More menu | 3.3 |
| Repeated across the 22 screens | Kicker and page header, chips, trust badges, toggles (switches), drawers, banners, list rows, approval cards, stage board, stat strips, charts, source links | 3.1 and 3.2 |
| Screen-specific | Landing tour, stepper, A4 preview, CTC table, token box | 3.4 |

Result: every pattern seen in the mocks has an entry; four patterns (skeleton, empty, error, offline) are new and need approval (D-015); the "Send" sample button is renamed and padded to a 44 px hit area (D-022).

## 8. Built components (Phase 3)

See them all, in every state and both themes, at `/design` and `/design/states` while `pnpm dev` runs. A **component** is a reusable piece of screen; its
**props** are the settings you pass to it, for example `<Button variant="primary">`.

| File in `web/src/` | Components | How to use |
|---|---|---|
| `components/ui/button.tsx` | `Button` | `variant`: `primary` (one per screen), `ink`, `outline` (default), `text`. `size`: `md`, `sm`, `lg`. `loading` blocks clicks and shows a spinner. `asChild` gives a link the button look |
| `components/ui/field.tsx` | `Field`, `Label`, `Input`, `Textarea`, `Select` | `<Field label="Email" error={message}>{(control) => <Input {...control} />}</Field>` ties label, hint and error to the input |
| `components/ui/switch.tsx`, `segmented.tsx`, `chip.tsx`, `tabs.tsx` | `Switch`, `Segmented`, `Chip`, `Tabs` | On/off, one-of-a-few, toggle, and keyboard tabs. Each needs a label |
| `components/ui/badge.tsx` | `Badge`, `TrustBadge`, `CountBadge` | Trust reads High trust, Check first or Risky. A count of 0 is hidden |
| `components/ui/sheet.tsx`, `dialog.tsx`, `menu.tsx` | `Sheet`, `Dialog`, `DropdownMenu`, `Tooltip` | Overlays: focus is kept inside, Escape closes, focus returns |
| `components/ui/toast.tsx` | `showToast`, `showUndoToast`, `Toaster` | Short messages; the undo version has an Undo button |
| `components/ui/layout.tsx` | `PageHeader`, `SectionHeading`, `Kicker`, `Panel`, `StatTile`, `ProgressBar` | `phoneTitle` and `phoneLead` are for screens whose phone mock differs |
| `components/ui/icons.tsx` | `Icon` | The mocks' line icons; decoration only |
| `components/states/` | `Loading`, `ListSkeleton`, `PageSkeleton`, `EmptyState`, `EmptyScreenState`, `ErrorState`, `Banner`, `OfflineNotice`, `PendingTag` | Wording of empty screens lives in `content/emptyStates.ts` (approved, D-047) |
| `components/layout/` | `AppShell`, `SideNav`, `TopBar`, `TabBar`, `PhoneHeader`, `Screen`, `SettingsMenu`, `ProgressNav`, `Logo`, `ThemeSwitch`, `ThemeToggle`, `LegalPage` | Menus are defined once in `nav.ts` |
| `features/landing/Tour.tsx`, `features/auth/LoginForm.tsx` | Landing tour, sign-in form | Screen parts |

**A new screen** uses `Screen` (title, kicker, lead, way back) and an empty, loading and error state before any data.

Not built yet (their phase builds them): the compound patterns of section 3.2 (list row, drawers with forms, approval card, stage board, charts, chat) and the 3D tour.

### Added in Phase 4 (screens approved by the founder, D-051)

| File in `web/src/` | Component | How to use |
|---|---|---|
| `components/ui/form-problem.tsx` | `FormProblem` | Why a form could not be sent: a red band, announced to screen readers |
| `components/layout/settings-layout.tsx` | `SettingsLayout` | The Settings menu and one section |
| `features/auth/AuthLayout.tsx` | `AuthLayout` | The two halves of the sign-in mock |
| `features/auth/PasswordInput.tsx`, `RecoveryCode.tsx`, `SignOutButton.tsx` | | Password with Show and Hide; the one-time code; the More page's sign-out |
| `features/account/` | `AccountView`, `ChangePassword` | Setting rows, device list, drawer and confirmation |
