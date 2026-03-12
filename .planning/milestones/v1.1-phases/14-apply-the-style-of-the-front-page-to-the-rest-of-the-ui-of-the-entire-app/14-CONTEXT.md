# Phase 14: UI Redesign — Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Apply the landing page's visual language (dark bg, blue/violet/orange gradients, glassmorphism, motion) to every app page: chat, login/signup/auth, settings, billing/subscribe, photo, and admin. Fix navigation dead-ends. Update the landing Hero right-side mockup. No new features — visual and navigation work only.

**Guiding principle:** Every page after the landing page should feel like a continuation of it — same world, same brand. Mimic the landing page style as closely as possible across all areas.

</domain>

<decisions>
## Implementation Decisions

### Dark theme baseline
- Background: black (`bg-black`) matching the landing page, not `bg-gray-950`
- Text: white / slate-400 for secondary
- Accent colors: blue → violet → orange gradients (same as landing)
- Glass surfaces: `bg-white/5 backdrop-blur-md border border-white/10` — use existing `GlassCard` component wherever possible
- Buttons: gradient `from-blue-600 to-violet-600` for primary CTAs, `bg-white/5 border-white/10` for secondary

### Navigation (fixes dead-end problem)
- Persistent navigation: bottom tab bar on mobile, top nav bar on desktop
- Tabs: Chat | Photos | Settings (3 tabs)
- Billing accessible from within Settings — NOT a top-level nav tab
- All pages must have a clear way back (back buttons where applicable, nav bar everywhere)

### Chat page
- Full dark screen — `bg-black`, full viewport height
- Header: Ava's avatar image + gradient name text + online status glow indicator
- User message bubbles: `bg-gradient-to-r from-blue-600 to-violet-600`, rounded
- Ava message bubbles: glassmorphism — `bg-white/5 backdrop-blur-md border border-white/10`, rounded
- Input bar: dark styled, consistent with overall theme

### Auth pages (login, signup, forgot password, reset password)
- Background: black, same as landing page
- Card: centered glassmorphism card (`GlassCard` or equivalent) with subtle gradient border
- Form inputs: `bg-white/5 border border-white/10`, on focus: blue/violet ring
- Buttons: same gradient primary button as landing page
- All auth pages updated (login, signup, forgot-password, reset-password)

### Settings page
- Background: black
- Each settings section (Persona, Platform, Spiciness, Mode-switch phrase, Notifications) becomes a `GlassCard`
- Option selectors (active state): gradient highlight instead of `bg-gray-900`
- New section at the bottom: "Subscription" — shows current plan status + "Manage Billing" button linking to `/billing`

### Billing / Subscribe pages
- Background: black, GlassCard-based layout
- Back button to return to Settings on all billing-related pages
- Consistent with rest of dark theme

### Landing Hero right-side mockup update
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

</decisions>

<specifics>
## Specific Ideas

- The existing `GlassCard` component (`bg-white/5 backdrop-blur-md border border-white/10`) is the right building block — use it everywhere instead of `bg-white rounded-2xl shadow-sm`
- Landing page uses `motion` from `motion/react` for animations — continue the same pattern in app pages
- The landing page's nav (`bg-black/80 backdrop-blur-sm border-b border-white/5`) is a good reference for the persistent top nav on desktop
- Hero right mockup: the existing notification card shell (black/40, backdrop-blur-md, rounded-3xl, violet top gradient bar) is a great container — replace its content with chat bubbles + locked photo

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 14-apply-the-style-of-the-front-page-to-the-rest-of-the-ui-of-the-entire-app*
*Context gathered: 2026-03-10*
