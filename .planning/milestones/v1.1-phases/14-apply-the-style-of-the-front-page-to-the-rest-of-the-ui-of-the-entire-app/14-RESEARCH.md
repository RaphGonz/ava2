# Phase 14: Apply the style of the front page to the rest of the UI — Research

**Researched:** 2026-03-10
**Domain:** React / Tailwind v4 / motion/react — visual redesign (dark theme, glassmorphism, persistent navigation)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Dark theme baseline
- Background: black (`bg-black`) matching the landing page, not `bg-gray-950`
- Text: white / slate-400 for secondary
- Accent colors: blue → violet → orange gradients (same as landing)
- Glass surfaces: `bg-white/5 backdrop-blur-md border border-white/10` — use existing `GlassCard` component wherever possible
- Buttons: gradient `from-blue-600 to-violet-600` for primary CTAs, `bg-white/5 border-white/10` for secondary

#### Navigation (fixes dead-end problem)
- Persistent navigation: bottom tab bar on mobile, top nav bar on desktop
- Tabs: Chat | Photos | Settings (3 tabs)
- Billing accessible from within Settings — NOT a top-level nav tab
- All pages must have a clear way back (back buttons where applicable, nav bar everywhere)

#### Chat page
- Full dark screen — `bg-black`, full viewport height
- Header: Ava's avatar image + gradient name text + online status glow indicator
- User message bubbles: `bg-gradient-to-r from-blue-600 to-violet-600`, rounded
- Ava message bubbles: glassmorphism — `bg-white/5 backdrop-blur-md border border-white/10`, rounded
- Input bar: dark styled, consistent with overall theme

#### Auth pages (login, signup, forgot password, reset password)
- Background: black, same as landing page
- Card: centered glassmorphism card (`GlassCard` or equivalent) with subtle gradient border
- Form inputs: `bg-white/5 border border-white/10`, on focus: blue/violet ring
- Buttons: same gradient primary button as landing page
- All auth pages updated (login, signup, forgot-password, reset-password)

#### Settings page
- Background: black
- Each settings section (Persona, Platform, Spiciness, Mode-switch phrase, Notifications) becomes a `GlassCard`
- Option selectors (active state): gradient highlight instead of `bg-gray-900`
- New section at the bottom: "Subscription" — shows current plan status + "Manage Billing" button linking to `/billing`

#### Billing / Subscribe pages
- Background: black, GlassCard-based layout
- Back button to return to Settings on all billing-related pages
- Consistent with rest of dark theme

#### Landing Hero right-side mockup update
- Replace the audio visualizer mockup (bars + "I have something for you...") with:
  - A flirty chat bubble exchange (2-3 messages, styled like the dark chat bubbles)
  - A blurred/locked photo with a "click to open" overlay beneath it
- Left side (tech/Jarvis mockup) stays as-is

### Claude's Discretion
- Exact gradient border implementation on glassmorphism cards
- Motion animation specifics (entrance animations, hover effects) — follow landing page patterns
- Exact spacing/typography adjustments
- Photo page dark theme styling
- Admin page already uses dark theme (`bg-gray-950`) — adjust to pure black to match

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

## Summary

Phase 14 is a pure visual and navigation restyling pass over the entire authenticated app. No new backend endpoints, no new features. The reference design already exists in the landing page — the task is to extract its visual language (black bg, blue/violet/orange gradients, glassmorphism via `GlassCard`, `motion/react` animations) and apply it uniformly to every other page.

The current codebase has a clear split: the landing page (`LandingPage.tsx` and its `components/landing/` siblings) is fully dark-themed with glassmorphism and motion. Every authenticated page (`ChatPage`, `LoginPage`, `SignupPage`, `ForgotPasswordPage`, `ResetPasswordPage`, `SettingsPage`, `AvatarSetupPage`, `SubscribePage`, `BillingPage`, `PhotoPage`) still uses the old white/gray-50 light theme or `bg-gray-950` dark. `BillingPage` and `AdminPage` are already partially migrated (they use `GlassCard` and `bg-gray-950`), so they need the smallest delta.

