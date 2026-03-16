---
phase: 17-gdpr-cookie-consent-banner
verified: 2026-03-16T12:00:00Z
status: human_needed
score: 11/11 must-haves verified
re_verification: false
human_verification:
  - test: "First-time visitor sees consent banner on landing page"
    expected: "Banner appears at bottom of http://localhost:5173 with 'We use cookies to improve your experience' text and Accept/Decline buttons"
    why_human: "AnimatePresence + GlassCard rendering requires browser DOM; banner visibility is a visual assertion"
  - test: "Accept stores consent and permanently hides banner"
    expected: "Clicking Accept writes 'accepted' to localStorage key 'ava-cookie-consent'; banner disappears; refreshing does not show banner again"
    why_human: "Cannot verify AnimatePresence exit animation or page-reload suppression without browser"
  - test: "Decline stores consent and permanently hides banner"
    expected: "Clicking Decline writes 'declined' to localStorage key 'ava-cookie-consent'; banner disappears; refreshing does not show banner again"
    why_human: "Same as above — requires real browser session"
  - test: "Banner absent on /login, /signup, and authenticated routes"
    expected: "Navigate to /login, /signup, /chat — no cookie consent banner visible on any of these pages"
    why_human: "Route isolation is structurally verified but final visual confirmation requires human"
  - test: "Sentry captures errors after Accept"
    expected: "After clicking Accept, Sentry.init() fires; error thrown in React renders as Sentry event (confirm via Sentry dashboard or browser devtools network tab showing sentry.io POST)"
    why_human: "Requires real Sentry DSN configured and network inspection"
---

# Phase 17: GDPR Cookie Consent Banner — Verification Report

**Phase Goal:** Implement a GDPR-compliant cookie consent banner that controls Sentry and analytics initialization
**Verified:** 2026-03-16T12:00:00Z
**Status:** human_needed (all automated checks passed; 5 items need browser verification)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | initSentry() calls Sentry.init() with VITE_SENTRY_DSN, gated by sentryInitialized flag (idempotent) | VERIFIED | `consent.ts` lines 4-15: `let sentryInitialized = false`; guard `if (sentryInitialized) return`; `Sentry.init({ dsn: import.meta.env.VITE_SENTRY_DSN })`|
| 2 | injectAnalytics() appends Plausible script to document.head, gated by analyticsInjected flag (idempotent) | VERIFIED | `consent.ts` lines 5, 18-26: `let analyticsInjected = false`; guard `if (analyticsInjected) return`; creates and appends `<script>` to `document.head` |
| 3 | initFromStoredConsent() reads localStorage key 'ava-cookie-consent' and calls init functions only when value is 'accepted' | VERIFIED | `consent.ts` lines 29-35: `localStorage.getItem(CONSENT_KEY)`; `if (stored === 'accepted')` guard; calls both `initSentry()` and `injectAnalytics()` |
| 4 | useCookieConsent hook reads consent state synchronously from localStorage in useState initializer — no async, no flash | VERIFIED | `useCookieConsent.ts` lines 12-15: `useState<ConsentValue | null>(() => { const stored = localStorage.getItem(CONSENT_KEY); return (stored as ConsentValue) ?? null })` — lazy initializer is synchronous |
| 5 | accept() writes 'accepted' to localStorage and calls initSentry()+injectAnalytics() | VERIFIED | `useCookieConsent.ts` lines 19-24: `localStorage.setItem(CONSENT_KEY, 'accepted')`; `initSentry()`; `injectAnalytics()` |
| 6 | decline() writes 'declined' to localStorage and does NOT call initSentry() or injectAnalytics() | VERIFIED | `useCookieConsent.ts` lines 26-30: `localStorage.setItem(CONSENT_KEY, 'declined')`; no calls to init functions; explicit comment confirms intentional omission |
| 7 | @sentry/react is present in frontend/package.json dependencies | VERIFIED | `frontend/package.json` line 14: `"@sentry/react": "^10.43.0"` |
| 8 | Banner renders only on LandingPage — absent from login, signup, chat, and all authenticated routes | VERIFIED | Grep confirms `CookieConsentBanner` imported and used only in `LandingPage.tsx` (line 9 import, line 19 JSX). `App.tsx`, `LoginPage.tsx`, `SignupPage.tsx`, `ChatPage.tsx` contain no reference. Router structure in App.tsx routes /login, /signup, /chat to separate page components. |
| 9 | A returning visitor with stored consent sees no banner (hasChosen=true from synchronous localStorage read) | VERIFIED | `useCookieConsent.ts`: `const hasChosen = consent !== null`; `CookieConsentBanner.tsx`: `{!hasChosen && (...)}` — if localStorage has 'accepted' or 'declined', `consent` is non-null at mount time, banner never renders |
| 10 | initFromStoredConsent() is called in main.tsx before createRoot | VERIFIED | `main.tsx` lines 10, 12: `initFromStoredConsent()` is called at module level before `createRoot(...)` |
| 11 | Sentry.reactErrorHandler is passed to all three createRoot error handlers | VERIFIED | `main.tsx` lines 13-15: `onUncaughtError: Sentry.reactErrorHandler()`, `onCaughtError: Sentry.reactErrorHandler()`, `onRecoverableError: Sentry.reactErrorHandler()` |

