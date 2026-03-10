---
phase: 14-apply-the-style-of-the-front-page-to-the-rest-of-the-ui-of-the-entire-app
verified: 2026-03-10T17:00:00Z
status: human_needed
score: 16/16 automated must-haves verified
human_verification:
  - test: "Navigate to /chat while authenticated and inspect the ChatPage header"
    expected: "Header shows Ava's avatar image (or violet-to-orange gradient initial circle with 'A'), gradient violet-to-orange name text, and a pulsing green online dot — NO Settings or Sign out buttons visible"
    why_human: "Avatar display depends on real API response (reference_image_url may be null in test env); pulsing animation requires browser"
  - test: "Open the app on a mobile viewport (<768px) and visit /chat, /settings, /billing"
    expected: "A fixed bottom tab bar appears with Chat, Photos, Settings icons — tab bar is NOT visible on /, /login, /signup"
    why_human: "CSS responsive breakpoints (md:hidden / md:flex) require a real browser at specific viewport sizes to verify"
  - test: "Open the app on a desktop viewport (>=768px) and visit /chat"
    expected: "A sticky top nav bar appears with 'Avasecret' brand name and Chat, Photos, Settings links — mobile bottom bar is hidden"
    why_human: "Responsive layout requires browser viewport verification"
  - test: "Visit /settings while authenticated"
    expected: "Page shows black background, 5 frosted GlassCard sections (Platform, Content Ceiling, Mode-Switch Phrase, Notifications, Subscription), blue-to-violet gradient active selectors for Platform and Spiciness, a Subscription card with plan name and Manage Billing link, a Sign out button at the bottom"
    why_human: "Active selector state requires user interaction; subscription section content depends on live billing API"
  - test: "Visit /billing while authenticated"
    expected: "Pure black background (not dark gray), '← Back to Settings' link visible at top, 'Manage billing' button uses blue-to-violet gradient"
    why_human: "Visual confirmation of bg-black vs bg-gray-950 distinction requires browser rendering"
  - test: "Visit the landing page / and examine the right-side mockup phone"
    expected: "Shows 3 chat bubbles ('Missing you already...', 'Show me something', 'Just for you...') and a blurred locked photo — NO audio visualizer bars present"
    why_human: "Visual element confirmation of mockup content replacement"
---

# Phase 14: Dark Glass UI Redesign — Verification Report

