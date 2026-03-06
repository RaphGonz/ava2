import { Link } from 'react-router-dom'

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      <nav className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <Link to="/" className="text-xl font-bold tracking-tight">Avasecret</Link>
      </nav>

      <main className="flex-1 max-w-3xl mx-auto px-6 py-12 space-y-8 text-gray-300 text-sm leading-relaxed">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Privacy Policy</h1>
          <p className="text-gray-500">Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">1. Who we are</h2>
          <p>
            Avasecret ("we", "us", "our") operates the website https://avasecret.org and provides
            an AI companion and assistant service. This Privacy Policy explains how we collect,
            use, and protect your personal information.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">2. Information we collect</h2>
          <ul className="list-disc list-inside space-y-2">
            <li><strong className="text-white">Account information:</strong> email address, name, and authentication credentials when you register.</li>
            <li><strong className="text-white">Profile data:</strong> avatar name, appearance description, and personality settings you configure.</li>
            <li><strong className="text-white">Conversation data:</strong> messages you send and receive through the service.</li>
            <li><strong className="text-white">Payment information:</strong> billing details processed securely by Stripe. We never store your card number.</li>
            <li><strong className="text-white">Usage data:</strong> pages visited, features used, and interaction timestamps.</li>
            <li><strong className="text-white">WhatsApp phone number:</strong> if you choose to connect your WhatsApp account.</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">3. How we use your information</h2>
          <ul className="list-disc list-inside space-y-2">
            <li>To provide and improve the Avasecret service.</li>
            <li>To personalise your AI companion based on your preferences.</li>
            <li>To process payments and manage your subscription.</li>
            <li>To send transactional emails (receipts, account notifications).</li>
            <li>To respond to support requests.</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">4. Third-party services</h2>
          <p>We use the following third-party services to operate Avasecret:</p>
          <ul className="list-disc list-inside space-y-2">
            <li><strong className="text-white">Supabase</strong> — authentication and database hosting.</li>
            <li><strong className="text-white">Stripe</strong> — payment processing. Subject to <a href="https://stripe.com/privacy" className="text-purple-400 hover:underline" target="_blank" rel="noreferrer">Stripe's Privacy Policy</a>.</li>
            <li><strong className="text-white">OpenAI</strong> — AI conversation processing. Messages are sent to OpenAI's API.</li>
            <li><strong className="text-white">Resend</strong> — transactional email delivery.</li>
            <li><strong className="text-white">Meta (WhatsApp)</strong> — optional WhatsApp messaging integration.</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">5. Data retention</h2>
          <p>
            We retain your data for as long as your account is active. You may request deletion
            of your account and associated data at any time by contacting us.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">6. Your rights</h2>
          <p>You have the right to:</p>
          <ul className="list-disc list-inside space-y-2">
            <li>Access the personal data we hold about you.</li>
            <li>Request correction of inaccurate data.</li>
            <li>Request deletion of your data.</li>
            <li>Object to processing of your data.</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">7. Cookies</h2>
          <p>
            We use browser local storage to maintain your session. We do not use third-party
            advertising cookies.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">8. Contact</h2>
          <p>
            For any privacy-related questions or requests, contact us at:{' '}
            <a href="mailto:privacy@avasecret.org" className="text-purple-400 hover:underline">
              privacy@avasecret.org
            </a>
          </p>
        </section>
      </main>

      <footer className="px-6 py-6 border-t border-gray-800 text-xs text-gray-500 text-center">
        © {new Date().getFullYear()} Avasecret
      </footer>
    </div>
  )
}
