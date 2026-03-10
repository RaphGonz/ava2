import { Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/useAuthStore'
import { GlassCard } from '../components/ui/GlassCard'
import { getAdminMetrics } from '../api/admin'
import type { MetricWindow } from '../api/admin'

// ─── AdminRoute Guard ─────────────────────────────────────────────────────────
// Only checks that a token exists. Actual admin enforcement is backend-only:
// GET /admin/metrics returns 403 for non-admins — AdminPage redirects on error.
// Avoids fragile client-side JWT decoding (app_metadata may not be in token payload).
export function AdminRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

// ─── StatCard ─────────────────────────────────────────────────────────────────

function StatCard({ title, metric }: { title: string; metric: MetricWindow }) {
  return (
    <GlassCard>
      <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-4">
        {title}
      </h3>
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-400">7 days</span>
          <span className="text-lg font-semibold text-white">{metric.d7.toLocaleString()}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-400">30 days</span>
          <span className="text-lg font-semibold text-white">{metric.d30.toLocaleString()}</span>
        </div>
        <div className="flex justify-between items-center border-t border-white/10 pt-2 mt-2">
          <span className="text-sm text-gray-400">All time</span>
          <span className="text-lg font-semibold text-white">{metric.all.toLocaleString()}</span>
        </div>
      </div>
    </GlassCard>
  )
}

// ─── AdminPage ────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const token = useAuthStore(s => s.token)!
  const { data: metrics, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: () => getAdminMetrics(token),
    staleTime: 0,              // Always fetch fresh on mount
    refetchOnWindowFocus: false, // Manual refresh only — no auto-polling
    retry: false,
    throwOnError: false,
  })

  // Backend is the source of truth for admin access — redirect silently on 403.
  // Wait for isLoading to be false before redirecting: cached error state from a
  // previous session must not fire before the fresh fetch completes.
  if (!isLoading && isError) return <Navigate to="/chat" replace />

  function formatFetchedAt(iso: string): string {
    try {
      return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } catch {
      return iso
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6 md:p-8">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
          {metrics?.fetched_at && (
            <p className="text-sm text-gray-400 mt-1">
              Last updated: {formatFetchedAt(metrics.fetched_at)}
            </p>
          )}
        </div>
        <button
          onClick={() => refetch()}
          className="text-sm text-gray-400 hover:text-white transition-colors px-3 py-1 rounded-lg border border-white/10 hover:border-white/30"
        >
          Refresh
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <GlassCard key={i}>
              <div className="animate-pulse space-y-3">
                <div className="h-3 bg-white/10 rounded w-2/3" />
                <div className="h-6 bg-white/10 rounded w-1/2" />
                <div className="h-6 bg-white/10 rounded w-1/2" />
                <div className="h-6 bg-white/10 rounded w-1/2" />
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      {/* Metric cards grid */}
      {metrics && !isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard title="Active Users" metric={metrics.active_users} />
          <StatCard title="Messages Sent" metric={metrics.messages_sent} />
          <StatCard title="Photos Generated" metric={metrics.photos_generated} />
          <StatCard title="Active Subscriptions" metric={metrics.active_subscriptions} />
          <StatCard title="New Signups" metric={metrics.new_signups} />
        </div>
      )}
    </div>
  )
}
