import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  ChevronRight, 
  ChevronLeft, 
  X, 
  ShieldCheck, 
  AlertCircle, 
  Sparkles, 
  Activity,
  Check,
  Trash2,
  Plus
} from 'lucide-react';
import { cn } from '../../../utils/cn';
import { api } from '../../../services/api';
import { useEliteStore } from '../../../stores/useEliteStore';
import { evaluateDiagnosis } from './DiagnosticEngine';

interface HouseWizardProps {
  onClose: () => void;
  onApplyDiagnostic: (diagnostic: {
    title: string;
    description: string;
    protocol: string[];
    treatmentPlan: { phase: string; act: string; price: number }[];
    warnings: string[];
  }) => void;
}

type Step = 'MOTIF' | 'CLINICAL' | 'RADIOLOGY' | 'RESULT';

interface EditableAct {
  phase: string;
  act: string;
  price: number;
  enabled: boolean;
}

export const HouseWizard: React.FC<HouseWizardProps> = ({ onClose, onApplyDiagnostic }) => {
  const [step, setStep] = useState<Step>('MOTIF');
  
  // State answers
  const [motif, setMotif] = useState<string>('');
  const [vitality, setVitality] = useState<string>('');
  const [percussion, setPercussion] = useState<string>('');
  const [palpation, setPalpation] = useState<string>('');
  const [radiology, setRadiology] = useState<string>('');
  const [lesionDuration, setLesionDuration] = useState<string>('');

  // Custom Pricing and Editable Treatment Plan
  const [editableActs, setEditableActs] = useState<EditableAct[]>([]);
  const [isLoadingPrices, setIsLoadingPrices] = useState<boolean>(false);
  const [showConfirm, setShowConfirm] = useState<boolean>(false);

  // New custom act form
  const [newActPhase, setNewActPhase] = useState<string>('CONSERVATRICE');
  const [newActName, setNewActName] = useState<string>('');
  const [newActPrice, setNewActPrice] = useState<string>('');

  // Active Pharmacovigilance
  const { lastPatientId } = useEliteStore();
  const [medicalHistory, setMedicalHistory] = useState('');

  useEffect(() => {
    if (lastPatientId) {
      api.get(`/patients/${lastPatientId}`)
         .then(res => setMedicalHistory(res.data.antecedents_medicaux || ''))
         .catch(err => console.error("Failed to fetch patient history for HouseWizard pharmacovigilance", err));
    }
  }, [lastPatientId]);

  // 1. MOTIF OPTIONS
  const motifs = [
    { id: 'DOULEUR', label: '⚡ Douleur Vive / Urgence', desc: 'Rage de dent, sensibilité chaud/froid' },
    { id: 'GONFLEMENT', label: '🎈 Abcès / Gonflement', desc: 'Gencive gonflée, tuméfaction' },
    { id: 'PARO', label: '🦷 Gencives / Mobilité', desc: 'Saignements, dents qui bougent' },
    { id: 'LESION', label: '👅 Lésion Muqueuse', desc: 'Tache blanche/rouge, ulcération' },
    { id: 'BILAN', label: '🔍 Consultation / Bilan', desc: 'Examen de routine, détartrage' }
  ];

  // 2. CLINICAL OPTIONS
  const vitalityOptions = [
    { id: 'POSITIVE_PERSISTANTE', label: 'Positive persistante', desc: 'Douleur vive restant après retrait du stimulus' },
    { id: 'POSITIVE_TRANSITOIRE', label: 'Positive transitoire', desc: 'Douleur brève cédant instantanément' },
    { id: 'NEGATIVE', label: 'Négative / Aucune', desc: 'Aucune sensation de froid (Nécrose)' }
  ];

  const percussionOptions = [
    { id: 'POSITIVE_AXIALE', label: 'Positive Axiale', desc: 'Douleur nette au tapotement vertical (apical)' },
    { id: 'POSITIVE_TRANSVERSALE', label: 'Positive Transversale', desc: 'Douleur latérale (parodontale)' },
    { id: 'NEGATIVE', label: 'Négative', desc: 'Aucune sensibilité' }
  ];

  const palpationOptions = [
    { id: 'SENSITIVE', label: 'Sensible', desc: 'Pression vestibulaire sensible' },
    { id: 'FLUCTUANTE', label: 'Fluctuante (Abcès)', desc: 'Zone molle, remplie de liquide' },
    { id: 'NEGATIVE', label: 'Normale', desc: 'Aucune anomalie' }
  ];

  // 3. RADIOLOGY OPTIONS
  const radiologyOptions = [
    { id: 'RADIOCLAIRE', label: 'Lésion radioclaire apicale', desc: 'Perte de substance osseuse périradiculaire' },
    { id: 'PERTE_OSSEUSE', label: 'Perte osseuse horizontale/verticale', desc: 'Dénudation radiculaire visible' },
    { id: 'PROXIMITE_NERF', label: 'Proximité canal alvéolaire (<2mm)', desc: 'Marge implantaire critique' },
    { id: 'AUCUNE', label: 'Aucune anomalie', desc: 'Os alvéolaire sain' }
  ];

  const durationOptions = [
    { id: 'MOINS_14', label: 'Moins de 14 jours', desc: 'Lésion récente, possible aphte ou traumatisme' },
    { id: 'PLUS_14', label: '14 jours ou plus', desc: 'Lésion persistante (Règle d\'or : Biopsie requise)' }
  ];

  // Clinically deterministic decision logic
  const calculateDiagnosis = () => {
    return evaluateDiagnosis({
      motif,
      vitality,
      percussion,
      palpation,
      radiology,
      lesionDuration,
      medicalHistory
    });
  };

  // Dynamic Loading of Physician Act/Price Habits
  useEffect(() => {
    if (step === 'RESULT') {
      const loadHabitsAndPrices = async () => {
        setIsLoadingPrices(true);
        const baseResult = calculateDiagnosis();
        const finalActs: EditableAct[] = [];

        try {
          for (const item of baseResult.treatmentPlan) {
            const response = await api.get(`/actes/catalog/search?q=${encodeURIComponent(item.act)}`);
            let finalPrice = item.price;
            
            if (response.data && response.data.length > 0) {
              const match = response.data.find(
                (h: any) => h.name.toLowerCase() === item.act.toLowerCase()
              ) || response.data[0];
              finalPrice = match.base_price;
            }
            
            finalActs.push({
              phase: item.phase,
              act: item.act,
              price: finalPrice,
              enabled: true
            });
          }
          setEditableActs(finalActs);
        } catch (err) {
          console.error("Error loading habits pricing:", err);
          setEditableActs(
            baseResult.treatmentPlan.map((i: any) => ({ ...i, enabled: true }))
          );
        } finally {
          setIsLoadingPrices(false);
        }
      };
      loadHabitsAndPrices();
    }
  }, [step, motif, vitality, percussion, palpation, radiology, lesionDuration]);

  const handleNext = () => {
    if (step === 'MOTIF') {
      if (motif === 'LESION') {
        setStep('RADIOLOGY'); 
      } else {
        setStep('CLINICAL');
      }
    } else if (step === 'CLINICAL') {
      setStep('RADIOLOGY');
    } else if (step === 'RADIOLOGY') {
      setStep('RESULT');
    }
  };

  const handlePrev = () => {
    if (step === 'RESULT') {
      setStep('RADIOLOGY');
    } else if (step === 'RADIOLOGY') {
      if (motif === 'LESION') {
        setStep('MOTIF');
      } else {
        setStep('CLINICAL');
      }
    } else if (step === 'CLINICAL') {
      setStep('MOTIF');
    }
  };

  const result = calculateDiagnosis();

  const handleApply = () => {
    onApplyDiagnostic({
      title: result.title,
      description: result.description,
      protocol: result.protocol,
      treatmentPlan: editableActs.filter(a => a.enabled).map(a => ({
        phase: a.phase,
        act: a.act,
        price: a.price
      })),
      warnings: result.warnings
    });
  };

  return (
    <div className="fixed inset-0 z-[10005] flex items-center justify-center p-4">
      {/* Backdrop with elegant blur */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="absolute inset-0 bg-slate-950/40 backdrop-blur-md"
      />

      {/* Center Popup Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="relative w-full max-w-xl bg-white/95 dark:bg-slate-900/95 border border-slate-200/50 dark:border-white/10 rounded-[2.5rem] shadow-[0_30px_70px_rgba(0,0,0,0.2)] dark:shadow-[0_30px_70px_rgba(0,0,0,0.5)] overflow-hidden flex flex-col max-h-[85vh] z-10 text-slate-800 dark:text-slate-100"
      >
        
        {/* HEADER */}
        <div className="px-6 py-4 bg-gradient-to-r from-primary/10 to-transparent flex items-center justify-between border-b border-slate-100 dark:border-white/5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-gradient-to-tr from-amber-500 to-yellow-500 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/20">
              <Brain size={16} className="text-white" />
            </div>
            <div>
              <h3 className="text-xs font-black uppercase tracking-widest text-slate-800 dark:text-white">Diagnostic Expert</h3>
              <p className="text-[9px] font-bold text-slate-400">Arbre Décisionnel Interactif</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 hover:bg-slate-100 dark:hover:bg-white/5 rounded-full text-slate-400 hover:text-slate-955 dark:hover:text-white transition-all"
          >
            <X size={18} />
          </button>
        </div>

        {/* STEP PROGRESS BAR */}
        <div className="px-6 pt-3 flex gap-1">
          {['MOTIF', 'CLINICAL', 'RADIOLOGY', 'RESULT'].map((s) => {
            const steps = ['MOTIF', 'CLINICAL', 'RADIOLOGY', 'RESULT'];
            const currentIdx = steps.indexOf(step);
            const active = steps.indexOf(s) <= currentIdx;
            
            // Skip clinical for Mucosal lesions
            if (s === 'CLINICAL' && motif === 'LESION') return null;

            return (
              <div 
                key={s}
                className={cn(
                  "h-1 flex-1 rounded-full transition-all duration-300",
                  active ? "bg-primary shadow-[0_0_10px_rgba(var(--primary-rgb),0.3)]" : "bg-slate-200 dark:bg-white/5"
                )}
              />
            );
          })}
        </div>

        {/* BODY */}
        <div className="flex-1 px-6 py-4 overflow-y-auto max-h-[55vh]">
          <AnimatePresence mode="wait">
            
            {/* STEP 1: MOTIF */}
            {step === 'MOTIF' && (
              <motion.div
                key="motif"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="space-y-4"
              >
                <div className="px-1">
                  <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Étape 1 : Quel est le motif principal ?</h4>
                </div>
                
                <div className="space-y-2">
                  {motifs.map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setMotif(m.id)}
                      className={cn(
                        "w-full text-left p-3.5 rounded-2xl border text-xs transition-all flex items-center justify-between group",
                        motif === m.id 
                          ? "bg-primary/10 border-primary text-primary shadow-sm" 
                          : "bg-slate-50/50 dark:bg-white/5 border-slate-200/50 dark:border-white/5 hover:border-slate-300 hover:bg-slate-50 dark:hover:bg-white/10"
                      )}
                    >
                      <div>
                        <div className="font-bold text-[12px]">{m.label}</div>
                        <div className="text-[10px] text-slate-400 mt-0.5">{m.desc}</div>
                      </div>
                      <ChevronRight size={14} className={cn("opacity-0 group-hover:opacity-100 transition-opacity", motif === m.id && "opacity-100 text-primary")} />
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* STEP 2: CLINICAL */}
            {step === 'CLINICAL' && (
              <motion.div
                key="clinical"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="space-y-5"
              >
                <div className="px-1">
                  <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Étape 2 : Examen Clinique Direct</h4>
                </div>
                
                {/* VITALITE */}
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-1">🧪 Vitalité Pulpaire (Test Froid)</label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {vitalityOptions.map(v => (
                      <button
                        key={v.id}
                        onClick={() => setVitality(v.id)}
                        className={cn(
                          "p-3 rounded-2xl border text-[10px] font-bold transition-all text-center flex flex-col justify-center min-h-[56px] leading-snug",
                          vitality === v.id
                            ? "bg-primary/10 border-primary text-primary"
                            : "bg-slate-50/50 dark:bg-white/5 border-slate-200/50 dark:border-white/5 hover:bg-slate-50 dark:hover:bg-white/10"
                        )}
                      >
                        {v.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* PERCUSSION */}
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-1">🔨 Percussion (Tapotement)</label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {percussionOptions.map(p => (
                      <button
                        key={p.id}
                        onClick={() => setPercussion(p.id)}
                        className={cn(
                          "p-3 rounded-2xl border text-[10px] font-bold transition-all text-center flex flex-col justify-center min-h-[56px] leading-snug",
                          percussion === p.id
                            ? "bg-primary/10 border-primary text-primary"
                            : "bg-slate-50/50 dark:bg-white/5 border-slate-200/50 dark:border-white/5 hover:bg-slate-50 dark:hover:bg-white/10"
                        )}
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* PALPATION */}
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-1">👉 Palpation Vestibulaire</label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {palpationOptions.map(p => (
                      <button
                        key={p.id}
                        onClick={() => setPalpation(p.id)}
                        className={cn(
                          "p-3 rounded-2xl border text-[10px] font-bold transition-all text-center flex flex-col justify-center min-h-[56px] leading-snug",
                          palpation === p.id
                            ? "bg-primary/10 border-primary text-primary"
                            : "bg-slate-50/50 dark:bg-white/5 border-slate-200/50 dark:border-white/5 hover:bg-slate-50 dark:hover:bg-white/10"
                        )}
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                </div>

              </motion.div>
            )}

            {/* STEP 3: RADIOLOGY */}
            {step === 'RADIOLOGY' && (
              <motion.div
                key="radiology"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="space-y-5"
              >
                <div className="px-1">
                  <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Étape 3 : Imagerie & Durée</h4>
                </div>

                {/* RADIO */}
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-1">📸 Observations Radiographiques</label>
                  <div className="space-y-2">
                    {radiologyOptions.map(r => (
                      <button
                        key={r.id}
                        onClick={() => setRadiology(r.id)}
                        className={cn(
                          "w-full text-left p-3.5 rounded-2xl border text-xs transition-all flex items-center justify-between group",
                          radiology === r.id 
                            ? "bg-primary/10 border-primary text-primary" 
                            : "bg-slate-50/50 dark:bg-white/5 border-slate-200/50 dark:border-white/5 hover:bg-slate-50 dark:hover:bg-white/10"
                        )}
                      >
                        <div>
                          <div className="font-bold text-[11px]">{r.label}</div>
                          <div className="text-[9px] text-slate-400 mt-0.5">{r.desc}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* DURATION (Lésion uniquement) */}
                {motif === 'LESION' && (
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-1">🕒 Présence de la Lésion</label>
                    <div className="space-y-2">
                      {durationOptions.map(d => (
                        <button
                          key={d.id}
                          onClick={() => setLesionDuration(d.id)}
                          className={cn(
                            "w-full text-left p-3.5 rounded-2xl border text-xs transition-all flex items-center justify-between group",
                            lesionDuration === d.id 
                              ? "bg-primary/10 border-primary text-primary" 
                              : "bg-slate-50/50 dark:bg-white/5 border-slate-200/50 dark:border-white/5 hover:bg-slate-50 dark:hover:bg-white/10"
                          )}
                        >
                          <div>
                            <div className="font-bold text-[11px]">{d.label}</div>
                            <div className="text-[9px] text-slate-400 mt-0.5">{d.desc}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

              </motion.div>
            )}

            {/* STEP 4: RESULT */}
            {step === 'RESULT' && (
              <motion.div
                key="result"
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.97 }}
                className="space-y-4 text-left"
              >
                {/* CLINICAL SUMMARY CARD */}
                <div className="p-4 bg-gradient-to-tr from-amber-500/10 to-yellow-500/5 rounded-[1.8rem] border border-amber-500/20 space-y-2">
                  <div className="flex items-center gap-2">
                    <Activity size={14} className="text-amber-500 animate-pulse" />
                    <span className="text-[9px] font-black text-amber-500 uppercase tracking-widest">Diagnostic Final Établi</span>
                  </div>
                  
                  <h3 className="text-sm font-black text-slate-900 dark:text-white leading-tight">
                    {result.title}
                  </h3>
                  
                  <p className="text-[11px] text-slate-600 dark:text-slate-300 font-semibold leading-relaxed">
                    {result.description}
                  </p>
                </div>

                {/* WARNINGS */}
                {result.warnings.map((w: string, idx: number) => (
                  <div key={idx} className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex gap-2.5 items-start">
                    <AlertCircle size={15} className="text-rose-600 shrink-0 mt-0.5" />
                    <p className="text-[10px] font-bold text-rose-600 leading-normal">
                      {w}
                    </p>
                  </div>
                ))}

                {/* PROTOCOL */}
                {result.protocol.length > 0 && (
                  <div className="p-4 bg-slate-50 dark:bg-white/5 rounded-2xl space-y-2 border border-slate-100 dark:border-white/5">
                    <h4 className="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
                      <ShieldCheck size={11} className="text-emerald-500" /> Recommandations Cliniques
                    </h4>
                    <ul className="space-y-1">
                      {result.protocol.map((p: string, idx: number) => (
                        <li key={idx} className="text-[10px] font-bold text-slate-700 dark:text-slate-300 list-disc list-inside">
                          {p}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* EDITABLE TREATMENT PLAN WITH HABITS INTEGRATION */}
                <div className="p-4 bg-slate-50 dark:bg-white/5 rounded-2xl space-y-3 border border-slate-100 dark:border-white/5">
                  <div className="flex items-center justify-between">
                    <h4 className="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
                      <Sparkles size={11} className="text-primary" /> Plan de Traitement Personnalisable
                    </h4>
                    {isLoadingPrices && (
                      <span className="text-[7px] font-black uppercase text-amber-500 animate-pulse">
                        🔄 Recherche habitudes...
                      </span>
                    )}
                  </div>

                  <div className="space-y-2">
                    {editableActs.map((tp, idx) => (
                      <div 
                        key={idx} 
                        className={cn(
                          "flex items-center justify-between gap-2 p-2.5 rounded-xl border transition-all text-[11px] font-bold",
                          tp.enabled 
                            ? "bg-white dark:bg-slate-900 border-slate-200/60 dark:border-white/5" 
                            : "bg-slate-100/50 dark:bg-white/2 opacity-40 border-transparent"
                        )}
                      >
                        {/* Enabled check option */}
                        <button
                          type="button"
                          onClick={() => {
                            setEditableActs(prev => prev.map((item, i) => i === idx ? { ...item, enabled: !item.enabled } : item));
                          }}
                          className={cn(
                            "w-5 h-5 rounded-lg border flex items-center justify-center transition-all",
                            tp.enabled 
                              ? "bg-primary border-primary text-white" 
                              : "border-slate-300 dark:border-white/10 text-transparent"
                          )}
                        >
                          <Check size={10} strokeWidth={4} />
                        </button>

                        {/* Phase & Description */}
                        <div className="flex-1 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                          <span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-wider w-fit">
                            {tp.phase}
                          </span>
                          <span className="text-slate-800 dark:text-white font-black truncate max-w-[200px]">
                            {tp.act}
                          </span>
                        </div>

                        {/* Price Input & Delete Button */}
                        <div className="flex items-center gap-1.5">
                          <input 
                            type="number"
                            value={tp.price === 0 ? '' : tp.price}
                            placeholder="Tarif"
                            disabled={!tp.enabled}
                            onChange={(e) => {
                              const newPrice = parseFloat(e.target.value) || 0;
                              setEditableActs(prev => prev.map((item, i) => i === idx ? { ...item, price: newPrice } : item));
                            }}
                            className="w-16 px-1.5 py-1 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-white/10 rounded-lg text-[10px] font-black text-right focus:outline-none focus:border-primary disabled:opacity-50"
                          />
                          <span className="text-[9px] font-black text-slate-400">MAD</span>
                          
                          <button
                            type="button"
                            onClick={() => {
                              setEditableActs(prev => prev.filter((_, i) => i !== idx));
                            }}
                            className="p-1 hover:bg-rose-500/10 text-slate-400 hover:text-rose-500 rounded-lg transition-colors"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* ADD ACT FORM */}
                  <div className="pt-2 border-t border-slate-200/50 dark:border-white/5 space-y-1.5">
                    <span className="text-[8px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">
                      Ajouter un acte personnalisé
                    </span>
                    <div className="flex flex-col sm:flex-row gap-1.5">
                      <select 
                        value={newActPhase} 
                        onChange={(e) => setNewActPhase(e.target.value)}
                        className="px-2 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl text-[9px] font-black uppercase text-slate-600 dark:text-slate-300"
                      >
                        <option value="DIAGNOSTIC">Diag</option>
                        <option value="CONSERVATRICE">Conservatrice</option>
                        <option value="ENDO">Endodontie</option>
                        <option value="PROTHESE">Prothèse</option>
                        <option value="PARO">Paro</option>
                        <option value="CHIRURGIE">Chirurgie</option>
                        <option value="IMPLANT">Implant</option>
                      </select>
                      
                      <input 
                        type="text" 
                        placeholder="Libellé de l'acte..." 
                        value={newActName}
                        onChange={(e) => setNewActName(e.target.value)}
                        className="flex-1 px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl text-[10px] font-semibold"
                      />
                      
                      <div className="flex items-center gap-1.5">
                        <input 
                          type="number" 
                          placeholder="Prix" 
                          value={newActPrice}
                          onChange={(e) => setNewActPrice(e.target.value)}
                          className="w-16 px-2 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl text-[10px] font-black text-right"
                        />
                        <span className="text-[9px] font-black text-slate-400 shrink-0">MAD</span>
                      </div>
                      
                      <button 
                        type="button"
                        onClick={() => {
                          if (newActName.trim()) {
                            setEditableActs(prev => [...prev, { 
                              phase: newActPhase, 
                              act: newActName.trim(), 
                              price: parseFloat(newActPrice) || 0, 
                              enabled: true 
                            }]);
                            setNewActName('');
                            setNewActPrice('');
                          }
                        }}
                        className="p-1.5 sm:px-3 bg-primary hover:bg-primary/95 text-white rounded-xl text-[10px] font-black transition-colors flex items-center justify-center gap-1 shrink-0"
                      >
                        <Plus size={12} /> <span className="sm:inline hidden">Ajouter</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Total Treatment Cost summary */}
                <div className="p-3.5 bg-slate-900 dark:bg-black/30 text-white rounded-2xl flex justify-between items-center">
                  <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Total chiffré</span>
                  <span className="text-sm font-black">
                    {editableActs.filter(a => a.enabled).reduce((sum, a) => sum + a.price, 0).toLocaleString()} MAD
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => setShowConfirm(true)}
                  className="w-full mt-2 py-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest hover:opacity-95 active:scale-98 transition-all shadow-lg flex items-center justify-center gap-2 group"
                >
                  <Check size={14} className="group-hover:scale-110 transition-transform" />
                  Appliquer au Patient
                </button>

              </motion.div>
            )}

          </AnimatePresence>
        </div>

        {/* FOOTER NAVIGATION */}
        {step !== 'RESULT' && (
          <div className="px-6 py-4 border-t border-slate-100 dark:border-white/5 flex items-center justify-between bg-slate-50/50 dark:bg-slate-955/20">
            <button
              onClick={handlePrev}
              disabled={step === 'MOTIF'}
              className="px-4 py-2 text-[9px] font-black uppercase tracking-widest text-slate-400 hover:text-slate-955 dark:hover:text-white disabled:opacity-20 flex items-center gap-1 transition-all"
            >
              <ChevronLeft size={12} /> Retour
            </button>
            
            <button
              onClick={handleNext}
              disabled={
                (step === 'MOTIF' && !motif) ||
                (step === 'CLINICAL' && (!vitality || !percussion || !palpation)) ||
                (step === 'RADIOLOGY' && !radiology) ||
                (step === 'RADIOLOGY' && motif === 'LESION' && !lesionDuration)
              }
              className="px-5 py-2.5 bg-slate-950 dark:bg-white text-white dark:text-slate-955 rounded-xl font-black text-[9px] uppercase tracking-widest hover:opacity-90 disabled:opacity-30 disabled:pointer-events-none flex items-center gap-1 transition-all"
            >
              Suivant <ChevronRight size={12} />
            </button>
          </div>
        )}

      </motion.div>

      {/* CONFIRMATION APPLY DIALOG OVERLAY */}
      <AnimatePresence>
        {showConfirm && (
          <div className="fixed inset-0 z-[10006] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowConfirm(false)}
              className="absolute inset-0 bg-slate-950/50 backdrop-blur-sm"
            />
            
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="relative w-full max-w-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-[2rem] shadow-2xl p-6 text-center space-y-4 z-10"
            >
              <div className="w-12 h-12 bg-emerald-500/10 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
                <ShieldCheck size={24} />
              </div>
              
              <div className="space-y-1.5">
                <h4 className="text-xs font-black uppercase tracking-wider">Confirmer l'application</h4>
                <p className="text-[10px] font-bold text-slate-500 leading-normal">
                  Voulez-vous appliquer définitivement ce diagnostic et ce plan de traitement personnalisé de <strong className="text-slate-900 dark:text-white font-black">{editableActs.filter(a => a.enabled).reduce((sum, a) => sum + a.price, 0).toLocaleString()} MAD</strong> à la fiche active du patient ?
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowConfirm(false)}
                  className="py-2.5 bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 text-slate-500 dark:text-slate-400 rounded-xl text-[9px] font-black uppercase tracking-widest transition-colors"
                >
                  Annuler
                </button>
                <button
                  type="button"
                  onClick={() => {
                    handleApply();
                    setShowConfirm(false);
                  }}
                  className="py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-[9px] font-black uppercase tracking-widest transition-colors"
                >
                  Confirmer et Appliquer
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
};
