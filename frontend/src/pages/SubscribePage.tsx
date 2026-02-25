/**
 * SubscribePage — shown when user tries to chat without an active subscription.
 * POST /billing/checkout → receives Stripe Checkout URL → redirect.
 */
import { useState } from 'react'
import { useAuthStore } from '../store/useAuthStore'
import { createCheckoutSession } from '../api/billing'

export default function SubscribePage() {
  const token = useAuthStore(s => s.token)!
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Read URL params for cancel feedback
  const params = new URLSearchParams(window.location.search)
  const cancelled = params.get('cancelled') === '1'

  const handleSubscribe = async () => {
    setLoading(true)
    setError(null)
    try {
      const { checkout_url } = await createCheckoutSession(token)
      window.location.href = checkout_url
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-gray-900 rounded-2xl p-8 space-y-6 text-center">
        <div>
          <h1 className="text-2xl font-bold">Unlock Ava</h1>
          <p className="text-gray-400 mt-2 text-sm">
            Subscribe to start chatting and receiving photos.
          </p>
        </div>

        {cancelled && (
          <p className="text-yellow-400 text-sm">
            Checkout cancelled — no charge made.
          </p>
        )}

        <div className="bg-gray-800 rounded-xl p-4 space-y-2">
          <p className="text-lg font-semibold">Monthly subscription</p>
          <ul className="text-gray-400 text-sm space-y-1 text-left">
            <li>Unlimited chat in secretary and intimate modes</li>
            <li>AI-generated photos during intimate conversations</li>
            <li>All persona styles included</li>
          </ul>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <button
          onClick={handleSubscribe}
          disabled={loading}
          className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors"
        >
          {loading ? 'Redirecting to checkout...' : 'Subscribe now'}
        </button>

        <p className="text-xs text-gray-500">
          Secure payment via Stripe. Cancel anytime.
        </p>
      </div>
    </div>
  )
}