**Score:** 11/11 truths verified

---

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `frontend/src/lib/consent.ts` | VERIFIED | 36 lines; exports `initSentry`, `injectAnalytics`, `initFromStoredConsent`; substantive (no stubs, module-level flags, real Sentry.init call, real DOM manipulation); wired from `useCookieConsent.ts` and `main.tsx` |
| `frontend/src/hooks/useCookieConsent.ts` | VERIFIED | 34 lines; exports `useCookieConsent`; substantive (real localStorage reads, real state updates, calls consent functions); wired from `CookieConsentBanner.tsx` |
| `frontend/src/components/CookieConsentBanner.tsx` | VERIFIED | 45 lines; exports `CookieConsentBanner`; substantive (real JSX with GlassCard, AnimatePresence, Accept/Decline buttons); wired in `LandingPage.tsx` |
| `frontend/src/main.tsx` | VERIFIED | Contains `initFromStoredConsent` and `Sentry.reactErrorHandler` — both wired correctly |
| `frontend/src/pages/LandingPage.tsx` | VERIFIED | Imports and renders `<CookieConsentBanner />` as first child inside root div (line 19) |
| `frontend/src/components/CookieConsentBanner.test.tsx` | VERIFIED | 47 lines (above 40-line minimum); 5 tests covering: show for new visitor, hide for accepted, hide for declined, localStorage write on Accept, localStorage write on Decline; uses `vi.mock('../lib/consent')` to stub side effects |
| `frontend/.env` | VERIFIED | Contains `VITE_SENTRY_DSN=` (empty, intentional) and `VITE_PLAUSIBLE_DOMAIN=avasecret.com` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `useCookieConsent.ts` | `consent.ts` | `import { initSentry, injectAnalytics }` | WIRED | Line 2: `import { initSentry, injectAnalytics } from '../lib/consent'`; both called in `accept()` |
| `consent.ts` | `@sentry/react` | `import * as Sentry from '@sentry/react'` | WIRED | Line 1: `import * as Sentry from '@sentry/react'`; used at line 11: `Sentry.init({...})` |
| `CookieConsentBanner.tsx` | `useCookieConsent.ts` | `useCookieConsent()` call | WIRED | Line 3 import, line 6: `const { hasChosen, accept, decline } = useCookieConsent()` |
| `LandingPage.tsx` | `CookieConsentBanner.tsx` | import + JSX render | WIRED | Line 9 import, line 19: `<CookieConsentBanner />` as first child inside root div |
| `main.tsx` | `consent.ts` | `initFromStoredConsent()` before createRoot | WIRED | Line 5 import, line 10: `initFromStoredConsent()` called at module level before `createRoot` |
| `main.tsx` | `@sentry/react` | `Sentry.reactErrorHandler()` on createRoot handlers | WIRED | Line 6 import, lines 13-15: passed to all three createRoot error handler props |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| COOK-01 | 17-02 | Visitor sees cookie consent banner on landing page before non-essential scripts load | SATISFIED | `CookieConsentBanner` rendered in `LandingPage.tsx` line 19; `initFromStoredConsent()` called before `createRoot` ensures no scripts load before banner decision for returning visitors; first-time visitors have no stored consent so banner is shown immediately |
| COOK-02 | 17-02 | Visitor can accept all cookies (Sentry + analytics enabled) | SATISFIED | `accept()` in `useCookieConsent.ts` calls `initSentry()` + `injectAnalytics()`; test case "stores accepted in localStorage and hides banner on Accept click" covers this |
| COOK-03 | 17-02 | Visitor can decline non-essential cookies (Sentry + analytics blocked; Stripe still loads) | SATISFIED | `decline()` in `useCookieConsent.ts` writes 'declined' but does NOT call `initSentry()` or `injectAnalytics()`; Stripe is loaded unconditionally (no evidence of consent-gated Stripe in codebase — correct per spec) |
| COOK-04 | 17-01 | Consent choice saved to localStorage and persists across sessions | SATISFIED | `accept()` calls `localStorage.setItem(CONSENT_KEY, 'accepted')`; `decline()` calls `localStorage.setItem(CONSENT_KEY, 'declined')`; `useCookieConsent` reads from localStorage synchronously in useState initializer |
| COOK-05 | 17-02 | Banner does not appear again once a choice has been made | SATISFIED | `hasChosen = consent !== null`; banner renders only when `!hasChosen`; on revisit, localStorage still has the stored value, consent is non-null, banner never mounts |
| COOK-06 | 17-01 | Sentry and analytics scripts only initialise after consent is granted (not on page load) | SATISFIED | No `Sentry.init()` at top level anywhere (grep confirms 0 matches outside `consent.ts`); `consent.ts` gates `Sentry.init()` behind `initSentry()` which is only called from `accept()` or `initFromStoredConsent()` (which checks `stored === 'accepted'`). `main.tsx` imports `* as Sentry` but only uses `Sentry.reactErrorHandler()` which is a no-op wrapper — does NOT call `Sentry.init()`. |

