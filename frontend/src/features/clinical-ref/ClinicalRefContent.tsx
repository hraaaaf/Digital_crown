import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, AlertCircle, CheckCircle2, Info, Pill } from 'lucide-react';
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
                  <label key={item.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100 cursor-pointer hover:border-primary/30 transition-all group">
                    <input type="checkbox" className="w-4 h-4 rounded-md border-slate-300 text-primary focus:ring-primary" style={{ accentColor: 'var(--primary)' }} />
                    <span className={cn(
                      "text-xs font-bold transition-all",
                      item.critical ? "text-red-600 flex items-center gap-1.5" : "text-slate-600"
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
                      <div className="absolute left-[11px] top-6 bottom-0 w-[2px] bg-slate-100" />
                    )}
                    <div className="absolute left-0 top-0 w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center text-[10px] font-black" style={{ color: 'var(--primary)' }}>
                      {step.order}
                    </div>
                    <div className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm">
                      <p className="text-xs font-bold text-slate-800">{step.label}</p>
                      {step.tip && (
                        <p className="text-[10px] text-slate-400 mt-1 font-medium flex items-center gap-1">
                          <Info size={10} className="text-primary" style={{ color: 'var(--primary)' }} />
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
                  <div key={i} className="p-4 bg-red-50/30 rounded-2xl border border-red-100">
                    <div className="flex items-center gap-2 mb-2 text-red-600">
                      <AlertCircle size={14} />
                      <span className="text-[10px] font-black uppercase tracking-widest">{p.risk}</span>
                    </div>
                    <p className="text-xs font-bold text-slate-700 leading-relaxed">{p.mitigation}</p>
                  </div>
                ))}
              </div>
            )}

            {/* DRUGS */}
            {activeTab === 'drugs' && (
              <div className="space-y-3">
                {protocol.drugs.map((d, i) => (
                  <div key={i} className="p-3 bg-white border border-slate-100 rounded-xl shadow-sm flex items-start gap-3">
                    <div className={cn(
                      "p-2 rounded-lg",
                      d.category === 'anesthesia' ? "bg-blue-50 text-blue-600" : 
                      d.category === 'antibiotic' ? "bg-emerald-50 text-emerald-600" : "bg-purple-50 text-purple-600"
                    )}>
                      <Pill size={16} />
                    </div>
                    <div>
                      <h4 className="text-xs font-black text-slate-800">{d.name}</h4>
                      <p className="text-[10px] text-slate-500 font-bold mt-0.5">{d.dose_adult}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* PATIENT */}
            {activeTab === 'patient' && (
              <div className="space-y-3">
                <div className="p-4 bg-emerald-50/30 rounded-2xl border border-emerald-100 mb-4">
                   <p className="text-[10px] font-black text-emerald-700 uppercase tracking-widest mb-2">Conseils à déléguer</p>
                   <ul className="space-y-3">
                     {protocol.patient_instructions.map((inst, i) => (
                       <li key={i} className="flex items-start gap-2 text-xs font-bold text-slate-700">
                         <CheckCircle2 size={14} className="text-emerald-500 mt-0.5 shrink-0" />
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
