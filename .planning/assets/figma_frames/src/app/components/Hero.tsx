import { motion } from "motion/react";
import { ArrowRight, Play } from "lucide-react";
import { useState, useEffect } from "react";

// Simple helper for typing animation
const TypingText = ({ text, delay = 0 }: { text: string; delay?: number }) => {
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    const timeout = setTimeout(() => {
      let currentText = "";
      const interval = setInterval(() => {
        if (currentText.length < text.length) {
          currentText += text[currentText.length];
          setDisplayedText(currentText);
        } else {
          clearInterval(interval);
        }
      }, 50);
      return () => clearInterval(interval);
    }, delay);
    return () => clearTimeout(timeout);
  }, [text, delay]);

  return <span>{displayedText}</span>;
};

export function Hero() {
  return (
    <section className="relative w-full h-screen overflow-hidden flex items-center justify-center bg-black text-white">
      {/* Background Layers */}
      <div className="absolute inset-0 z-0">
        {/* Right Side (Violet/Orange) - Base Layer */}
        <div className="absolute inset-0 bg-gradient-to-br from-violet-900 to-orange-900">
          <img
            src="https://images.unsplash.com/photo-1608951303964-dda98fb5265a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx3b21hbiUyMGZpbmdlciUyMG9uJTIwbGlwcyUyMHNoaCUyMGdlc3R1cmUlMjBkYXJrJTIwaW50aW1hdGUlMjBjbG9zZSUyMHVwfGVufDF8fHx8MTc3MjAyMDA2Mnww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
            alt="Woman with finger on lips"
            className="w-full h-full object-cover opacity-40 mix-blend-overlay"
          />
        </div>

        {/* Left Side (Blue) - Clipped Layer */}
        <div 
          className="absolute inset-0 bg-blue-950 z-10"
          style={{ clipPath: "polygon(0 0, 65% 0, 35% 100%, 0 100%)" }}
        >
          <img
            src="https://images.unsplash.com/photo-1764747492867-84b495c80e3f?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMGJsdWUlMjBmbHVpZCUyMHRlY2hub2xvZ3klMjB3YXZlfGVufDF8fHx8MTc3MjAxODg3Nnww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
            alt="Abstract Blue Wave"
            className="w-full h-full object-cover opacity-60 mix-blend-overlay"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-blue-900/80 to-transparent" />
        </div>
      </div>

      {/* Content Container */}
      <div className="relative z-20 container mx-auto px-6 h-full flex flex-col md:flex-row items-center justify-between">
        
        {/* Left Content (Tech/Jarvis) */}
        <div className="w-full md:w-1/2 flex flex-col items-start justify-center h-full pr-12 pt-20">
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="mb-8"
          >
            <h1 className="text-5xl md:text-7xl font-bold tracking-tighter mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-100 to-blue-400">
              L'IA qui prends soin de votre énergie<br/>la journée.
            </h1>
            
            {/* UI Jarvis Mockup */}
            <div className="w-full max-w-md bg-slate-900/80 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4 shadow-2xl transform hover:scale-105 transition-transform duration-500">
              <div className="flex items-center justify-between mb-4 border-b border-slate-700 pb-2">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"/>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"/>
                  <div className="w-3 h-3 rounded-full bg-green-500"/>
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

          <div className="flex gap-4 mt-8 md:hidden">
            {/* Mobile buttons will be centered later or handled by the main CTA block */}
          </div>
        </div>

        {/* Right Content (Intime/Her) */}
        <div className="w-full md:w-1/2 flex flex-col items-end justify-center h-full pl-12 pt-20 text-right">
          <motion.div 
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mb-8 flex flex-col items-end"
          >
            <h1 className="text-5xl md:text-7xl font-bold tracking-tighter mb-6 bg-clip-text text-transparent bg-gradient-to-r from-violet-200 to-orange-200">
              ...et de votre intimité la nuit.
            </h1>

            {/* UI Her Mockup (Mobile) */}
            <div className="w-64 bg-black/40 backdrop-blur-md border border-white/10 rounded-3xl p-4 shadow-[0_0_50px_-12px_rgba(124,58,237,0.5)] transform hover:scale-105 transition-transform duration-500 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-orange-500"/>
              <div className="flex justify-center mb-6 mt-2">
                <div className="w-16 h-1 bg-white/20 rounded-full"/>
              </div>
              
              {/* Notification */}
              <div className="bg-white/10 backdrop-blur-xl rounded-xl p-3 mb-4 border border-white/5 relative overflow-hidden group">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-violet-500 to-orange-500 flex items-center justify-center text-xs font-bold">A</div>
                  <div className="flex flex-col items-start">
                    <span className="text-xs font-bold text-white">AVA Companion</span>
                    <span className="text-[10px] text-white/60">Maintenant</span>
                  </div>
                </div>
                <div className="text-sm text-left text-white/90 filter blur-[4px] group-hover:blur-0 transition-all duration-500 cursor-pointer">
                  J'ai une surprise pour toi...
                </div>
              </div>

              {/* Audio visualizer hint */}
              <div className="flex items-center justify-center gap-1 h-8 mt-8 opacity-60">
                 {[...Array(5)].map((_, i) => (
                   <div key={i} className="w-1 bg-white/50 rounded-full animate-pulse" style={{ height: Math.random() * 24 + 8 + 'px', animationDelay: i * 0.1 + 's' }} />
                 ))}
              </div>
            </div>
          </motion.div>
        </div>

        {/* Center CTA */}
        <div className="absolute bottom-10 left-0 right-0 flex flex-col items-center justify-center gap-4 z-30">
          <div className="flex flex-col md:flex-row gap-4">
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-8 py-4 rounded-full bg-gradient-to-r from-blue-600 via-violet-600 to-orange-600 text-white font-bold text-lg shadow-[0_0_30px_-5px_rgba(79,70,229,0.5)] hover:shadow-[0_0_50px_-5px_rgba(79,70,229,0.7)] transition-all flex items-center gap-2"
            >
              Créer mon AVA <ArrowRight className="w-5 h-5" />
            </motion.button>
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-8 py-4 rounded-full bg-white/5 backdrop-blur-sm border border-white/10 text-white font-medium text-lg hover:bg-white/10 transition-all flex items-center gap-2"
            >
              <Play className="w-4 h-4 fill-current" /> Voir la démo
            </motion.button>
          </div>
        </div>
      </div>
    </section>
  );
}
