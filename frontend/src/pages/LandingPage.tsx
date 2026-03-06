import { Link } from 'react-router-dom'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <span className="text-xl font-bold tracking-tight">Avasecret</span>
        <div className="flex items-center gap-4">
          <Link to="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
            Sign in
          </Link>
          <Link
            to="/signup"
            className="text-sm bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Get started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-6 py-20">
        <h1 className="text-5xl font-bold tracking-tight mb-6 max-w-2xl">
          Your personal AI companion
        </h1>
        <p className="text-lg text-gray-400 max-w-xl mb-10">
          Avasecret is an AI assistant that adapts to you — helping with tasks, answering
          questions, and keeping you company, on web or WhatsApp.
        </p>
        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            to="/signup"
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-8 py-3 rounded-xl transition-colors"
          >
            Create your Ava
          </Link>
          <Link
            to="/login"
            className="bg-gray-800 hover:bg-gray-700 text-white font-semibold px-8 py-3 rounded-xl transition-colors"
          >
            Sign in
          </Link>
        </div>
      </main>

      {/* Features */}
      <section className="px-6 py-16 border-t border-gray-800">
        <div className="max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-3xl mb-3">🤝</div>
            <h3 className="font-semibold mb-2">Always available</h3>
            <p className="text-sm text-gray-400">
              Chat on the web app or WhatsApp — your Ava is there whenever you need her.
            </p>
          </div>
          <div>
            <div className="text-3xl mb-3">⚡</div>
            <h3 className="font-semibold mb-2">Smart assistant</h3>
            <p className="text-sm text-gray-400">
              Schedule meetings, search the web, and get things done — all through conversation.
            </p>
          </div>
          <div>
            <div className="text-3xl mb-3">✨</div>
            <h3 className="font-semibold mb-2">Truly personal</h3>
            <p className="text-sm text-gray-400">
              Customise her name, appearance, and personality to match exactly what you're looking for.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-6 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500">
        <span>© {new Date().getFullYear()} Avasecret</span>
        <div className="flex gap-4">
          <Link to="/privacy" className="hover:text-gray-300 transition-colors">
            Privacy Policy
          </Link>
          <Link to="/terms" className="hover:text-gray-300 transition-colors">
            Terms of Use
          </Link>
        </div>
      </footer>
    </div>
  )
}
