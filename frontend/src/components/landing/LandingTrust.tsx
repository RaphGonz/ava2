import { GlassCard } from '../ui/GlassCard';
import { Lock, Power, CloudLightning } from 'lucide-react';

export function LandingTrust() {
  return (
    <section className="bg-slate-50 py-24 px-6 text-slate-900">
      <div className="container mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-blue-900">Trust & Security</h2>
          <p className="text-slate-600 max-w-2xl mx-auto">
            Your data is sacred. We built AVA like a digital vault, not an advertising product.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">

          <GlassCard
            variant="base"
            className="bg-white/80 border-slate-200 shadow-sm hover:shadow-md hover:border-blue-200 transition-all"
          >
            <div className="bg-blue-50 w-12 h-12 rounded-full flex items-center justify-center mb-6 text-blue-600">
              <Lock className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-slate-800">End-to-End Encryption</h3>
            <p className="text-slate-500 leading-relaxed">
              Your conversations are encrypted before they leave your device. No one — not even our
              engineers — can read them.
            </p>
          </GlassCard>

          <GlassCard
            variant="base"
            className="bg-white/80 border-slate-200 shadow-sm hover:shadow-md hover:border-red-200 transition-all"
          >
            <div className="bg-red-50 w-12 h-12 rounded-full flex items-center justify-center mb-6 text-red-600">
              <Power className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-slate-800">Full Control</h3>
            <p className="text-slate-500 leading-relaxed">
              Instantly erase your local history with one tap. Full GDPR compliance: your data
              belongs to you.
            </p>
          </GlassCard>

          <GlassCard
            variant="base"
            className="bg-white/80 border-slate-200 shadow-sm hover:shadow-md hover:border-purple-200 transition-all"
          >
            <div className="bg-purple-50 w-12 h-12 rounded-full flex items-center justify-center mb-6 text-purple-600">
              <CloudLightning className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-slate-800">Cloud Intelligence</h3>
            <p className="text-slate-500 leading-relaxed">
              Heavy processing stays in the secure cloud, preserving your device's battery and
              performance.
            </p>
          </GlassCard>

        </div>
      </div>
    </section>
  );
}
