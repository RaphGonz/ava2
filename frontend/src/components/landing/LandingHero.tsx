import { motion } from "motion/react";
import { ArrowRight, Play } from "lucide-react";
import { Link } from "react-router-dom";

export function LandingHero() {
  return (
    <section className="relative w-full h-screen overflow-hidden flex items-center justify-center bg-black text-white">
      {/* Background Layers */}
      <div className="absolute inset-0 z-0">
        {/* Right Side (Violet/Orange) - Base Layer */}
        <div className="absolute inset-0 bg-gradient-to-br from-violet-900 to-orange-900" />

        {/* Left Side (Blue) - Clipped Layer */}
        <div
          className="absolute inset-0 bg-blue-950 z-10"
          style={{ clipPath: "polygon(0 0, 65% 0, 35% 100%, 0 100%)" }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-blue-900/80 to-transparent" />
        </div>
      </div>

      {/* Content Container */}
      <div className="relative z-20 container mx-auto px-6 h-full flex flex-col md:flex-row items-center justify-between">

        {/* Left Content (Tech/Jarvis) */}
        <div className="w-full md:w-1/2 flex flex-col items-start justify-center h-full pr-4 md:pr-12 pt-20">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="mb-8"
          >
            <h1 className="text-4xl md:text-5xl lg:text-7xl font-bold tracking-tighter mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-100 to-blue-400">
              The AI that takes care of your day.
            </h1>

            {/* Jarvis OS Mockup */}
            <div className="w-full max-w-md bg-slate-900/80 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4 shadow-2xl transform hover:scale-105 transition-transform duration-500">
              <div className="flex items-center justify-between mb-4 border-b border-slate-700 pb-2">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                </div>
                <div className="text-xs text-slate-400 font-mono">AVA_OS_V1.2</div>
              </div>
              <div className="space-y-3 font-mono text-sm">
                <div className="flex items-center text-blue-300">
                  <span className="mr-2">09:00</span>
                  <span className="bg-blue-500/20 px-2 py-0.5 rounded border border-blue-500/30 w-full">Deep Work: Q3 Strategy</span>
                </div>
                <div className="flex items-center text-slate-400">
                  <span className="mr-2">11:30</span>
                  <span className="bg-slate-700/30 px-2 py-0.5 rounded w-full">Client Sync: Alpha Corp</span>
                </div>
                <div className="flex items-center text-blue-300">
                  <span className="mr-2">14:00</span>
                  <span className="bg-blue-500/20 px-2 py-0.5 rounded border border-blue-500/30 w-full">Review: Design System</span>
                </div>
                <div className="pt-2 text-xs text-blue-400/80 animate-pulse">
                  &gt; Optimizing schedule for peak flow...
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Right Content (Companion) */}
        <div className="hidden md:flex w-full md:w-1/2 flex-col items-end justify-center h-full pl-12 pt-20 text-right">
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mb-8 flex flex-col items-end"
          >
            <h1 className="text-4xl md:text-5xl lg:text-7xl font-bold tracking-tighter mb-6 bg-clip-text text-transparent bg-gradient-to-r from-violet-200 to-orange-200">
              ...and keeps you company at night.
            </h1>

            {/* Mobile chat mockup */}
            <div className="w-64 bg-black/40 backdrop-blur-md border border-white/10 rounded-3xl p-4 shadow-[0_0_50px_-12px_rgba(124,58,237,0.5)] transform hover:scale-105 transition-transform duration-500 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-orange-500" />
              <div className="flex justify-center mb-6 mt-2">
                <div className="w-16 h-1 bg-white/20 rounded-full" />
              </div>

              {/* Chat bubbles */}
              <div className="space-y-2 mb-3">
                {/* Ava message */}
                <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl rounded-bl-sm px-3 py-2 text-xs text-white/90 text-left max-w-[85%]">
                  Missing you already... 🌙
                </div>
                {/* User message */}
                <div className="bg-gradient-to-r from-blue-600 to-violet-600 rounded-xl rounded-br-sm px-3 py-2 text-xs text-white text-right ml-auto max-w-[75%]">
                  Show me something
                </div>
                {/* Ava message */}
                <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl rounded-bl-sm px-3 py-2 text-xs text-white/90 text-left max-w-[85%]">
                  Just for you... 💜
                </div>
              </div>
              {/* Blurred locked photo */}
              <div className="relative rounded-xl overflow-hidden h-24">
                <div className="absolute inset-0 bg-gradient-to-b from-violet-800/30 to-orange-800/30 backdrop-blur-lg" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-white/70 text-xs font-medium">🔒 Click to unlock</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Center CTA */}
        <div className="absolute bottom-10 left-0 right-0 flex flex-col items-center justify-center gap-4 z-30">
          <div className="flex flex-col md:flex-row gap-4">
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link
                to="/signup"
                className="px-8 py-4 rounded-full bg-gradient-to-r from-blue-600 via-violet-600 to-orange-600 text-white font-bold text-lg shadow-[0_0_30px_-5px_rgba(79,70,229,0.5)] hover:shadow-[0_0_50px_-5px_rgba(79,70,229,0.7)] transition-all flex items-center gap-2"
              >
                Create my Ava <ArrowRight className="w-5 h-5" />
              </Link>
            </motion.div>
            <button
              className="px-8 py-4 rounded-full bg-white/5 backdrop-blur-sm border border-white/10 text-white font-medium text-lg hover:bg-white/10 transition-all flex items-center gap-2"
              onClick={() => {}}
            >
              <Play className="w-4 h-4 fill-current" /> Watch the demo
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
