import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ChatBubble from './ChatBubble'

describe('ChatBubble', () => {
  it('renders user bubble content', () => {
    render(<ChatBubble role="user" content="Hello Ava" />)
    expect(screen.getByText('Hello Ava')).toBeInTheDocument()
  })

  it('renders assistant bubble content', () => {
    render(<ChatBubble role="assistant" content="Hi there!" />)
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
  })

  it('user bubble has gradient class', () => {
    const { container } = render(<ChatBubble role="user" content="test" />)
    const bubble = container.querySelector('[class*="from-blue-600"]')
    expect(bubble).toBeTruthy()
  })

  it('assistant bubble has glassmorphism class', () => {
    const { container } = render(<ChatBubble role="assistant" content="test" />)
    const bubble = container.querySelector('[class*="backdrop-blur"]')
    expect(bubble).toBeTruthy()
  })
})
