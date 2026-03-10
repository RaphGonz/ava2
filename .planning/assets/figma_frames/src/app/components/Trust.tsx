import { GlassCard } from "./ui/GlassCard";
import { Lock, Power, CloudLightning } from "lucide-react";

export function Trust() {
  return (
    <section className="bg-slate-50 py-24 px-6 text-slate-900">
      <div className="container mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-blue-900">Confiance & Sécurité</h2>
          <p className="text-slate-600 max-w-2xl mx-auto">
            Vos données sont sacrées. Nous avons construit AVA comme un coffre-fort numérique, 
            pas comme un produit publicitaire.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          <GlassCard 
            className="bg-white/80 border-slate-200 shadow-sm hover:shadow-md hover:border-blue-200 transition-all"
            variant="base"
          >
            <div className="bg-blue-50 w-12 h-12 rounded-full flex items-center justify-center mb-6 text-blue-600">
              <Lock className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-slate-800">Chiffrement End-to-End</h3>
            <p className="text-slate-500 leading-relaxed">
              Vos conversations intimes sont chiffrées avant même de quitter votre appareil. 
              Personne, pas même nos ingénieurs, ne peut les lire.
            </p>
          </GlassCard>

          <GlassCard 
            className="bg-white/80 border-slate-200 shadow-sm hover:shadow-md hover:border-red-200 transition-all"
            variant="base"
          >
            <div className="bg-red-50 w-12 h-12 rounded-full flex items-center justify-center mb-6 text-red-600">
              <Power className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-slate-800">Contrôle Absolu</h3>
            <p className="text-slate-500 leading-relaxed">
              Le "Panic Button" efface instantanément votre historique local. 
              Respect total du RGPD : vos données vous appartiennent.
            </p>
          </GlassCard>

          <GlassCard 
            className="bg-white/80 border-slate-200 shadow-sm hover:shadow-md hover:border-purple-200 transition-all"
            variant="base"
          >
            <div className="bg-purple-50 w-12 h-12 rounded-full flex items-center justify-center mb-6 text-purple-600">
              <CloudLightning className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-slate-800">Cerveau Déporté</h3>
            <p className="text-slate-500 leading-relaxed">
              L'intelligence lourde reste dans le cloud sécurisé, préservant la batterie 
              et la fluidité de votre appareil.
            </p>
          </GlassCard>

        </div>
      </div>
    </section>
  );
}
