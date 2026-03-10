import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Send, Sparkles, Lock, Mic } from "lucide-react";
import { clsx } from "clsx";

export function MagicMoment() {
  const [stage, setStage] = useState<
    "idle" | "typing_assistant" | "assistant_response" | "trigger_prompt" | "typing_safe" | "activated"
  >("idle");
  
  const [inputValue, setInputValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const simulateTyping = (text: string, nextStage: "assistant_response" | "activated") => {
    let currentText = "";
    let i = 0;
    const interval = setInterval(() => {
      if (i < text.length) {
        currentText += text.charAt(i);
        setInputValue(currentText);
        i++;
      } else {
        clearInterval(interval);
        setTimeout(() => {
             setStage(nextStage);
        }, 500);
      }
    }, 50);
  };

  const handleInteraction = () => {
    if (stage === "idle") {
      setStage("typing_assistant");
      simulateTyping("Ajoute une réunion à 9h", "assistant_response");
    } else if (stage === "trigger_prompt") {
      setStage("typing_safe");
      simulateTyping("Blue Velvet", "activated");
    }
  };

  // Auto-advance from response to trigger prompt
  useEffect(() => {
    if (stage === "assistant_response") {
      const timer = setTimeout(() => {
        setInputValue("");
        setStage("trigger_prompt");
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [stage]);

  const isActivated = stage === "activated";

  return (
    <section className="relative w-full h-screen overflow-hidden flex flex-col items-center justify-center">
      {/* Background Transition */}
      <motion.div
        className="absolute inset-0 z-0 bg-slate-950"
        animate={{
          background: isActivated
            ? "linear-gradient(135deg, #4c1d95 0%, #ea580c 100%)"
            : "linear-gradient(135deg, #020617 0%, #0f172a 100%)",
        }}
        transition={{ duration: 1.5, ease: "easeInOut" }}
      />
      
      {/* Shockwave Effect on Activation */}
      <AnimatePresence>
        {isActivated && (
          <motion.div
            initial={{ scale: 0, opacity: 1 }}
            animate={{ scale: 20, opacity: 0 }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            className="absolute rounded-full w-24 h-24 bg-orange-500 z-10 blur-xl"
          />
        )}
      </AnimatePresence>

      <div className="relative z-20 container mx-auto px-6 max-w-2xl text-center">
        
        {/* Header Text */}
        <motion.h2
          layout
          className={clsx(
            "text-4xl md:text-5xl font-bold mb-8 transition-colors duration-1000",
            isActivated ? "text-white" : "text-blue-100"
          )}
        >
          {isActivated ? "Mode Compagnon Activé" : "L'Assistant d'abord..."}
        </motion.h2>

        {/* Chat Interface */}
        <motion.div
          layout
          className={clsx(
            "relative bg-black/40 backdrop-blur-xl border rounded-2xl p-6 shadow-2xl transition-all duration-1000",
            isActivated 
              ? "border-orange-500/50 shadow-[0_0_50px_-10px_rgba(234,88,12,0.5)]" 
              : "border-blue-500/30 shadow-[0_0_30px_-10px_rgba(59,130,246,0.3)]"
          )}
        >
          {/* Messages Area */}
          <div className="h-40 flex flex-col justify-end gap-4 mb-6 overflow-hidden">
             <AnimatePresence mode="popLayout">
               {stage !== "idle" && stage !== "typing_assistant" && (
                 <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="self-end bg-slate-700/50 text-white px-4 py-2 rounded-2xl rounded-tr-sm text-sm"
                 >
                   Ajoute une réunion à 9h
                 </motion.div>
               )}
               {(stage === "assistant_response" || stage === "trigger_prompt" || stage === "typing_safe" || stage === "activated") && (
                 <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="self-start bg-blue-600/20 text-blue-200 border border-blue-500/30 px-4 py-2 rounded-2xl rounded-tl-sm text-sm flex items-center gap-2"
                 >
                   <Sparkles className="w-3 h-3" /> Réunion ajoutée à l'agenda.
                 </motion.div>
               )}
               {isActivated && (
                 <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5 }}
                    className="self-center mt-4 bg-gradient-to-r from-violet-600 to-orange-600 text-white px-6 py-3 rounded-xl shadow-lg text-lg font-medium"
                 >
                   Je t'attendais... On passe en privé ?
                 </motion.div>
               )}
             </AnimatePresence>
          </div>

          {/* Input Area */}
          <div 
            className="relative"
            onClick={handleInteraction}
          >
            <input
              ref={inputRef}
              type="text"
              readOnly
              inputMode="none"
              value={inputValue}
              placeholder={
                stage === "idle" ? "Cliquez ici pour essayer..." : 
                stage === "trigger_prompt" ? "Tapez le Safe Word..." : ""
              }
              className={clsx(
                "w-full bg-black/20 border text-white placeholder:text-white/30 rounded-xl px-4 py-4 pr-12 focus:outline-none transition-all duration-500 cursor-pointer",
                isActivated ? "border-orange-500/50 focus:border-orange-500" : "border-blue-500/30 focus:border-blue-400"
              )}
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50">
               {isActivated ? <Lock className="w-5 h-5 text-orange-400" /> : <Send className="w-5 h-5" />}
            </div>
          </div>

          {/* Helper Text */}
          <motion.div 
            key={stage}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-4 text-sm text-white/50 font-mono"
          >
             {stage === "idle" && "Essayez de taper : 'Ajoute une réunion à 9h'"}
             {stage === "trigger_prompt" && "Maintenant, tapez votre Safe Word (ex: 'Blue Velvet')"}
             {isActivated && "Accès sécurisé établi via Neural-Link."}
          </motion.div>

        </motion.div>
      </div>
    </section>
  );
}