The single most important structural addition is a persistent `AppNav` component (bottom tab bar on mobile, top bar on desktop) shared by all authenticated pages. This eliminates navigation dead-ends and should be added to `App.tsx` or as a wrapper layout component, rendered inside `ProtectedRoute` wrapping. The Hero mockup update in `LandingHero.tsx` is isolated to one file.

**Primary recommendation:** Build `AppNav` first (wave 1), then restyle auth pages (wave 2), then chat + components (wave 3), then settings + billing + supporting pages (wave 4), then the Hero mockup update (wave 5).

---

## Standard Stack

### Core (already installed — no new dependencies needed)

| Library | Version | Purpose | Role in Phase 14 |
|---------|---------|---------|-----------------|
| tailwindcss | ^4.2.1 | Utility-first CSS | All styling — Tailwind v4 CSS-first config (no tailwind.config.js) |
| motion | ^12.35.1 | Animation | `motion/react` import — entrance animations, hover effects |
| clsx + tailwind-merge | ^2.1.1 / ^3.5.0 | Class merging | Used inside `GlassCard` already — reuse same `cn()` helper |
| lucide-react | ^0.577.0 | Icons | Navigation tab icons, back arrows |
| react-router-dom | ^7.13.1 | Routing | `useLocation` for active nav tab detection |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @tanstack/react-query | ^5.90.21 | Data fetching | Settings page needs subscription status for the new Subscription section |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| motion/react (already installed) | framer-motion | motion IS framer-motion v12 — same API, different package name. Do NOT import from framer-motion — the project standardized on `motion/react` in Phase 10. |

**Installation:** No new packages needed. Everything required is already in `frontend/package.json`.

---

## Architecture Patterns

### Recommended Structure for New Files

```
frontend/src/
├── components/
│   ├── AppNav.tsx           # NEW — persistent nav (bottom mobile, top desktop)
│   ├── ChatBubble.tsx       # MODIFY — dark theme
│   ├── ChatInput.tsx        # MODIFY — dark theme
│   ├── MessageList.tsx      # MODIFY — dark bg for scroll area
│   └── GoogleSignInButton.tsx  # MODIFY — dark-themed border/colors
├── pages/
│   ├── ChatPage.tsx         # MODIFY — full dark restyle + header
│   ├── LoginPage.tsx        # MODIFY — black bg, GlassCard, gradient button
│   ├── SignupPage.tsx       # MODIFY — black bg, GlassCard, gradient button
│   ├── ForgotPasswordPage.tsx  # MODIFY — black bg, GlassCard, gradient button
│   ├── ResetPasswordPage.tsx   # MODIFY — black bg, GlassCard, gradient button
│   ├── SettingsPage.tsx     # MODIFY — black bg, GlassCard sections, subscription section
│   ├── AvatarSetupPage.tsx  # MODIFY — black bg, GlassCard, gradient button
│   ├── SubscribePage.tsx    # MODIFY — GlassCard layout, gradient button
│   ├── BillingPage.tsx      # MODIFY — bg-black (was bg-gray-950), back button
│   ├── PhotoPage.tsx        # MODIFY — minor dark polish
│   └── AdminPage.tsx        # MODIFY — bg-black (was bg-gray-950)
└── components/landing/
    └── LandingHero.tsx      # MODIFY — replace right mockup content
```

### Pattern 1: AppNav Component (Persistent Navigation)

**What:** A single navigation component that renders differently based on viewport. On mobile: fixed bottom tab bar. On desktop: sticky top bar. Uses `useLocation()` to highlight the active tab.

**When to use:** Wrap all authenticated pages — insert inside `ProtectedRoute` in `App.tsx`, or create a layout wrapper component.

