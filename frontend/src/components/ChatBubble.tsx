interface ChatBubbleProps {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

const PHOTO_RE = /\[PHOTO\](.*?)\[\/PHOTO\]/s

function renderContent(content: string) {
  const match = content.match(PHOTO_RE)
  if (!match) return <span>{content}</span>

  const before = content.slice(0, match.index)
  const url = match[1].trim()
  const after = content.slice((match.index ?? 0) + match[0].length)

  return (
    <>
      {before && <span>{before}</span>}
      <img
        src={url}
        alt="Photo from Ava"
        className="rounded-xl max-w-full mt-1"
        style={{ maxHeight: 320 }}
      />
      {after && <span>{after}</span>}
    </>
  )
}

export default function ChatBubble({ role, content, timestamp }: ChatBubbleProps) {
  const isUser = role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div
        className={`max-w-[75%] px-4 py-2 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-gradient-to-r from-blue-600 to-violet-600 text-white rounded-br-sm'
            : 'bg-white/5 backdrop-blur-md border border-white/10 text-white rounded-bl-sm'
        }`}
      >
        {renderContent(content)}
        {timestamp && (
          <p className={`text-xs mt-1 ${isUser ? 'text-gray-400' : 'text-gray-400'}`}>
            {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>
    </div>
  )
}
