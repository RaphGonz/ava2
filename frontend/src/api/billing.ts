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