**Example:**
```typescript
// frontend/src/components/AppNav.tsx
import { Link, useLocation } from 'react-router-dom'
import { MessageSquare, Image, Settings } from 'lucide-react'

const NAV_TABS = [
  { path: '/chat', label: 'Chat', icon: MessageSquare },
  { path: '/photo', label: 'Photos', icon: Image },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export function AppNav() {
  const { pathname } = useLocation()
  return (
    <>
      {/* Desktop: top bar */}
      <nav className="hidden md:flex sticky top-0 z-50 w-full bg-black/80 backdrop-blur-sm border-b border-white/5 px-6 py-4 items-center justify-between">
        <span className="text-lg font-bold text-white">Avasecret</span>
        <div className="flex items-center gap-6">
          {NAV_TABS.map(tab => (
            <Link
              key={tab.path}
              to={tab.path}
              className={`text-sm transition-colors ${
                pathname === tab.path
                  ? 'text-white font-medium'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.label}
            </Link>
          ))}
        </div>
      </nav>
      {/* Mobile: bottom tab bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-md border-t border-white/10 flex justify-around py-2">
        {NAV_TABS.map(tab => {
          const Icon = tab.icon
          const isActive = pathname === tab.path
          return (
            <Link
              key={tab.path}
              to={tab.path}
              className={`flex flex-col items-center gap-1 px-4 py-1 text-xs transition-colors ${
                isActive ? 'text-white' : 'text-slate-500'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'stroke-[url(#grad)]' : ''}`} />
              {tab.label}
            </Link>
          )
        })}
      </nav>
      {/* Mobile bottom padding spacer */}
      <div className="md:hidden h-16" />
    </>
  )
}
```

**Key detail:** `AppNav` must NOT appear on landing, login, signup, auth/callback, forgot-password, or reset-password pages. Insert it only inside `OnboardingGate`/`ProtectedRoute` layout or conditionally by route. The cleanest approach: create a `<AuthenticatedLayout>` wrapper used for `/chat`, `/settings`, `/billing`, `/photo` routes that renders `AppNav` + the page children.

### Pattern 2: GlassCard Usage for Section Cards

**What:** Replace every `bg-white rounded-2xl shadow-sm border border-gray-100` section card with `<GlassCard>`. The component already exists in `frontend/src/components/ui/GlassCard.tsx`.

**When to use:** Every "section box" inside authenticated pages.

**Example:**
```typescript
// Replace this (SettingsPage current):
<section className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">

// With this:
<GlassCard className="p-5">
  {/* section content */}
</GlassCard>
```

### Pattern 3: Gradient Primary Button

**What:** The landing page's primary CTA button style applied to all primary buttons.

```typescript
// Primary CTA — matches landing page nav + hero
<button className="w-full bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white rounded-lg py-2 text-sm font-medium transition-all disabled:opacity-50">
  Submit
</button>

// Secondary button
<button className="w-full bg-white/5 border border-white/10 text-white rounded-lg py-2 text-sm font-medium hover:bg-white/10 transition-all">
  Cancel
</button>
```

### Pattern 4: Dark Form Inputs

**What:** All form inputs adopt the dark glass style with blue/violet focus ring.

```typescript
// Replace border-gray-200 focus:ring-gray-900 inputs with:
<input
  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50"
/>
```

### Pattern 5: motion/react Entrance Animation

**What:** Match the landing page's `initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}` pattern for page-level containers.

```typescript
import { motion } from 'motion/react'

// Page card entrance (auth pages):
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.4 }}
>
  <GlassCard>...</GlassCard>
</motion.div>
```

**Critical:** Import from `motion/react`, NOT `framer-motion`. The vitest config mocks `motion/react` — tests will continue to work without changes.

### Pattern 6: Chat Bubble Restyle

**What:** User bubbles become gradient; Ava bubbles become glassmorphism.

```typescript
// ChatBubble.tsx — restyle both bubble types:
// User bubble:
'bg-gradient-to-r from-blue-600 to-violet-600 text-white rounded-br-sm'

