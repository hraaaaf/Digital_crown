import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  Zap, 
  RefreshCcw, 
  ChevronRight,
  ShieldCheck,
  Stethoscope,
  Pill,
  Trash2
} from 'lucide-react';
import { cn } from '../../../../utils/cn';
import { api } from '../../../../services/api';
import type { ValidationError, CoherenceWarning } from '../useDocumentGenerator';

interface DrugItem {
  id: number;
  name: string;
  dosage: string;
  forme: string;
  posologie: string;
}

interface PrescriptionAgenticStudioProps {
  patientId: string;
  drugs: DrugItem[];
  setDrugs: (drugs: DrugItem[]) => void;
  onUpdateDrug: (id: number, field: keyof DrugItem, val: string) => void;
  onRemoveDrug: (id: number) => void;
  onAddDrug: () => void;
  validationErrors: ValidationError[];
}

export const PrescriptionAgenticStudio: React.FC<PrescriptionAgenticStudioProps> = ({
  patientId,
  drugs,
  setDrugs,
  onUpdateDrug,
  onRemoveDrug,
  onAddDrug,
  validationErrors
}) => {
  const [step, setStep] = useState<'IDLE' | 'RESEARCH' | 'ASSESSMENT' | 'PLANNING'>('IDLE');
  const [assessment, setAssessment] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Étape 1 : Engager l'Agent Chercheur
  const runClinicalResearch = async () => {
    setLoading(true);
    setStep('RESEARCH');
    try {
      const res = await api.get(`/api/prescriptions/agentic/assessment/${patientId}`);
      setAssessment(res.data);
      setStep('ASSESSMENT');
    } catch (err) {
      console.error("Erreur Recherche IA:", err);
      setStep('IDLE');
    } finally {
      setLoading(false);
    }
  };

  // Étape 2 : Engager l'Agent Architecte
  const designTreatmentPlan = async () => {
    setLoading(true);
    setStep('PLANNING');
    try {
      const res = await api.post(`/api/prescriptions/agentic/design`, {
        assessment,
        patient_context: {
          id: patientId
        }
      });
      
      // Transformer le plan en drogues réelles
      const newDrugs = res.data.prescriptions.map((p: any, idx: number) => ({
        id: Date.now() + idx,
        name: p.medicament,
        dosage: p.dosage,
        forme: p.forme,
        posologie: p.posologie
      }));
      
      setDrugs(newDrugs);
    } catch (err) {
      console.error("Erreur Architecte IA:", err);
      setStep('ASSESSMENT');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* HEADER ELITE */}
      <div className="flex items-center justify-between bg-white/40 p-4 rounded-3xl border border-white/60 backdrop-blur-xl shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary/10 text-primary rounded-2xl flex items-center justify-center animate-pulse">
            <Brain size={22} />
          </div>
          <div>
            <h3 className="text-sm font-black text-slate-800 uppercase tracking-widest leading-none mb-1">IAmina Clinical Intelligence</h3>
            <span className="text-[10px] font-black text-primary/60 uppercase tracking-[0.2em]">Agentic Prescription v4.0</span>
          </div>
        </div>
        
        {step === 'IDLE' && (
          <button 
            onClick={runClinicalResearch}
            className="px-6 py-2 bg-primary text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-primary/20 hover:scale-105 transition-all flex items-center gap-2"
          >
            <Sparkles size={14} /> Analyser le Cas
          </button>
        )}
      </div>

      <AnimatePresence mode="wait">
        {/* ÉTAPE : RECHERCHE */}
        {step === 'RESEARCH' && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }} 
            exit={{ opacity: 0, y: -10 }}
            className="p-12 flex flex-col items-center justify-center text-center space-y-6 bg-white/20 rounded-[2.5rem] border border-dashed border-primary/30"
          >
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full animate-pulse" />
              <RefreshCcw size={48} className="text-primary animate-spin-slow relative z-10" />
            </div>
            <div>
              <h4 className="text-lg font-black text-slate-800 mb-2">Recherche Scientifique en cours...</h4>
              <p className="text-xs text-slate-500 font-medium max-w-xs mx-auto">
                L'agent IA analyse les antécédents, les allergies et les recommandations HAS pour ce patient.
              </p>
            </div>
          </motion.div>
        )}

        {/* ÉTAPE : BILAN (ASSESSMENT) */}
        {step === 'ASSESSMENT' && assessment && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }} 
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-4"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Risques Identifiés */}
              <div className="bg-red-50/50 p-6 rounded-[2rem] border border-red-100">
                <div className="flex items-center gap-2 text-red-600 mb-4">
                  <ShieldCheck size={18} />
                  <span className="text-xs font-black uppercase tracking-widest">Points de Vigilance</span>
                </div>
                <ul className="space-y-2">
                  {assessment.risques_identifies.map((r: string, i: number) => (
                    <li key={i} className="text-[11px] font-bold text-red-700 flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1 shrink-0" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Molécules Recommandées */}
              <div className="bg-emerald-50/50 p-6 rounded-[2rem] border border-emerald-100">
                <div className="flex items-center gap-2 text-emerald-600 mb-4">
                  <Stethoscope size={18} />
                  <span className="text-xs font-black uppercase tracking-widest">Recommandations Moléculaires</span>
                </div>
                <div className="space-y-3">
                  {assessment.recommandations_moleculaires.map((m: any, i: number) => (
                    <div key={i} className="bg-white/40 p-2 rounded-xl border border-emerald-100/50">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-black text-emerald-700 uppercase">{m.molecule}</span>
                        <span className={cn(
                          "px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-tighter",
                          m.priorite === 'haute' ? "bg-emerald-200 text-emerald-800" : "bg-slate-200 text-slate-600"
                        )}>{m.priorite}</span>
                      </div>
                      <p className="text-[9px] text-emerald-600/80 font-bold leading-tight">{m.justification}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-primary/5 p-6 rounded-[2.5rem] border border-primary/10 flex items-center justify-between">
              <div className="flex-1 pr-6">
                <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em] block mb-2">Stratégie Thérapeutique IA</span>
                <p className="text-xs text-slate-700 font-bold italic leading-relaxed">"{assessment.strategie_globale}"</p>
              </div>
              <button 
                onClick={designTreatmentPlan}
                className="px-8 py-3 bg-primary text-white rounded-2xl text-[11px] font-black uppercase tracking-widest shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all flex items-center gap-3 shrink-0"
              >
                Établir le Plan <ChevronRight size={18} />
              </button>
            </div>
          </motion.div>
        )}

        {/* ÉTAPE : PLAN (ORDO RÉELLE) */}
        {(step === 'PLANNING' || step === 'IDLE' || (step === 'ASSESSMENT' && drugs.length > 0)) && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }}
            className="space-y-4"
          >
            {/* Si on est en train de planifier */}
            {step === 'PLANNING' && loading && (
              <div className="p-12 text-center bg-white/40 rounded-[2.5rem] border border-dashed border-primary/20 flex flex-col items-center gap-4">
                <Zap size={32} className="text-primary animate-pulse" />
                <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Architecte IA en action...</span>
              </div>
            )}

            {/* Liste des prescriptions */}
            <div className="space-y-4">
              {drugs.map((drug, idx) => {
                const fieldError = validationErrors.find(e => e.field === `drug_${idx}`);
                return (
                  <motion.div 
                    layout
                    initial={{ opacity: 0, x: -10 }} 
                    animate={{ opacity: 1, x: 0 }} 
                    key={drug.id} 
                    className={cn(
                      "bg-white/40 p-5 rounded-[2rem] border transition-all group relative",
                      fieldError ? "border-red-200 bg-red-50/20" : "border-white/60 hover:bg-white/80"
                    )}
                  >
                    <div className="grid grid-cols-12 gap-6 items-start">
                      <div className="col-span-5">
                        <div className="flex items-center gap-3 mb-2">
                           <div className="w-8 h-8 bg-primary/5 text-primary rounded-xl flex items-center justify-center">
                              <Pill size={16} />
                           </div>
                           <input 
                            type="text" 
                            className="w-full bg-transparent border-none p-0 focus:ring-0 font-black text-primary text-base uppercase"
                            style={{ color: 'var(--primary)' }} 
                            placeholder="MÉDICAMENT..." 
                            value={drug.name} 
                            onChange={(e) => onUpdateDrug(drug.id, 'name', e.target.value.toUpperCase())} 
                          />
                        </div>
                        <input 
                          type="text" 
                          className="w-full bg-transparent border-none p-0 focus:ring-0 text-[10px] font-black text-slate-400 uppercase tracking-widest"
                          placeholder="FORME & DOSAGE..." 
                          value={`${drug.forme} - ${drug.dosage}`} 
                          onChange={(e) => {
                            const [f, d] = e.target.value.split(' - ');
                            onUpdateDrug(drug.id, 'forme', f || '');
                            onUpdateDrug(drug.id, 'dosage', d || '');
                          }}
                        />
                      </div>

                      <div className="col-span-6">
                        <textarea 
                          rows={2}
                          className="w-full bg-slate-100/50 border-none rounded-2xl p-3 text-[11px] font-bold text-slate-700 focus:ring-1 focus:ring-primary/20 resize-none"
                          placeholder="Posologie et conseils..."
                          value={drug.posologie}
                          onChange={(e) => onUpdateDrug(drug.id, 'posologie', e.target.value)}
                        />
                        {fieldError && (
                          <div className="mt-1 text-[9px] font-black text-red-500 uppercase tracking-widest flex items-center gap-1">
                            <AlertCircle size={10} /> {fieldError.message}
                          </div>
                        )}
                      </div>

                      <div className="col-span-1 flex justify-center pt-3">
                        <button 
                          onClick={() => onRemoveDrug(drug.id)}
                          className="p-2 text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            <button 
              onClick={onAddDrug} 
              className="w-full py-4 border-2 border-dashed border-slate-200 text-slate-400 rounded-3xl flex items-center justify-center gap-2 hover:border-primary hover:text-primary hover:bg-primary/5 transition-all font-bold mt-2"
            >
              <PlusIcon size={18} /> Ajouter manuellement
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const PlusIcon = ({ size }: { size: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
);
