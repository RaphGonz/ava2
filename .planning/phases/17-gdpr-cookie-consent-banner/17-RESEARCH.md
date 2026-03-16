# Phase 17: GDPR Cookie Consent Banner - Research

**Researched:** 2026-03-16
**Domain:** GDPR cookie consent — React, localStorage, deferred Sentry init, analytics gating
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| COOK-01 | Visitor sees a cookie consent banner on the landing page before any non-essential scripts load | CookieConsentBanner component rendered in LandingPage before Sentry/analytics init |
| COOK-02 | Visitor can accept all cookies (Sentry + analytics enabled) | Banner "Accept" button sets consent=true in localStorage + calls initSentry() + injectAnalytics() |
| COOK-03 | Visitor can decline non-essential cookies (Sentry + analytics blocked; Stripe still loads) | Banner "Decline" button sets consent=false; Stripe loads unconditionally in LandingPricing |
| COOK-04 | Consent choice is saved to localStorage and persists across sessions | useCookieConsent hook reads/writes "ava-cookie-consent" key in localStorage |
| COOK-05 | Banner does not appear again once a choice has been made | Hook returns hasChosen=true when key exists; LandingPage conditionally renders banner |
| COOK-06 | Sentry and analytics scripts only initialise after consent is granted (not on page load) | main.tsx no longer imports instrument.ts unconditionally; init happens inside consent callback |
</phase_requirements>

## Summary

This phase adds a GDPR-compliant cookie consent banner to the landing page only. Authenticated users are considered to have accepted via Terms of Service, so no banner appears on any post-auth route. The implementation is entirely frontend — no backend changes needed.

The core architecture is a `useCookieConsent` custom hook backed by localStorage (key `ava-cookie-consent`), a `CookieConsentBanner` component styled with the project's existing GlassCard / dark-glass system, and a `consent.ts` service module that conditionally calls `Sentry.init()` and injects the analytics `<script>` tag into `<head>` when consent is granted. Sentry's `@sentry/react` v10 and an analytics provider (Plausible recommended — lightweight, privacy-first) must both be installed as part of this phase since neither is currently in the project.

The key technical challenge is that Sentry's React SDK docs recommend importing `instrument.ts` as the first import in `main.tsx`. This phase inverts that: Sentry must NOT be initialized at module load time. Instead, `Sentry.init()` is called dynamically inside the consent grant handler, and `createRoot` must be configured with `Sentry.reactErrorHandler` only if consent has already been stored from a prior session. This is verified to work: Sentry.init() can be called at any time before the first error event, and the loader-script path for CDN is not needed here since the project uses npm packages.

**Primary recommendation:** Build a custom `useCookieConsent` hook + `CookieConsentBanner` component — no third-party consent library needed for this scope. Install `@sentry/react` and Plausible analytics. Gate both behind the consent hook.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @sentry/react | ^10.42.0 (latest) | Error monitoring + performance | Official Sentry SDK for React 19; supports reactErrorHandler for createRoot |
| Plausible (script injection) | N/A (CDN script) | Privacy-first analytics | No cookies, no GDPR consent required by itself — but project decisions gate it; simple `<script>` tag |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| zustand persist (already installed) | ^5.0.11 | Already stores auth in localStorage | Do NOT use zustand for consent — plain localStorage is simpler and avoids rerender coupling |
| motion/react (already installed) | ^12.35.1 | AnimatePresence for banner slide-in | Same import convention as existing project code |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Plausible CDN script | react-plausible-analytics package | Plausible CDN is simpler; wrapper package adds overhead for simple pageview tracking |
| Custom hook | react-cookie-consent npm package | Library adds bundle weight; custom hook is 30 lines and matches project patterns precisely |
| @sentry/react npm | Sentry CDN loader script | npm is already the project pattern; CDN loader has window.sentryOnLoad API but adds external dependency |

**Installation:**
```bash
cd frontend && npm install @sentry/react
```

