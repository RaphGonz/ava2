import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { useAuthStore } from './store/useAuthStore'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import ChatPage from './pages/ChatPage'
import SettingsPage from './pages/SettingsPage'
import PhotoPage from './pages/PhotoPage'
import AvatarSetupPage from './pages/AvatarSetupPage'
import SubscribePage from './pages/SubscribePage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import AuthCallbackPage from './pages/AuthCallbackPage'
import { getMyAvatar } from './api/avatars'
import { supabase } from './lib/supabaseClient'

const queryClient = new QueryClient()

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

/**
 * OnboardingGate — wraps /chat and /settings.
 * Redirects to /avatar-setup if user has not yet created an avatar.
 * Uses React Query with queryKey ['avatar'] so AvatarSetupPage can invalidate it on completion.
 */
function OnboardingGate({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token)!
  const { data: avatar, isLoading } = useQuery({
    queryKey: ['avatar'],
    queryFn: () => getMyAvatar(token),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    )
  }

  if (avatar === null) return <Navigate to="/avatar-setup" replace />

  return <>{children}</>
}

/**
 * AuthBridge — subscribes to Supabase auth state changes to handle Google OAuth redirects.
 *
 * After a Google OAuth sign-in, Supabase redirects the user back to / with an access_token
 * in the URL fragment. The @supabase/supabase-js client (detectSessionInUrl: true) auto-reads
 * the fragment and emits SIGNED_IN. This component bridges that session into the Zustand store
 * (useAuthStore.setAuth) so the rest of the app works identically to email/password auth.
 *
 * New Google signup detection: if provider=google AND created_at < 60s ago, call
 * POST /auth/send-welcome to trigger the welcome email (Pitfall 5 fix from RESEARCH.md).
 */
function AuthBridge() {
  const setAuth = useAuthStore(s => s.setAuth)
  const navigate = useNavigate()

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session) {
        const { access_token } = session
        const user_id = session.user.id

        // Populate the Zustand store — same interface as email/password auth (Pitfall 8 fix)
        setAuth(access_token, user_id)

        // After OAuth redirect, the user ends up on /login (ProtectedRoute redirected them
        // before the store was populated). Navigate to /chat to complete the sign-in.
        const path = window.location.pathname
        if (path === '/login' || path === '/') {
          navigate('/chat', { replace: true })
        }

        // Detect new Google signup and trigger welcome email (EMAI-02 Google path)
        const isGoogle = session.user.app_metadata?.provider === 'google'
        const createdAt = new Date(session.user.created_at ?? 0)
        const isNewUser = (Date.now() - createdAt.getTime()) < 60_000

        if (isGoogle && isNewUser) {
          // Best-effort — fire and forget, non-blocking
          fetch('/auth/send-welcome', {
            method: 'POST',
            headers: { Authorization: `Bearer ${access_token}` },
          }).catch(err => {
            console.warn('[AuthBridge] send-welcome failed (non-blocking):', err)
          })
        }
      }
    })

    return () => subscription.unsubscribe()
  }, [setAuth, navigate])

  return null
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthBridge />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route
            path="/avatar-setup"
            element={<ProtectedRoute><AvatarSetupPage /></ProtectedRoute>}
          />
          <Route
            path="/subscribe"
            element={<ProtectedRoute><SubscribePage /></ProtectedRoute>}
          />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <OnboardingGate>
                  <ChatPage />
                </OnboardingGate>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <OnboardingGate>
                  <SettingsPage />
                </OnboardingGate>
              </ProtectedRoute>
            }
          />
          <Route path="/photo" element={<PhotoPage />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
