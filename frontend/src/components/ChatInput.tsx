import { useState } from 'react'

interface ChatInputProps {
  onSend: (text: string) => void
  disabled?: boolean
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed) return
    onSend(trimmed)
    setText('')
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as unknown as React.FormEvent)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-white/10 px-4 py-3 bg-black/80 backdrop-blur-sm">
      <div className="flex items-end gap-2">
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Message Ava..."
          rows={1}
          className="flex-1 resize-none bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 max-h-32 overflow-y-auto"
          style={{ minHeight: '38px' }}
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white rounded-xl px-4 py-2 text-sm font-medium transition-all disabled:opacity-40 flex-shrink-0"
        >
          Send
        </button>
      </div>
    </form>
  )
}