Note: Plausible analytics does not require npm install — it is a `<script>` tag injected into the DOM. If the project decides to use a different analytics provider (GA4, PostHog, etc.), swap only the `injectAnalytics()` function in `consent.ts`.

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/
├── hooks/
│   └── useCookieConsent.ts       # localStorage read/write, hasChosen + consent state
├── lib/
│   └── consent.ts                 # initSentry(), injectAnalytics(), initFromStoredConsent()
├── components/
│   └── CookieConsentBanner.tsx    # Banner UI using GlassCard + motion/react
├── pages/
│   └── LandingPage.tsx            # Renders <CookieConsentBanner> conditionally
└── main.tsx                       # initFromStoredConsent() called before createRoot
```

### Pattern 1: useCookieConsent Hook (localStorage)
**What:** Read/write consent state from localStorage key `ava-cookie-consent`. Returns `{ consent, hasChosen, accept, decline }`.
**When to use:** Any component that needs to know consent state or trigger a consent action.

```typescript
// frontend/src/hooks/useCookieConsent.ts
// No external library — plain localStorage

const CONSENT_KEY = 'ava-cookie-consent'

type ConsentValue = 'accepted' | 'declined'

export function useCookieConsent() {
  const [consent, setConsent] = useState<ConsentValue | null>(() => {
    const stored = localStorage.getItem(CONSENT_KEY)
    return (stored as ConsentValue) ?? null
  })

  const hasChosen = consent !== null

  const accept = () => {
    localStorage.setItem(CONSENT_KEY, 'accepted')
    setConsent('accepted')
    initSentry()       // from consent.ts
    injectAnalytics()  // from consent.ts
  }

  const decline = () => {
    localStorage.setItem(CONSENT_KEY, 'declined')
    setConsent('declined')
    // Sentry and analytics intentionally not initialized
  }

  return { consent, hasChosen, accept, decline }
}
```

### Pattern 2: consent.ts — Deferred Sentry Init
**What:** Module with idempotent init functions. Sentry.init() is safe to call once; guard with a `let initialized = false` flag.
**When to use:** Called from `accept()` in the hook, and from `initFromStoredConsent()` in main.tsx for returning visitors.

```typescript
// frontend/src/lib/consent.ts
import * as Sentry from '@sentry/react'

let sentryInitialized = false
let analyticsInjected = false

export function initSentry() {
  if (sentryInitialized) return
  sentryInitialized = true
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    tracesSampleRate: 0.1,
    environment: import.meta.env.MODE,
  })
}

export function injectAnalytics() {
  if (analyticsInjected) return
  analyticsInjected = true
  const script = document.createElement('script')
  script.defer = true
  script.setAttribute('data-domain', import.meta.env.VITE_PLAUSIBLE_DOMAIN)
  script.src = 'https://plausible.io/js/script.js'
  document.head.appendChild(script)
}

/** Called at app startup (main.tsx) before createRoot — handles returning visitors */
export function initFromStoredConsent() {
  const stored = localStorage.getItem('ava-cookie-consent')
  if (stored === 'accepted') {
    initSentry()
    injectAnalytics()
  }
}
```

### Pattern 3: main.tsx Integration (React 19)
**What:** `initFromStoredConsent()` runs before `createRoot` so returning visitors who already accepted have Sentry active from page load. For first-time visitors (no stored consent), Sentry stays uninitialized.
**When to use:** This is the ONLY correct integration point in main.tsx.

```typescript
// frontend/src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { initFromStoredConsent } from './lib/consent.ts'
import * as Sentry from '@sentry/react'

// Returning visitors: init Sentry before React tree mounts (if consent stored)
initFromStoredConsent()

createRoot(document.getElementById('root')!, {
  onUncaughtError: Sentry.reactErrorHandler(),
  onCaughtError: Sentry.reactErrorHandler(),
  onRecoverableError: Sentry.reactErrorHandler(),
}).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

Note: `Sentry.reactErrorHandler` is safe to pass even if Sentry has not been initialized — it is a no-op when no DSN is configured. Verified via Sentry docs: "If no DSN is set, the SDK will not send any events."