// Ava bubble:
'bg-white/5 backdrop-blur-md border border-white/10 text-white rounded-bl-sm'
```

### Pattern 7: Landing Hero Right Mockup Replacement

**What:** The right-side notification card (`w-64 bg-black/40 backdrop-blur-md border border-white/10 rounded-3xl`) stays — only its inner content changes. Replace the `bg-white/10 notification block` + audio visualizer with 2-3 chat bubbles and a blurred locked photo.

```typescript
// Inner content replacement in LandingHero.tsx:
{/* Chat bubbles */}
<div className="space-y-2 mb-3">
  {/* Ava message */}
  <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl rounded-bl-sm px-3 py-2 text-xs text-white/90 text-left max-w-[85%]">
    Missing you already... 🌙
  </div>
  {/* User message */}
  <div className="bg-gradient-to-r from-blue-600 to-violet-600 rounded-xl rounded-br-sm px-3 py-2 text-xs text-white text-right ml-auto max-w-[75%]">
    Show me something
  </div>
  {/* Ava message */}
  <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl rounded-bl-sm px-3 py-2 text-xs text-white/90 text-left max-w-[85%]">
    Just for you... 💜
  </div>
</div>
{/* Blurred locked photo */}
<div className="relative rounded-xl overflow-hidden h-24">
  <div className="absolute inset-0 bg-gradient-to-b from-violet-800/30 to-orange-800/30 backdrop-blur-lg" />
  <div className="absolute inset-0 flex items-center justify-center">
    <span className="text-white/70 text-xs font-medium">🔒 Click to unlock</span>
  </div>
