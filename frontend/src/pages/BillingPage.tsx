import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/useAuthStore'
import {
  getSubscription,
  getInvoices,
  createPortalSession,
  createCheckoutSession,
} from '../api/billing'
import { GlassCard } from '../components/ui/GlassCard'
import { CreditCard, Calendar, ExternalLink, X } from 'lucide-react'
import { Link } from 'react-router-dom'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function formatStatus(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1)
}

// ─── BillingPage ─────────────────────────────────────────────────────────────

export default function BillingPage() {
  const token = useAuthStore(s => s.token)!

  // Cancel flow state — Plan 03 will implement step logic
  const [cancelStep, setCancelStep] = useState<
    'idle' | 'survey-q1' | 'survey-q2' | 'confirming' | 'cancelled'
  >('idle')

  // Upgrade modal state
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)

  // Portal loading/error state
  const [portalLoading, setPortalLoading] = useState(false)
  const [portalError, setPortalError] = useState<string | null>(null)

  // Checkout loading state (for Upgrade modal)
  const [checkoutLoading, setCheckoutLoading] = useState(false)

  // Subscription query — staleTime 60s allows refetch on window focus after Stripe Portal session
  const {
    data: subscription,
    isLoading: subLoading,
  } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => getSubscription(token),
    staleTime: 60 * 1000,
    // refetchOnWindowFocus is TRUE by default — do NOT disable
  })

  // Invoices query — 5 min staleTime (invoices change less frequently)
  const {
    data: invoices,
    isLoading: invoicesLoading,
  } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => getInvoices(token),
    staleTime: 5 * 60 * 1000,
  })

  // ─── Handlers ──────────────────────────────────────────────────────────────

  async function handleManageBilling() {
    setPortalError(null)
    setPortalLoading(true)
    try {
      const url = await createPortalSession(token)
      window.open(url, '_blank')
    } catch {
      setPortalError('Could not open billing portal. Please try again.')
    } finally {
      setPortalLoading(false)
    }
  }

  async function handleResubscribe() {
    setPortalError(null)
    setPortalLoading(true)
    try {
      const url = await createPortalSession(token)
      window.open(url, '_blank')
    } catch {
      setPortalError('Could not open billing portal. Please try again.')
    } finally {
      setPortalLoading(false)
    }
  }

  async function handleCheckout() {
    setCheckoutLoading(true)
    try {
      const { checkout_url } = await createCheckoutSession(token)
      window.location.href = checkout_url
    } catch {
      setCheckoutLoading(false)
    }
  }

  function handleCancelClick() {
    // Cancel flow implemented in Plan 03
    console.log('[BillingPage] Cancel clicked — Plan 03 will implement this flow')
    // TODO: Plan 03 — implement cancel survey flow using setCancelStep
    void setCancelStep // suppress unused variable warning
  }

  // ─── Render ────────────────────────────────────────────────────────────────

  const hasNoSubscription =
    !subLoading && (!subscription || subscription.status === 'none')

  const isActive = subscription?.status === 'active'
  const isCancellingAtPeriodEnd = isActive && subscription?.cancel_at_period_end === true

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-2xl mx-auto px-4 py-12">
        <h1 className="text-2xl font-semibold mb-8 flex items-center gap-2">
          <CreditCard className="w-6 h-6 text-violet-400" />
          Billing
        </h1>

        {/* ── Cancel flow placeholder (Plan 03) ── */}
        {cancelStep !== 'idle' && (
          <div className="mb-6 p-4 rounded-xl bg-white/5 border border-white/10 text-gray-400">
            Cancel flow coming in Plan 03
          </div>
        )}

        {/* ── Subscription Info ── */}
        <GlassCard className="bg-white/5 border-white/10 mb-6">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-4">
            Current Plan
          </h2>

          {subLoading ? (
            /* Skeleton */
            <div className="space-y-3 animate-pulse">
              <div className="h-5 bg-white/10 rounded w-1/3" />
              <div className="h-4 bg-white/10 rounded w-1/4" />
              <div className="h-4 bg-white/10 rounded w-2/5" />
            </div>
          ) : hasNoSubscription ? (
            <div className="space-y-3">
              <p className="text-gray-400">No active subscription.</p>
              <Link
                to="/subscribe"
                className="text-sm text-violet-400 hover:text-violet-300 underline"
              >
                Subscribe to Ava Monthly
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Plan name */}
              <div className="flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-violet-400" />
                <span className="font-medium">
                  {subscription?.plan_name ?? 'Ava Monthly'}
                </span>
              </div>

              {/* Status */}
              <div className="flex items-center gap-2">
                <span
                  className={`text-sm ${
                    isActive ? 'text-green-400' : 'text-yellow-400'
                  }`}
                >
                  {formatStatus(subscription?.status ?? '')}
                </span>
              </div>

              {/* Next billing date */}
              {subscription?.current_period_end && (
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Calendar className="w-4 h-4" />
                  {isCancellingAtPeriodEnd ? (
                    <span>
                      Access until{' '}
                      <span className="text-gray-300">
                        {formatDate(subscription.current_period_end)}
                      </span>
                    </span>
                  ) : (
                    <span>
                      Next billing:{' '}
                      <span className="text-gray-300">
                        {formatDate(subscription.current_period_end)}
                      </span>
                    </span>
                  )}
                </div>
              )}

              {/* Resubscribe notice */}
              {isCancellingAtPeriodEnd && subscription?.current_period_end && (
                <p className="text-sm text-gray-400 mt-1">
                  Your subscription will end on{' '}
                  <span className="text-gray-300">
                    {formatDate(subscription.current_period_end)}
                  </span>
                  . You'll keep access until then.
                </p>
              )}
            </div>
          )}
        </GlassCard>

        {/* ── Action Buttons ── */}
        {!subLoading && !hasNoSubscription && (
          <div className="flex flex-col gap-3 mb-6">
            {/* Manage billing */}
            <button
              onClick={handleManageBilling}
              disabled={portalLoading}
              className="px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 disabled:opacity-60 disabled:cursor-not-allowed font-medium transition-colors"
            >
              {portalLoading ? 'Opening portal…' : 'Manage billing'}
            </button>

            {/* Upgrade */}
            <button
              onClick={() => setUpgradeModalOpen(true)}
              className="px-5 py-2.5 rounded-xl border border-violet-500 text-violet-400 hover:bg-violet-500/10 font-medium transition-colors"
            >
              Upgrade
            </button>

            {/* Portal error */}
            {portalError && (
              <p className="text-sm text-red-400">{portalError}</p>
            )}

            {/* Cancel or Resubscribe */}
            {isActive && !isCancellingAtPeriodEnd && (
              <button
                onClick={handleCancelClick}
                className="text-sm text-gray-500 hover:text-gray-300 underline mt-4 self-start"
              >
                Cancel subscription
              </button>
            )}

            {isCancellingAtPeriodEnd && (
              <button
                onClick={handleResubscribe}
                disabled={portalLoading}
                className="text-sm text-gray-500 hover:text-gray-300 underline mt-4 self-start disabled:opacity-60"
              >
                Resubscribe
              </button>
            )}
          </div>
        )}

        {/* ── Invoice History ── */}
        <GlassCard className="bg-white/5 border-white/10">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-4">
            Invoice history
          </h2>

          {invoicesLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-4 bg-white/10 rounded w-full" />
              <div className="h-4 bg-white/10 rounded w-full" />
              <div className="h-4 bg-white/10 rounded w-3/4" />
            </div>
          ) : !invoices || invoices.length === 0 ? (
            <p className="text-gray-500 text-sm">No invoices yet.</p>
          ) : (
            <div className="space-y-3">
              {invoices.map((inv, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between py-2 border-b border-white/5 last:border-0"
                >
                  <div className="flex items-center gap-4 text-sm">
                    {/* Date */}
                    <span className="text-gray-300">
                      {new Date(inv.date * 1000).toLocaleDateString()}
                    </span>
                    {/* Amount */}
                    <span className="text-white font-medium">
                      ${(inv.amount_paid / 100).toFixed(2)}
                    </span>
                    {/* Status badge */}
                    <span
                      className={`text-xs ${
                        inv.status === 'paid'
                          ? 'text-green-400'
                          : inv.status === 'open'
                          ? 'text-yellow-400'
                          : 'text-gray-400'
                      }`}
                    >
                      {inv.status}
                    </span>
                  </div>
                  {/* PDF link */}
                  <a
                    href={inv.invoice_pdf}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-violet-400 transition-colors"
                    aria-label="View invoice PDF"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>

      {/* ── Upgrade Modal ── */}
      {upgradeModalOpen && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <GlassCard className="bg-gray-900 border-white/10 w-full max-w-md relative">
            {/* Close button */}
            <button
              onClick={() => setUpgradeModalOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
              aria-label="Close upgrade modal"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-xl font-semibold mb-6">Upgrade your plan</h2>

            {/* MVP: single plan option */}
            <div className="bg-white/5 border border-violet-500/30 rounded-xl p-5 mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">Ava Monthly</span>
                <span className="text-violet-400 font-semibold">$9.99/month</span>
              </div>
              <p className="text-sm text-gray-400">
                Full access to your AI companion — chat, secretary skills, and photo generation.
              </p>
            </div>

            <button
              onClick={handleCheckout}
              disabled={checkoutLoading}
              className="w-full py-3 rounded-xl bg-violet-600 hover:bg-violet-700 disabled:opacity-60 disabled:cursor-not-allowed font-medium transition-colors"
            >
              {checkoutLoading ? 'Redirecting…' : 'Subscribe'}
            </button>
          </GlassCard>
        </div>
      )}
    </div>
  )
}