### Pattern 4: CookieConsentBanner Component
**What:** Fixed-position banner at bottom of screen, styled with GlassCard, animated with AnimatePresence from `motion/react`. Only renders on LandingPage.
**When to use:** Rendered inside LandingPage when `!hasChosen`.

```typescript
// frontend/src/components/CookieConsentBanner.tsx
import { AnimatePresence } from 'motion/react'
import { GlassCard } from './ui/GlassCard'
import { useCookieConsent } from '../hooks/useCookieConsent'

export function CookieConsentBanner() {
  const { hasChosen, accept, decline } = useCookieConsent()

  return (
    <AnimatePresence>
      {!hasChosen && (
        <div className="fixed bottom-4 left-4 right-4 z-50 max-w-2xl mx-auto">
          <GlassCard
            initial={{ y: 80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 80, opacity: 0 }}
            transition={{ type: 'spring', damping: 25 }}
            className="flex flex-col sm:flex-row items-start sm:items-center gap-4"
          >
            <p className="text-sm text-slate-300 flex-1">
              We use cookies to improve your experience (error tracking + analytics).
              Payments always work regardless of your choice.{' '}
              <a href="/privacy" className="text-blue-400 hover:text-blue-300 underline">Privacy policy</a>
            </p>
            <div className="flex gap-3 shrink-0">
              <button
                onClick={decline}
                className="text-sm text-slate-400 hover:text-white transition-colors px-4 py-2"
              >
                Decline
              </button>
              <button
                onClick={accept}
                className="text-sm bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white px-4 py-2 rounded-lg transition-all font-medium"
              >
                Accept
              </button>
            </div>
          </GlassCard>
        </div>
      )}
    </AnimatePresence>
  )
}
```

### Pattern 5: LandingPage Integration
**What:** Add `<CookieConsentBanner />` as the first child inside the page wrapper div. Banner has `z-50` so it floats above all content.

```typescript
// In LandingPage.tsx, inside the return:
<div className="w-full min-h-screen bg-black text-white overflow-x-hidden">
  <CookieConsentBanner />   {/* ADD THIS LINE — renders only when !hasChosen */}
  <nav ...>
  ...
</div>
```

### Anti-Patterns to Avoid
- **Importing instrument.ts unconditionally in main.tsx:** Sentry would initialize before consent is checked. Instead, call `initSentry()` from `consent.ts` only when accepted.
- **Using zustand for consent state:** Zustand persist is async-hydrated; plain localStorage.getItem() in useState initializer is synchronous, which is correct here.
- **Showing the banner on authenticated routes:** Authenticated users accepted via ToS. Banner must only be rendered inside LandingPage, not in App.tsx root.
- **Blocking Stripe for declined users:** Per locked decisions, Stripe always loads. LandingPricing already loads Stripe unconditionally — do not add consent checks there.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Analytics injection timing | Custom event queue or mutation observer | Simple idempotent `injectAnalytics()` with guard flag | Script tag injection is one-liner; no complex timing needed for Plausible |
| Cross-tab consent sync | localStorage event listener for "storage" event | Not needed for v1.2 scope | Out-of-scope per requirements; localStorage-only is sufficient |
| Consent withdrawal UI | Settings page consent toggle | Not in scope | Explicitly out of scope in REQUIREMENTS.md |

**Key insight:** The requirements are narrow (accept/decline, no granularity, no withdrawal UI). A 3-file custom implementation (hook + service + component) is superior to any third-party library for this scope.

## Common Pitfalls

### Pitfall 1: Sentry.init() Called Before Consent Check at Module Load
**What goes wrong:** If `instrument.ts` is imported at the top of `main.tsx`, Sentry initializes immediately on page load for ALL visitors — including those who decline.
**Why it happens:** Sentry's official docs show `import './instrument'` as the first line. That pattern assumes all users have consented.
**How to avoid:** Do NOT create an `instrument.ts` file or any top-level Sentry import that calls `Sentry.init()`. Use the `consent.ts` module pattern instead — only call `Sentry.init()` inside `initSentry()` which is called post-consent.
**Warning signs:** If Sentry is capturing events in the network tab before the user interacts with the banner.

