import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock the auth store
vi.mock('../store/useAuthStore')
// Mock the admin API
vi.mock('../api/admin')

import { useAuthStore } from '../store/useAuthStore'
import * as adminApi from '../api/admin'
import AdminPage, { AdminRoute } from '../pages/AdminPage'

// Helper: create a JWT-like token with given payload for testing atob decode
function makeTestToken(payload: Record<string, unknown>): string {
  const header = btoa(JSON.stringify({ alg: 'HS256' }))
  const body = btoa(JSON.stringify(payload))
  return `${header}.${body}.fakesig`
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/admin']}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('AdminRoute', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('redirects to /login when no token', () => {
    vi.mocked(useAuthStore).mockReturnValue(null as any)
    const { container } = render(
      <Wrapper>
        <Routes>
          <Route path="/admin" element={<AdminRoute><div>admin content</div></AdminRoute>} />
          <Route path="/login" element={<div>login page</div>} />
          <Route path="/chat" element={<div>chat page</div>} />
        </Routes>
      </Wrapper>
    )
    expect(container.textContent).toContain('login page')
    expect(container.textContent).not.toContain('admin content')
  })

  it('redirects to /chat for non-admin token (no is_admin flag)', () => {
    const token = makeTestToken({ sub: 'user-123', user_metadata: {} })
    vi.mocked(useAuthStore).mockReturnValue(token as any)
    const { container } = render(
      <Wrapper>
        <Routes>
          <Route path="/admin" element={<AdminRoute><div>admin content</div></AdminRoute>} />
          <Route path="/chat" element={<div>chat page</div>} />
        </Routes>
      </Wrapper>
    )
    expect(container.textContent).toContain('chat page')
    expect(container.textContent).not.toContain('admin content')
  })

  it('renders children for admin token (is_admin: true)', () => {
    const token = makeTestToken({ sub: 'admin-456', user_metadata: { is_admin: true } })
    vi.mocked(useAuthStore).mockReturnValue(token as any)
    render(
      <Wrapper>
        <Routes>
          <Route path="/admin" element={<AdminRoute><div>admin content</div></AdminRoute>} />
        </Routes>
      </Wrapper>
    )
    expect(screen.getByText('admin content')).toBeTruthy()
  })
})

describe('AdminPage metric cards', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders all 5 metric card titles when data is loaded', async () => {
    const token = makeTestToken({ sub: 'admin-456', user_metadata: { is_admin: true } })
    vi.mocked(useAuthStore).mockReturnValue(token as any)
    vi.mocked(adminApi.getAdminMetrics).mockResolvedValue({
      active_users:         { d7: 10, d30: 25, all: 100 },
      messages_sent:        { d7: 500, d30: 1200, all: 9999 },
      photos_generated:     { d7: 20, d30: 55, all: 300 },
      active_subscriptions: { d7: 3, d30: 8, all: 42 },
      new_signups:          { d7: 5, d30: 12, all: 75 },
      fetched_at:           '2026-03-10T12:00:00Z',
    })

    const { findByText } = render(
      <Wrapper>
        <Routes>
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </Wrapper>
    )

    // All 5 metric titles must appear
    await findByText(/active users/i)
    await findByText(/messages sent/i)
    await findByText(/photos generated/i)
    await findByText(/active subscriptions/i)
    await findByText(/new signups/i)
  })
})
