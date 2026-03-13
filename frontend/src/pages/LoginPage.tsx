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
import shhhh from '../assets/Shhhh.png'
import writing from '../assets/writing.png'

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
    <div className="min-h-screen flex items-center justify-center bg-black relative overflow-hidden">
      {/* Hero background — same as LandingHero */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `url(${shhhh})`,
              backgroundSize: 'auto 100%',
              backgroundPosition: 'right center',
              backgroundRepeat: 'no-repeat',
              WebkitMaskImage: 'linear-gradient(to left, black 70%, transparent 90%)',
              maskImage: 'linear-gradient(to left, black 70%, transparent 90%)',
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-br from-violet-900/60 to-orange-900/60" />
        </div>
        <img
          src={writing}
          alt=""
          className="absolute left-0 top-0 h-full w-auto pointer-events-none"
          style={{
            zIndex: 5,
            WebkitMaskImage: 'linear-gradient(to right, black 70%, transparent 90%)',
            maskImage: 'linear-gradient(to right, black 70%, transparent 90%)',
          }}
        />
        <div
          className="absolute inset-0 z-10"
          style={{ clipPath: 'polygon(0 0, 65% 0, 35% 100%, 0 100%)' }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-blue-900/80 to-transparent" />
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative z-20 w-full max-w-sm"
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
  )
}