</div>
```

### Anti-Patterns to Avoid

- **`bg-gray-50` or `bg-white` backgrounds:** Every page background must be `bg-black`. No exceptions in authenticated pages.
- **`border-gray-100`, `border-gray-200`, `text-gray-900` on auth pages:** Replace all with dark equivalents.
- **`focus:ring-gray-900`:** Replace with `focus:ring-blue-500/50` on all inputs.
- **`bg-gray-900` active state for buttons:** Replace with gradient `from-blue-600 to-violet-600`.
- **`bg-gray-800`, `bg-gray-700` in AvatarSetupPage and SubscribePage:** Replace with `bg-white/5 border border-white/10`.
- **Importing from `framer-motion`:** Always import from `motion/react`.
- **Adding AppNav to non-authenticated pages:** Landing, login, signup, forgot-password, reset-password should not show AppNav.
- **Removing the `OnboardingGate` `bg-gray-950` loading state:** The loading state in `App.tsx` `OnboardingGate` also needs to be updated to `bg-black`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Glassmorphism cards | Custom backdrop-blur divs | `GlassCard` component | Already exists, has 3 variants, uses motion.div |
| Class merging | Ternary string concatenation | `cn()` helper (clsx + twMerge) | Already in GlassCard.tsx, extract if needed |
| Navigation active state | Manual className ternaries | `useLocation()` + path comparison | React Router's stable hook |
| Gradient text | SVG text / canvas | `bg-clip-text text-transparent bg-gradient-to-r` | Pure Tailwind, no JS |
| Entrance animations | Custom CSS keyframes | `motion/react` `initial`/`animate` | Already installed, patterns established in landing |

**Key insight:** The visual system is already fully built in the landing page components. Phase 14 is extraction and propagation, not invention.

---

## Common Pitfalls

### Pitfall 1: AppNav Renders on Auth / Landing Pages

**What goes wrong:** If `AppNav` is placed globally (e.g. directly in `App.tsx` root), it shows on the landing page, login, and signup — breaking the landing page's standalone nav.

**Why it happens:** Easy to put nav at root level for convenience.

**How to avoid:** Create an `AuthenticatedLayout` component that wraps only the post-auth routes (`/chat`, `/settings`, `/billing`, `/photo`). OR use `useLocation()` inside `AppNav` to conditionally return null on public routes. The layout wrapper approach is cleaner.

**Warning signs:** Landing page shows a double nav bar or bottom tab bar appears on login.

### Pitfall 2: Mobile Bottom Tab Bar Covered by Page Content

**What goes wrong:** `fixed bottom-0` tab bar overlaps content at the bottom of scrollable pages.

**Why it happens:** Pages use `h-screen` or `min-h-screen` without accounting for the 64px tab bar.

**How to avoid:** Add `pb-16 md:pb-0` to page-level containers on mobile, OR add a spacer div after the tab bar as shown in the AppNav example. The spacer div approach is simpler.

**Warning signs:** Last settings section or chat input hidden behind the nav bar on mobile.

### Pitfall 3: Chat Input Bar Pushed Below Tab Bar

**What goes wrong:** On mobile, the fixed chat input bar and fixed bottom nav bar overlap.

**Why it happens:** ChatPage uses `h-screen flex flex-col` — the `ChatInput` is already at the flex bottom. Adding a fixed bottom nav creates a z-index/overlap conflict.

**How to avoid:** On the ChatPage specifically, the bottom tab bar must account for the chat input. Best approach: the tab bar uses `z-50`, and the chat input container gets `pb-16 md:pb-0` to sit above the tab bar. Alternatively, do not use `fixed` for the tab bar on ChatPage — use a layout approach that keeps everything in the flex column.

**Warning signs:** Send button unreachable on mobile.

### Pitfall 4: GlassCard `className` Override Breaks on Light Backgrounds

**What goes wrong:** `GlassCard` default is `bg-white/5` — invisible on light backgrounds. This was a documented pitfall in Phase 10 (State.md: "GlassCard className override required for visible cards on light bg-slate-50 sections").

**How to avoid:** Since all Phase 14 backgrounds are `bg-black`, the default `bg-white/5` is correct. No override needed. Only watch for accidentally using GlassCard on a `bg-white` or `bg-slate-50` background.

**Warning signs:** Cards are invisible (0% opacity on white background).

### Pitfall 5: `motion/react` vs `framer-motion` Import

**What goes wrong:** TypeScript compiles but the vitest mock doesn't apply, causing test failures.

**Why it happens:** Confusing the two package names. The vitest config in `vitest.config.ts` aliases `motion/react` to the mock — NOT `framer-motion`.

**How to avoid:** Always import `import { motion } from 'motion/react'`. Never `framer-motion`.

**Warning signs:** Tests fail with "motion is not a function" or unexpected animation behavior in tests.

### Pitfall 6: Settings Page Subscription Section Requires API Call

**What goes wrong:** The new "Subscription" section at the bottom of SettingsPage needs the current subscription status — this means an additional API call (`getSubscription`) or passing data via React Query.

**Why it happens:** SettingsPage currently only fetches preferences. The subscription data lives at `/billing/subscription`.

**How to avoid:** Add a `useQuery(['subscription'])` inside SettingsPage (or reuse the existing query if already in cache from BillingPage). Keep it minimal — just display plan name + status + a Link to `/billing`. No cancel flow in Settings.

**Warning signs:** Empty or "undefined" plan name in the Settings subscription section.

### Pitfall 7: AvatarSetupPage Onboarding Flow Context

**What goes wrong:** AvatarSetupPage is styled with `bg-gray-950` + `bg-gray-900` containers + `bg-gray-800` inputs — heavy gray palette. Updating to `bg-black` + `GlassCard` + `bg-white/5` inputs requires touching every className in the file.

**Why it happens:** This page was built early and has not been updated since.

**How to avoid:** Treat this as a complete visual rewrite of the page. The logic stays identical — only classNames change. Follow the auth page pattern: `bg-black` outer, centered `GlassCard` inner, gradient inputs, gradient primary button.

**Warning signs:** Purple button (`bg-purple-600`) remains — should become blue/violet gradient.

### Pitfall 8: GoogleSignInButton Dark Border

**What goes wrong:** `GoogleSignInButton` has `border-gray-200 text-gray-700 hover:bg-gray-50` — light theme styles. On a black background it looks wrong.

**Why it happens:** The button was designed for light backgrounds.

**How to avoid:** Update to `border-white/20 text-white hover:bg-white/5`. Keep the Google G logo SVG unchanged (it uses official Google brand colors — do not modify).

**Warning signs:** Gray-bordered button on black background.

---

## Code Examples

Verified patterns from the existing codebase:

### GlassCard Import and Usage

```typescript
// Source: frontend/src/components/ui/GlassCard.tsx (existing)
import { GlassCard } from '../components/ui/GlassCard'

