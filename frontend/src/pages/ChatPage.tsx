import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/useAuthStore'
import { useChatHistory, useSendMessage, ApiError } from '../api/chat'
import { getMyAvatar } from '../api/avatars'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'

export default function ChatPage() {
  const token = useAuthStore(s => s.token)
  const [subscriptionRequired, setSubscriptionRequired] = useState(false)

  const { data: avatar } = useQuery({
    queryKey: ['avatar'],
    queryFn: () => getMyAvatar(token!),
    staleTime: 5 * 60 * 1000,
  })

  const { data: messages = [], isLoading } = useChatHistory(token)
  const sendMutation = useSendMessage(token, {
    onError: (err: unknown) => {
      if (err instanceof ApiError && err.status === 402) {
        setSubscriptionRequired(true)
      }
    },
  })

  function handleSend(text: string) {
    sendMutation.mutate(text)
  }

  return (
    <div className="h-screen flex flex-col bg-black">
      {/* Header */}
      <div className="flex items-center px-4 py-3 border-b border-white/10 bg-black/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          {avatar?.reference_image_url ? (
            <img
              src={avatar.reference_image_url}
              alt={avatar.name ?? 'Ava'}
              className="w-9 h-9 rounded-full object-cover"
            />
          ) : (
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-orange-500 flex items-center justify-center text-white text-sm font-bold">
              A
            </div>
          )}
          <div>
            <p className="text-sm font-semibold">
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-orange-400">
                {avatar?.name ?? 'Ava'}
              </span>
            </p>
            <div className="flex items-center gap-1.5">
              <div className="relative flex">
                <div className="w-2 h-2 rounded-full bg-green-400" />
                <div className="absolute inset-0 rounded-full bg-green-400 animate-ping opacity-75" />
              </div>
              <p className="text-xs text-slate-400">Online</p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* Subscription required banner */}
      {subscriptionRequired && (
        <div className="bg-white/5 border border-white/10 rounded-lg p-3 mx-4 mb-2 flex items-center justify-between">
          <p className="text-slate-300 text-sm">Subscription required to send messages.</p>
          <a
            href="/subscribe"
            className="text-violet-400 underline text-sm font-medium ml-4 whitespace-nowrap"
          >
            Subscribe
          </a>
        </div>
      )}

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={sendMutation.isPending} />
    </div>
  )
}
