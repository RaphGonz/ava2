import { Navigate, Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { useAuthStore } from '../store/useAuthStore'
import { LandingHero } from '../components/landing/LandingHero'
import { LandingDualPromise } from '../components/landing/LandingDualPromise'
import { LandingTrust } from '../components/landing/LandingTrust'
import { LandingPricing } from '../components/landing/LandingPricing'
import { LandingFooter } from '../components/landing/LandingFooter'
import { CookieConsentBanner } from '../components/CookieConsentBanner'

export default function LandingPage() {
  const token = useAuthStore(s => s.token)

  // Zustand persist is synchronous — no loading state needed (avoids flash per Pitfall 4)
  if (token) return <Navigate to="/chat" replace />

  return (
    <div className="w-full min-h-screen bg-black text-white overflow-x-hidden">
      <CookieConsentBanner />
      <nav className="sticky top-0 z-50 w-full bg-black/80 backdrop-blur-sm border-b border-white/5">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <span className="text-xl font-bold tracking-tight text-white">Avasecret</span>
          <div className="flex items-center gap-4">
            <a href="https://www.instagram.com/ava.secret.ia/" target="_blank" rel="noopener noreferrer" aria-label="Instagram" className="text-slate-400 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
              </svg>
            </a>
            <a href="https://www.tiktok.com/@avasecret.ia" target="_blank" rel="noopener noreferrer" aria-label="TikTok" className="text-slate-400 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.18 8.18 0 0 0 4.78 1.52V6.75a4.85 4.85 0 0 1-1.01-.06z"/>
              </svg>
            </a>
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