// Base usage (dark bg):
<GlassCard>...</GlassCard>

// With active-warm variant (orange glow):
<GlassCard variant="active-warm">...</GlassCard>

// With active-cool variant (blue glow):
<GlassCard variant="active-cool">...</GlassCard>

// With className override:
<GlassCard className="p-5 mb-4">...</GlassCard>
```

### Gradient Text (Ava name in ChatPage header)

```typescript
// Source: landing page pattern (LandingHero.tsx, LandingDualPromise.tsx)
<span className="bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-orange-400 font-bold">
  Ava
</span>
```

### Online Status Glow Indicator

```typescript
// Small pulsing green dot for "online" status in chat header
<div className="relative">
  <div className="w-2 h-2 rounded-full bg-green-400" />
  <div className="absolute inset-0 rounded-full bg-green-400 animate-ping opacity-75" />
</div>
```

### Dark Auth Card Wrapper

```typescript
// Pattern for all auth pages:
<div className="min-h-screen flex items-center justify-center bg-black">
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4 }}
    className="w-full max-w-sm"
  >
    <GlassCard className="p-8">
      {/* form content */}
    </GlassCard>
  </motion.div>
</div>
```

### Active Nav Tab Gradient Highlight (Settings selectors)

```typescript
// Replace bg-gray-900 active state with gradient:
className={`py-2 px-3 rounded-xl text-sm border transition-all ${
  isActive
    ? 'bg-gradient-to-r from-blue-600 to-violet-600 border-transparent text-white'
    : 'border-white/10 text-slate-400 hover:border-white/20 hover:text-white bg-white/5'
}`}
```

### Landing Page Nav Reference (for desktop AppNav)

```typescript
// Source: frontend/src/pages/LandingPage.tsx (existing)
<nav className="sticky top-0 z-50 w-full bg-black/80 backdrop-blur-sm border-b border-white/5">
  <div className="container mx-auto px-6 py-4 flex items-center justify-between">
    ...
  </div>
