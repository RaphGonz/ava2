/**
 * Billing API — creates Stripe Checkout session and returns redirect URL.
 */
export async function createCheckoutSession(token: string): Promise<{ checkout_url: string }> {
  const res = await fetch('/billing/checkout', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Billing unavailable' }))
    throw new Error(err.detail || 'Failed to create checkout session')
  }
  return res.json()
}

// ─── Types ───────────────────────────────────────────────────────────────────

export type SubscriptionData = {
  status: 'active' | 'inactive' | 'past_due' | 'canceled' | 'none'
  plan_name?: string
  current_period_end?: string
  cancel_at_period_end?: boolean
  stripe_customer_id?: string
  stripe_subscription_id?: string
}

export type Invoice = {
  date: number        // Unix timestamp
  amount_paid: number // cents
  status: string
  invoice_pdf: string
}

// ─── API Functions ────────────────────────────────────────────────────────────

export async function getSubscription(token: string): Promise<SubscriptionData> {
  const res = await fetch('/billing/subscription', {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Failed to fetch subscription')
  return res.json()
}

export async function getInvoices(token: string): Promise<Invoice[]> {
  const res = await fetch('/billing/invoices', {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) return []
  return res.json()
}

export async function createPortalSession(token: string): Promise<string> {
  // Returns portal URL. Never cache this — call fresh on every button click (Pitfall 4).
  const res = await fetch('/billing/portal-session', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Failed to create billing portal session')
  const data = await res.json()
  return data.portal_url
}

export async function cancelSubscription(
  token: string,
  survey: { q1: string; q2: string }
): Promise<{ cancel_at_period_end: boolean; current_period_end: number }> {
  const res = await fetch('/billing/cancel', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(survey),
  })
  if (!res.ok) throw new Error('Cancellation failed')
  return res.json()
}
