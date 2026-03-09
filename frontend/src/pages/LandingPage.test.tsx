import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LandingPage from './LandingPage'

// Mock useAuthStore to return unauthenticated state (no token)
vi.mock('../store/useAuthStore', () => ({
  useAuthStore: (selector: (s: { token: null }) => unknown) =>
    selector({ token: null }),
}))

function renderLanding() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <LandingPage />
    </MemoryRouter>
  )
}

describe('LandingPage — LAND-01: Required sections present', () => {
  it('renders a hero section', () => {
    renderLanding()
    // Hero section is identifiable by the primary headline text
    expect(screen.getByText(/The AI that takes care of your day/i)).toBeInTheDocument()
  })

  it('renders a features/DualPromise section', () => {
    renderLanding()
    expect(screen.getByText(/Assistant Mode/i)).toBeInTheDocument()
    expect(screen.getByText(/Companion Mode/i)).toBeInTheDocument()
  })

  it('renders a pricing section', () => {
    renderLanding()
    expect(screen.getByText(/Choose your plan/i)).toBeInTheDocument()
    expect(screen.getByText(/Premium/i)).toBeInTheDocument()
  })
})

describe('LandingPage — LAND-02: CTAs link to /signup', () => {
  it('primary CTA links to /signup', () => {
    renderLanding()
    const ctaLinks = screen.getAllByRole('link', { name: /Create my Ava/i })
    expect(ctaLinks.length).toBeGreaterThan(0)
    expect(ctaLinks[0]).toHaveAttribute('href', '/signup')
  })

  it('Get started link routes to /signup', () => {
    renderLanding()
    const links = screen.getAllByRole('link', { name: /Get started/i })
    expect(links.length).toBeGreaterThan(0)
    links.forEach(link => expect(link).toHaveAttribute('href', '/signup'))
  })
})

describe('LandingPage — LAND-03: No prohibited copy', () => {
  it('contains no prohibited NSFW or adult language', () => {
    const { container } = renderLanding()
    const html = container.innerHTML

    const prohibited = [
      'intimate', 'explicit', 'NSFW', 'adult', '18+',
      'intimité', 'Créer', 'mois', 'ShieldAlert',
    ]
    prohibited.forEach(word => {
      expect(html).not.toContain(word)
    })
  })

  it('contains no French copy', () => {
    const { container } = renderLanding()
    const html = container.innerHTML

    const frenchWords = ['Gratuit', 'Maintenant', 'Choisissez', 'Confiance', 'Démoriser']
    frenchWords.forEach(word => {
      expect(html).not.toContain(word)
    })
  })
})

describe('LandingPage — Auth redirect', () => {
  it('redirects authenticated users away from landing page', () => {
    vi.mock('../store/useAuthStore', () => ({
      useAuthStore: (selector: (s: { token: string }) => unknown) =>
        selector({ token: 'fake-token' }),
    }))
    // With a token, the Navigate component renders; landing content does not
    const { container } = render(
      <MemoryRouter initialEntries={['/']}>
        <LandingPage />
      </MemoryRouter>
    )
    // Hero headline should NOT be present for authenticated user
    expect(container.innerHTML).not.toContain('The AI that takes care')
  })
})
