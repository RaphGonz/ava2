import { motion } from "motion/react";
import { Brain, Heart, Zap, Lock } from "lucide-react";
import { GlassCard } from "./ui/GlassCard";

export function DualPromise() {
  return (
    <section className="relative w-full py-20 px-6 bg-black text-white overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-black via-slate-900 to-black pointer-events-none" />
      
      <div className="relative z-10 container mx-auto">
        <div className="flex flex-col md:flex-row gap-8 items-stretch justify-center">
          
          {/* Assistant Mode Card */}
          <GlassCard 
            variant="active-cool"
            className="flex-1 min-h-[500px] flex flex-col group relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/20 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/2 pointer-events-none" />
            
            <div className="flex items-center gap-4 mb-6">
              <div className="p-3 rounded-xl bg-blue-500/20 border border-blue-500/30 text-blue-400 group-hover:text-blue-300 transition-colors">
                <Brain className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-bold text-white group-hover:text-blue-200 transition-colors">Mode Assistant</h3>
            </div>

            <p className="text-slate-300 mb-8 leading-relaxed">
              Une intelligence analytique pure pour structurer votre chaos. 
              Gestion d'agenda, emails, synthèse de documents.
              Elle ne dort jamais, ne juge jamais.
            </p>

            {/* Visual: Mini Agenda */}
            <div className="mt-auto bg-slate-900/50 rounded-xl p-4 border border-blue-500/10">
               <div className="space-y-3">
                 {[1, 2, 3].map((i) => (
                   <div key={i} className="flex items-center gap-3 opacity-70">
                     <div className="w-1 h-8 bg-blue-500 rounded-full" />
                     <div className="flex-1 space-y-1">
                       <div className="h-2 w-2/3 bg-slate-700 rounded" />
                       <div className="h-2 w-1/2 bg-slate-800 rounded" />
                     </div>
                   </div>
                 ))}
               </div>
            </div>
          </GlassCard>

          {/* Companion Mode Card */}
          <GlassCard 
            variant="active-warm"
            className="flex-1 min-h-[500px] flex flex-col group relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-64 h-64 bg-orange-500/20 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/2 pointer-events-none" />
            
            <div className="flex items-center gap-4 mb-6">
              <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500/20 to-orange-500/20 border border-orange-500/30 text-orange-400 group-hover:text-orange-300 transition-colors">
                <Heart className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-bold text-white group-hover:text-orange-200 transition-colors">Mode Compagnon</h3>
            </div>

            <p className="text-slate-300 mb-8 leading-relaxed">
              Plus qu'une IA, une présence. Connexion émotionnelle, 
              écoute active et partage multimédia privé.
              Apprenez à lâcher prise.
            </p>

            {/* Visual: Blurred Button */}
            <div className="mt-auto h-32 flex items-center justify-center relative">
               <div className="absolute inset-0 bg-gradient-to-r from-violet-600/20 to-orange-600/20 rounded-xl blur-xl" />
               <motion.button
                 whileHover={{ scale: 1.05 }}
                 whileTap={{ scale: 0.95 }}
                 className="relative px-8 py-3 rounded-full bg-white/5 backdrop-blur-xl border border-white/10 text-white/50 font-medium group-hover:text-white/80 transition-all overflow-hidden"
               >
                 <span className="blur-[2px] group-hover:blur-0 transition-all duration-500">
                   Maintenir pour révéler
                 </span>
               </motion.button>
            </div>
          </GlassCard>

        </div>
      </div>
    </section>
  );
}
