import { Link, useLocation } from 'react-router-dom'
import { MessageSquare, Image, Settings } from 'lucide-react'

const NAV_TABS = [
  { path: '/chat', label: 'Chat', icon: MessageSquare },
  { path: '/photo', label: 'Photos', icon: Image },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export function AppNav() {
  const { pathname } = useLocation()
  return (
    <>
      {/* Desktop: sticky top bar — matches landing page nav style */}
      <nav className="hidden md:flex sticky top-0 z-50 w-full bg-black/80 backdrop-blur-sm border-b border-white/5 px-6 py-4 items-center justify-between">
        <span className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-violet-400">
          Avasecret
        </span>
        <div className="flex items-center gap-6">
          {NAV_TABS.map(tab => (
            <Link
              key={tab.path}
              to={tab.path}
              className={`text-sm transition-colors ${
                pathname === tab.path
                  ? 'text-white font-medium'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.label}
            </Link>
          ))}
        </div>
      </nav>
      {/* Mobile: fixed bottom tab bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-md border-t border-white/10 flex justify-around py-2">
        {NAV_TABS.map(tab => {
          const Icon = tab.icon
          const isActive = pathname === tab.path
          return (
            <Link
              key={tab.path}
              to={tab.path}
              className={`flex flex-col items-center gap-1 px-4 py-1 text-xs transition-colors ${
                isActive ? 'text-white' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <Icon
                className={`w-5 h-5 ${
                  isActive
                    ? 'stroke-current'
                    : ''
                }`}
                style={isActive ? { stroke: 'url(#appNavGrad)' } : undefined}
              />
              {tab.label}
            </Link>
          )
        })}
        {/* SVG gradient definition for active icon — hidden element */}
        <svg width="0" height="0" className="absolute">
          <defs>
            <linearGradient id="appNavGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#2563eb" />
              <stop offset="100%" stopColor="#7c3aed" />
            </linearGradient>
          </defs>
        </svg>
      </nav>
      {/* Spacer so content is not hidden behind mobile tab bar */}
      <div className="md:hidden h-16" />
    </>
  )
}
