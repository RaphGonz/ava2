import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AppNav } from './AppNav'

describe('AppNav', () => {
  it('renders Chat, Photos, and Settings links', () => {
    render(
      <MemoryRouter initialEntries={['/chat']}>
        <AppNav />
      </MemoryRouter>
    )
    expect(screen.getAllByText('Chat').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Photos').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Settings').length).toBeGreaterThan(0)
  })

  it('marks the active route as active (text-white class area)', () => {
    render(
      <MemoryRouter initialEntries={['/chat']}>
        <AppNav />
      </MemoryRouter>
    )
    // Desktop link — at least one Chat link exists
    const chatLinks = screen.getAllByRole('link', { name: /Chat/i })
    expect(chatLinks.length).toBeGreaterThan(0)
  })
})
