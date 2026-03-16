import { useState } from 'react'
import { initSentry, injectAnalytics } from '../lib/consent'

const CONSENT_KEY = 'ava-cookie-consent'

type ConsentValue = 'accepted' | 'declined'

export function useCookieConsent() {
  // Lazy useState initializer — synchronous read from localStorage.
  // This is intentional: synchronous init prevents the banner from flashing
  // for one frame on returning visitors (Pitfall 3 in research).
  const [consent, setConsent] = useState<ConsentValue | null>(() => {
    const stored = localStorage.getItem(CONSENT_KEY)
    return (stored as ConsentValue) ?? null
  })

  const hasChosen = consent !== null

  const accept = () => {
    localStorage.setItem(CONSENT_KEY, 'accepted')
    setConsent('accepted')
    initSentry()
    injectAnalytics()
  }

  const decline = () => {
    localStorage.setItem(CONSENT_KEY, 'declined')
    setConsent('declined')
    // Sentry and analytics intentionally not initialized on decline
  }

  return { consent, hasChosen, accept, decline }
}
