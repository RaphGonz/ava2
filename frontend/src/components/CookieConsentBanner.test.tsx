import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CookieConsentBanner } from './CookieConsentBanner'

// consent.ts makes real DOM/Sentry calls -- stub to isolate banner behavior
vi.mock('../lib/consent', () => ({
  initSentry: vi.fn(),
  injectAnalytics: vi.fn(),
  initFromStoredConsent: vi.fn(),
}))

beforeEach(() => {
  localStorage.clear()
})

describe('CookieConsentBanner', () => {
  it('shows banner when no consent stored', () => {
    render(<CookieConsentBanner />)
    expect(screen.getByText(/We use cookies/i)).toBeInTheDocument()
  })

  it('does not show banner when consent already accepted', () => {
    localStorage.setItem('ava-cookie-consent', 'accepted')
    render(<CookieConsentBanner />)
    expect(screen.queryByText(/We use cookies/i)).not.toBeInTheDocument()
  })

  it('does not show banner when consent already declined', () => {
    localStorage.setItem('ava-cookie-consent', 'declined')
    render(<CookieConsentBanner />)
    expect(screen.queryByText(/We use cookies/i)).not.toBeInTheDocument()
  })

  it('stores accepted in localStorage and hides banner on Accept click', () => {
    render(<CookieConsentBanner />)
    fireEvent.click(screen.getByRole('button', { name: /Accept/i }))
    expect(localStorage.getItem('ava-cookie-consent')).toBe('accepted')
    expect(screen.queryByText(/We use cookies/i)).not.toBeInTheDocument()
  })

  it('stores declined in localStorage and hides banner on Decline click', () => {
    render(<CookieConsentBanner />)
    fireEvent.click(screen.getByRole('button', { name: /Decline/i }))
    expect(localStorage.getItem('ava-cookie-consent')).toBe('declined')
    expect(screen.queryByText(/We use cookies/i)).not.toBeInTheDocument()
  })
})
