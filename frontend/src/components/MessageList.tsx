import { useEffect, useRef } from 'react'
import ChatBubble from './ChatBubble'
import type { ChatMessage } from '../api/chat'

interface MessageListProps {
  messages: ChatMessage[]
  isLoading: boolean
}

export default function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (isLoading && messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        Loading...
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
      {messages.length === 0 && (
        <p className="text-center text-gray-400 text-sm mt-8">
          Say hello to Ava
        </p>
      )}
      {messages.map(msg => (
        <ChatBubble
          key={msg.id}
          role={msg.role}
          content={msg.content}
          timestamp={msg.created_at}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
