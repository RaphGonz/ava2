/**
 * AvatarSetupPage -- shown once during onboarding (before /chat access).
 * Avatar is locked after this step -- it cannot be modified post-signup.
 *
 * Flow per CONTEXT.md locked decision:
 *   1. User fills in avatar details (all four AVTR-01 through AVTR-04 fields)
 *   2. Submit -> createAvatar -> triggerReferenceImage (POST returns 202 immediately)
 *   3. Poll GET /avatars/me every 3s -- show "Generating your Ava..." spinner
 *   4. When reference_image_url appears: display image with Regenerate/Approve buttons
 *   5. User approves -> navigate to /chat (avatar query invalidated)
 *
 * GAP-3 fix: the old flow called generateReferenceImage() which awaited the image URL
 * synchronously (60-120s). Nginx proxy_read_timeout (60s) killed the connection before
 * ComfyUI finished. Now we fire-and-forget and poll.
 */
import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/useAuthStore'
import {
  createAvatar,
  triggerReferenceImage,
  pollForReferenceImage,
  type AvatarData,
} from '../api/avatars'

const PERSONALITIES = [
  { value: 'playful', label: 'Playful' },
  { value: 'dominant', label: 'Dominant' },
  { value: 'shy', label: 'Shy' },
  { value: 'caring', label: 'Caring' },
  { value: 'intellectual', label: 'Intellectual' },
  { value: 'adventurous', label: 'Adventurous' },
]

export default function AvatarSetupPage() {
  const token = useAuthStore(s => s.token)!
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [form, setForm] = useState<AvatarData>({
    name: '',
    age: 25,
    personality: 'caring',
    gender: '',
    nationality: '',
    physical_description: '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [referenceImageUrl, setReferenceImageUrl] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)

  // Ref to store the polling cleanup function -- allows Regenerate to cancel active poll
  const stopPollingRef = useRef<(() => void) | null>(null)

  const handleChange = (field: keyof AvatarData, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      // Create avatar (one-time -- locked after this step)
      await createAvatar(token, form)
      // Trigger reference image generation and start polling
      await handleGenerateReference()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setSaving(false)
    }
  }

  const handleGenerateReference = async () => {
    // Cancel any active polling loop before starting a new one (Regenerate case)
    if (stopPollingRef.current) {
      stopPollingRef.current()
      stopPollingRef.current = null
    }

    setGenerating(true)
    setError(null)
    // Clear the previous image so the spinner shows during re-generation
    setReferenceImageUrl(null)

    try {
      // Fire-and-forget POST -- backend returns 202 immediately, ComfyUI runs in background
      await triggerReferenceImage(token)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Image generation failed')
      setGenerating(false)
      return
    }

    // Start polling GET /avatars/me every 3 seconds (5-minute timeout)
    const cleanup = pollForReferenceImage(
      token,
      // onFound: image is ready
      (url: string) => {
        setReferenceImageUrl(url)
        setGenerating(false)
        stopPollingRef.current = null
      },
      // onTimeout: 5 minutes elapsed without image
      () => {
        setError('Generation timed out -- please try again')
        setGenerating(false)
        stopPollingRef.current = null
      },
      // onError: network error during polling (non-fatal, polling continues)
      (_err: Error) => {
        // Polling continues -- transient network errors are expected
        // Only show error to user on timeout or trigger failure
      },
    )
    stopPollingRef.current = cleanup
  }

  const handleApprove = async () => {
    // Cancel any active polling loop before navigating away
    if (stopPollingRef.current) {
      stopPollingRef.current()
      stopPollingRef.current = null
    }
    // Invalidate avatar query so App.tsx gate sees the new avatar and routes to /chat
    // (RESEARCH.md Pitfall 7: cache invalidation prevents redirect loop)
    await queryClient.invalidateQueries({ queryKey: ['avatar'] })
    navigate('/chat', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-gray-900 rounded-2xl p-8 space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Meet your Ava</h1>
          <p className="text-gray-400 mt-1 text-sm">
            Describe your companion -- we'll generate her look and you can adjust until it's perfect.
          </p>
        </div>

        {/* Generating spinner -- shown after form submission while polling */}
        {generating && (
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-300 text-sm">Generating your Ava...</p>
            <p className="text-gray-500 text-xs">This takes about 60-90 seconds</p>
          </div>
        )}

        {/* Avatar form -- hidden while generating or after image is ready */}
        {!generating && !referenceImageUrl && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
              <input
                type="text"
                required
                value={form.name}
                onChange={e => handleChange('name', e.target.value)}
                placeholder="e.g. Ava"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Age (20+)</label>
                <input
                  type="number"
                  required
                  min={20}
                  max={99}
                  value={form.age}
                  onChange={e => handleChange('age', parseInt(e.target.value, 10))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Gender</label>
                <input
                  type="text"
                  value={form.gender || ''}
                  onChange={e => handleChange('gender', e.target.value)}
                  placeholder="e.g. woman"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Nationality / Ethnicity</label>
              <input
                type="text"
                value={form.nationality || ''}
                onChange={e => handleChange('nationality', e.target.value)}
                placeholder="e.g. French, Japanese, Brazilian..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Appearance</label>
              <textarea
                value={form.physical_description || ''}
                onChange={e => handleChange('physical_description', e.target.value)}
                placeholder="e.g. dark wavy hair, brown eyes, athletic build, casual style..."
                rows={3}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Personality</label>
              <div className="grid grid-cols-3 gap-2">
                {PERSONALITIES.map(p => (
                  <button
                    key={p.value}
                    type="button"
                    onClick={() => handleChange('personality', p.value)}
                    className={`py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                      form.personality === p.value
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <p className="text-red-400 text-sm">{error}</p>
            )}

            <button
              type="submit"
              disabled={saving || !form.name}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors"
            >
              {saving ? 'Creating your Ava...' : 'Create Ava & Generate Photo'}
            </button>
          </form>
        )}

        {/* Reference image preview + approve/regenerate loop */}
        {!generating && referenceImageUrl && (
          <div className="space-y-4">
            <p className="text-sm text-gray-400">
              Here's your Ava -- approve this look or regenerate until you're happy.
            </p>
            <img
              src={referenceImageUrl}
              alt="Your Ava reference"
              className="w-full rounded-xl object-cover aspect-[2/3]"
            />
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <div className="flex gap-3">
              <button
                onClick={handleGenerateReference}
                disabled={generating}
                className="flex-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white font-medium py-3 rounded-xl transition-colors"
              >
                Regenerate
              </button>
              <button
                onClick={handleApprove}
                className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 rounded-xl transition-colors"
              >
                Looks perfect
              </button>
            </div>
          </div>
        )}

        {/* Error state when generation failed (and not currently generating) */}
        {!generating && !referenceImageUrl && error && (
          <div className="space-y-3">
            <p className="text-red-400 text-sm">{error}</p>
            <button
              onClick={handleGenerateReference}
              className="w-full bg-gray-700 hover:bg-gray-600 text-white font-medium py-3 rounded-xl transition-colors"
            >
              Try again
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
