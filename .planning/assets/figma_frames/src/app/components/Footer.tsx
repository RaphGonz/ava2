import { ShieldAlert } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-black text-slate-500 py-12 px-6 border-t border-slate-900">
      <div className="container mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center mb-12">
          <div className="mb-8 md:mb-0">
            <h2 className="text-2xl font-bold text-white mb-2">AVA</h2>
            <p className="text-sm">Votre intelligence augmentée.</p>
          </div>
          <div className="flex gap-8 text-sm">
            <a href="#" className="hover:text-white transition-colors">CGU</a>
            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-white transition-colors">Disclaimer IA</a>
          </div>
        </div>

        <div className="border-t border-slate-900 pt-8 flex flex-col items-center">
          <div className="bg-red-950/30 border border-red-900/50 rounded-lg p-4 flex items-center gap-3 max-w-xl text-red-200/80 text-sm">
            <ShieldAlert className="w-5 h-5 flex-shrink-0" />
            <p>
              <strong>Avertissement :</strong> Ce service est réservé aux adultes de plus de 18 ans. 
              Une vérification d'identité est requise pour accéder aux fonctionnalités du Mode Compagnon.
              L'IA peut générer du contenu imprévisible.
            </p>
          </div>
          <div className="mt-8 text-xs text-slate-700">
            © 2026 AVA AI Inc. Tous droits réservés.
          </div>
        </div>
      </div>
    </footer>
  );
}
