import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LoginPage from './LoginPage'

// Mock supabase client
vi.mock('../lib/supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
    },
  },
}))

// Mock GoogleSignInButton
vi.mock('../components/GoogleSignInButton', () => ({
  GoogleSignInButton: () => <button>Continue with Google</button>,
}))

describe('LoginPage', () => {
  it('renders on black background', () => {
    const { container } = render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )
    const bgEl = container.querySelector('[class*="bg-black"]')
    expect(bgEl).toBeTruthy()
  })

  it('renders email and password inputs', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )
    expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument()
  })
})