</nav>
```

---

## State of the Art

| Old Approach (pre Phase 14) | New Approach (Phase 14 target) | Impact |
|-----------------------------|-------------------------------|--------|
| Light theme: `bg-gray-50`, `bg-white`, `border-gray-100` | Dark theme: `bg-black`, `GlassCard`, `border-white/10` | Visual brand consistency |
| No persistent navigation — dead-ends | `AppNav` bottom/top bar | Navigation fixed |
| `bg-gray-900` active button state | Gradient `from-blue-600 to-violet-600` | Brand color consistency |
| Audio visualizer in Hero mockup | Chat bubbles + locked photo mockup | More representative product preview |
| `bg-gray-950` in AdminPage, BillingPage | `bg-black` | Pure black consistency |
| `bg-purple-600` primary CTA buttons | `from-blue-600 to-violet-600` gradient | Brand accent color alignment |

**Deprecated/outdated:**
- `bg-gray-50`, `bg-white`, `bg-gray-100` page backgrounds: replace with `bg-black`
- `border-gray-100`, `border-gray-200`: replace with `border-white/10`
- `text-gray-900` for headings: replace with `text-white`
- `focus:ring-gray-900` on inputs: replace with `focus:ring-blue-500/50`
- `bg-gray-900` for active states: replace with gradient

---

## Page-by-Page Change Inventory

This is the key planning artifact — each page's delta from current to target:

### AppNav (new component)
- Create `frontend/src/components/AppNav.tsx`
- Bottom tab bar (mobile) + top bar (desktop)
- Tabs: Chat (/chat) | Photos (/photo) | Settings (/settings)
- Integrate into App.tsx as a layout around authenticated routes

### ChatPage.tsx
- `bg-white max-w-2xl mx-auto` → `bg-black` full viewport
- Header: replace `w-8 h-8 rounded-full bg-gray-900` avatar with actual avatar image (or gradient letter), gradient name text, online status glow
- Remove separate Settings/Sign out buttons from header (now in AppNav + Settings page)
- Keep sign out accessible (from Settings page)

### ChatBubble.tsx
- User: `bg-gray-900` → `bg-gradient-to-r from-blue-600 to-violet-600`
- Ava: `bg-gray-100 text-gray-900` → `bg-white/5 backdrop-blur-md border border-white/10 text-white`

### ChatInput.tsx
- `border-t border-gray-100 bg-white` → `border-t border-white/10 bg-black/80 backdrop-blur-sm`
- Textarea: `border-gray-200 focus:ring-gray-900` → `bg-white/5 border-white/10 text-white focus:ring-blue-500/50`
- Send button: `bg-gray-900` → gradient

### MessageList.tsx
- Loading/empty state text: `text-gray-400` stays fine on dark
- Empty state bg: no change needed (inherits from ChatPage)

### LoginPage.tsx
- Outer: `bg-gray-50` → `bg-black`
- Card: `bg-white rounded-2xl shadow-sm border border-gray-100` → `<GlassCard>`
- Labels: `text-gray-700` → `text-slate-300`
- Inputs: → dark glass style
- Divider: `bg-gray-100` → `bg-white/10`
- Primary button: → gradient
- Links: `text-gray-500` → `text-slate-400`
- GoogleSignInButton: dark border + text

### SignupPage.tsx
- Same set of changes as LoginPage

### ForgotPasswordPage.tsx
- Same set of changes as LoginPage (simpler — no Google button)

### ResetPasswordPage.tsx
- Same set of changes (3 states: tokenError, success, form — all need dark styling)

### SettingsPage.tsx
- Outer: `bg-gray-50` → `bg-black`
- Each `<section className="bg-white...">` → `<GlassCard>`
- Header back button: `text-gray-400 hover:text-gray-700` → `text-slate-400 hover:text-white`
- Persona/platform buttons: active → gradient
- Spiciness buttons: active → gradient
- Input: dark glass
- Save button: → gradient
- Add Subscription section (new GlassCard at bottom)

### BillingPage.tsx
- Already uses `GlassCard` and dark styling
- `bg-gray-950` → `bg-black`
- Add back button to Settings
- Buttons already use violet — update primary to blue/violet gradient

### SubscribePage.tsx
- `bg-gray-950` → `bg-black`
- `bg-gray-900` card → `GlassCard`
- `bg-gray-800` feature list → `bg-white/5 border border-white/10`
- `bg-purple-600` button → gradient
- Add back button

### AvatarSetupPage.tsx
- `bg-gray-950` → `bg-black`
- `bg-gray-900` card → `GlassCard`
- `bg-gray-800` inputs → dark glass
- `bg-purple-600` buttons → gradient
- Spinner: `border-purple-600` → `border-violet-500`

### PhotoPage.tsx
- Already `bg-black` — minimal changes needed
- `text-gray-300`, `text-gray-400`, `text-gray-600` stay fine
- Minor: add subtle backdrop styling to header

### AdminPage.tsx
- `bg-gray-950` → `bg-black`
- Already uses `GlassCard` — no card changes needed

### LandingHero.tsx
- Right mockup inner content: replace notification block + audio bars with chat bubbles + locked photo blur panel
- Container (`w-64 bg-black/40 backdrop-blur-md ...`) stays unchanged

### OnboardingGate (App.tsx)
- Loading state: `bg-gray-950` → `bg-black`

---

## Open Questions

1. **Avatar image in ChatPage header**
   - What we know: The avatar has a `reference_image_url` (from `getMyAvatar`) and a `name`
   - What's unclear: Should the header fetch the avatar data just to show the image? Or use a gradient initial?
   - Recommendation: Use React Query `['avatar']` (already fetched by `OnboardingGate`) — access it with `useQuery` in `ChatPage`. If null/loading, fall back to gradient initial "A" in a `from-violet-500 to-orange-500` circle. Keep it lightweight.

2. **Sign-out location after removing it from ChatPage header**
   - What we know: Sign out button currently lives in ChatPage header; Settings page is getting AppNav
   - What's unclear: Where does sign out live in the new layout?
   - Recommendation: Add a "Sign out" button at the bottom of SettingsPage (below the Subscription section), styled as a secondary ghost button. This is the conventional pattern for mobile apps.

3. **Photo tab route in AppNav**
   - What we know: `/photo` currently requires a `?url=` param to display anything — it's not a browseable gallery
   - What's unclear: What should the Photos tab show if no URL is provided?
   - Recommendation: For Phase 14 (visual only), the Photos tab can link to `/photo` and show a placeholder state ("Your photos appear here during conversations"). Gallery is deferred.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest ^4.0.18 + @testing-library/react ^16.3.2 |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm test -- --run` |
