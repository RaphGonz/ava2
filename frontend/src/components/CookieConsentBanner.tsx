import { AnimatePresence } from 'motion/react'
import { GlassCard } from './ui/GlassCard'
import { useCookieConsent } from '../hooks/useCookieConsent'

export function CookieConsentBanner() {
  const { hasChosen, accept, decline } = useCookieConsent()

  return (
    <AnimatePresence>
      {!hasChosen && (
        <div className="fixed bottom-4 left-4 right-4 z-50 max-w-2xl mx-auto">
          <GlassCard
            initial={{ y: 80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 80, opacity: 0 }}
            transition={{ type: 'spring', damping: 25 }}
            className="flex flex-col sm:flex-row items-start sm:items-center gap-4"
          >
            <p className="text-sm text-slate-300 flex-1">
              We use cookies to improve your experience (error tracking + analytics).
              Payments always work regardless of your choice.{' '}
              <a href="/privacy" className="text-blue-400 hover:text-blue-300 underline">
                Privacy policy
              </a>
            </p>
            <div className="flex gap-3 shrink-0">
              <button
                onClick={decline}
                className="text-sm text-slate-400 hover:text-white transition-colors px-4 py-2"
              >
                Decline
              </button>
              <button
                onClick={accept}
                className="text-sm bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white px-4 py-2 rounded-lg transition-all font-medium"
              >
                Accept
              </button>
            </div>
          </GlassCard>
        </div>
      )}
    </AnimatePresence>
  )
}