### Pitfall 2: reactErrorHandler No-Op When Sentry Not Initialized
**What goes wrong:** Developer worries that passing `Sentry.reactErrorHandler()` to `createRoot` when Sentry hasn't been initialized will throw.
**Why it happens:** Misunderstanding of the SDK behavior.
**How to avoid:** No workaround needed. When no DSN is set (Sentry not initialized), `reactErrorHandler` returns a function that does nothing. Confirmed via Sentry docs. Safe to always pass to createRoot.

### Pitfall 3: Banner Flash on Returning Visitors (hasChosen = false for one render)
**What goes wrong:** On returning visitors who have already chosen, the banner flickers for one frame before disappearing.
**Why it happens:** If consent state is loaded asynchronously (e.g., useEffect), the initial render assumes no choice was made.
**How to avoid:** Initialize consent state synchronously in `useState(() => localStorage.getItem(CONSENT_KEY))`. This is the lazy initializer pattern — runs once, synchronously, before first render. No flash.

### Pitfall 4: Analytics Script Injected Multiple Times
**What goes wrong:** `injectAnalytics()` is called multiple times (e.g., from React re-renders) and multiple analytics scripts appear in `<head>`.
**Why it happens:** Missing idempotency guard.
**How to avoid:** Use the `let analyticsInjected = false` module-level guard in `consent.ts`. Module scope persists for the lifetime of the page.

