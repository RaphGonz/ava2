/**
 * ResetPasswordPage — Stage 2 of the password reset flow.
 *
 * Supabase redirects the user here as:
 *   /reset-password?token=<token_hash>&type=recovery
 *
 * The supabase-js client with detectSessionInUrl: true auto-detects the recovery
 * session from the URL when the page loads. We then call supabase.auth.updateUser()
 * with the new password.
 *
 * Per CONTEXT.md: expired/used link shows a dedicated error with link back to forgot-password
 * (not redirect to login).
 */
import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { GlassCard } from '../components/ui/GlassCard'
import { supabase } from '../lib/supabaseClient'

export default function ResetPasswordPage() {
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [tokenError, setTokenError] = useState(false)
  const navigate = useNavigate()

  // Detect if the recovery session is valid on mount
  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        // No session = link expired or already used
        setTokenError(true)
      }
    })
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const { error: updateError } = await supabase.auth.updateUser({ password })
      if (updateError) throw updateError
      setSuccess(true)
      // Redirect to login after 2 seconds
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to reset password'
      if (msg.toLowerCase().includes('expired') || msg.toLowerCase().includes('invalid')) {
        setTokenError(true)
      } else {
        setError(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  // Per CONTEXT.md: dedicated error page with link back to forgot-password form
  if (tokenError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-sm"
        >
          <GlassCard className="p-8 text-center">
            <h1 className="text-2xl font-semibold text-white mb-2">Link expired</h1>
            <p className="text-slate-400 text-sm mb-6">
              This reset link has expired or has already been used.
              Password reset links are valid for 5 minutes.
            </p>
            <Link
              to="/forgot-password"
              className="inline-block bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white rounded-lg py-2 px-6 text-sm font-medium transition-all"
            >
              Request a new link
            </Link>
          </GlassCard>
        </motion.div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-sm"
        >
          <GlassCard className="p-8 text-center">
            <h1 className="text-2xl font-semibold text-white mb-2">Password updated</h1>
            <p className="text-slate-400 text-sm">Redirecting you to sign in...</p>
          </GlassCard>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-black">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-sm"
      >
        <GlassCard className="p-8">
          <h1 className="text-2xl font-semibold text-white mb-1">Choose a new password</h1>
          <p className="text-slate-400 text-sm mb-6">Must be at least 8 characters.</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">New password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={8}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50"
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Confirm password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                required
                minLength={8}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50"
                placeholder="••••••••"
              />
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white rounded-lg py-2 text-sm font-medium transition-all disabled:opacity-50"
            >
              {loading ? 'Updating...' : 'Update password'}
            </button>
          </form>
        </GlassCard>
      </motion.div>
    </div>
  )
}
