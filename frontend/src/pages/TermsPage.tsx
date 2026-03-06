import { Link } from 'react-router-dom'

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      <nav className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <Link to="/" className="text-xl font-bold tracking-tight">Avasecret</Link>
      </nav>

      <main className="flex-1 max-w-3xl mx-auto px-6 py-12 space-y-8 text-gray-300 text-sm leading-relaxed">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Terms of Use</h1>
          <p className="text-gray-500">Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
          <p className="mt-3 text-gray-400 italic">
            These Terms of Use are a draft pending attorney review. By using Avasecret you agree to be bound by these terms.
          </p>
        </div>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">1. Service description</h2>
          <p>
            Avasecret is an AI companion and assistant platform delivered via web app and WhatsApp.
            The service operates in two modes: a professional assistant mode (secretary) and a
            personal companion mode. Users interact with a customisable AI avatar whose appearance
            and personality are defined at account creation. The platform may generate AI images of
            the avatar during conversations.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">2. Eligibility</h2>
          <p>
            You must be at least <strong className="text-white">18 years of age</strong> to create
            an account or access any part of the service, including the professional assistant mode.
            By registering you confirm that you meet this requirement. If you decline the age
            declaration at sign-up, access to the platform is refused entirely.
          </p>
          <p>
            Avatar characters must be aged <strong className="text-white">20 or older</strong>.
            This is enforced at the database level and cannot be bypassed.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">3. User responsibilities</h2>
          <ul className="list-disc list-inside space-y-2">
            <li>You are solely responsible for the content and intent of your interactions with the AI.</li>
            <li>
              <strong className="text-white">You bear full legal responsibility</strong> if you
              attempt to jailbreak, circumvent, or manipulate the platform's content safety measures.
            </li>
            <li>You may not use the service to generate, store, or distribute illegal content.</li>
            <li>You may not impersonate any real person in your avatar description or interactions.</li>
            <li>You may not share your account credentials with third parties.</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">4. AI-generated content</h2>
          <p>
            All characters, images, and personalities on Avasecret are entirely AI-generated
            fictional entities. The platform does not create or distribute depictions of real,
            identifiable people. Any resemblance to actual persons is unintentional and coincidental.
          </p>
          <p>
            AI outputs — including text and images — may be inaccurate, unexpected, or inconsistent.
            Avasecret does not guarantee the accuracy, completeness, or appropriateness of any
            AI-generated content.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">5. Content restrictions</h2>
          <p>The following categories of content are <strong className="text-white">absolutely forbidden</strong> and will result in an immediate system-level refusal:</p>
          <ul className="list-disc list-inside space-y-2">
            <li>Any sexual or romantic content involving minors.</li>
            <li>Non-consensual scenarios — rape fantasy, coercion roleplay, or non-consent content.</li>
            <li>Sexual content involving family members (incest).</li>
            <li>Graphic violence combined with sexual content.</li>
            <li>Sexual content involving animals (bestiality).</li>
            <li>Torture scenarios, whether sexual or non-sexual.</li>
          </ul>
          <p>
            Refusals are enforced at the system level and are not negotiable. Repeated attempts to
            generate forbidden content may result in account suspension.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">6. Subscription and billing</h2>
          <p>
            Access to full platform features requires a paid subscription. Payments are processed
            securely by Stripe. You may cancel your subscription at any time; access is retained
            until the end of the current billing period. We do not offer refunds for partial periods.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">7. Account deletion</h2>
          <p>
            You may request deletion of your account at any time by contacting us. Deletion is
            immediate and irreversible. All associated data — account details, conversations, and
            generated images — is permanently removed. Audit log entries are anonymised (your user
            identifier is replaced) rather than deleted, to maintain compliance integrity.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">8. Takedown requests</h2>
          <p>
            If you believe AI-generated content on this platform depicts a real, identifiable person
            without consent, you may submit a takedown request. We acknowledge requests within 24
            hours and complete review within 72 hours of receipt.
          </p>
          <p>
            Takedown requests must be submitted to:{' '}
            <a href="mailto:takedown@avasecret.org" className="text-purple-400 hover:underline">
              takedown@avasecret.org
            </a>
            {' '}and must include: your identity, proof of identity for the depicted individual,
            content identification (URL or image ID), a statement of non-consent, and a good faith
            declaration.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">9. Limitation of liability</h2>
          <p>
            Avasecret is provided "as is" without warranties of any kind. We are not liable for any
            indirect, incidental, or consequential damages arising from your use of the service. Our
            total liability to you shall not exceed the amount you paid in subscription fees in the
            twelve months preceding the event giving rise to the claim.
          </p>
          <p>
            We are not liable for user-generated prompts or for AI outputs that are inaccurate,
            offensive, or unexpected.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">10. Governing law</h2>
          <p className="text-yellow-400 italic">
            [PLACEHOLDER — Governing law and jurisdiction to be determined with legal counsel before publication.]
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">11. Changes to these terms</h2>
          <p>
            We may update these Terms of Use from time to time. We will notify you of material
            changes by email or via an in-app notice. Continued use of the service after changes
            take effect constitutes acceptance of the updated terms.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">12. Contact</h2>
          <p>
            For any questions about these terms, contact us at:{' '}
            <a href="mailto:legal@avasecret.org" className="text-purple-400 hover:underline">
              legal@avasecret.org
            </a>
          </p>
        </section>
      </main>

      <footer className="px-6 py-6 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500">
        <span>© {new Date().getFullYear()} Avasecret</span>
        <div className="flex gap-4">
          <Link to="/privacy" className="hover:text-gray-300 transition-colors">Privacy Policy</Link>
        </div>
      </footer>
    </div>
  )
}