### Pitfall 5: Missing VITE_SENTRY_DSN Crashes Build
**What goes wrong:** `import.meta.env.VITE_SENTRY_DSN` is undefined in environments where .env is not set; Sentry.init() receives `undefined` as DSN.
**Why it happens:** Forgetting to add env var to `.env` and to deployment environment.
**How to avoid:** Sentry.init() with `dsn: undefined` is a no-op (does not throw). Still, add `VITE_SENTRY_DSN` to `.env` (empty string for dev is fine if you don't want local Sentry reporting). Document in the plan that the DSN must be added to the production environment.

### Pitfall 6: Banner Renders on /login, /signup, etc.
**What goes wrong:** If `<CookieConsentBanner />` is placed in App.tsx, it appears on all pre-auth pages including login, signup.
**Why it happens:** Placing the banner globally rather than per-page.
**How to avoid:** Import and render `<CookieConsentBanner />` only inside `LandingPage.tsx`. The banner is a landing-page concern, not a global layout concern.

### Pitfall 7: Vitest Test Fails Due to localStorage in useState Initializer
**What goes wrong:** Tests fail with "localStorage is not defined" or banner always shows/hides incorrectly.
**Why it happens:** jsdom is the test environment; localStorage exists but may not be reset between tests.
**How to avoid:** In test files, use `beforeEach(() => localStorage.clear())`. The existing vitest config already uses `environment: 'jsdom'`, so localStorage is available.

## Code Examples

### Env var additions to frontend/.env
```bash
# Sentry — error monitoring (gated behind cookie consent)
VITE_SENTRY_DSN=

# Analytics — Plausible (gated behind cookie consent)
VITE_PLAUSIBLE_DOMAIN=avasecret.com
```

### Testing the banner with Vitest + Testing Library
```typescript
// Source: Vitest + @testing-library/react (already in devDependencies)
import { render, screen, fireEvent } from '@testing-library/react'
import { CookieConsentBanner } from './CookieConsentBanner'

beforeEach(() => localStorage.clear())

it('shows banner when no consent stored', () => {
  render(<CookieConsentBanner />)
  expect(screen.getByText(/We use cookies/i)).toBeInTheDocument()
})

it('hides banner after accept', () => {
  render(<CookieConsentBanner />)
  fireEvent.click(screen.getByRole('button', { name: /Accept/i }))
  expect(localStorage.getItem('ava-cookie-consent')).toBe('accepted')
})

it('does not show banner when consent already stored', () => {
  localStorage.setItem('ava-cookie-consent', 'accepted')
  render(<CookieConsentBanner />)
  expect(screen.queryByText(/We use cookies/i)).not.toBeInTheDocument()
})
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sentry CDN loader script with `window.sentryOnLoad` | `@sentry/react` npm package with conditional `Sentry.init()` call | SDK v8+ | npm package is the standard for React apps; CDN loader only needed for non-bundled environments |
| `Sentry.init()` in instrument.ts imported first in main.tsx | Call `Sentry.init()` from consent handler + `initFromStoredConsent()` in main.tsx | React 19 era | Consent-first architecture; no unconditional init at module load |
| Cookies for consent storage | localStorage | Last 3 years | localStorage is simpler, avoids Set-Cookie header overhead; still legally valid for consent |

**Deprecated/outdated:**
- `Sentry.setUser` before consent: Do not call any Sentry API that transmits PII before consent is granted. For this project, Sentry only captures errors/traces (no explicit user ID sent), so this is not a concern for the current scope.

## Open Questions

1. **Which analytics provider is intended?**
   - What we know: No analytics script or package exists in the project. The requirements and decisions say "analytics" without specifying the provider.
   - What's unclear: Plausible vs. GA4 vs. PostHog vs. something else.
   - Recommendation: Use Plausible (privacy-first, GDPR-friendly, lightweight CDN script). If the team wants GA4, swap only the `injectAnalytics()` function — the architecture is identical. The planner should default to Plausible but leave `injectAnalytics()` as the extension point.

2. **Should Sentry be configured in dev environment?**
   - What we know: `VITE_SENTRY_DSN` does not exist in `.env`. Sentry.init() with undefined DSN is a no-op.
   - What's unclear: Does the team want dev errors to also go to Sentry, or only production?
   - Recommendation: Leave `VITE_SENTRY_DSN=` (empty) in `.env` for dev. The plan should note that the production DSN must be added to the deployment environment secrets.

## Validation Architecture

> workflow.nyquist_validation is not present in config.json — skip this section.

(Config has `workflow.research: false, workflow.plan_check: true, workflow.verifier: true` — no nyquist_validation key. Skipping Validation Architecture section.)

## Sources

### Primary (HIGH confidence)
- [Sentry React docs](https://docs.sentry.io/platforms/javascript/guides/react/) — React 19 setup, reactErrorHandler, Sentry.init() configuration
- [Sentry lazy load docs](https://docs.sentry.io/platforms/javascript/install/lazy-load-sentry/) — conditional initialization, forceLoad, window.sentryOnLoad
- Project codebase inspection — confirmed no Sentry/analytics in package.json, .env, or src files
- Project codebase inspection — confirmed vitest + jsdom + @testing-library/react already installed; motion/react mock already exists

### Secondary (MEDIUM confidence)
- [Sentry GitHub Discussion #6211](https://github.com/getsentry/sentry-javascript/discussions/6211) — opt-in tracing after consent; beforeSendTransaction pattern; maintainer responses
- [npm @sentry/react](https://www.npmjs.com/package/@sentry/react) — latest version 10.42.0 confirmed
- [GDPR cookie consent React patterns](https://gdpr.direct/guides/cookie-consent-implementation) — localStorage pattern, consent hook structure

### Tertiary (LOW confidence)
- WebSearch results on Plausible + React/Vite — no single authoritative source found for exact injection pattern; CDN script injection is standard practice, LOW confidence on Plausible being the right provider (team should confirm)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — @sentry/react v10 confirmed via npm; custom hook pattern verified via codebase inspection; no library needed for consent
- Architecture: HIGH — deferred Sentry.init() pattern confirmed via Sentry official docs; localStorage synchronous init pattern is well-established
- Pitfalls: HIGH — pitfalls 1-6 verified against actual project code; pitfall 7 confirmed via vitest.config.ts showing jsdom environment

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (Sentry SDK updates frequently; verify @sentry/react version before install)
