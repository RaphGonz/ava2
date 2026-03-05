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
import { signIn } from '../api/auth'
import { useAuthStore } from '../store/useAuthStore'
import { GoogleSignInButton } from '../components/GoogleSignInButton'
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 w-full max-w-sm">
        <h1 className="text-2xl font-semibold text-gray-900 mb-1">Welcome back</h1>
        <p className="text-gray-500 text-sm mb-6">Sign in to chat with Ava</p>

        {/* Google Sign-In — above email/password form per CONTEXT.md locked decision */}
        <GoogleSignInButton onError={setGoogleError} />
        {googleError && (
          <p className="text-red-500 text-xs mt-2">{googleError}</p>
        )}

        {/* "or" divider */}
        <div className="flex items-center gap-3 my-5">
          <div className="flex-1 h-px bg-gray-100" />
          <span className="text-xs text-gray-400">or</span>
          <div className="flex-1 h-px bg-gray-100" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
              placeholder="••••••••"
            />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gray-900 text-white rounded-lg py-2 text-sm font-medium hover:bg-gray-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <div className="flex items-center justify-between mt-5 text-sm text-gray-500">
          {/*
            CONTEXT.md locked decision: hide Forgot password link for Google-only accounts.
            isGoogleOnlyUser=true when identities contains google but NOT email (checked on mount).
            Linked accounts (both google + email identities) DO see the link — they have a password.
          */}
          {!isGoogleOnlyUser && (
            <Link to="/forgot-password" className="hover:text-gray-700 hover:underline">
              Forgot password?
            </Link>
          )}
          <Link
            to="/signup"
            className={`text-gray-900 font-medium hover:underline ${isGoogleOnlyUser ? 'ml-auto' : ''}`}
          >
            Create account
          </Link>
        </div>
      </div>
    </div>
  )
}
