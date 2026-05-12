import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { X, Shield, AlertCircle, ChevronLeft, Printer, Share2 } from 'lucide-react';
import type { ClinicalProtocol } from './types';
import { cn } from '../../utils/cn';

interface SoinModeProps {
  protocol: ClinicalProtocol;
  onClose: () => void;
}

export const ClinicalSoinMode: React.FC<SoinModeProps> = ({ protocol, onClose }) => {
  // Verrouiller le scroll du body
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = 'unset'; };
  }, []);

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[200] bg-[#020617] text-white flex flex-col font-sans"
    >
      {/* HEADER IMMERSIF */}
      <header className="flex items-center justify-between px-8 py-6 border-b border-white/10 bg-[#020617]/80 backdrop-blur-md">
        <div className="flex items-center gap-6">
          <button 
            onClick={onClose}
            className="group flex items-center gap-2 text-white/60 hover:text-white transition-colors"
          >
            <div className="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center group-hover:border-white/40 transition-all">
              <ChevronLeft size={20} />
            </div>
            <span className="font-outfit text-xs uppercase tracking-widest font-black">Retour Bibliothèque</span>
          </button>
          
          <div className="h-8 w-[1px] bg-white/10 mx-2" />
          
          <div>
            <div className="flex items-center gap-3 mb-1">
              <span className="font-outfit text-[10px] bg-primary/20 text-primary px-2 py-0.5 rounded-full uppercase tracking-widest font-black">
                {protocol.category}
              </span>
              <span className="text-white/40 text-[10px] font-outfit uppercase tracking-widest">{protocol.act_code}</span>
            </div>
            <h1 className="font-serif text-2xl tracking-tight">{protocol.act_names[0]}</h1>
          </div>
        </div>

        <div className="flex items-center gap-4">
           <div className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-2xl border border-white/10">
             <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
             <span className="font-outfit text-[10px] uppercase tracking-widest font-black text-white/60">Mode Soin Actif</span>
           </div>
           <button onClick={onClose} className="w-12 h-12 bg-white text-black rounded-full flex items-center justify-center hover:scale-110 transition-all shadow-xl">
             <X size={24} />
           </button>
        </div>
      </header>

      {/* CONTENT GRID */}
      <div className="flex-1 overflow-hidden grid grid-cols-[1fr_400px]">
        {/* LEFT: MAIN STEPS (High visibility) */}
        <div className="overflow-y-auto px-12 py-12 custom-scrollbar border-r border-white/10">
          <div className="max-w-[800px] mx-auto space-y-12 pb-32">
            <section>
              <h2 className="font-outfit text-[11px] uppercase tracking-[0.2em] text-white/40 font-black mb-8 flex items-center gap-3">
                <div className="w-8 h-[1px] bg-white/20" /> Protocole Opératoire
              </h2>
              
              <div className="space-y-8">
                {protocol.steps.map((step, idx) => (
                  <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    key={idx} 
                    className="group relative pl-16"
                  >
                    <div className="absolute left-0 top-0 w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-xl font-serif italic text-primary group-hover:bg-primary group-hover:text-white transition-all duration-500">
                      {step.order}
                    </div>
                    <div className="pt-1">
                      <h3 className="text-2xl md:text-3xl font-medium tracking-tight leading-tight mb-3 text-white/90 group-hover:text-white transition-colors">
                        {step.label}
                      </h3>
                      {step.tip && (
                        <div className="flex items-start gap-3 p-4 bg-primary/5 border border-primary/20 rounded-2xl">
                          <AlertCircle size={18} className="text-primary shrink-0 mt-0.5" />
                          <p className="text-sm md:text-base text-white/70 font-medium leading-relaxed italic">
                            {step.tip}
                          </p>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </section>
          </div>
        </div>

        {/* RIGHT: CRITICAL INFO (Checklist & Risks) */}
        <aside className="bg-white/2 overflow-y-auto px-8 py-12 custom-scrollbar flex flex-col gap-10">
          {/* CRITICAL CHECKLIST */}
          <section>
            <h3 className="font-outfit text-[10px] uppercase tracking-[0.2em] text-white/40 font-black mb-6">Points Critiques</h3>
            <div className="space-y-3">
              {protocol.checklist.map((item, i) => (
                <div key={i} className={cn(
                  "p-4 rounded-2xl border transition-all flex items-start gap-3",
                  item.critical 
                    ? "bg-rose-500/10 border-rose-500/30 text-rose-200" 
                    : "bg-white/5 border-white/10 text-white/80"
                )}>
                  <div className={cn(
                    "w-5 h-5 rounded-md border flex items-center justify-center mt-0.5",
                    item.critical ? "border-rose-500/50" : "border-white/20"
                  )}>
                    {item.critical && <AlertCircle size={12} className="text-rose-500" />}
                  </div>
                  <span className="text-sm font-bold leading-snug">{item.label}</span>
                </div>
              ))}
            </div>
          </section>

          {/* PITFALLS */}
          <section>
            <h3 className="font-outfit text-[10px] uppercase tracking-[0.2em] text-white/40 font-black mb-6">Risques & Vigilance</h3>
            <div className="space-y-4">
              {protocol.pitfalls.map((p, i) => (
                <div key={i} className="p-5 bg-amber-500/10 border border-amber-500/30 rounded-2xl">
                  <div className="flex items-center gap-2 mb-2 text-amber-500">
                    <Shield size={16} />
                    <span className="text-[10px] font-black uppercase tracking-widest">{p.risk}</span>
                  </div>
                  <p className="text-sm font-medium text-amber-100/90 leading-relaxed">{p.mitigation}</p>
                </div>
              ))}
            </div>
          </section>

          {/* QUICK DRUGS */}
          <section className="mt-auto pt-8 border-t border-white/10">
            <div className="flex items-center justify-between mb-4">
              <span className="font-outfit text-[10px] uppercase tracking-[0.2em] text-white/40 font-black">Médication Rapide</span>
              <Share2 size={16} className="text-white/20" />
            </div>
            <div className="flex flex-wrap gap-2">
              {protocol.drugs.map((d, i) => (
                <div key={i} className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-[11px] font-bold text-white/80">
                  {d.name}
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>

      {/* FOOTER ACTIONS */}
      <footer className="px-8 py-5 border-t border-white/10 bg-[#020617] flex justify-between items-center">
        <div className="flex items-center gap-8 text-[10px] text-white/40 font-black uppercase tracking-widest">
           <span className="flex items-center gap-2"><kbd className="bg-white/10 px-2 py-1 rounded border border-white/10 text-white">Esc</kbd> Quitter</span>
           <span className="flex items-center gap-2"><kbd className="bg-white/10 px-2 py-1 rounded border border-white/10 text-white">P</kbd> Imprimer</span>
        </div>
        
        <div className="flex gap-4">
          <button className="flex items-center gap-2 px-6 py-3 bg-white/5 border border-white/10 rounded-2xl text-sm font-bold hover:bg-white/10 transition-all">
            <Printer size={18} /> Imprimer Guide
          </button>
          <button className="flex items-center gap-2 px-8 py-3 bg-primary text-white rounded-2xl text-sm font-black shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all">
            Valider l'acte
          </button>
        </div>
      </footer>
    </motion.div>
  );
};
