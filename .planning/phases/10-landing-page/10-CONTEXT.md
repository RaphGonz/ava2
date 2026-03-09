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
- Figma frames are the source of truth — follow them as closely as possible
- Exported frames will be placed in `.planning/assets/` before planning/implementation begins
- Adaptation is allowed where the Figma conflicts with existing code patterns (components, Tailwind classes, routing) — match the visual intent rather than pixel-perfect replication if needed

### Sections
- Hero, features, and pricing sections — all three are present in the Figma (including pricing)
- No need to invent layout or copy — follow what the Figma shows

### CTA behavior
- All CTA buttons route directly to `/signup` — no intermediate pages
- Secondary "Sign in" links route to `/login`

### Authenticated user redirect
- Logged-in users navigating to `/` are redirected to `/chat`
- Landing page never renders for authenticated users

### Mobile responsiveness
- The page must be responsive — adapt the Figma layout for mobile breakpoints
- Where the Figma only shows desktop, apply standard responsive patterns (stack columns, adjust font sizes, etc.)

### Claude's Discretion
- Exact mobile breakpoint behaviour where Figma doesn't specify
- Animation / hover states not shown in static frames
- Minor spacing/typography adjustments to match existing Tailwind design system

</decisions>

<specifics>
## Specific Ideas

- "Follow the Figma frames as much as possible, but you can also adapt to what's already been done" — the existing `LandingPage.tsx` skeleton (dark bg, purple CTAs, Tailwind) is acceptable as a base; refine to match Figma rather than rewrite from scratch if they align
- Figma export location: `.planning/assets/` — planner should read these images before writing any code

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 10-landing-page*
*Context gathered: 2026-03-09*
