import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle2, Info, Pill } from 'lucide-react';
import type { ClinicalProtocol } from './types';
import { ClinicalRefTabs } from './ClinicalRefTabs';
import { cn } from '../../utils/cn';

interface ContentProps {
  protocol: ClinicalProtocol;
}

export const ClinicalRefContent: React.FC<ContentProps> = ({ protocol }) => {
  const [activeTab, setActiveTab] = useState('checklist');

  return (
    <div className="flex flex-col h-full">
      <ClinicalRefTabs activeTab={activeTab} onTabChange={setActiveTab} />

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar mt-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="space-y-4"
          >
            {/* CHECKLIST */}
            {activeTab === 'checklist' && (
              <div className="space-y-3">
                {protocol.checklist.map((item) => (
                  <label key={item.id} className="flex items-center gap-3 p-3 bg-[var(--bg-medical-pearl)] rounded-xl border border-[var(--border-color)] cursor-pointer hover:border-[var(--primary)]/30 transition-all group">
                    <input type="checkbox" className="w-4 h-4 rounded-md border-[var(--border-color)] text-[var(--primary)] focus:ring-[var(--primary)]" style={{ accentColor: 'var(--primary)' }} />
                    <span className={cn(
                      "text-xs font-bold transition-all",
                      item.critical ? "text-rose-500 flex items-center gap-1.5" : "text-[var(--text-main)]"
                    )}>
                      {item.critical && <AlertCircle size={12} />}
                      {item.label}
                    </span>
                  </label>
                ))}
              </div>
            )}

            {/* STEPS */}
            {activeTab === 'steps' && (
              <div className="space-y-4">
                {protocol.steps.map((step) => (
                  <div key={step.order} className="relative pl-8 pb-1 last:pb-0">
                    {step.order !== protocol.steps.length && (
                      <div className="absolute left-[11px] top-6 bottom-0 w-[2px] bg-[var(--border-color)]" />
                    )}
                    <div className="absolute left-0 top-0 w-6 h-6 rounded-lg bg-[var(--primary)]/10 flex items-center justify-center text-[10px] font-black" style={{ color: 'var(--primary)' }}>
                      {step.order}
                    </div>
                    <div className="bg-[var(--card-bg)] p-4 rounded-xl border border-[var(--border-color)] shadow-sm">
                      <p className="text-xs font-bold text-[var(--text-main)]">{step.label}</p>
                      {step.tip && (
                        <p className="text-[10px] text-[var(--text-muted)] mt-2 font-medium flex items-center gap-1.5">
                          <Info size={11} className="text-[var(--primary)]" />
                          {step.tip}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* PITFALLS */}
            {activeTab === 'pitfalls' && (
              <div className="space-y-3">
                {protocol.pitfalls.map((p, i) => (
                  <div key={i} className="p-4 bg-rose-500/5 rounded-2xl border border-rose-500/20">
                    <div className="flex items-center gap-2 mb-2 text-rose-500">
                      <AlertCircle size={14} />
                      <span className="text-[10px] font-black uppercase tracking-widest">Risque : {p.risk}</span>
                    </div>
                    <p className="text-xs font-bold text-[var(--text-main)] leading-relaxed">{p.mitigation}</p>
                  </div>
                ))}
              </div>
            )}

            {/* DRUGS */}
            {activeTab === 'drugs' && (
              <div className="space-y-3">
                {protocol.drugs.map((d, i) => (
                  <div key={i} className="p-3 bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl shadow-sm flex items-start gap-3">
                    <div className={cn(
                      "p-2 rounded-lg",
                      d.category === 'anesthesia' ? "bg-blue-500/10 text-blue-500" : 
                      d.category === 'antibiotic' ? "bg-emerald-500/10 text-emerald-500" : "bg-purple-500/10 text-purple-500"
                    )}>
                      <Pill size={16} />
                    </div>
                    <div>
                      <h4 className="text-xs font-black text-[var(--text-main)]">{d.name}</h4>
                      <p className="text-[10px] text-[var(--text-muted)] font-bold mt-0.5">{d.dose_adult}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* PATIENT */}
            {activeTab === 'patient' && (
              <div className="space-y-3">
                <div className="p-5 bg-emerald-500/5 rounded-2xl border border-emerald-500/20 mb-4">
                   <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-3">Conseils Post-Opératoires</p>
                   <ul className="space-y-3">
                     {protocol.patient_instructions.map((inst, i) => (
                       <li key={i} className="flex items-start gap-2.5 text-xs font-bold text-[var(--text-main)]">
                         <CheckCircle2 size={15} className="text-emerald-500 mt-0.5 shrink-0" />
                         <span>{inst.instruction}</span>
                       </li>
                     ))}
                   </ul>
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};
