import * as Sentry from '@sentry/react'

const CONSENT_KEY = 'ava-cookie-consent'

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
  script.setAttribute('data-domain', import.meta.env.VITE_PLAUSIBLE_DOMAIN ?? 'avasecret.com')
  script.src = 'https://plausible.io/js/script.js'
  document.head.appendChild(script)
}

/** Called at app startup (main.tsx) before createRoot — handles returning visitors who already accepted */
export function initFromStoredConsent() {
  const stored = localStorage.getItem(CONSENT_KEY)
  if (stored === 'accepted') {
    initSentry()
    injectAnalytics()
  }
}
