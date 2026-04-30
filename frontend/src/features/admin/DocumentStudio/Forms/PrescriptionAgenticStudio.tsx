import React, { useState } from 'react';
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
  Trash2,
  Plus
} from 'lucide-react';
import { cn } from '../../../../utils/cn';
import { api } from '../../../../services/api';
import type { ValidationError } from '../useDocumentGenerator';

export interface DrugItem {
  id: number;
  name: string;
  dosage: string;
  forme: string;
  posologie: string;
  type?: 'MEDICAMENT' | 'EXAMEN';
}

interface PrescriptionAgenticStudioProps {
  patientId: string;
  drugs: DrugItem[];
  setDrugs: (drugs: DrugItem[]) => void;
  onUpdateDrug: (id: number, field: keyof DrugItem, val: string) => void;
  onRemoveDrug: (id: number) => void;
  onAddDrug: () => void;
  validationErrors: ValidationError[];
  onSaveHabit?: (context: string, drugs: DrugItem[]) => void;
  hasChanges?: boolean;
}

export const PrescriptionAgenticStudio: React.FC<PrescriptionAgenticStudioProps> = ({
  patientId,
  drugs,
  setDrugs,
  onUpdateDrug,
  onRemoveDrug,
  onAddDrug,
  validationErrors,
  onSaveHabit,
  hasChanges
}) => {
  const [step, setStep] = useState<'IDLE' | 'RESEARCH' | 'ASSESSMENT' | 'PLANNING'>('IDLE');
  const [assessment, setAssessment] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // ÉTATS AUTOCOMPLETE
  const [activeSearchId, setActiveSearchId] = useState<{id: number, field: string} | null>(null);
  const [suggestions, setSuggestions] = useState<any>({ medications: [], dosages: [], posologies: [] });
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Étape 1 : Engager l'Agent Chercheur (Local First + Habits Aware)
  const runClinicalResearch = async () => {
    setLoading(true);
    setStep('RESEARCH');
    try {
      const res = await api.get(`/prescriptions/agentic/assessment/${patientId}`);
      setAssessment(res.data);
      setStep('ASSESSMENT');
    } catch (err) {
      console.error("Erreur Recherche IA:", err);
      setStep('IDLE');
    } finally {
      setLoading(false);
    }
  };

  // Étape 2 : Engager l'Agent Architecte (Synthesis)
  const designTreatmentPlan = async () => {
    setLoading(true);
    setStep('PLANNING');
    try {
      const res = await api.post(`/prescriptions/agentic/design`, {
        assessment,
        patient_context: { id: patientId }
      });
      
      const newDrugs = res.data.prescriptions.map((p: any, idx: number) => ({
        id: Date.now() + idx,
        name: p.medicament,
        dosage: p.dosage,
        forme: p.forme,
        posologie: p.posologie,
        type: 'MEDICAMENT'
      }));
      
      setDrugs(newDrugs);
    } catch (err) {
      console.error("Erreur Architecte IA:", err);
      setStep('ASSESSMENT');
    } finally {
      setLoading(false);
    }
  };

  // RECHERCHE D'HABITUDES
  const handleSearch = async (id: number, field: string, val: string) => {
    onUpdateDrug(id, field as keyof DrugItem, val);
    if (field === 'name' && val.length >= 1) {
      setActiveSearchId({id, field});
      const res = await api.get(`/prescriptions/habits/suggest?q=${val}`);
      setSuggestions(res.data);
      setShowSuggestions(true);
    } else if (field === 'dosage' || field === 'posologie') {
      // Pour dose et posologie, on attend que le nom soit fixé
      const drug = drugs.find(d => d.id === id);
      if (drug?.name) {
        setActiveSearchId({id, field});
        const res = await api.get(`/prescriptions/habits/details?med_name=${drug.name}`);
        setSuggestions({ medications: [], ...res.data });
        setShowSuggestions(true);
      }
    } else {
      setShowSuggestions(false);
    }
  };

  const applySuggestion = (id: number, field: string, val: string) => {
    onUpdateDrug(id, field as keyof DrugItem, val);
    setShowSuggestions(false);
    setActiveSearchId(null);
    
    // Si on a choisi un médicament, on récupère ses détails habituels
    if (field === 'name') {
      api.get(`/prescriptions/habits/details?med_name=${val}`).then(res => {
        if (res.data.dosages.length === 1) onUpdateDrug(id, 'dosage', res.data.dosages[0]);
        if (res.data.posologies.length === 1) onUpdateDrug(id, 'posologie', res.data.posologies[0]);
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* HEADER ELITE V4.7 */}
      <div className="flex items-center justify-between bg-white/40 p-5 rounded-[2.5rem] border border-white/60 backdrop-blur-2xl shadow-xl shadow-primary/5">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse" />
            <div className="w-12 h-12 bg-gradient-to-br from-primary to-blue-600 text-white rounded-2xl flex items-center justify-center relative z-10 shadow-lg shadow-primary/30">
              <Brain size={24} className={loading ? "animate-spin-slow" : ""} />
            </div>
          </div>
          <div>
            <h3 className="text-sm font-black text-slate-800 uppercase tracking-widest leading-none mb-1 flex items-center gap-2">
              IAmina Clinical Intelligence
              <span className="bg-primary/10 text-primary text-[8px] px-2 py-0.5 rounded-full">v4.7</span>
            </h3>
            <div className="flex items-center gap-2">
               <span className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em]">Zero Friction & Habits Aware</span>
               {assessment?.source && (
                 <span className="flex items-center gap-1 text-[9px] font-black text-emerald-500 uppercase tracking-widest">
                   <Zap size={10} /> {assessment.source}
                 </span>
               )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {hasChanges && onSaveHabit && assessment?.act_context && (
            <button 
              onClick={() => onSaveHabit(assessment.act_context, drugs)}
              className="px-4 py-2 bg-emerald-100 text-emerald-700 rounded-xl text-[9px] font-black uppercase tracking-widest hover:bg-emerald-200 transition-all flex items-center gap-2"
            >
              <CheckCircle2 size={12} /> Mémoriser comme standard
            </button>
          )}

          {step === 'IDLE' && (
            <>
              <button 
                onClick={() => {
                  setDrugs([{ id: Date.now(), name: '', dosage: '', forme: 'Comprimés', posologie: '', type: 'MEDICAMENT' }]);
                  setStep('PLANNING');
                }}
                className="px-5 py-2.5 bg-slate-100 text-slate-600 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-200 transition-all flex items-center gap-2"
              >
                <Plus size={14} /> Rédaction Libre
              </button>
              <button 
                onClick={runClinicalResearch}
                className="px-6 py-2.5 bg-primary text-white rounded-2xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-primary/25 hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
              >
                <Sparkles size={14} /> Analyser le Cas
              </button>
            </>
          )}
          
          {(step === 'ASSESSMENT' || step === 'PLANNING') && (
            <button 
              onClick={() => {
                setStep('IDLE');
                setAssessment(null);
              }}
              className="p-2.5 bg-slate-100 text-slate-400 rounded-xl hover:bg-slate-200 transition-all"
              title="Réinitialiser"
            >
              <RefreshCcw size={16} />
            </button>
          )}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {step === 'RESEARCH' && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }} 
            exit={{ opacity: 0, y: -10 }}
            className="p-16 flex flex-col items-center justify-center text-center space-y-8 bg-white/30 rounded-[3rem] border border-dashed border-primary/30 backdrop-blur-sm"
          >
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full animate-pulse scale-150" />
              <div className="w-20 h-20 bg-white rounded-3xl flex items-center justify-center shadow-2xl relative z-10 border border-primary/10">
                <RefreshCcw size={40} className="text-primary animate-spin-slow" />
              </div>
            </div>
            <div className="max-w-sm">
              <h4 className="text-xl font-black text-slate-800 mb-3">Moteur de Mémoire Local...</h4>
              <p className="text-xs text-slate-500 font-bold leading-relaxed">
                Apprentissage de vos habitudes, calcul des doses pédiatriques et validation des interactions médicamenteuses.
              </p>
            </div>
          </motion.div>
        )}

        {step === 'ASSESSMENT' && assessment && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.98 }} 
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Colonne Gauche : Sécurité & Bilan */}
              <div className="lg:col-span-7 space-y-6">
                <div className="bg-white/60 p-8 rounded-[2.5rem] border border-white/60 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
                    <div className="prose prose-slate prose-sm max-w-none">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 bg-emerald-500/10 text-emerald-600 rounded-xl flex items-center justify-center">
                          <ShieldCheck size={22} />
                        </div>
                        <div>
                          <h4 className="text-xs font-black text-slate-800 uppercase tracking-widest">Bilan Scientifique</h4>
                          <p className="text-[10px] font-bold text-slate-400">Habits Engine v2.0 (Local)</p>
                        </div>
                      </div>
                      <div className="space-y-4">
                         {assessment.risques_identifies.length > 0 ? (
                            <div className="p-4 bg-red-50 rounded-2xl border border-red-100">
                               <span className="text-[9px] font-black text-red-600 uppercase tracking-widest block mb-2">Risques Détectés</span>
                               <ul className="m-0 p-0 list-none space-y-1.5">
                                 {assessment.risques_identifies.map((r: string, i: number) => (
                                   <li key={i} className="text-[11px] font-bold text-red-700 flex items-start gap-2">
                                     <div className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 shrink-0" />
                                     {r}
                                   </li>
                                 ))}
                               </ul>
                            </div>
                         ) : (
                            <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100 flex items-center gap-3">
                               <CheckCircle2 size={20} className="text-emerald-500" />
                               <span className="text-xs font-bold text-emerald-700 uppercase tracking-widest">Sécurité Clinique Validée</span>
                            </div>
                         )}
                         
                         <div className="p-5 bg-primary/5 rounded-2xl border border-primary/10">
                            <span className="text-[9px] font-black text-primary uppercase tracking-widest block mb-2">Stratégie Thérapeutique</span>
                            <p className="text-xs font-bold text-slate-700 leading-relaxed italic">"{assessment.strategie_globale}"</p>
                            <p className="text-[10px] text-primary/60 font-black mt-2 uppercase">{assessment.dosage_note}</p>
                         </div>
                      </div>
                    </div>
                </div>
              </div>

              {/* Colonne Droite : Suggestions & Action */}
              <div className="lg:col-span-5 space-y-6">
                <div className="bg-slate-900 p-8 rounded-[2.5rem] text-white shadow-2xl shadow-primary/20 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-12 bg-primary/20 blur-[100px] rounded-full group-hover:scale-150 transition-transform duration-1000" />
                  
                  <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-6">
                       <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                          <Stethoscope size={20} className="text-primary-light" />
                       </div>
                       <h4 className="text-xs font-black uppercase tracking-widest">Suggestions</h4>
                    </div>

                    <div className="space-y-3 mb-8">
                      {assessment.recommandations_moleculaires.map((m: any, i: number) => (
                        <div key={i} className="bg-white/5 p-3 rounded-2xl border border-white/10 hover:bg-white/10 transition-colors">
                           <div className="flex items-center justify-between mb-1">
                             <span className="text-[10px] font-black text-primary-light uppercase">{m.molecule}</span>
                             <div className="flex gap-1">
                               {m.noms_commerciaux.slice(0,2).map((n: string) => (
                                 <span key={n} className="px-1.5 py-0.5 bg-white/10 rounded text-[7px] font-black uppercase tracking-tighter">{n}</span>
                               ))}
                             </div>
                           </div>
                           <p className="text-[9px] text-white/40 font-bold leading-tight">{m.justification}</p>
                        </div>
                      ))}
                    </div>

                    <button 
                      onClick={designTreatmentPlan}
                      className="w-full py-4 bg-primary text-white rounded-2xl text-[11px] font-black uppercase tracking-[0.2em] shadow-xl shadow-primary/40 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3"
                    >
                      Établir l'Ordonnance <ChevronRight size={18} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {(step === 'PLANNING' || step === 'IDLE' || (step === 'ASSESSMENT' && drugs.length > 0)) && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }}
            className="space-y-4"
          >
            {step === 'PLANNING' && loading && (
              <div className="p-20 text-center bg-white/40 rounded-[3rem] border border-dashed border-primary/20 flex flex-col items-center gap-6 backdrop-blur-sm">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                  <Zap size={32} className="text-primary animate-bounce" />
                </div>
                <div>
                  <h4 className="text-sm font-black text-slate-800 uppercase tracking-widest mb-2">Génération du plan...</h4>
                  <p className="text-[10px] font-bold text-slate-400">Application de vos habitudes et structuration finale.</p>
                </div>
              </div>
            )}

            <div className="space-y-3">
              {drugs.map((drug, idx) => {
                const fieldError = validationErrors.find(e => e.field === `drug_${idx}`);
                const isRadio = drug.type === 'EXAMEN';

                return (
                  <motion.div 
                    layout
                    initial={{ opacity: 0, y: 10 }} 
                    animate={{ opacity: 1, y: 0 }} 
                    key={drug.id} 
                    className={cn(
                      "bg-white/60 p-5 rounded-[2.5rem] border transition-all group relative backdrop-blur-xl",
                      fieldError ? "border-red-200 bg-red-50/20" : "border-white/80 hover:bg-white hover:shadow-2xl hover:shadow-slate-200/30",
                      isRadio && "border-amber-100 bg-amber-50/10"
                    )}
                  >
                    <div className="grid grid-cols-12 gap-6 items-start">
                      <div className="col-span-1 flex flex-col items-center gap-3 pt-2 border-r border-slate-100 pr-4">
                         <button 
                            onClick={() => {
                                const newType = drug.type === 'MEDICAMENT' ? 'EXAMEN' : 'MEDICAMENT';
                                onUpdateDrug(drug.id, 'type', newType);
                                if (newType === 'EXAMEN') {
                                    onUpdateDrug(drug.id, 'dosage', '');
                                    onUpdateDrug(drug.id, 'forme', '');
                                    onUpdateDrug(drug.id, 'posologie', '');
                                } else {
                                    onUpdateDrug(drug.id, 'forme', 'Comprimés');
                                }
                            }}
                            title={isRadio ? "Mode Examen (Radio/Labo)" : "Mode Médicament"}
                            className={cn(
                                "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
                                isRadio ? "bg-amber-100 text-amber-600 shadow-lg shadow-amber-200/50" : "bg-slate-100 text-slate-400 hover:bg-primary/10 hover:text-primary"
                            )}
                         >
                            {isRadio ? <AlertCircle size={20} /> : <Pill size={18} />}
                         </button>
                         <span className="text-[7px] font-black uppercase text-slate-400">{isRadio ? 'EXAMEN' : 'MÉD.'}</span>
                      </div>

                      <div className="col-span-11 grid grid-cols-12 gap-6">
                        <div className={cn("relative", isRadio ? "col-span-11" : "col-span-5")}>
                            <input 
                              type="text" 
                              className="w-full bg-transparent border-none p-0 focus:ring-0 font-black text-slate-800 text-base uppercase placeholder:text-slate-200"
                              placeholder={isRadio ? "NOM DE L'EXAMEN / RADIOGRAPHIE..." : "MÉDICAMENT..."}
                              value={drug.name} 
                              onChange={(e) => handleSearch(drug.id, 'name', e.target.value.toUpperCase())}
                              onFocus={() => {
                                if (drug.name.length >= 1) handleSearch(drug.id, 'name', drug.name);
                              }}
                            />
                            {showSuggestions && activeSearchId?.id === drug.id && activeSearchId?.field === 'name' && suggestions.medications.length > 0 && (
                                <div className="absolute left-0 top-full mt-2 w-full bg-white border border-slate-100 rounded-2xl shadow-2xl z-50 overflow-hidden py-2 animate-in fade-in zoom-in duration-200">
                                    {suggestions.medications.map((m: string) => (
                                        <button 
                                            key={m} 
                                            onClick={() => applySuggestion(drug.id, 'name', m)}
                                            className="w-full px-5 py-2 text-left text-xs font-bold text-slate-600 hover:bg-primary/5 hover:text-primary transition-colors flex items-center justify-between"
                                        >
                                            {m}
                                            <ChevronRight size={14} className="opacity-0 group-hover:opacity-100" />
                                        </button>
                                    ))}
                                </div>
                            )}

                            {!isRadio && (
                                <div className="flex items-center gap-2 mt-1.5">
                                    <div className="relative group/forme">
                                        <select 
                                            className="appearance-none bg-slate-100/80 px-3 py-1.5 rounded-lg text-[9px] font-black text-primary uppercase tracking-widest outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all cursor-pointer pr-8"
                                            value={drug.forme} 
                                            onChange={(e) => onUpdateDrug(drug.id, 'forme', e.target.value)}
                                        >
                                            {['COMPRIMÉS', 'SACHETS', 'GÉLULES', 'BAIN DE BOUCHE', 'AMPOULES', 'SIROP', 'POMMADE', 'CRÈME', 'GOUTTES', 'OVULES'].map(f => (
                                                <option key={f} value={f}>{f}</option>
                                            ))}
                                        </select>
                                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-primary/40 group-hover/forme:text-primary transition-colors">
                                            <ChevronRight size={10} className="rotate-90" />
                                        </div>
                                    </div>

                                    <span className="text-slate-200 text-[10px] font-bold">•</span>
                                    
                                    <div className="relative flex-1">
                                        <input 
                                            type="text" 
                                            className="w-full bg-transparent border-none p-0 focus:ring-0 text-[10px] font-black text-slate-400 uppercase tracking-widest placeholder:text-slate-200"
                                            placeholder="DOSAGE..." 
                                            value={drug.dosage} 
                                            onFocus={() => handleSearch(drug.id, 'dosage', drug.dosage)}
                                            onChange={(e) => handleSearch(drug.id, 'dosage', e.target.value)} 
                                        />
                                        {showSuggestions && activeSearchId?.id === drug.id && activeSearchId?.field === 'dosage' && suggestions.dosages.length > 0 && (
                                            <div className="absolute left-0 top-full mt-1 bg-white border border-slate-100 rounded-lg shadow-xl z-50 py-1 min-w-[80px]">
                                                {suggestions.dosages.map((d: string) => (
                                                    <button key={d} onClick={() => applySuggestion(drug.id, 'dosage', d)} className="w-full px-3 py-1 text-left text-[9px] font-black text-slate-500 hover:bg-slate-50">{d}</button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>

                        {!isRadio ? (
                            <div className="col-span-6 relative">
                                <div className="bg-slate-50/50 p-4 rounded-2xl border border-slate-100 group-hover:bg-white transition-colors">
                                    <textarea 
                                        rows={1}
                                        className="w-full bg-transparent border-none p-0 text-[12px] font-bold text-slate-600 focus:ring-0 resize-none placeholder:text-slate-300"
                                        placeholder="Posologie habituelle..."
                                        value={drug.posologie}
                                        onFocus={() => handleSearch(drug.id, 'posologie', drug.posologie)}
                                        onChange={(e) => handleSearch(drug.id, 'posologie', e.target.value)}
                                    />
                                    {showSuggestions && activeSearchId?.id === drug.id && activeSearchId?.field === 'posologie' && suggestions.posologies.length > 0 && (
                                        <div className="absolute left-0 top-full mt-1 w-full bg-white border border-slate-100 rounded-xl shadow-xl z-50 py-2">
                                            {suggestions.posologies.map((p: string) => (
                                                <button key={p} onClick={() => applySuggestion(drug.id, 'posologie', p)} className="w-full px-4 py-1.5 text-left text-[10px] font-bold text-slate-500 hover:bg-slate-50">{p}</button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                                {fieldError && !isRadio && (
                                    <div className="mt-2 text-[9px] font-black text-red-500 uppercase tracking-widest flex items-center gap-1">
                                        <AlertCircle size={10} /> {fieldError.message}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="col-span-12 mt-2">
                                <div className="flex items-center gap-3 p-3 bg-amber-50/50 rounded-xl border border-amber-100 text-amber-700">
                                    <AlertCircle size={16} />
                                    <span className="text-[10px] font-bold">MODE EXAMEN : Aucun dosage ou posologie requis. Un avertissement de radioprotection sera ajouté au document.</span>
                                </div>
                                <input 
                                    type="text" 
                                    className="mt-2 w-full bg-transparent border-none p-0 text-[11px] font-bold text-slate-400 italic focus:ring-0 placeholder:text-slate-200"
                                    placeholder="Note optionnelle pour le radiologue..."
                                    value={drug.posologie}
                                    onChange={(e) => onUpdateDrug(drug.id, 'posologie', e.target.value)}
                                />
                            </div>
                        )}

                        <div className="absolute top-4 right-4 flex items-center">
                            <button 
                                onClick={() => onRemoveDrug(drug.id)}
                                className="p-2 text-slate-200 hover:text-red-500 transition-all opacity-0 group-hover:opacity-100"
                            >
                                <Trash2 size={18} />
                            </button>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            <div className="flex gap-4 mt-4">
               <button 
                onClick={onAddDrug} 
                className="flex-1 py-5 border-2 border-dashed border-slate-200 text-slate-400 rounded-[2.5rem] flex items-center justify-center gap-3 hover:border-primary hover:text-primary hover:bg-primary/5 transition-all font-black text-xs uppercase tracking-widest"
              >
                <Plus size={20} /> Ajouter une ligne
              </button>
              
              <button 
                  onClick={async () => {
                      // ENREGISTREMENT DES HABITUDES LIGNE PAR LIGNE
                      try {
                          for (const drug of drugs) {
                              if (drug.name.trim()) {
                                  await api.post('/prescriptions/habits/record', {
                                      medication_name: drug.name,
                                      dosage: drug.dosage,
                                      posologie: drug.posologie
                                  });
                              }
                          }
                          if (onSaveHabit && assessment?.act_context) {
                              onSaveHabit(assessment.act_context, drugs);
                          } else {
                              alert('✅ Habitudes de saisie mémorisées !');
                          }
                      } catch (e) {
                          console.error("Erreur enregistrement habitudes:", e);
                      }
                  }}
                  className="px-8 py-5 bg-white text-slate-800 border border-slate-200 rounded-[2.5rem] flex items-center justify-center gap-3 hover:bg-slate-50 transition-all font-black text-xs uppercase tracking-widest shadow-lg shadow-slate-200/50"
                >
                  <Brain size={20} className="text-primary" /> Mémoriser mes habitudes
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      {showSuggestions && <div className="fixed inset-0 z-40" onClick={() => setShowSuggestions(false)} />}
    </div>
  );
};
