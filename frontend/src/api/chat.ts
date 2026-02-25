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
        return r.json() as Promise<{ reply: string }>
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['chat-history'] }),
    onError: options?.onError,
  })
}
