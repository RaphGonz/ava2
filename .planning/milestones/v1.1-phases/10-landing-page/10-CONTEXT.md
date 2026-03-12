# Phase 10: Landing Page - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the placeholder `LandingPage.tsx` with a real acquisition page built from the Figma design. The page must have at minimum: hero, features, and pricing sections, with CTAs routing visitors to signup. Authenticated users are redirected away. Creating avatars, chat, and billing interactions are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Design source
- Figma code export is the source of truth — located at `.planning/assets/figma_frames/src/app/`
- Components to port: `Hero.tsx`, `DualPromise.tsx`, `Trust.tsx`, `Pricing.tsx`, `Footer.tsx`
- Adaptation is allowed where the Figma conflicts with existing code patterns (routing, Tailwind version) — match visual intent rather than pixel-perfect replication

### Sections (from Figma, in order)
- **Hero** — full-screen split layout (left: blue/tech "Jarvis" side with schedule mockup, right: violet/orange companion side with mobile notification). CTAs: "Create my Ava" (→/signup) + "Watch the demo" (secondary, no-op for now)
- **DualPromise** — two glass cards side by side: "Assistant Mode" (blue, Brain icon) and "Companion Mode" (warm orange, Heart icon)
- **Trust** — light background section with 3 cards: end-to-end encryption, user control, secure cloud
- **Pricing** — 3 tiers: Basic (Free), Premium (€19/month, highlighted), Elite (€49/month)
- **Footer** — simple footer with Privacy Policy and Terms links
- **MagicMoment section: REMOVED** — the interactive companion-mode activation demo is dropped entirely (Stripe compliance concern)

### Language
- All copy in **English** (translate from Figma's French)
- Existing app is English; landing page must match

### Stripe compliance (LAND-03)
- No "intimate", "explicit", "NSFW", "adult", "18+" language
- Figma's "intimité" → translate as "connection" or "companionship"
- Remove the 18+ footer disclaimer from Figma's Footer component
- Companion mode framing: "emotional connection" / "personal companion" — never suggestive
- The DualPromise "Companion Mode" blurred button text is decorative — planner may replace or remove

### CTA behavior
- All primary CTA buttons route directly to `/signup` — no intermediate pages
- Secondary "Sign in" / "Watch demo" links: Sign in → `/login`, Watch demo → no-op (href="#" or omit)

### Authenticated user redirect
- Logged-in users navigating to `/` are redirected to `/chat`
- Landing page never renders for authenticated users

### Mobile responsiveness
- The page must be responsive — adapt the Figma layout for mobile breakpoints
- Where the Figma only shows desktop, apply standard responsive patterns (stack columns, adjust font sizes)

### Dependencies to add
- `motion/react` — used for animations (Framer Motion v12 package name)
- `lucide-react` — icons throughout
- `clsx` + `tailwind-merge` — used by GlassCard component

### GlassCard component
- Port `GlassCard.tsx` from `.planning/assets/figma_frames/src/app/components/ui/GlassCard.tsx` to `frontend/src/components/ui/GlassCard.tsx`
- Three variants: `base`, `active-warm`, `active-cool`

### Claude's Discretion
- Exact English copy for each section (translate intent from French, not word-for-word)
- Exact mobile breakpoint behaviour where Figma doesn't specify
- Whether to use Unsplash hero images or replace with CSS gradients only
- Minor spacing/typography adjustments to match existing Tailwind v4 setup

</decisions>

<specifics>
## Specific Ideas

- "Follow the Figma frames as much as possible, but you can also adapt to what's already been done"
- Hero has a split diagonal layout using `clip-path: polygon(0 0, 65% 0, 35% 100%, 0 100%)` — keep this visual structure
- Pricing "POPULAR" badge on Premium tier with warm gradient highlight — keep
- Figma uses `motion/react` import (not `framer-motion`) — this is Framer Motion v12

</specifics>

<deferred>
## Deferred Ideas

- "Watch the demo" button — actual demo video is a future phase
- Elite tier "Contact Sales" flow — future phase

</deferred>

---

*Phase: 10-landing-page*
*Context gathered: 2026-03-09*
