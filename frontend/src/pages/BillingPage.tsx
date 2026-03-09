import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/useAuthStore'
import {
  getSubscription,
  getInvoices,
  createPortalSession,
  createCheckoutSession,
  cancelSubscription,
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

// ─── Types ────────────────────────────────────────────────────────────────────

type CancelStep = 'idle' | 'survey-q1' | 'survey-q2' | 'confirming' | 'cancelled'

// ─── BillingPage ─────────────────────────────────────────────────────────────

export default function BillingPage() {
  const token = useAuthStore(s => s.token)!
  const queryClient = useQueryClient()

  // Cancel flow state machine
  const [cancelStep, setCancelStep] = useState<CancelStep>('idle')
  const [surveyQ1, setSurveyQ1] = useState('')
  const [surveyQ2, setSurveyQ2] = useState('')
  const [isCancelling, setIsCancelling] = useState(false)
  const [cancelError, setCancelError] = useState<string | null>(null)

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

  async function handleConfirmCancel() {
    setIsCancelling(true)
    setCancelError(null)
    try {
      await cancelSubscription(token, { q1: surveyQ1, q2: surveyQ2 })
      await queryClient.invalidateQueries({ queryKey: ['subscription'] })
      setCancelStep('cancelled')
    } catch {
      setCancelError('Something went wrong. Please try again.')
    } finally {
      setIsCancelling(false)
    }
  }

  function handleCancelClick() {
    setCancelError(null)
    setSurveyQ1('')
    setSurveyQ2('')
    setCancelStep('survey-q1')
  }

  // ─── Render ────────────────────────────────────────────────────────────────

  const hasNoSubscription =
    !subLoading && (!subscription || subscription.status === 'none')

  const isActive = subscription?.status === 'active'
  const isCancellingAtPeriodEnd = isActive && subscription?.cancel_at_period_end === true

  const accessUntilDate = subscription?.current_period_end
    ? formatDate(subscription.current_period_end)
    : ''

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-2xl mx-auto px-4 py-12">
        <h1 className="text-2xl font-semibold mb-8 flex items-center gap-2">
          <CreditCard className="w-6 h-6 text-violet-400" />
          Billing
        </h1>

        {/* ── Cancel Flow State Machine ── */}
        {cancelStep !== 'idle' && (
          <GlassCard className="bg-white/5 border-white/10 mb-6">

            {/* Survey Q1 */}
            {cancelStep === 'survey-q1' && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold">Before you go...</h2>
                <p className="text-gray-300 text-sm">
                  What did you like most about Ava?
                </p>
                <textarea
                  value={surveyQ1}
                  onChange={e => setSurveyQ1(e.target.value)}
                  placeholder="Share your thoughts (optional)"
                  rows={3}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-violet-500/50"
                />
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setCancelStep('survey-q2')}
                    className="text-sm text-gray-400 hover:text-gray-200 transition-colors"
                  >
                    Skip
                  </button>
                  <button
                    onClick={() => setCancelStep('survey-q2')}
                    className="px-4 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-700 text-sm font-medium transition-colors"
                  >
                    Next &rarr;
                  </button>
                </div>
                {/* 3-click shortcut: Cancel → skip shortcut → Confirm */}
                <div className="pt-1">
                  <button
                    onClick={() => setCancelStep('confirming')}
                    className="text-xs text-gray-500 hover:text-gray-300 underline transition-colors"
                  >
                    Skip survey and cancel
                  </button>
                </div>
                <button
                  onClick={() => setCancelStep('idle')}
                  className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
                >
                  &larr; Back
                </button>
              </div>
            )}

            {/* Survey Q2 */}
            {cancelStep === 'survey-q2' && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold">One more question</h2>
                <p className="text-gray-300 text-sm">
                  Why are you leaving?
                </p>
                <textarea
                  value={surveyQ2}
                  onChange={e => setSurveyQ2(e.target.value)}
                  placeholder="Your feedback helps us improve (optional)"
                  rows={3}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-violet-500/50"
                />
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setCancelStep('confirming')}
                    className="text-sm text-gray-400 hover:text-gray-200 transition-colors"
                  >
                    Skip
                  </button>
                  <button
                    onClick={() => setCancelStep('confirming')}
                    className="px-4 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-700 text-sm font-medium transition-colors"
                  >
                    Next &rarr;
                  </button>
                </div>
                <button
                  onClick={() => setCancelStep('survey-q1')}
                  className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
                >
                  &larr; Back
                </button>
              </div>
            )}

            {/* Confirming step */}
            {cancelStep === 'confirming' && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold">Are you sure?</h2>
                {accessUntilDate && (
                  <p className="text-sm text-gray-300">
                    Your access continues until{' '}
                    <span className="text-white font-medium">{accessUntilDate}</span>
                    . You won't be charged again.
                  </p>
                )}
                <div className="flex items-center gap-4 flex-wrap">
                  <button
                    onClick={handleConfirmCancel}
                    disabled={isCancelling}
                    className="px-5 py-2 rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-60 disabled:cursor-not-allowed text-sm font-medium transition-colors"
                  >
                    {isCancelling ? 'Cancelling…' : 'Yes, cancel my subscription'}
                  </button>
                  <button
                    onClick={() => setCancelStep('idle')}
                    className="text-sm text-gray-400 hover:text-gray-200 underline transition-colors"
                  >
                    Never mind
                  </button>
                </div>
                {cancelError && (
                  <p className="text-sm text-red-400">{cancelError}</p>
                )}
              </div>
            )}

            {/* Cancelled step — warm post-cancel message */}
            {cancelStep === 'cancelled' && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold">Subscription cancelled</h2>
                <p className="text-sm text-gray-300">
                  We're sad to see you go.{' '}
                  {accessUntilDate ? (
                    <>
                      You'll keep access until{' '}
                      <span className="text-white font-medium">{accessUntilDate}</span>.
                    </>
                  ) : (
                    "You'll keep access until the end of your billing period."
                  )}
                </p>
                <p className="text-sm text-gray-400">
                  You can resubscribe anytime from this page.
                </p>
                <button
                  onClick={() => setCancelStep('idle')}
                  className="px-4 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-sm font-medium transition-colors"
                >
                  Done
                </button>
              </div>
            )}

          </GlassCard>
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

        {/* ── Action Buttons — hidden while cancel flow is open ── */}
        {!subLoading && !hasNoSubscription && cancelStep === 'idle' && (
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
