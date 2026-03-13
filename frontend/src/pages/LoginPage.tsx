/**
 * LoginPage
 *
 * CONTEXT.md locked decision: "Forgot password link is hidden or disabled for users
 * who signed up via Google."
 *
 * Implementation: on mount, call supabase.auth.getSession(). If a session exists and
 * the user's identities array contains ONLY provider='google' (no 'email' identity),
 * set isGoogleOnlyUser=true and hide the Forgot password link.
 *
 * This follows RESEARCH.md Pitfall 2 detection pattern: check identities array, not
 * app_metadata.provider, because a linked account would have both identities present.
 */
import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { signIn } from '../api/auth'
import { useAuthStore } from '../store/useAuthStore'
import { GoogleSignInButton } from '../components/GoogleSignInButton'
import { GlassCard } from '../components/ui/GlassCard'
import { supabase } from '../lib/supabaseClient'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [googleError, setGoogleError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  // Per CONTEXT.md: hide Forgot password link for Google-only accounts (no email identity)
  const [isGoogleOnlyUser, setIsGoogleOnlyUser] = useState(false)
  const setAuth = useAuthStore(s => s.setAuth)
  const navigate = useNavigate()

  useEffect(() => {
    // If there's already an active Supabase session, the user just completed OAuth
    // (or is already logged in). Redirect immediately — don't render the login form.
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        setAuth(data.session.access_token, data.session.user.id)
        navigate('/chat', { replace: true })
        return
      }
    })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // Detect if the currently-stored session (if any) belongs to a Google-only account.
    // A Google-only account has identities containing only provider='google' — no 'email' identity.
    // If both exist (linked account), the user does have a password, so show the link.
    supabase.auth.getSession().then(({ data }) => {
      const identities = data.session?.user?.identities ?? []
      const hasEmailIdentity = identities.some(id => id.provider === 'email')
      const hasGoogleIdentity = identities.some(id => id.provider === 'google')
      if (hasGoogleIdentity && !hasEmailIdentity) {
        setIsGoogleOnlyUser(true)
      }
    })
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { access_token, user_id } = await signIn(email, password)
      setAuth(access_token, user_id)
      navigate('/chat')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Sign in failed'
      // Per CONTEXT.md: specific message for Google-only accounts (no password set)
      if (msg.toLowerCase().includes('invalid') || msg.includes('no password')) {
        setError('This account was created with Google. Please sign in with Google.')
      } else {
        setError(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-black text-white">
      <nav className="w-full bg-black/80 backdrop-blur-sm border-b border-white/5">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold tracking-tight text-white">Avasecret</Link>
          <div className="flex items-center gap-4">
            <a href="https://www.instagram.com/ava.secret.ia/" target="_blank" rel="noopener noreferrer" aria-label="Instagram" className="text-slate-400 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
              </svg>
            </a>
            <a href="https://www.tiktok.com/@avasecret.ia" target="_blank" rel="noopener noreferrer" aria-label="TikTok" className="text-slate-400 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.18 8.18 0 0 0 4.78 1.52V6.75a4.85 4.85 0 0 1-1.01-.06z"/>
              </svg>
            </a>
          </div>
        </div>
      </nav>

      <div className="flex-1 flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-sm"
      >
        <GlassCard className="p-8">
          <h1 className="text-2xl font-semibold text-white mb-1">Welcome back</h1>
          <p className="text-slate-400 text-sm mb-6">Sign in to chat with Ava</p>

          {/* Google Sign-In — above email/password form per CONTEXT.md locked decision */}
          <GoogleSignInButton onError={setGoogleError} />
          {googleError && (
            <p className="text-red-500 text-xs mt-2">{googleError}</p>
          )}

          {/* "or" divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-xs text-slate-500">or</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
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
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="flex items-center justify-between mt-5 text-sm text-slate-400">
            {/*
              CONTEXT.md locked decision: hide Forgot password link for Google-only accounts.
              isGoogleOnlyUser=true when identities contains google but NOT email (checked on mount).
              Linked accounts (both google + email identities) DO see the link — they have a password.
            */}
            {!isGoogleOnlyUser && (
              <Link to="/forgot-password" className="hover:text-white transition-colors hover:underline">
                Forgot password?
              </Link>
            )}
            <Link
              to="/signup"
              className={`text-white font-medium hover:underline ${isGoogleOnlyUser ? 'ml-auto' : ''}`}
            >
              Create account
            </Link>
          </div>
        </GlassCard>
      </motion.div>
      </div>
    </div>
  )
}
