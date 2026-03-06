/**
 * GoogleSignInButton — reusable Google OAuth sign-in button.
 *
 * Follows Google Sign-In branding guidelines (white button, Google G icon, "Continue with Google").
 * Used on both LoginPage and SignupPage per CONTEXT.md locked decision.
 * After click: redirects to Google → returns to / → App.tsx onAuthStateChange extracts session.
 */
import { supabase } from '../lib/supabaseClient'

interface Props {
  /** Called with an error message if the OAuth initiation fails (e.g. popup blocked) */
  onError: (message: string) => void
  disabled?: boolean
}

export function GoogleSignInButton({ onError, disabled }: Props) {
  async function handleClick() {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        // redirectTo must be whitelisted in Supabase Dashboard -> Auth -> URL Configuration
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    if (error) {
      // Per CONTEXT.md: inline error below the button
      onError('Google sign-in was cancelled. Try again or use email/password.')
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      className="w-full flex items-center justify-center gap-3 border border-gray-200 rounded-lg py-2 px-4 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
    >
      {/* Google's official G logo SVG */}
      <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
        <path
          fill="#4285F4"
          d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"
        />
        <path
          fill="#34A853"
          d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z"
        />
        <path
          fill="#FBBC05"
          d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707s.102-1.167.282-1.707V4.961H.957C.347 6.175 0 7.55 0 9s.348 2.826.957 4.039l3.007-2.332z"
        />
        <path
          fill="#EA4335"
          d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.961L3.964 7.293C4.672 5.166 6.656 3.58 9 3.58z"
        />
      </svg>
      Continue with Google
    </button>
  )
}
