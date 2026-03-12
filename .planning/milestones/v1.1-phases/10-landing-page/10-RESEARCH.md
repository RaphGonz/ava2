# Phase 10: Landing Page - Research

**Researched:** 2026-03-09
**Domain:** React 19 + Tailwind v4 + Framer Motion v12 — marketing landing page with auth-aware routing
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Design source
- Figma code export is the source of truth — located at `.planning/assets/figma_frames/src/app/`
- Components to port: `Hero.tsx`, `DualPromise.tsx`, `Trust.tsx`, `Pricing.tsx`, `Footer.tsx`
- Adaptation is allowed where the Figma conflicts with existing code patterns (routing, Tailwind version) — match visual intent rather than pixel-perfect replication

#### Sections (from Figma, in order)
- **Hero** — full-screen split layout (left: blue/tech "Jarvis" side with schedule mockup, right: violet/orange companion side with mobile notification). CTAs: "Create my Ava" (→/signup) + "Watch the demo" (secondary, no-op for now)
- **DualPromise** — two glass cards side by side: "Assistant Mode" (blue, Brain icon) and "Companion Mode" (warm orange, Heart icon)
- **Trust** — light background section with 3 cards: end-to-end encryption, user control, secure cloud
- **Pricing** — 3 tiers: Basic (Free), Premium (€19/month, highlighted), Elite (€49/month)
- **Footer** — simple footer with Privacy Policy and Terms links
- **MagicMoment section: REMOVED** — the interactive companion-mode activation demo is dropped entirely (Stripe compliance concern)

