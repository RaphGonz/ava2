import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'
import { useChatHistory, useSendMessage } from '../api/chat'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'

export default function ChatPage() {
  const token = useAuthStore(s => s.token)
  const clearAuth = useAuthStore(s => s.clearAuth)
  const navigate = useNavigate()

  const { data: messages = [], isLoading } = useChatHistory(token)
  const sendMutation = useSendMessage(token)

  function handleSend(text: string) {
    sendMutation.mutate(text)
  }

  function handleSignOut() {
    clearAuth()
    navigate('/login')
  }

  return (
    <div className="h-screen flex flex-col bg-white max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gray-900 flex items-center justify-center text-white text-xs font-semibold">
            A
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">Ava</p>
            <p className="text-xs text-gray-400">Your AI companion</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/settings')}
            className="text-gray-400 hover:text-gray-700 text-sm px-2 py-1 rounded transition-colors"
          >
            Settings
          </button>
          <button
            onClick={handleSignOut}
            className="text-gray-400 hover:text-gray-700 text-sm px-2 py-1 rounded transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>

      {/* Messages */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={sendMutation.isPending} />
    </div>
  )
}
