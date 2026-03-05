/**
 * Supabase JS client — used ONLY for Google OAuth sign-in (implicit flow for SPA).
 *
 * This is the one-time exception to the "frontend has no direct Supabase client" rule
 * documented in STATE.md. Do NOT use this client for data queries — those go through
 * the FastAPI backend. This client's sole purpose is to drive the OAuth flow and
 * extract the resulting session.
 *
 * Implicit flow (not PKCE): this is a pure SPA with no SSR. The Supabase JS client
 * with detectSessionInUrl: true automatically reads the access_token from the URL
 * fragment after the Google redirect and stores it in localStorage.
 * Source: https://supabase.com/docs/guides/auth/sessions/implicit-flow
 */
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    '[supabaseClient] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY not set. ' +
    'Google Sign-In and password reset will not work until these are configured.'
  )
}

export const supabase = createClient(supabaseUrl ?? '', supabaseAnonKey ?? '', {
  auth: {
    detectSessionInUrl: true,  // default true — auto-processes OAuth redirect fragments
    persistSession: true,       // stores tokens in localStorage
    autoRefreshToken: true,     // refreshes before expiry
  },
})
