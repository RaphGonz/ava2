import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export function useChatHistory(token: string | null) {
  return useQuery({
    queryKey: ['chat-history'],
    queryFn: () =>
      fetch('/chat/history', {
        headers: { Authorization: `Bearer ${token}` },
      }).then(r => {
        if (!r.ok) throw new Error('Failed to load history')
        return r.json() as Promise<ChatMessage[]>
      }),
    enabled: !!token,
    refetchInterval: 3000,
  })
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

interface UseSendMessageOptions {
  onError?: (err: unknown) => void
}

export function useSendMessage(token: string | null, options?: UseSendMessageOptions) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (text: string) =>
      fetch('/chat', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      }).then(async r => {
        if (!r.ok) {
          const body = await r.json().catch(() => ({ detail: 'Failed to send message' }))
          throw new ApiError(body.detail || 'Failed to send message', r.status)
        }
        return r.json() as Promise<ChatMessage>  // ChatMessage, not { reply: string }
      }),
    // onMutate: REMOVED — no optimistic hack needed.
    // The server now returns the real user message row immediately.
    // Keeping onMutate alongside onSuccess would create a duplicate bubble:
    //   optimistic id (temp) + real id (from server) = two identical messages until next poll.
    onSuccess: (userMessage: ChatMessage) => {
      // Append the real user message row to the cache immediately.
      // Do NOT call invalidateQueries — that triggers a full refetch which returns
      // the user message but NOT the assistant reply yet (background task still running).
      // The 3s poll in useChatHistory does the honest work of picking up the assistant reply.
      queryClient.setQueryData<ChatMessage[]>(['chat-history'], prev => [
        ...(prev ?? []),
        userMessage,
      ])
    },
    onError: options?.onError,
  })
}