| Full suite command | `cd frontend && npm test -- --run` |

### Phase Requirements → Test Map

Phase 14 has no new functional requirements in REQUIREMENTS.md (all v1.1 requirements are already marked complete). This phase is visual-only — the behaviors to verify are visual correctness and navigation flows. Most verification is manual/visual. Automated tests cover non-regression.

| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| LandingPage renders without crash after Hero mockup change | smoke | `cd frontend && npm test -- --run LandingPage` | ✅ LandingPage.test.tsx |
| AdminPage renders GlassCards and stat data | smoke | `cd frontend && npm test -- --run AdminPage` | ✅ AdminPage.test.tsx |
| AppNav renders chat/photos/settings links | unit | `cd frontend && npm test -- --run AppNav` | ❌ Wave 0 |
| Auth pages (login/signup) render dark glassmorphism card | smoke | `cd frontend && npm test -- --run LoginPage` | ❌ Wave 0 |
| ChatBubble user bubble has gradient class | unit | `cd frontend && npm test -- --run ChatBubble` | ❌ Wave 0 |

Visual fidelity (bg-black on correct pages, gradient buttons, GlassCard presence) is manual-only — automated snapshot tests are outside Phase 14 scope.

### Sampling Rate

- **Per task commit:** `cd frontend && npm test -- --run` (full suite, ~5s)
- **Per wave merge:** `cd frontend && npm test -- --run`
- **Phase gate:** Full suite green + manual visual review before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend/src/components/AppNav.test.tsx` — covers nav link rendering + active state
- [ ] `frontend/src/pages/LoginPage.test.tsx` — covers dark theme render (bg-black, GlassCard)
- [ ] `frontend/src/components/ChatBubble.test.tsx` — covers gradient user bubble, glass Ava bubble

*(Existing tests: `LandingPage.test.tsx`, `AdminPage.test.tsx` — both must stay GREEN throughout)*

---

## Sources

### Primary (HIGH confidence)

- Direct codebase inspection (`frontend/src/`) — all file contents read directly
- `frontend/package.json` — confirmed exact library versions (motion ^12.35.1, tailwindcss ^4.2.1)
- `frontend/vitest.config.ts` — confirmed `motion/react` aliasing pattern
- `frontend/src/components/ui/GlassCard.tsx` — confirmed API (3 variants, extends HTMLMotionProps)
- `frontend/src/components/landing/LandingHero.tsx` — confirmed current mockup structure (audio bars)
- `frontend/src/pages/LandingPage.tsx` — confirmed nav pattern (`bg-black/80 backdrop-blur-sm border-b border-white/5`)

### Secondary (MEDIUM confidence)

- `.planning/STATE.md` accumulated decisions — confirmed `motion/react` (not `framer-motion`) is the project standard (Phase 10 decision)
- `14-CONTEXT.md` — user decisions verified against actual component code

### Tertiary (LOW confidence)

- None — all research was against the actual codebase; no web searches required for this phase

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries inspected directly in package.json
- Architecture: HIGH — based on actual component inspection, no guesswork
- Pitfalls: HIGH — derived from actual code differences between current and target, plus Phase 10 STATE.md decisions
- Page-by-page inventory: HIGH — every page file read directly

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable — no library upgrades expected mid-phase)
