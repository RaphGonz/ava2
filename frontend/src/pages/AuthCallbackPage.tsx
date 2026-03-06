/**
 * AuthCallbackPage — dedicated landing page for Supabase OAuth redirects.
 *
 * Supabase redirects here after Google OAuth completes (redirectTo in signInWithOAuth).
 * This page is NOT protected, so React Router won't redirect away from it, giving
 * Supabase time to read the session from the URL hash/code before anything else happens.
 *
 * Flow:
 * 1. Browser loads /auth/callback#access_token=... (or ?code=...)
 * 2. Supabase client processes the URL and fires SIGNED_IN
 * 3. We set auth in Zustand store and navigate to /chat
 */
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import { useAuthStore } from '../store/useAuthStore'

export default function AuthCallbackPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore(s => s.setAuth)

  useEffect(() => {
    // Try immediate session (already processed by supabase singleton on module load)
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        setAuth(data.session.access_token, data.session.user.id)
        navigate('/chat', { replace: true })
      }
    })

    // Also subscribe in case getSession() returns null while processing is still in-flight
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session) {
        setAuth(session.access_token, session.user.id)
        navigate('/chat', { replace: true })
      } else if (event === 'SIGNED_OUT') {
        navigate('/login', { replace: true })
      }
    })

    return () => subscription.unsubscribe()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-gray-400 text-sm">Signing in...</p>
    </div>
  )
}
