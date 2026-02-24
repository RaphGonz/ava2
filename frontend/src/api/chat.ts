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

export function useSendMessage(token: string | null) {
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
      }).then(r => {
        if (!r.ok) throw new Error('Failed to send message')
        return r.json() as Promise<{ reply: string }>
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['chat-history'] }),
  })
}
