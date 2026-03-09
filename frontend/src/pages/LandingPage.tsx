import { Navigate, Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { useAuthStore } from '../store/useAuthStore'
import { LandingHero } from '../components/landing/LandingHero'
import { LandingDualPromise } from '../components/landing/LandingDualPromise'
import { LandingTrust } from '../components/landing/LandingTrust'
import { LandingPricing } from '../components/landing/LandingPricing'
import { LandingFooter } from '../components/landing/LandingFooter'

export default function LandingPage() {
  const token = useAuthStore(s => s.token)

  // Zustand persist is synchronous — no loading state needed (avoids flash per Pitfall 4)
  if (token) return <Navigate to="/chat" replace />

  return (
    <div className="w-full min-h-screen bg-black text-white overflow-x-hidden">
      <nav className="sticky top-0 z-50 w-full bg-black/80 backdrop-blur-sm border-b border-white/5">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <span className="text-xl font-bold tracking-tight text-white">Avasecret</span>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-sm text-slate-400 hover:text-white transition-colors">
              Sign in
            </Link>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link
                to="/signup"
                className="text-sm bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white px-4 py-2 rounded-lg transition-all font-medium"
              >
                Get started
              </Link>
            </motion.div>
          </div>
        </div>
      </nav>
      <LandingHero />
      <LandingDualPromise />
      <LandingTrust />
      <LandingPricing />
      <LandingFooter />
    </div>
  )
}