All 6 requirements are SATISFIED with direct implementation evidence.

---

### Orphaned Requirements

None. All 6 COOK requirements declared in REQUIREMENTS.md are mapped to Phase 17 and covered by plans 17-01 (COOK-04, COOK-06) and 17-02 (COOK-01, COOK-02, COOK-03, COOK-05).

---

### Anti-Patterns Found

| File | Pattern | Severity | Verdict |
|------|---------|----------|---------|
| `main.tsx` line 6 | `import * as Sentry from '@sentry/react'` at top level | Info | NOT a violation. This import is used exclusively for `Sentry.reactErrorHandler()` (a no-op wrapper when uninitialized). It does NOT call `Sentry.init()`. COOK-06 is satisfied. |

No blockers, stubs, placeholder comments, empty implementations, or TODO markers found across any of the 5 modified files.

---

### Commit Verification

All 5 task commits documented in SUMMARY files exist in git history:

| Commit | Description |
|--------|-------------|
| `7f299e6` | chore(17-01): install @sentry/react and add env var placeholders |
| `38bcf38` | feat(17-01): create consent.ts service module with deferred Sentry and analytics init |
| `98a6ab1` | feat(17-01): create useCookieConsent hook with synchronous localStorage state |
| `5100aaa` | feat(17-02): create CookieConsentBanner component and tests |
| `b19d5ea` | feat(17-02): wire main.tsx and LandingPage with consent init |

---

### Human Verification Required

The following tests require a running browser. Run `cd frontend && npm run dev` first.

#### 1. First-time visitor banner appearance

**Test:** Open http://localhost:5173 in a fresh incognito window (no prior localStorage)
**Expected:** A banner appears at the bottom of the page with text "We use cookies to improve your experience (error tracking + analytics)" and two buttons: "Decline" and "Accept"
**Why human:** AnimatePresence slide-in animation and GlassCard visual rendering cannot be verified programmatically

#### 2. Accept flow — banner dismissal and persistence

**Test:** On the landing page, click "Accept"
**Expected:** Banner disappears (slide-out animation), DevTools > Application > Local Storage shows `ava-cookie-consent = accepted`. Refresh the page — banner does NOT reappear.
**Why human:** localStorage write + AnimatePresence exit + page-reload suppression requires real browser session

#### 3. Decline flow — banner dismissal and persistence

**Test:** Open a new incognito window, visit landing page, click "Decline"
**Expected:** Banner disappears, `ava-cookie-consent = declined` in localStorage. Refresh — banner does NOT reappear.
**Why human:** Same as above

#### 4. Banner isolation — no banner on auth/app routes

**Test:** Visit /login, /signup, and (after signing in) /chat
**Expected:** No cookie consent banner visible on any of these pages
**Why human:** Route isolation is structurally confirmed but final visual check requires human

#### 5. Sentry activation after Accept (optional — requires real DSN)

**Test:** Add a real Sentry DSN to `frontend/.env` as `VITE_SENTRY_DSN=https://...`, restart dev server, accept cookies in browser, then trigger a JS error
**Expected:** Error appears in Sentry dashboard; network tab shows a POST to sentry.io
**Why human:** Requires external service configuration and network inspection

---

### Gaps Summary

No gaps found. All 11 observable truths are verified, all 6 artifacts are substantive and wired, all 6 key links are connected, and all 6 COOK requirements have direct implementation evidence. The phase goal — GDPR-compliant consent banner controlling Sentry and analytics initialization — is architecturally complete.

Status is `human_needed` (not `gaps_found`) because the automated structural verification is comprehensive and no implementation defects were found. The human verification items are standard browser smoke tests for a UI feature, not gap closures.

---

_Verified: 2026-03-16T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
