import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/useAuthStore'
import { getPreferences, updatePreferences, updatePersona, type Preferences } from '../api/preferences'

const SPICINESS_OPTIONS = [
  { value: 'mild', label: 'Mild', description: 'Flirty and playful, nothing explicit' },
  { value: 'spicy', label: 'Spicy', description: 'Suggestive and sensual' },
  { value: 'explicit', label: 'Explicit', description: 'Fully adult content' },
] as const

const PERSONA_OPTIONS = [
  { value: 'playful', label: 'Playful' },
  { value: 'dominant', label: 'Dominant' },
  { value: 'shy', label: 'Shy' },
  { value: 'caring', label: 'Caring' },
  { value: 'intellectual', label: 'Intellectual' },
  { value: 'adventurous', label: 'Adventurous' },
] as const

export default function SettingsPage() {
  const token = useAuthStore(s => s.token)
  const navigate = useNavigate()

  const [prefs, setPrefs] = useState<Preferences>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    getPreferences(token)
      .then(setPrefs)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [token])

  async function handleSave() {
    if (!token) return
    setSaving(true)
    setError(null)
    try {
      await updatePreferences(token, {
        preferred_platform: prefs.preferred_platform,
        spiciness_level: prefs.spiciness_level,
        mode_switch_phrase: prefs.mode_switch_phrase ?? undefined,
        notif_prefs: prefs.notif_prefs,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-400 text-sm">Loading settings...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-lg mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <button
            onClick={() => navigate('/chat')}
            className="text-gray-400 hover:text-gray-700 transition-colors"
            aria-label="Back to chat"
          >
            &larr; Back
          </button>
          <h1 className="text-xl font-semibold text-gray-900">Settings</h1>
        </div>

        <div className="space-y-6">
          {/* Persona Selector */}
          <section className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <h2 className="text-sm font-semibold text-gray-900 mb-1">Ava's Persona</h2>
            <p className="text-xs text-gray-500 mb-4">Choose Ava's personality</p>
            <div className="grid grid-cols-3 gap-2">
              {PERSONA_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => updatePersona(token!, opt.value).catch(e => setError(e.message))}
                  className="py-2 px-3 rounded-xl text-sm border border-gray-200 hover:border-gray-900 hover:bg-gray-900 hover:text-white transition-colors"
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </section>

          {/* Platform Preference */}
          <section className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <h2 className="text-sm font-semibold text-gray-900 mb-1">Preferred Platform</h2>
            <p className="text-xs text-gray-500 mb-4">Ava will only reply on your preferred platform</p>
            <div className="flex gap-3">
              {(['whatsapp', 'web'] as const).map(platform => (
                <button
                  key={platform}
                  onClick={() => setPrefs(p => ({ ...p, preferred_platform: platform }))}
                  className={`flex-1 py-2 px-4 rounded-xl text-sm font-medium border transition-colors ${
                    prefs.preferred_platform === platform
                      ? 'bg-gray-900 text-white border-gray-900'
                      : 'bg-white text-gray-700 border-gray-200 hover:border-gray-400'
                  }`}
                >
                  {platform === 'whatsapp' ? 'WhatsApp' : 'Web App'}
                </button>
              ))}
            </div>
          </section>

          {/* Spiciness Ceiling */}
          <section className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <h2 className="text-sm font-semibold text-gray-900 mb-1">Content Ceiling</h2>
            <p className="text-xs text-gray-500 mb-4">Ava will not escalate beyond this level</p>
            <div className="space-y-2">
              {SPICINESS_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setPrefs(p => ({ ...p, spiciness_level: opt.value }))}
                  className={`w-full flex items-center gap-3 py-3 px-4 rounded-xl text-left border transition-colors ${
                    prefs.spiciness_level === opt.value
                      ? 'bg-gray-900 text-white border-gray-900'
                      : 'bg-white text-gray-700 border-gray-200 hover:border-gray-400'
                  }`}
                >
                  <div>
                    <p className="text-sm font-medium">{opt.label}</p>
                    <p className={`text-xs ${prefs.spiciness_level === opt.value ? 'text-gray-300' : 'text-gray-400'}`}>
                      {opt.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </section>

          {/* Custom Mode-Switch Phrase */}
          <section className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <h2 className="text-sm font-semibold text-gray-900 mb-1">Mode-Switch Phrase</h2>
            <p className="text-xs text-gray-500 mb-3">
              Type this phrase to switch between secretary and intimate mode.
              Leave blank to use the defaults ("I'm alone" / "stop").
              Tip: choose something you wouldn't normally say.
            </p>
            <input
              type="text"
              value={prefs.mode_switch_phrase ?? ''}
              onChange={e => setPrefs(p => ({ ...p, mode_switch_phrase: e.target.value || undefined }))}
              placeholder="e.g. just us now"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
            />
          </section>

          {/* Notification Preferences */}
          <section className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
            <h2 className="text-sm font-semibold text-gray-900 mb-1">WhatsApp Notifications</h2>
            <p className="text-xs text-gray-500 mb-4">Control when Ava reaches out on WhatsApp</p>
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-sm text-gray-700">Enable WhatsApp notifications</span>
              <input
                type="checkbox"
                checked={(prefs.notif_prefs as Record<string, unknown>)?.whatsapp_enabled !== false}
                onChange={e => setPrefs(p => ({
                  ...p,
                  notif_prefs: { ...(p.notif_prefs as object ?? {}), whatsapp_enabled: e.target.checked }
                }))}
                className="w-4 h-4 rounded"
              />
            </label>
          </section>

          {/* Error / Success feedback */}
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
          {saved && <p className="text-green-600 text-sm text-center">Settings saved</p>}

          {/* Save button */}
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-gray-900 text-white rounded-xl py-3 text-sm font-medium hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
