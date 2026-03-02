/**
 * Avatar API client module.
 * createAvatar: POST /avatars -- called on first (and only) setup during onboarding
 * triggerReferenceImage: POST /avatars/me/reference-image -- fires background job (returns 202)
 * pollForReferenceImage: polls GET /avatars/me until reference_image_url appears
 * getMyAvatar: GET /avatars/me -- used by App.tsx onboarding gate
 *
 * NOTE: No updateAvatar -- avatar is locked after onboarding (user decision).
 * NOTE: triggerReferenceImage replaces the old generateReferenceImage -- the endpoint now
 *       returns 202 immediately; the image URL appears on the avatar row asynchronously.
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
  reference_image_url?: string | null
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

/**
 * Fire-and-forget: tell the backend to start generating the reference image.
 * Returns immediately (202 Accepted). The actual image URL will appear on the
 * avatar row asynchronously -- use pollForReferenceImage() to wait for it.
 */
export async function triggerReferenceImage(token: string): Promise<void> {
  const res = await fetch('/avatars/me/reference-image', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Image generation failed' }))
    throw new Error(err.detail || 'Image generation failed')
  }
  // 202 accepted -- image not ready yet, polling begins
}

/**
 * Poll GET /avatars/me every `intervalMs` milliseconds.
 * When avatar.reference_image_url is non-null, calls onFound(url) and stops polling.
 * If polling exceeds `timeoutMs` (default: 5 minutes), calls onTimeout() and stops.
 *
 * Returns a cleanup function -- call it in useEffect cleanup or on unmount to cancel polling.
 *
 * @param token      Bearer token for the authenticated user
 * @param onFound    Called with the URL when reference_image_url is ready
 * @param onTimeout  Called when polling exceeds timeoutMs without finding the URL
 * @param onError    Called if a polling fetch throws (network error etc.)
 * @param intervalMs Poll interval in ms (default: 3000)
 * @param timeoutMs  Max polling duration in ms (default: 300000 = 5 minutes)
 */
export function pollForReferenceImage(
  token: string,
  onFound: (url: string) => void,
  onTimeout: () => void,
  onError: (err: Error) => void,
  intervalMs = 3000,
  timeoutMs = 300_000,
): () => void {
  const startedAt = Date.now()
  let active = true

  const intervalId = setInterval(async () => {
    if (!active) return

    // Timeout check -- stop polling if we have waited too long
    if (Date.now() - startedAt > timeoutMs) {
      active = false
      clearInterval(intervalId)
      onTimeout()
      return
    }

    try {
      const avatar = await getMyAvatar(token)
      if (avatar?.reference_image_url) {
        active = false
        clearInterval(intervalId)
        onFound(avatar.reference_image_url)
      }
      // null/undefined -- still generating, continue polling
    } catch (err) {
      // Network errors during polling are non-fatal -- log and continue
      // (unless we are past the timeout, which is checked at the top)
      onError(err instanceof Error ? err : new Error(String(err)))
    }
  }, intervalMs)

  // Return cleanup function -- call in useEffect cleanup or Regenerate handler
  return () => {
    active = false
    clearInterval(intervalId)
  }
}