**Phase Goal:** Apply the dark glass visual language of the landing page to the entire authenticated app — every page uses bg-black backgrounds, GlassCard sections, gradient buttons, and the AppNav persistent navigation.
**Verified:** 2026-03-10T17:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | AppNav renders bottom tab bar on mobile and top bar on desktop with Chat, Photos, Settings links | VERIFIED | `AppNav.tsx` lines 15-34 (desktop sticky nav) and 36-68 (mobile fixed bottom bar), both with Chat/Photos/Settings via `NAV_TABS` |
| 2 | AppNav does NOT appear on landing, login, signup, forgot-password, reset-password, auth/callback pages | VERIFIED | `App.tsx` lines 137-144: those routes render their pages directly without `AuthenticatedLayout` |
| 3 | Authenticated pages (/chat, /settings, /billing, /photo, /admin) receive AppNav via AuthenticatedLayout | VERIFIED | `App.tsx` lines 153-204: all 5 routes explicitly wrapped in `AuthenticatedLayout` which renders `AppNav` as sibling to children |
| 4 | Login, signup, forgot-password, reset-password pages use bg-black outer background | VERIFIED | `LoginPage.tsx` line 82, `SignupPage.tsx` line 34, `ForgotPasswordPage.tsx` line 32, `ResetPasswordPage.tsx` lines 72, 99, 116: all use `bg-black` |
| 5 | Each auth page has a centered GlassCard with motion entrance animation | VERIFIED | All 4 auth pages import `motion` from `motion/react` and `GlassCard` from `../components/ui/GlassCard` with `initial={{ opacity: 0, y: 20 }}` entrance |
| 6 | All form inputs use dark glass style: bg-white/5 border-white/10 text-white | VERIFIED | `LoginPage.tsx` lines 114, 126; all auth pages and settings/avatar pages use identical dark glass input pattern |
| 7 | Primary submit buttons use gradient from-blue-600 to-violet-600 | VERIFIED | Verified across: `LoginPage.tsx:133`, `SignupPage.tsx:85`, `ForgotPasswordPage.tsx:77`, `ResetPasswordPage.tsx:155`, `ChatInput.tsx:42`, `SettingsPage.tsx:207`, `SubscribePage.tsx:62`, `AvatarSetupPage.tsx:247` |
| 8 | GoogleSignInButton uses border-white/20 text-white hover:bg-white/5 | VERIFIED | `GoogleSignInButton.tsx` line 36: `border border-white/20 ... text-white hover:bg-white/5` |
| 9 | ChatPage uses bg-black full-viewport layout with no max-width constraint | VERIFIED | `ChatPage.tsx` line 33: `h-screen flex flex-col bg-black` — no `max-w-2xl mx-auto` |
| 10 | ChatPage header contains gradient avatar name and online glow dot — no Settings/Sign out buttons | VERIFIED | `ChatPage.tsx` lines 35-63: dark header with `from-violet-400 to-orange-400` gradient name text and `animate-ping` green dot; no Settings/Sign out buttons present |
| 11 | User message bubbles use bg-gradient-to-r from-blue-600 to-violet-600 | VERIFIED | `ChatBubble.tsx` line 14: `bg-gradient-to-r from-blue-600 to-violet-600` |
| 12 | Ava message bubbles use bg-white/5 backdrop-blur-md border-white/10 | VERIFIED | `ChatBubble.tsx` line 15: `bg-white/5 backdrop-blur-md border border-white/10` |
| 13 | ChatInput uses dark glass style with gradient send button | VERIFIED | `ChatInput.tsx` line 27: form uses `border-white/10 bg-black/80 backdrop-blur-sm`; send button line 42: `bg-gradient-to-r from-blue-600 to-violet-600` |
| 14 | SettingsPage uses bg-black, 5 GlassCard sections, gradient active selectors, Subscription section + Sign out | VERIFIED | `SettingsPage.tsx` line 77: `bg-black`; 5 `GlassCard` instances (Platform, Content Ceiling, Mode-Switch Phrase, Notifications, Subscription); gradient selectors lines 101-106, 122-126; sign out button line 213 |
| 15 | BillingPage uses bg-black with Back to Settings button | VERIFIED | `BillingPage.tsx` line 149: `bg-black text-white`; Back to Settings link lines 157-162 |
| 16 | SubscribePage, AvatarSetupPage, AdminPage use bg-black | VERIFIED | `SubscribePage.tsx` line 32: `bg-black`; `AvatarSetupPage.tsx` line 139: `bg-black`; `AdminPage.tsx` line 75: `bg-black` |
| 17 | LandingHero right mockup shows chat bubbles + locked blurred photo (no audio visualizer) | VERIFIED | `LandingHero.tsx` lines 88-108: 3 chat bubble divs and a `backdrop-blur-lg` locked photo block; `BAR_HEIGHTS` constant is absent (grep confirmed NOT FOUND) |

