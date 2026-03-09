import { Link } from 'react-router-dom'

export function LandingFooter() {
  return (
    <footer className="bg-black text-slate-500 py-12 px-6 border-t border-slate-900">
      <div className="container mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center mb-8">
          <div className="mb-6 md:mb-0">
            <h2 className="text-2xl font-bold text-white mb-1">AVA</h2>
            <p className="text-sm">Your augmented intelligence.</p>
          </div>
          <div className="flex gap-8 text-sm">
            <Link to="/terms" className="hover:text-white transition-colors">Terms of Use</Link>
            <Link to="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
          </div>
        </div>
        <div className="border-t border-slate-900 pt-6 text-center text-xs text-slate-700">
          &copy; 2026 Avasecret. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