#### Language
- All copy in **English** (translate from Figma's French)
- Existing app is English; landing page must match

#### Stripe compliance (LAND-03)
- No "intimate", "explicit", "NSFW", "adult", "18+" language
- Figma's "intimité" → translate as "connection" or "companionship"
- Remove the 18+ footer disclaimer from Figma's Footer component
- Companion mode framing: "emotional connection" / "personal companion" — never suggestive
- The DualPromise "Companion Mode" blurred button text is decorative — planner may replace or remove

#### CTA behavior
- All primary CTA buttons route directly to `/signup` — no intermediate pages
- Secondary "Sign in" / "Watch demo" links: Sign in → `/login`, Watch demo → no-op (href="#" or omit)

#### Authenticated user redirect
- Logged-in users navigating to `/` are redirected to `/chat`
- Landing page never renders for authenticated users

#### Mobile responsiveness
- The page must be responsive — adapt the Figma layout for mobile breakpoints
- Where the Figma only shows desktop, apply standard responsive patterns (stack columns, adjust font sizes)

#### Dependencies to add
- `motion/react` — used for animations (Framer Motion v12 package name)
- `lucide-react` — icons throughout
- `clsx` + `tailwind-merge` — used by GlassCard component

#### GlassCard component
- Port `GlassCard.tsx` from `.planning/assets/figma_frames/src/app/components/ui/GlassCard.tsx` to `frontend/src/components/ui/GlassCard.tsx`
- Three variants: `base`, `active-warm`, `active-cool`

### Claude's Discretion
- Exact English copy for each section (translate intent from French, not word-for-word)
- Exact mobile breakpoint behaviour where Figma doesn't specify
- Whether to use Unsplash hero images or replace with CSS gradients only
- Minor spacing/typography adjustments to match existing Tailwind v4 setup

### Deferred Ideas (OUT OF SCOPE)
- "Watch the demo" button — actual demo video is a future phase
- Elite tier "Contact Sales" flow — future phase
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LAND-01 | Visitor lands on a designed page with hero section, features section, and pricing | Figma export provides complete component source; Hero + DualPromise + Trust = features; Pricing = pricing section |
| LAND-02 | Visitor can click a CTA button and reach the sign-up flow directly | React Router `<Link to="/signup">` pattern; all primary CTAs map to /signup; existing routing already has /signup route |
| LAND-03 | Landing page copy frames Ava as an AI companion/assistant (Stripe-compliant — no explicit NSFW framing) | Full copy translation map documented below; 18+ footer disclaimer removed; specific French→English translation guidance provided |
</phase_requirements>

---

## Summary

Phase 10 replaces the existing placeholder `LandingPage.tsx` with a fully-designed acquisition page ported from the Figma export. The work is primarily a React component authoring task: port five sections (Hero, DualPromise, Trust, Pricing, Footer), install three new npm dependencies (`motion/react`, `lucide-react`, `clsx`/`tailwind-merge`), create a shared `GlassCard` UI component, translate all French copy to compliant English, and wire authenticated-user redirect logic.

The codebase is React 19 + Vite + TypeScript + Tailwind v4 (CSS-first, no `tailwind.config.js`). The `"/"` route in `frontend/src/App.tsx` already renders `<LandingPage />` — no routing changes are needed. Auth state comes from the Zustand store (`useAuthStore`) where `token: string | null` is the single signal for authenticated vs unauthenticated. The redirect to `/chat` for authenticated users is a small wrapper added at the top of `LandingPage`.

The key risks are: (1) Tailwind v4 uses `@import "tailwindcss"` without `tailwind.config.js`, so arbitrary values in the Figma source (e.g., `shadow-[0_0_30px_-5px_...]`) work fine but custom theme tokens do not exist — use inline arbitrary values throughout; (2) `motion/react` is the Framer Motion v12 package name (not `framer-motion`) — the import path matters; (3) the Figma Footer has an 18+ disclaimer that MUST be removed for Stripe compliance.

**Primary recommendation:** Port components directly from the Figma source with minimal changes — adapt CTAs from `<button>` to `<Link to="/signup">`, translate French copy, remove the 18+ footer block, and add the auth-redirect guard at the top of `LandingPage`.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React 19 | ^19.2.0 | UI framework | Already installed |
| react-router-dom | ^7.13.1 | Client-side routing, `<Link>` for CTAs | Already installed |
| Tailwind v4 | ^4.2.1 | Utility-first CSS | Already installed; CSS-first config |
| TypeScript | ~5.9.3 | Type safety | Already installed |

### New Dependencies to Install

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| motion/react | ^12.x | Framer Motion v12 — animations | Figma export uses this exact import; `whileHover`, `whileTap`, `initial`/`animate`/`transition` |
| lucide-react | ^0.x | SVG icon set | Figma uses Brain, Heart, ArrowRight, Play, Check, Star, Zap, Lock, Power, CloudLightning |
| clsx | ^2.x | Conditional class merging | Used in GlassCard `cn()` helper |
| tailwind-merge | ^2.x | Tailwind class deduplication | Used in GlassCard `cn()` helper alongside clsx |

**Installation:**
```bash
cd frontend && npm install motion lucide-react clsx tailwind-merge
```

Note: The Framer Motion v12 npm package name is `motion`, and the import path is `motion/react`. Do NOT install `framer-motion` — that is the v10/v11 package name.

### Already Installed (Confirmed)

| Library | Version | Role in this phase |
|---------|---------|-------------------|
| zustand | ^5.0.11 | Read `token` from `useAuthStore` for auth redirect |
| @tanstack/react-query | ^5.x | Not needed for landing page itself |

---

## Architecture Patterns

### Recommended Project Structure

```
frontend/src/
├── pages/
│   └── LandingPage.tsx          # Main page: auth guard + section assembly
├── components/
│   ├── ui/
│   │   └── GlassCard.tsx        # NEW — ported from Figma, shared UI primitive
│   └── landing/
│       ├── LandingHero.tsx      # NEW — Hero section
│       ├── LandingDualPromise.tsx # NEW — DualPromise section
│       ├── LandingTrust.tsx     # NEW — Trust section
│       ├── LandingPricing.tsx   # NEW — Pricing section
│       └── LandingFooter.tsx    # NEW — Footer section
```

Landing-specific components are grouped under `components/landing/` to keep them isolated from the app-level components (ChatBubble, MessageList, etc.) which are at `components/`.

### Pattern 1: Auth-Aware Landing Page Guard

The `LandingPage.tsx` must redirect authenticated users to `/chat` before rendering anything. The auth signal is `useAuthStore(s => s.token)` — non-null means authenticated.

```typescript
// frontend/src/pages/LandingPage.tsx
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'
import { LandingHero } from '../components/landing/LandingHero'
// ...other section imports

export default function LandingPage() {
  const token = useAuthStore(s => s.token)

  // Authenticated users never see the landing page
  if (token) return <Navigate to="/chat" replace />

  return (
    <main className="w-full min-h-screen bg-black text-white overflow-x-hidden selection:bg-orange-500/30 selection:text-orange-200">
      <LandingHero />
      <LandingDualPromise />
      <LandingTrust />
      <LandingPricing />
      <LandingFooter />
    </main>
  )
}
```

**Why `replace`:** Prevents the back button from sending an authenticated user back to the landing page.

**Note on AuthBridge:** `AuthBridge` in `App.tsx` already handles the Google OAuth redirect case — after OAuth sign-in, it calls `setAuth()` which populates `token`, triggering a re-render of LandingPage which then redirects. This means the guard works automatically for both email/password and Google OAuth flows.

### Pattern 2: CTA Buttons as React Router Links

Figma buttons are `<button>` elements. In the ported version, all primary CTAs must be `<Link>` to enable client-side navigation.

```typescript
// Source: React Router v7 docs — Link component
import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { ArrowRight } from 'lucide-react'

// Primary CTA
<motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
  <Link
    to="/signup"
    className="px-8 py-4 rounded-full bg-gradient-to-r from-blue-600 via-violet-600 to-orange-600 text-white font-bold text-lg flex items-center gap-2"
  >
    Create my Ava <ArrowRight className="w-5 h-5" />
  </Link>
</motion.div>

// Secondary no-op (Watch Demo)
<button
  className="px-8 py-4 rounded-full bg-white/5 backdrop-blur-sm border border-white/10 text-white font-medium text-lg flex items-center gap-2"
  onClick={() => {}} // deferred
>
  <Play className="w-4 h-4 fill-current" /> Watch the demo
</button>
```

**Note:** `motion.div` wrapping a `<Link>` is correct. Do NOT use `motion.a` or try to pass `to` prop to `motion.div`.

### Pattern 3: GlassCard as motion.div

The `GlassCard` component from Figma already wraps `motion.div` and accepts `HTMLMotionProps<"div">`. Port it unchanged — this is the correct pattern for Tailwind v4 + motion/react.

```typescript
// frontend/src/components/ui/GlassCard.tsx
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { motion, HTMLMotionProps } from 'motion/react'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

interface GlassCardProps extends HTMLMotionProps<'div'> {
  variant?: 'base' | 'active-warm' | 'active-cool'
  children: React.ReactNode
  className?: string
}

export function GlassCard({ variant = 'base', children, className, ...props }: GlassCardProps) {
  const variants = {
    base: 'bg-white/5 border-white/10 hover:border-white/20 hover:bg-white/10',
    'active-warm': 'bg-orange-500/10 border-orange-500/30 shadow-[0_0_30px_-5px_rgba(249,115,22,0.3)]',
    'active-cool': 'bg-blue-500/10 border-blue-500/30 shadow-[0_0_30px_-5px_rgba(59,130,246,0.3)]',
  }
  return (
    <motion.div
      className={cn('backdrop-blur-md border rounded-2xl p-6 transition-all duration-300', variants[variant], className)}
      {...props}
    >
      {children}
    </motion.div>
  )
}
```

### Pattern 4: Framer Motion v12 (motion/react) Animation Props

Framer Motion v12 uses `motion/react` as the package import. The animation API is unchanged from v10/v11 for the props used in this design.

```typescript
// Source: Framer Motion v12 docs — motion component
import { motion } from 'motion/react'

// Entry animation
<motion.div
  initial={{ opacity: 0, x: -50 }}
  animate={{ opacity: 1, x: 0 }}
  transition={{ duration: 0.8 }}
>

// Hover/tap interaction
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
>
```

### Pattern 5: Tailwind v4 Arbitrary Values

Tailwind v4 uses CSS-first configuration with `@import "tailwindcss"` in `index.css` (already present). Custom shadows, clip-paths, and gradients from the Figma are expressed as arbitrary values — they work without any config changes.

```typescript
// clip-path diagonal split — works in Tailwind v4 as inline style (not a utility class)
<div style={{ clipPath: 'polygon(0 0, 65% 0, 35% 100%, 0 100%)' }}>

// Custom shadow as Tailwind arbitrary value
className="shadow-[0_0_30px_-5px_rgba(79,70,229,0.5)]"

// Opacity modifier on colors
className="bg-orange-500/10 border-orange-500/30"
```

`clip-path` must remain an inline `style` prop — Tailwind does not have a `clip-path` utility class by default. All other arbitrary values work as Tailwind classes.

### Anti-Patterns to Avoid

- **Using `<a href="/signup">` instead of `<Link to="/signup">`:** Will cause a full page reload, losing React state. Always use `<Link>` from `react-router-dom`.
- **Wrapping `<Link>` inside `<motion.button>`:** `<motion.button>` renders a `<button>`, which cannot contain block-level anchors. Wrap with `<motion.div>` instead.
- **Using `framer-motion` import:** The v10/v11 package. This project uses `motion/react` (Framer Motion v12).
- **Adding a `tailwind.config.js`:** This project uses Tailwind v4 CSS-first config. No JS config file should be created.
- **Putting `useAuthStore` outside the component:** Zustand hooks must be called inside React components or custom hooks.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Conditional class merging | Custom string concatenation | `clsx` + `tailwind-merge` via `cn()` | Handles falsy values, Tailwind class conflicts |
| Icon SVGs | Inline SVG or emoji | `lucide-react` | Consistent stroke width, tree-shakeable, accessible |
| Hover/tap animations | CSS transitions only | `motion/react` `whileHover`/`whileTap` | Handles gesture cancellation, spring physics |
| Auth guard redirect | Manual `window.location` | React Router `<Navigate replace>` | Client-side, preserves history stack |
| Typing animation | Custom `setInterval` logic | The Figma `TypingText` component | Already implemented and tested in the Figma source |

**Key insight:** The Figma export is a nearly-complete implementation. The task is porting + translating, not designing from scratch.

---

## Common Pitfalls

### Pitfall 1: 18+ Footer Disclaimer Not Removed
**What goes wrong:** The Figma `Footer.tsx` contains a red warning block with `ShieldAlert` icon and "18+ adults only" language. If ported verbatim, this violates LAND-03 and Stripe compliance.
**Why it happens:** Direct copy-paste from Figma without reading the content.
**How to avoid:** The entire `<div className="border-t border-slate-900 pt-8 flex flex-col items-center">` block containing the red disclaimer must be removed. Only retain: logo, footer links (Privacy Policy, Terms), copyright line.
**Warning signs:** The `ShieldAlert` import from `lucide-react` in `Footer.tsx` — its presence means the disclaimer is still there.

### Pitfall 2: French Copy Not Translated
**What goes wrong:** Page renders with French text, failing LAND-03 and confusing English users.
**Why it happens:** Components ported without reviewing string content.
**How to avoid:** Every string literal in every component must be reviewed. See the full translation map in the Code Examples section below.
**Warning signs:** Any occurrence of "Créer", "Votre", "Choisissez", "Gratuit", "mois", "Confiance", "Démoriser", "Compagnon", "Mode" (French) in the output HTML.

### Pitfall 3: Wrong Framer Motion Package
**What goes wrong:** `npm install framer-motion` or `import { motion } from 'framer-motion'` — TypeScript compiles but may produce version conflicts or missing exports.
**Why it happens:** Muscle memory from pre-v12 projects.
**How to avoid:** Install `motion` (not `framer-motion`). Import from `motion/react`. The Figma source already uses the correct import — follow it exactly.
**Warning signs:** `Cannot find module 'motion/react'` after installing `framer-motion`.

### Pitfall 4: Auth Redirect Causes Flash of Landing Page
**What goes wrong:** Authenticated user briefly sees the landing page before being redirected to `/chat`.
**Why it happens:** Zustand's `persist` middleware rehydrates from `localStorage` synchronously before the first render, so `token` is available on the first render. This means the redirect via `<Navigate>` happens on the first render — there should be no flash.
**How to avoid:** The synchronous `if (token) return <Navigate to="/chat" replace />` pattern is correct. Do NOT add a loading state here — Zustand persist is synchronous.
**Warning signs:** If a loading state is added before the auth check, it will actually cause a flash.

### Pitfall 5: clip-path Used as Tailwind Class
**What goes wrong:** `className="clip-path-[polygon(...)]"` — Tailwind v4 does not have a built-in clip-path utility.
**Why it happens:** Other Tailwind arbitrary values work; `clip-path` looks like it should too.
**How to avoid:** Use `style={{ clipPath: 'polygon(0 0, 65% 0, 35% 100%, 0 100%)' }}` as an inline style prop.
**Warning signs:** The diagonal split does not appear; the left blue section covers the full width.

### Pitfall 6: Trust Section GlassCard on Light Background
**What goes wrong:** The Trust section (`bg-slate-50`) uses `GlassCard` with `variant="base"` which has `bg-white/5` — nearly invisible on a light background. The Figma overrides this with `className="bg-white/80 border-slate-200"`.
**Why it happens:** Using `GlassCard` without the className override.
**How to avoid:** Always pass the light-theme override classNames on Trust section cards: `className="bg-white/80 border-slate-200 shadow-sm hover:shadow-md"`.
**Warning signs:** Trust cards appear transparent/invisible on the slate background.

### Pitfall 7: Pricing CTAs Are Plain Buttons
**What goes wrong:** Figma `Pricing.tsx` uses `<button>` elements. The Basic tier "Get started" and Premium tier "Unlock Ava" must route to `/signup`.
**Why it happens:** Direct port without adapting navigation.
**How to avoid:** Basic and Premium buttons become `<Link to="/signup">`. Elite "Contact Sales" stays as a `<button>` (disabled or no-op — future phase per deferred decisions).
**Warning signs:** Clicking "Get started" or "Unlock Ava" does nothing or causes a full page reload.

### Pitfall 8: `Math.random()` in Audio Visualizer Causes React Hydration Warning
**What goes wrong:** The Hero's audio visualizer uses `Math.random()` to set bar heights in JSX — this generates different values on each render, causing React strict mode double-render issues.
**Why it happens:** Direct port of the Figma snippet.
**How to avoid:** Pre-compute bar heights as a constant array outside the component, or use `useMemo`.
**Warning signs:** Console warnings about "Each child in a list should have a unique 'key' prop" or flickering animation bars.

---

## Code Examples

### Complete French → English Copy Translation Map

```
// Hero section
"L'IA qui prends soin de votre énergie la journée."
→ "The AI that takes care of your day."

"...et de votre intimité la nuit."  [NOTE: violates LAND-03 — replace entirely]
→ "...and keeps you company at night."

"AVA_OS_V1.2" → "AVA_OS_V1.2"  [keep — it's a UI mockup label]
"Deep Work: Q3 Strategy" → "Deep Work: Q3 Strategy"  [keep — English already]

// Hero mobile mockup notification
"AVA Companion" → "AVA Companion"  [keep]
"Maintenant" → "Now"
"J'ai une surprise pour toi..." → [REMOVE or replace with benign English, e.g. "I have something for you..."]

// DualPromise section
"Mode Assistant" → "Assistant Mode"
"Une intelligence analytique pure pour structurer votre chaos."
→ "Pure analytical intelligence to organise your day."
"Gestion d'agenda, emails, synthèse de documents."
→ "Calendar management, email drafts, document summaries."
"Elle ne dort jamais, ne juge jamais."
→ "Always available. Never judgmental."

"Mode Compagnon" → "Companion Mode"
"Plus qu'une IA, une présence. Connexion émotionnelle,
écoute active et partage multimédia privé.
Apprenez à lâcher prise."
→ "More than an AI, a presence. Emotional connection,
active listening and private media sharing.
Learn to unwind."

// DualPromise blurred button
"Maintenir pour révéler" → "Hold to reveal"  [decorative only — keep or remove per discretion]

// Trust section
"Confiance & Sécurité" → "Trust & Security"
"Vos données sont sacrées. Nous avons construit AVA comme un coffre-fort numérique,
pas comme un produit publicitaire."
→ "Your data is sacred. We built AVA like a digital vault,
not an advertising product."

"Chiffrement End-to-End" → "End-to-End Encryption"
"Vos conversations intimes sont chiffrées avant même de quitter votre appareil.
Personne, pas même nos ingénieurs, ne peut les lire."
→ "Your conversations are encrypted before they leave your device.
No one — not even our engineers — can read them."

"Contrôle Absolu" → "Full Control"
"Le 'Panic Button' efface instantanément votre historique local.
Respect total du RGPD : vos données vous appartiennent."
→ "Instantly erase your local history with one tap.
Full GDPR compliance: your data belongs to you."

"Cerveau Déporté" → "Cloud Intelligence"
"L'intelligence lourde reste dans le cloud sécurisé, préservant la batterie
et la fluidité de votre appareil."
→ "Heavy processing stays in the secure cloud,
preserving your device's battery and performance."

// Pricing section
"Choisissez votre Relation" → "Choose your plan"
"AVA s'adapte à vos besoins, de l'organisation professionnelle à l'intimité profonde."
[NOTE: "intimité profonde" violates LAND-03]
→ "AVA adapts to your needs, from professional organisation to personal companionship."

"Gratuit" → "Free"
"Pour découvrir l'efficacité pure." → "Start with the essentials."
"Mode Assistant (Jarvis)" → "Assistant Mode"
"Agenda Synchronisé" → "Synced Calendar"
"Support Email" → "Email Support"
"Commencer" → "Get started"  [→ Link to /signup]

"L'expérience complète, jour et nuit." → "The complete experience, day and night."
"Mode Compagnon (Her)" → "Companion Mode"
"Photos Illimitées (Selfies)" → "Unlimited Photos"
"Personnalité Unique" → "Custom Personality"
"Réponses Prioritaires" → "Priority Responses"
"Débloquer AVA" → "Unlock Ava"  [→ Link to /signup]
"POPULAIRE" → "POPULAR"

"Le futur de l'interaction humaine." → "The future of human interaction."
"Tout le Premium" → "Everything in Premium"
"Appels Vidéo (Beta 4K)" → "Video Calls (Beta)"
"Accès Anticipé API" → "Early API Access"
"Support Dédié 24/7" → "Dedicated 24/7 Support"
"Contacter Sales" → "Contact Sales"  [button, no-op — future phase]

// Footer
"Votre intelligence augmentée." → "Your augmented intelligence."
"CGU" → "Terms of Use"  [→ Link to /terms]
"Privacy Policy" → "Privacy Policy"  [→ Link to /privacy]
"Disclaimer IA" → "AI Disclaimer"  [→ keep or remove, discretion]
"© 2026 AVA AI Inc. Tous droits réservés." → "© 2026 Avasecret. All rights reserved."

// REMOVE ENTIRELY from Footer:
// The entire red ShieldAlert disclaimer block (18+ adults warning)
```

### Auth Redirect Guard

```typescript
// frontend/src/pages/LandingPage.tsx
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'

export default function LandingPage() {
  const token = useAuthStore(s => s.token)
  if (token) return <Navigate to="/chat" replace />
  // ... render page
}
```

### Pre-computed Audio Visualizer (avoids Math.random in render)

```typescript
// Compute heights once — stable across renders
const BAR_HEIGHTS = [18, 28, 14, 32, 20]

// In JSX:
{BAR_HEIGHTS.map((height, i) => (
  <div
    key={i}
    className="w-1 bg-white/50 rounded-full animate-pulse"
    style={{ height: `${height}px`, animationDelay: `${i * 0.1}s` }}
  />
))}
```

### Pricing Tier CTA Navigation

```typescript
// Basic and Premium → /signup
// Elite → no-op button (future phase)
import { Link } from 'react-router-dom'
import { motion } from 'motion/react'

// Basic
<Link to="/signup" className="w-full py-3 rounded-xl border border-white/10 text-white hover:bg-white/5 transition-colors font-medium text-center block">
  Get started
</Link>

// Premium (with motion)
<motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
  <Link to="/signup" className="w-full py-4 rounded-xl bg-gradient-to-r from-orange-500 to-pink-600 text-white font-bold shadow-lg shadow-orange-500/25 hover:shadow-orange-500/40 transition-all text-center block">
    Unlock Ava
  </Link>
</motion.div>

// Elite — no-op
<button disabled className="w-full py-3 rounded-xl border border-white/10 text-white/50 font-medium cursor-not-allowed">
  Contact Sales
</button>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `framer-motion` package | `motion` package, import from `motion/react` | Framer Motion v12 (2024) | Different package name; same API for basic usage |
| `tailwind.config.js` | `@import "tailwindcss"` in CSS, no JS config | Tailwind v4 (2025) | Arbitrary values still work; no `theme.extend` |
| `import { motion } from 'framer-motion'` | `import { motion } from 'motion/react'` | Framer Motion v12 | Import path change only |

**Confirmed already in use in this project:**
- Tailwind v4 CSS-first: `@import "tailwindcss"` in `frontend/src/index.css` — confirmed
- React 19: `"react": "^19.2.0"` — confirmed
- Zustand v5 with persist: auth store uses `persist` middleware — confirmed

---

## Open Questions

1. **Unsplash images vs. CSS gradients for Hero background**
   - What we know: Figma uses Unsplash URLs with `utm_source=figma`. These are public URLs that may have rate limits or require attribution.
   - What's unclear: Whether Unsplash images should be kept, hosted locally, or replaced with pure CSS gradients (which are simpler and have no dependency).
   - Recommendation: Use CSS gradients only (already present as fallbacks in the Figma — `bg-gradient-to-br from-violet-900 to-orange-900`). Remove Unsplash `<img>` tags. This eliminates external image dependency and reduces page load complexity. This is Claude's discretion per CONTEXT.md.

2. **Nav bar presence on landing page**
   - What we know: The existing `LandingPage.tsx` has a nav bar with "Sign in" and "Get started" links. The Figma components do not show a separate nav — the Hero section handles CTAs inline.
   - What's unclear: Whether to retain the nav bar from the current placeholder or match the Figma which has no explicit top nav.
   - Recommendation: Add a minimal sticky nav bar at the top of `LandingPage.tsx` (logo + Sign in + Get started) as it improves UX and the existing placeholder already has it. The Figma sections are self-contained enough to work with or without a nav.

---

## Validation Architecture

> `workflow.nyquist_validation` key is absent from `.planning/config.json` — treating as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None detected — no vitest.config.*, no jest.config.*, no test scripts in package.json |
| Config file | None — Wave 0 must create `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm run test -- --run` |
| Full suite command | `cd frontend && npm run test -- --run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LAND-01 | Page renders hero, features (DualPromise/Trust), and pricing sections | smoke (render test) | `cd frontend && npm run test -- --run src/pages/LandingPage.test.tsx` | ❌ Wave 0 |
| LAND-02 | CTA buttons link to /signup | unit (link href check) | `cd frontend && npm run test -- --run src/pages/LandingPage.test.tsx` | ❌ Wave 0 |
| LAND-03 | No prohibited words in rendered output | unit (text content check) | `cd frontend && npm run test -- --run src/pages/LandingPage.test.tsx` | ❌ Wave 0 |

All three requirements are testable in a single test file using `@testing-library/react` and `vitest`.

### Sampling Rate

- **Per task commit:** `cd frontend && npm run test -- --run`
- **Per wave merge:** `cd frontend && npm run test -- --run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend/vitest.config.ts` — test framework config; requires installing `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`
- [ ] `frontend/src/pages/LandingPage.test.tsx` — covers LAND-01, LAND-02, LAND-03
- [ ] Update `frontend/package.json` `"test"` script: `"test": "vitest"`
- [ ] Framework install: `cd frontend && npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom`

**Note:** Given the `config.json` `"mode": "yolo"` setting and the purely visual nature of this phase, the planner may reasonably reduce test scope to a single smoke test that renders the page and checks for the three required section headings. Manual browser verification is the primary QA gate for visual fidelity.

---

## Sources

### Primary (HIGH confidence)

- Direct read of `.planning/assets/figma_frames/src/app/` — all five component files read verbatim
- Direct read of `frontend/src/App.tsx` — routing and AuthBridge logic confirmed
- Direct read of `frontend/src/store/useAuthStore.ts` — auth signal confirmed as `token: string | null`
- Direct read of `frontend/package.json` — installed dependencies confirmed
- Direct read of `frontend/src/index.css` — Tailwind v4 CSS-first config confirmed
- Direct read of `frontend/src/pages/LandingPage.tsx` — existing placeholder confirmed

### Secondary (MEDIUM confidence)

- Framer Motion v12 package name `motion` / import `motion/react` — confirmed by Figma source using `import { motion } from "motion/react"` + `import { motion, HTMLMotionProps } from "motion/react"`
- Tailwind v4 clip-path limitation — inline `style` prop required; confirmed by Tailwind v4 not shipping a clip-path utility (CSS arbitrary values work for most props but not all)

### Tertiary (LOW confidence)

- Unsplash rate limits / attribution requirements — not verified; recommendation to avoid Unsplash URLs based on operational risk reasoning, not confirmed policy

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies and versions confirmed from `package.json` and Figma source
- Architecture: HIGH — existing `App.tsx` routing confirmed; `useAuthStore` token pattern confirmed
- Component content: HIGH — all Figma source files read verbatim
- Pitfalls: HIGH — most identified from direct inspection of source (18+ disclaimer in Footer, French copy, Math.random in JSX)
- Copy translation map: MEDIUM — translations reviewed for accuracy and Stripe compliance; exact English phrasing is Claude's discretion

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (30 days — stable design; Figma source is a fixed file)
