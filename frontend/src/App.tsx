import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { useAuthStore } from './store/useAuthStore'
import LoginPage from './pages/LoginPage'
import ChatPage from './pages/ChatPage'
import SettingsPage from './pages/SettingsPage'
import PhotoPage from './pages/PhotoPage'
import AvatarSetupPage from './pages/AvatarSetupPage'
import SubscribePage from './pages/SubscribePage'
import { getMyAvatar } from './api/avatars'

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
    staleTime: 5 * 60 * 1000, // 5 min cache — re-checks on window focus
    retry: false,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    )
  }

  // No avatar found (404 returns null from getMyAvatar) → send to onboarding
  if (avatar === null) return <Navigate to="/avatar-setup" replace />

  return <>{children}</>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
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
