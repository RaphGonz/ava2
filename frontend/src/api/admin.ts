/**
 * Admin API — fetches operator metrics from GET /admin/metrics.
 * Endpoint is admin-only (backend raises 403 for non-admins).
 * AdminRoute guard prevents non-admin users from ever calling this.
 */

export type MetricWindow = {
  d7: number
  d30: number
  all: number
}

export type AdminMetrics = {
  active_users: MetricWindow
  messages_sent: MetricWindow
  photos_generated: MetricWindow
  active_subscriptions: MetricWindow
  new_signups: MetricWindow
  fetched_at: string  // ISO datetime string — displayed as last-updated timestamp
}

export async function getAdminMetrics(token: string): Promise<AdminMetrics> {
  const res = await fetch('/admin/metrics', {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch metrics' }))
    throw new Error(err.detail || `Admin metrics fetch failed: ${res.status}`)
  }
  return res.json()
}
