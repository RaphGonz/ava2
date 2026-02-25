/**
 * Avatar API client module.
 * createAvatar: POST /avatars — called on first (and only) setup during onboarding
 * generateReferenceImage: POST /avatars/me/reference-image — triggers reference image generation
 * getMyAvatar: GET /avatars/me — used by App.tsx onboarding gate
 *
 * NOTE: No updateAvatar — avatar is locked after onboarding (user decision).
 */

export interface AvatarData {
  name: string
  age: number
  personality: string
  physical_description?: string
  gender?: string
  nationality?: string
}

export interface AvatarResponse extends AvatarData {
  id: string
  user_id: string
  created_at: string
  reference_image_url?: string
}

export async function getMyAvatar(token: string): Promise<AvatarResponse | null> {
  const res = await fetch('/avatars/me', {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (res.status === 404) return null
  if (!res.ok) throw new Error('Failed to fetch avatar')
  return res.json()
}

export async function createAvatar(token: string, data: AvatarData): Promise<AvatarResponse> {
  const res = await fetch('/avatars', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || 'Failed to create avatar')
  }
  return res.json()
}

export async function generateReferenceImage(token: string): Promise<{ reference_image_url: string }> {
  const res = await fetch('/avatars/me/reference-image', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Image generation failed' }))
    throw new Error(err.detail || 'Image generation failed')
  }
  return res.json()
}
