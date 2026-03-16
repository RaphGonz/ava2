import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { initFromStoredConsent } from './lib/consent.ts'
import * as Sentry from '@sentry/react'

// Returning visitors: initialize Sentry before React tree mounts if they already accepted.
// For first-time visitors (no stored consent), this is a no-op.
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