**Score:** 17/17 truths verified (automated)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/components/AppNav.tsx` | AppNav with Chat/Photos/Settings, mobile+desktop layouts | VERIFIED | 74 lines, exports `AppNav`, both nav layouts present |
| `frontend/src/App.tsx` | AuthenticatedLayout wrapping 5 authenticated routes | VERIFIED | `AuthenticatedLayout` defined at line 66, applied to /chat, /settings, /billing, /photo, /admin |
| `frontend/src/components/AppNav.test.tsx` | Test scaffold — 2 passing tests | VERIFIED | 28 lines, 2 tests GREEN |
| `frontend/src/components/ChatBubble.test.tsx` | 4 tests including gradient and backdrop-blur assertions | VERIFIED | 27 lines, all 4 assertions GREEN |
| `frontend/src/pages/LoginPage.test.tsx` | bg-black assertion test | VERIFIED | 40 lines, bg-black and input tests GREEN |
| `frontend/src/pages/LoginPage.tsx` | Dark-themed login page — bg-black, GlassCard, gradient button | VERIFIED | `bg-black` line 82, `GlassCard` line 89, gradient button line 133 |
| `frontend/src/pages/SignupPage.tsx` | Dark-themed signup page | VERIFIED | `bg-black` line 34, `GlassCard` line 41, gradient button line 85 |
| `frontend/src/pages/ForgotPasswordPage.tsx` | Dark-themed forgot-password page | VERIFIED | `bg-black` line 32, `GlassCard` line 39, gradient button line 77 |
| `frontend/src/pages/ResetPasswordPage.tsx` | Dark-themed reset-password — all 3 states | VERIFIED | All 3 states (tokenError/success/form) use `bg-black` + `GlassCard` |
| `frontend/src/components/GoogleSignInButton.tsx` | Dark-bordered Google button | VERIFIED | `border-white/20 text-white hover:bg-white/5` line 36 |
| `frontend/src/components/ChatBubble.tsx` | Gradient user bubble, glass Ava bubble | VERIFIED | `from-blue-600 to-violet-600` for user, `bg-white/5 backdrop-blur-md` for assistant |
| `frontend/src/components/ChatInput.tsx` | Dark glass input bar | VERIFIED | `border-white/10 bg-black/80 backdrop-blur-sm` + gradient send button |
| `frontend/src/pages/ChatPage.tsx` | Full dark chat page with avatar header | VERIFIED | `bg-black`, avatar query at line 13, dark header at line 35 |
| `frontend/src/pages/SettingsPage.tsx` | Dark settings with GlassCards and subscription section | VERIFIED | 5 GlassCards, gradient selectors, subscription section, sign out button |
| `frontend/src/pages/BillingPage.tsx` | bg-black with Back to Settings | VERIFIED | `bg-black` line 149, back link lines 157-162 |
| `frontend/src/pages/SubscribePage.tsx` | bg-black, GlassCard, gradient subscribe button | VERIFIED | `bg-black` line 32, `GlassCard` line 34, gradient button line 62 |
| `frontend/src/pages/AvatarSetupPage.tsx` | bg-black, GlassCard, dark inputs, gradient buttons, violet spinner | VERIFIED | `bg-black` line 139, `GlassCard` line 141, `border-violet-500` spinner line 152, gradient buttons lines 247/276 |
| `frontend/src/pages/AdminPage.tsx` | bg-black (was bg-gray-950) | VERIFIED | `bg-black` line 75 |
| `frontend/src/components/landing/LandingHero.tsx` | Chat bubbles + locked photo mockup — no audio visualizer | VERIFIED | Chat bubbles lines 88-101, locked photo lines 103-108; `BAR_HEIGHTS` grep: NOT FOUND |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `App.tsx` | `AppNav.tsx` | `AuthenticatedLayout` renders `<AppNav />` as sibling to children | WIRED | `App.tsx` line 3: `import { AppNav } from './components/AppNav'`; line 69: `<AppNav />` inside `AuthenticatedLayout` |
| `App.tsx` | /chat, /settings, /billing, /photo, /admin routes | Wrapped in `AuthenticatedLayout` | WIRED | Lines 154-204: all 5 routes confirmed wrapped |
| `LoginPage.tsx` | `GlassCard.tsx` | GlassCard imported and used as card wrapper | WIRED | Line 20: import; line 89: `<GlassCard className="p-8">` |
| `LoginPage.tsx` | `GoogleSignInButton.tsx` | GoogleSignInButton rendered inside form | WIRED | Line 19: import; line 94: `<GoogleSignInButton onError={setGoogleError} />` |
| `ChatPage.tsx` | `ChatBubble.tsx` (via MessageList) | MessageList renders ChatBubble | WIRED | `ChatPage.tsx` line 7 imports `MessageList`; line 66: `<MessageList messages={messages} isLoading={isLoading} />` |
| `ChatPage.tsx` | `useQuery(['avatar'])` | Avatar query fetched with same queryKey as OnboardingGate | WIRED | `ChatPage.tsx` lines 13-17: `useQuery({ queryKey: ['avatar'], queryFn: () => getMyAvatar(token!) })` |
| `SettingsPage.tsx` | `/billing` | Subscription section Link to='/billing' | WIRED | `SettingsPage.tsx` line 195: `<Link to="/billing" ...>Manage Billing →</Link>` |
| `BillingPage.tsx` | `/settings` | Back button using Link to /settings | WIRED | `BillingPage.tsx` line 157: `<Link to="/settings" ...>← Back to Settings</Link>` |
| `LandingHero.tsx` | `LandingPage.test.tsx` | Test renders LandingPage which renders LandingHero — must not crash | WIRED | LandingPage.test.tsx: 8 tests all GREEN; no crash |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| UI-01 | 14-01 | AppNav persistent navigation component exists and renders Chat/Photos/Settings | SATISFIED | `AppNav.tsx` verified — desktop top bar and mobile bottom tab bar both present with correct links |
| UI-02 | 14-01 | Authenticated pages wrapped in AuthenticatedLayout to receive AppNav | SATISFIED | `App.tsx` — /chat, /settings, /billing, /photo, /admin all wrapped in `AuthenticatedLayout` |
| UI-03 | 14-02 | Auth pages (login, signup, forgot-password, reset-password) use dark glass visual language | SATISFIED | All 4 pages use `bg-black` + `GlassCard` + gradient buttons + dark inputs; GoogleSignInButton dark-bordered |
| UI-04 | 14-03 | Chat interface (ChatPage, ChatBubble, ChatInput) uses dark glass visual language | SATISFIED | `ChatBubble` gradient/glass verified; `ChatInput` dark glass verified; `ChatPage` bg-black full-viewport with avatar header |
| UI-05 | 14-04 | Remaining authenticated pages (Settings, Billing, Subscribe, AvatarSetup, Admin) use bg-black + GlassCard | SATISFIED | All 5 pages verified: `bg-black` on each, GlassCards used for content sections |
| UI-06 | 14-04 | LandingHero mockup updated to chat bubbles + locked photo (replaces audio visualizer) | SATISFIED | `LandingHero.tsx` chat bubbles and locked photo present; `BAR_HEIGHTS` constant absent |

**IMPORTANT NOTE:** UI-01 through UI-06 are referenced in `ROADMAP.md` and all 4 plan files but are NOT formally defined in `.planning/REQUIREMENTS.md`. The REQUIREMENTS.md file only covers requirements through ADMN-03 (Phase 12). Phase 14 requirement IDs (UI-01 through UI-06) exist solely in the ROADMAP.md and plan frontmatter as informal tracking identifiers. This is not a gap in implementation — all behaviors are satisfied — but is a documentation gap in REQUIREMENTS.md.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | All files are substantive implementations with no stubs, TODO markers, or placeholder returns |

Note: `placeholder` strings found in SettingsPage, BillingPage, and AvatarSetupPage are form input `placeholder` attributes (user-facing hint text), not code anti-patterns.

### Human Verification Required

#### 1. AppNav Responsive Layout Verification

**Test:** Open the app in a browser. On a mobile viewport (<768px), navigate to /chat, /settings, /billing. On a desktop viewport (>=768px), navigate to /chat.
**Expected:** Mobile shows a fixed bottom tab bar with Chat, Photos, Settings icons. Desktop shows a sticky top bar with "Avasecret" brand name and Chat, Photos, Settings text links. Bottom bar must NOT appear on /, /login, /signup.
**Why human:** CSS responsive breakpoints (`hidden md:flex` / `md:hidden`) require browser rendering at specific viewport widths; cannot be verified with grep.

#### 2. ChatPage Avatar Header

**Test:** Sign in and navigate to /chat. Examine the header bar.
**Expected:** Avatar image appears (or gradient violet-to-orange circle with "A" if no image), name text shows in gradient (violet to orange), a green pulsing dot appears next to "Online". No Settings button, no Sign out button visible in the header.
**Why human:** Avatar image depends on real API response; animate-ping CSS animation requires browser; header layout requires visual inspection.

#### 3. SettingsPage Active State Selectors

**Test:** Navigate to /settings. Click different Platform buttons (WhatsApp / Web App) and Content Ceiling options (Mild / Spicy / Explicit).
**Expected:** Active selection shows a blue-to-violet gradient background. Inactive options show a dark glass style (`bg-white/5 border-white/10 text-slate-400`).
**Why human:** Active state depends on user interaction; visual gradient confirmation requires browser.

#### 4. BillingPage Visual Confirmation

**Test:** Navigate to /billing while authenticated.
**Expected:** Pure black background (not dark gray), "← Back to Settings" link visible below the heading, "Manage billing" button shows blue-to-violet gradient.
**Why human:** The distinction between `bg-black` and `bg-gray-950` is subtle and should be visually confirmed; back button placement confirmation.

#### 5. LandingHero Chat Bubbles Mockup

**Test:** Navigate to / (landing page) on a desktop viewport. Examine the right-side phone mockup.
**Expected:** Shows 3 chat bubbles ("Missing you already... 🌙", "Show me something", "Just for you... 💜") and a blurred locked photo with "🔒 Click to unlock" text. The old audio visualizer bars should be completely absent.
**Why human:** Visual composition of the right mockup requires browser to confirm correct rendering and absence of old content.

### Gaps Summary

No automated gaps found. All 17 observable truths are verified. All 19 artifacts pass all three levels (exists, substantive, wired). All 9 key links are wired. All 6 requirement IDs have supporting implementation evidence.

The `human_needed` status reflects 5 items that cannot be programmatically verified: responsive layout behavior, animated elements, interactive active-state selectors, and visual confirmation of design choices. The automated verification is clean — this is not a sign of incomplete implementation.

**Pre-existing test failure:** `AdminPage.test.tsx` — "renders all 5 metric card titles when data is loaded" — confirmed pre-existing before Phase 14 began (documented in all three SUMMARY files for Plans 01, 03, and 04). This failure is unrelated to Phase 14 changes and is out of scope.

**Documentation gap:** UI-01 through UI-06 are not formally defined in `.planning/REQUIREMENTS.md`. They are referenced only in ROADMAP.md and plan frontmatter. This is a tracking gap but does not affect implementation correctness.

---
_Verified: 2026-03-10T17:00:00Z_
_Verifier: Claude (gsd-verifier)_
