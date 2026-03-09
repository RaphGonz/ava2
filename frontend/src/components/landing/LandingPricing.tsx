import { GlassCard } from '../ui/GlassCard';
import { Check, Star, Zap } from 'lucide-react';
import { motion } from 'motion/react';
import { Link } from 'react-router-dom';

export function LandingPricing() {
  const features = {
    basic: ['Smart Scheduling', 'Synced Calendar', 'Email Support'],
    premium: ['Night Mode', 'Unlimited Photos', 'Custom Personality', 'Priority Responses'],
    elite: ['All features included', 'Video Calls (Beta)', 'Early API Access', 'Dedicated 24/7 Support'],
  };

  return (
    <section className="relative bg-slate-900 py-32 px-6 overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full max-w-4xl bg-gradient-to-r from-blue-900/20 via-purple-900/20 to-orange-900/20 blur-3xl pointer-events-none" />

      <div className="container mx-auto relative z-10">
        <div className="text-center mb-20">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">Choose your plan</h2>
          <p className="text-slate-400 max-w-xl mx-auto text-lg">
            AVA adapts to your needs, from professional organisation to personal companionship.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center max-w-6xl mx-auto">

          {/* Basic */}
          <GlassCard className="bg-slate-800/50 border-slate-700 hover:border-blue-500/30">
            <h3 className="text-2xl font-bold text-white mb-2">Basic</h3>
            <div className="text-4xl font-bold text-blue-400 mb-6">
              €4.99<span className="text-xl text-slate-400 font-normal">/month</span>
            </div>
            <p className="text-slate-400 mb-8 text-sm">Start with the essentials.</p>
            <ul className="space-y-4 mb-8">
              {features.basic.map((f, i) => (
                <li key={i} className="flex items-center gap-3 text-slate-300">
                  <Check className="w-5 h-5 text-blue-500" /> {f}
                </li>
              ))}
            </ul>
            <Link
              to="/signup"
              className="w-full py-3 rounded-xl border border-white/10 text-white hover:bg-white/5 transition-colors font-medium text-center block"
            >
              Get started
            </Link>
          </GlassCard>

          {/* Premium - The Target */}
          <GlassCard
            variant="active-warm"
            className="transform scale-105 z-10 bg-slate-800/80 border-orange-500/50 shadow-[0_0_50px_-10px_rgba(234,88,12,0.3)] relative"
          >
            <div className="absolute top-0 right-0 bg-gradient-to-l from-orange-500 to-pink-500 text-white text-xs font-bold px-3 py-1 rounded-bl-xl shadow-lg">
              POPULAR
            </div>
            <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-orange-400 mb-2">
              Premium
            </h3>
            <div className="text-5xl font-bold text-white mb-6">
              €19.99<span className="text-xl text-slate-400 font-normal">/month</span>
            </div>
            <p className="text-slate-300 mb-8 text-sm">The complete experience, day and night.</p>
            <ul className="space-y-4 mb-8">
              {features.premium.map((f, i) => (
                <li key={i} className="flex items-center gap-3 text-white">
                  <Star className="w-5 h-5 text-orange-400 fill-orange-400/20" /> {f}
                </li>
              ))}
            </ul>
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Link
                to="/signup"
                className="w-full py-4 rounded-xl bg-gradient-to-r from-orange-500 to-pink-600 text-white font-bold shadow-lg shadow-orange-500/25 hover:shadow-orange-500/40 transition-all text-center block"
              >
                Unlock Ava
              </Link>
            </motion.div>
          </GlassCard>

          {/* Elite */}
          <GlassCard className="bg-slate-800/50 border-slate-700 hover:border-purple-500/30">
            <h3 className="text-2xl font-bold text-white mb-2">Elite</h3>
            <div className="text-4xl font-bold text-purple-400 mb-6">
              €49.99<span className="text-xl text-slate-400 font-normal">/month</span>
            </div>
            <p className="text-slate-400 mb-8 text-sm">The future of human interaction.</p>
            <ul className="space-y-4 mb-8">
              {features.elite.map((f, i) => (
                <li key={i} className="flex items-center gap-3 text-slate-300">
                  <Zap className="w-5 h-5 text-purple-500" /> {f}
                </li>
              ))}
            </ul>
            <button
              disabled
              className="w-full py-3 rounded-xl border border-white/10 text-white/50 font-medium cursor-not-allowed"
            >
              Contact Sales
            </button>
          </GlassCard>

        </div>
      </div>
    </section>
  );
}
