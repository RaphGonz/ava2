export interface Preferences {
  whatsapp_phone?: string
  preferred_platform?: 'whatsapp' | 'web'
  spiciness_level?: 'mild' | 'spicy' | 'explicit'
  mode_switch_phrase?: string | null
  notif_prefs?: Record<string, unknown>
}

export async function getPreferences(token: string): Promise<Preferences> {
  const res = await fetch('/preferences/', {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (res.status === 404) return {}
  if (!res.ok) throw new Error('Failed to load preferences')
  return res.json()
}

export async function updatePreferences(token: string, patch: Partial<Preferences>): Promise<void> {
  const res = await fetch('/preferences/', {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(patch),
  })
  if (!res.ok) throw new Error('Failed to update preferences')
}

export async function updatePersona(token: string, persona: string): Promise<void> {
  const res = await fetch('/avatars/me/persona', {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ personality: persona }),
  })
  if (!res.ok) throw new Error('Failed to update persona')
}
