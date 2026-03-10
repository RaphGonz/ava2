import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/useAuthStore'
import { getPreferences, updatePreferences, updatePersona, type Preferences } from '../api/preferences'
import { getSubscription } from '../api/billing'
import { signOut } from '../api/auth'
import { GlassCard } from '../components/ui/GlassCard'

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

  const { data: subscription, isLoading: subscriptionLoading } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => getSubscription(token!),
    staleTime: 60 * 1000,
    enabled: !!token,
  })

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

  async function handleSignOut() {
    await signOut()
    useAuthStore.getState().clearAuth()
    navigate('/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <p className="text-slate-400 text-sm">Loading settings...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black">
      <div className="max-w-lg mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <button
            onClick={() => navigate('/chat')}
            className="text-slate-400 hover:text-white transition-colors"
            aria-label="Back to chat"
          >
            &larr; Back
          </button>
          <h1 className="text-xl font-semibold text-white">Settings</h1>
        </div>

        <div className="space-y-6">
          {/* Persona Selector */}
          <GlassCard className="p-5">
            <h2 className="text-sm font-semibold text-white mb-1">Ava's Persona</h2>
            <p className="text-xs text-slate-400 mb-4">Choose Ava's personality</p>
            <div className="grid grid-cols-3 gap-2">
              {PERSONA_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => updatePersona(token!, opt.value).catch(e => setError(e.message))}
                  className="py-2 px-3 rounded-xl text-sm border border-white/10 text-slate-400 hover:border-white/20 hover:text-white bg-white/5 transition-all"
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </GlassCard>

          {/* Platform Preference */}
          <GlassCard className="p-5">
            <h2 className="text-sm font-semibold text-white mb-1">Preferred Platform</h2>
            <p className="text-xs text-slate-400 mb-4">Ava will only reply on your preferred platform</p>
            <div className="flex gap-3">
              {(['whatsapp', 'web'] as const).map(platform => (
                <button
                  key={platform}
                  onClick={() => setPrefs(p => ({ ...p, preferred_platform: platform }))}
                  className={`flex-1 py-2 px-4 rounded-xl text-sm font-medium border transition-all ${
                    prefs.preferred_platform === platform
                      ? 'bg-gradient-to-r from-blue-600 to-violet-600 border-transparent text-white'
                      : 'border-white/10 text-slate-400 hover:border-white/20 hover:text-white bg-white/5'
                  }`}
                >
                  {platform === 'whatsapp' ? 'WhatsApp' : 'Web App'}
                </button>
              ))}
            </div>
          </GlassCard>

          {/* Spiciness Ceiling */}
          <GlassCard className="p-5">
            <h2 className="text-sm font-semibold text-white mb-1">Content Ceiling</h2>
            <p className="text-xs text-slate-400 mb-4">Ava will not escalate beyond this level</p>
            <div className="space-y-2">
              {SPICINESS_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setPrefs(p => ({ ...p, spiciness_level: opt.value }))}
                  className={`w-full flex items-center gap-3 py-3 px-4 rounded-xl text-left border transition-all ${
                    prefs.spiciness_level === opt.value
                      ? 'bg-gradient-to-r from-blue-600 to-violet-600 border-transparent text-white'
                      : 'border-white/10 text-slate-400 hover:border-white/20 hover:text-white bg-white/5'
                  }`}
                >
                  <div>
                    <p className="text-sm font-medium">{opt.label}</p>
                    <p className={`text-xs ${prefs.spiciness_level === opt.value ? 'text-white/70' : 'text-slate-400'}`}>
                      {opt.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </GlassCard>

          {/* Custom Mode-Switch Phrase */}
          <GlassCard className="p-5">
            <h2 className="text-sm font-semibold text-white mb-1">Mode-Switch Phrase</h2>
            <p className="text-xs text-slate-400 mb-3">
              Type this phrase to switch between secretary and intimate mode.
              Leave blank to use the defaults ("I'm alone" / "stop").
              Tip: choose something you wouldn't normally say.
            </p>
            <input
              type="text"
              value={prefs.mode_switch_phrase ?? ''}
              onChange={e => setPrefs(p => ({ ...p, mode_switch_phrase: e.target.value || undefined }))}
              placeholder="e.g. just us now"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white placeholder-gray-500 text-sm focus:outline-none focus:border-blue-500/50"
            />
          </GlassCard>

          {/* Notification Preferences */}
          <GlassCard className="p-5">
            <h2 className="text-sm font-semibold text-white mb-1">WhatsApp Notifications</h2>
            <p className="text-xs text-slate-400 mb-4">Control when Ava reaches out on WhatsApp</p>
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-sm text-slate-300">Enable WhatsApp notifications</span>
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
          </GlassCard>

          {/* Error / Success feedback */}
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
          {saved && <p className="text-green-400 text-sm text-center">Settings saved</p>}

          {/* Subscription section */}
          <GlassCard className="p-5">
            <h2 className="text-sm font-semibold text-white mb-1">Subscription</h2>
            {subscriptionLoading ? (
              <p className="text-slate-400 text-sm">Loading...</p>
            ) : subscription ? (
              <div className="space-y-2">
                <p className="text-sm text-slate-300">
                  Plan: <span className="text-white font-medium">{subscription.plan_name ?? 'Ava Monthly'}</span>
                </p>
                <p className={`text-sm ${subscription.status === 'active' ? 'text-green-400' : 'text-yellow-400'}`}>
                  {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-400">No active subscription.</p>
            )}
            <Link
              to="/billing"
              className="mt-3 inline-block text-sm text-violet-400 hover:text-violet-300 transition-colors"
            >
              Manage Billing →
            </Link>
          </GlassCard>

          {/* Save button */}
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white rounded-xl py-3 text-sm font-medium transition-all disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>

          {/* Sign out button */}
          <button
            onClick={handleSignOut}
            className="w-full bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 rounded-xl py-3 text-sm font-medium transition-colors mt-4"
          >
            Sign out
          </button>
        </div>
      </div>
    </div>
  )
}
