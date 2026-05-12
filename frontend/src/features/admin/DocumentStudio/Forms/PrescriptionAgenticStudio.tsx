import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain, CheckCircle2, AlertCircle, Zap, RefreshCcw, ChevronRight,
  ShieldCheck, Stethoscope, Pill, Trash2, Plus, Microscope,
  Package, Droplets, FlaskConical, Wind, BadgeMinus, Hash,
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
  quantite?: number;
  non_substituable?: boolean;
}

interface PrescriptionAgenticStudioProps {
  patientId: string;
  drugs: DrugItem[];
  setDrugs: (drugs: DrugItem[]) => void;
  onUpdateDrug: (id: number, field: keyof DrugItem, val: any) => void;
  onRemoveDrug: (id: number) => void;
  onAddDrug: () => void;
  validationErrors: ValidationError[];
  onSaveHabit?: (context: string, drugs: DrugItem[]) => void;
  hasChanges?: boolean;
  coherenceWarnings?: { level: string; message: string }[];
}

const FORMES = [
  { l: 'COMPRIMÉS', icon: Pill },
  { l: 'SACHETS', icon: Package },
  { l: 'GÉLULES', icon: Pill },
  { l: 'BAIN DE BOUCHE', icon: Droplets },
  { l: 'AMPOULES', icon: FlaskConical },
  { l: 'SIROP', icon: Droplets },
  { l: 'POMMADE', icon: BadgeMinus },
  { l: 'CRÈME', icon: BadgeMinus },
  { l: 'GOUTTES', icon: Droplets },
  { l: 'SPRAY', icon: Wind },
  { l: 'AUTRE', icon: Hash },
];

function getFormeIcon(forme: string) {
  const match = FORMES.find(f => forme.startsWith(f.l) || forme.toUpperCase().startsWith(f.l));
  const Icon = match?.icon || Pill;
  return <Icon size={13} />;
}

function useDebounce<T extends (...args: any[]) => void>(fn: T, delay: number): T {
  const fnRef = useRef(fn);
  useEffect(() => { fnRef.current = fn; }, [fn]);

  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  return useCallback((...args: Parameters<T>) => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      fnRef.current(...args);
    }, delay);
  }, [delay]) as T;
}


export const PrescriptionAgenticStudio: React.FC<PrescriptionAgenticStudioProps> = ({
  patientId, drugs, setDrugs, onUpdateDrug, onRemoveDrug, onAddDrug,
  validationErrors, onSaveHabit, coherenceWarnings = [],
}) => {
  const [step, setStep] = useState<'IDLE' | 'RESEARCH' | 'ASSESSMENT' | 'PLANNING'>('IDLE');
  const [assessment, setAssessment] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [savingHabits, setSavingHabits] = useState(false);

  const [activeSearchId, setActiveSearchId] = useState<{ id: number; field: string } | null>(null);
  const [suggestions, setSuggestions] = useState<{ medications: string[]; dosages: string[]; posologies: string[] }>({
    medications: [], dosages: [], posologies: [],
  });
  const [formeDropdownCoords, setFormeDropdownCoords] = useState<{ top: number; left: number; width: number } | null>(null);
  const [presets, setPresets] = useState<any[]>([]);
  const [showPresets, setShowPresets] = useState(true);

  // --- QUICK ENTRY EVOLVED ---
  const [quickVal, setQuickVal] = useState('');
  const [quickSuggestions, setQuickSuggestions] = useState<string[]>([]);
  const [quickHighlightedIdx, setQuickHighlightedIdx] = useState(-1);

  // --- SILENT CLINICAL ASSESSMENT (Phase 2) ---
  useEffect(() => {
    if (!patientId) return;
    
    const silentResearch = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/prescriptions/agentic/assessment/${patientId}`);
        setAssessment(res.data);
      } catch (err) {
        console.error('Silent AI Error:', err);
      } finally {
        setLoading(false);
      }
    };
    silentResearch();
  }, [patientId]);

  const designTreatmentPlan = async () => {
    setLoading(true);
    setStep('PLANNING');
    try {
      const res = await api.post(`/prescriptions/agentic/design`, {
        assessment,
        patient_context: { id: patientId },
      });
      setDrugs(res.data.prescriptions.map((p: any, idx: number) => ({
        id: Date.now() + idx,
        name: p.medicament, dosage: p.dosage,
        forme: p.forme, posologie: p.posologie,
        type: 'MEDICAMENT', quantite: 1, non_substituable: false,
      })));
    } catch {
      setStep('ASSESSMENT');
    } finally {
      setLoading(false);
    }
  };

  // --- Autocomplete avec debounce (250ms) ---
  const fetchSuggestions = useCallback(async (id: number, field: string, val: string, abortSignal?: AbortSignal) => {
    try {
      if (field === 'name' && val.length >= 1) {
        const res = await api.get(`/prescriptions/habits/suggest?q=${encodeURIComponent(val)}`, { signal: abortSignal });
        setSuggestions(res.data);
      } else if ((field === 'dosage' || field === 'posologie')) {
        const drug = drugs.find(d => d.id === id);
        if (drug?.name) {
          const res = await api.get(`/prescriptions/habits/details?med_name=${encodeURIComponent(drug.name)}`, { signal: abortSignal });
          setSuggestions({ medications: [], ...res.data });
        }
      }
    } catch (err: any) {
      if (err.name === 'CanceledError') return;
      console.error('Fetch suggestions error:', err);
    }
  }, [drugs]);
  
  const fetchPresets = useCallback(async () => {
    try {
      const res = await api.get('/prescriptions/habits/presets');
      setPresets(res.data);
    } catch (err) {
      console.error('Erreur presets:', err);
    }
  }, []);

  useEffect(() => {
    fetchPresets();
  }, [fetchPresets]);

  const debouncedFetch = useDebounce(fetchSuggestions, 250);

  const handleSearch = (id: number, field: string, val: string) => {
    onUpdateDrug(id, field as keyof DrugItem, val);
    setActiveSearchId({ id, field });
    if (val.length >= 1) {
      debouncedFetch(id, field, val);
    } else {
      setSuggestions({ medications: [], dosages: [], posologies: [] });
      setActiveSearchId(null);
    }
  };

  const handleQuickSearch = useDebounce(async (val: string) => {
    const trimmed = val.trim();
    // On cherche le médicament (le premier mot)
    const searchPart = trimmed.split(' ')[0];
    
    if (searchPart.length < 1) {
      setQuickSuggestions([]);
      return;
    }

    try {
      const res = await api.get(`/prescriptions/habits/suggest?q=${encodeURIComponent(searchPart)}`);
      const meds = res.data.medications || [];
      console.log(`[QuickSearch] Found ${meds.length} meds for "${searchPart}"`);
      setQuickSuggestions(meds);
    } catch (err) {
      console.error('Quick search error:', err);
    }
  }, 300);


  const parseQuickEntry = (text: string): DrugItem => {
    const originalText = text;
    const parts = text.trim().split(/\s+/);
    const drug: DrugItem = {
      id: Date.now(),
      name: parts[0].toUpperCase(),
      dosage: '',
      forme: 'COMPRIMÉS',
      posologie: '',
      type: 'MEDICAMENT',
      quantite: 1,
      non_substituable: false
    };
    // 1. Détection de la forme
    let formeTextFound = '';
    const formesMap: Record<string, string> = {
      'sachet': 'SACHETS',
      'gelule': 'GÉLULES',
      'gélule': 'GÉLULES',
      'bain': 'BAIN DE BOUCHE',
      'sirop': 'SIROP',
      'pommade': 'POMMADE',
      'crème': 'CRÈME',
      'creme': 'CRÈME',
      'goutte': 'GOUTTES',
      'ampoule': 'AMPOULES',
      'spray': 'SPRAY',
      'comprimé': 'COMPRIMÉS',
      'comprime': 'COMPRIMÉS',
      'cp': 'COMPRIMÉS'
    };

    for (const [key, value] of Object.entries(formesMap)) {
      const reg = new RegExp(`\\b${key}s?\\b`, 'i');
      const m = text.match(reg);
      if (m) {
        drug.forme = value;
        formeTextFound = m[0];
        break;
      }
    }

    // 2. Détection du dosage (ex: 1g, 500mg)
    let dosageTextFound = '';
    const dosageMatch = text.match(/\b\d+(\s?)(g|mg|mcg|ml|l|ui)\b/i);
    if (dosageMatch) {
      drug.dosage = dosageMatch[0].toUpperCase().replace(/\s/g, '');
      dosageTextFound = dosageMatch[0];
    }

    // 3. Détection de la quantité
    let qtyTextFound = '';
    const qtyMatch = text.match(/(qsp|x|qty|qté|qte)\s*(\d+)/i) || text.match(/\b(\d+)\s*(boite|boîte|pack|unité)s?\b/i);
    if (qtyMatch) {
      const num = qtyMatch[2] || qtyMatch[1];
      drug.quantite = parseInt(num);
      qtyTextFound = qtyMatch[0];
    }

    // 4. Extraction de la posologie (le reste du texte)
    let poso = originalText;
    
    // On retire le nom s'il est au début
    if (poso.toUpperCase().startsWith(drug.name)) {
      poso = poso.substring(drug.name.length);
    }
    
    // Retrait chirurgical des éléments identifiés pour ne laisser que la posologie
    if (dosageTextFound) poso = poso.replace(dosageTextFound, '');
    if (formeTextFound) poso = poso.replace(formeTextFound, '');
    if (qtyTextFound) poso = poso.replace(qtyTextFound, '');

    drug.posologie = poso.replace(/\s+/g, ' ').trim();
    
    return drug;
  };

  const applySuggestion = useCallback((id: number, field: string, val: string) => {
    onUpdateDrug(id, field as keyof DrugItem, val);
    setSuggestions({ medications: [], dosages: [], posologies: [] });
    setActiveSearchId(null);
    if (field === 'name') {
      api.get(`/prescriptions/habits/details?med_name=${encodeURIComponent(val)}`).then(res => {
        if (res.data.dosages?.length === 1) onUpdateDrug(id, 'dosage', res.data.dosages[0]);
        if (res.data.posologies?.length === 1) onUpdateDrug(id, 'posologie', res.data.posologies[0]);
      }).catch(() => {});
    }
  }, [onUpdateDrug]);

  // Ajouter une molécule depuis les suggestions IA — sans race condition
  const addMolecule = useCallback((molecule: string) => {
    const newId = Date.now();
    const newDrug: DrugItem = {
      id: newId, name: molecule, dosage: '', forme: 'COMPRIMÉS',
      posologie: '', type: 'MEDICAMENT', quantite: 1, non_substituable: false,
    };
    setDrugs([...drugs, newDrug]);
    // Récupère les détails habituels après que le drug est dans le state
    api.get(`/prescriptions/habits/details?med_name=${encodeURIComponent(molecule)}`).then(res => {
      if (res.data.dosages?.length === 1) onUpdateDrug(newId, 'dosage', res.data.dosages[0]);
      if (res.data.posologies?.length === 1) onUpdateDrug(newId, 'posologie', res.data.posologies[0]);
    }).catch(() => {});
  }, [drugs, setDrugs, onUpdateDrug]);

  // Batch save — un seul appel API
  const handleBatchSave = async () => {
    const validDrugs = drugs.filter(d => d.name.trim());
    if (!validDrugs.length) return;
    setSavingHabits(true);
    try {
      await api.post('/prescriptions/habits/record-batch', validDrugs.map(d => ({
        medication_name: d.name, dosage: d.dosage, posologie: d.posologie,
      })));
      if (onSaveHabit && assessment?.act_context) {
        onSaveHabit(assessment.act_context, drugs);
      } else {
        alert('Habitudes mémorisées.');
      }
    } catch {
      alert('Erreur lors de la mémorisation.');
    } finally {
      setSavingHabits(false);
    }
  };

  // Fermeture du dropdown Forme au scroll ou resize
  useEffect(() => {
    if (!formeDropdownCoords) return;
    const close = () => { setActiveSearchId(null); setFormeDropdownCoords(null); };
    window.addEventListener('scroll', close, true);
    window.addEventListener('resize', close);
    return () => { window.removeEventListener('scroll', close, true); window.removeEventListener('resize', close); };
  }, [formeDropdownCoords]);

  const handleFormeOpen = (e: React.MouseEvent<HTMLButtonElement>, drugId: number) => {
    e.stopPropagation();
    if (activeSearchId?.id === drugId && activeSearchId?.field === 'forme_dropdown') {
      setActiveSearchId(null);
      setFormeDropdownCoords(null);
    } else {
      const rect = e.currentTarget.getBoundingClientRect();
      setFormeDropdownCoords({ top: rect.bottom + 8, left: rect.left, width: rect.width });
      setActiveSearchId({ id: drugId, field: 'forme_dropdown' });
    }
  };

  // Keyboard navigation dans les suggestions
  const [highlightedIdx, setHighlightedIdx] = useState(-1);
  useEffect(() => setHighlightedIdx(-1), [activeSearchId]);

  const getActiveSuggestions = (field: string): string[] => {
    if (field === 'name') return suggestions.medications;
    if (field === 'dosage') return suggestions.dosages;
    if (field === 'posologie') return suggestions.posologies;
    return [];
  };

  const handleKeyDown = (e: React.KeyboardEvent, id: number, field: string) => {
    const list = getActiveSuggestions(field);
    if (!list.length) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setHighlightedIdx(i => Math.min(i + 1, list.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setHighlightedIdx(i => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && highlightedIdx >= 0) { e.preventDefault(); applySuggestion(id, field, list[highlightedIdx]); }
    if (e.key === 'Escape') { setSuggestions({ medications: [], dosages: [], posologies: [] }); setActiveSearchId(null); }
  };

  return (
    <div className="space-y-6">
      {/* HEADER ELITE CONDENSÉ */}
      <div className="flex items-center justify-between bg-white/40 p-4 rounded-[2rem] border border-white/60 backdrop-blur-2xl shadow-lg shadow-primary/5">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-br from-primary to-blue-600 text-white rounded-xl flex items-center justify-center relative z-10 shadow-md shadow-primary/30">
              <Brain size={20} className={loading ? 'animate-pulse' : ''} />
            </div>
          </div>
          <div>
            <h3 className="text-[11px] font-black text-slate-800 uppercase tracking-[0.2em] leading-none mb-1 flex items-center gap-2">
              IAmina Intelligence
              <span className="bg-primary/10 text-primary text-[7px] px-1.5 py-0.5 rounded-full">v4.8</span>
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* COHERENCE BADGE COMPACT */}
          <div className={cn(
            "px-3 py-1.5 rounded-xl border transition-all flex items-center gap-2",
            coherenceWarnings.length === 0 
              ? "bg-emerald-50/50 border-emerald-100 text-emerald-600" 
              : "bg-amber-50/50 border-amber-100 text-amber-600 animate-pulse"
          )}>
            <ShieldCheck size={12} className={coherenceWarnings.length > 0 ? "hidden" : ""} />
            <AlertCircle size={12} className={coherenceWarnings.length === 0 ? "hidden" : ""} />
            <span className="text-[8px] font-black uppercase tracking-widest">
              {coherenceWarnings.length === 0 ? "Cohérence OK" : "Audit Requis"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {loading && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-primary/5 text-primary rounded-xl">
              <RefreshCcw size={12} className="animate-spin" />
              <span className="text-[8px] font-black uppercase tracking-widest">Analyse en cours...</span>
            </div>
          )}
          
          <button
            onClick={() => { setStep('IDLE'); setAssessment(null); }}
            className="p-2 bg-slate-100 text-slate-400 rounded-xl hover:bg-slate-200 transition-all"
          >
            <RefreshCcw size={14} />
          </button>
        </div>
      </div>

      {/* COMMAND BAR & SPEED-PILLS (Phase 3) */}
      <div className="space-y-4">
          <div className="relative group">
            <div className="absolute inset-y-0 left-6 flex items-center text-primary/40 group-focus-within:text-primary transition-colors">
              <Zap size={18} />
            </div>
            <input
              type="text"
              value={quickVal}
              onChange={(e) => {
                const v = e.target.value;
                setQuickVal(v);
                handleQuickSearch(v);
              }}
              className="w-full bg-white/60 border border-white/80 backdrop-blur-xl rounded-[2rem] pl-16 pr-8 py-5 text-sm font-bold text-slate-800 focus:bg-white focus:border-primary/30 focus:shadow-2xl focus:shadow-primary/5 transition-all outline-none placeholder:text-slate-300"
              placeholder="Saisie Rapide : Taper un médicament, un dosage ou une posologie... (Ex: Augmentin 1g sachet 2x/j)"
              onKeyDown={(e) => {
                if (e.key === 'ArrowDown') {
                  e.preventDefault();
                  setQuickHighlightedIdx(i => Math.min(i + 1, quickSuggestions.length - 1));
                } else if (e.key === 'ArrowUp') {
                  e.preventDefault();
                  setQuickHighlightedIdx(i => Math.max(i - 1, 0));
                } else if (e.key === 'Enter') {
                  e.preventDefault();
                  let finalVal = quickVal;
                  if (quickHighlightedIdx >= 0) {
                    const sugg = quickSuggestions[quickHighlightedIdx];
                    const parts = quickVal.split(' ');
                    parts[0] = sugg; // On remplace le premier mot par la suggestion
                    finalVal = parts.join(' ');
                  }
                  
                  if (finalVal.trim()) {
                    const newDrug = parseQuickEntry(finalVal);
                    setDrugs([newDrug, ...drugs]);
                    setQuickVal('');
                    setQuickSuggestions([]);
                    setQuickHighlightedIdx(-1);
                    setStep('PLANNING');
                  }
                } else if (e.key === 'Escape') {
                  setQuickSuggestions([]);
                }
              }}
              onBlur={() => setTimeout(() => setQuickSuggestions([]), 200)}
            />
            
            {/* SUGGESTIONS SAISIE RAPIDE */}
            <AnimatePresence>
              {quickSuggestions.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute left-6 right-6 top-full mt-2 bg-white border border-slate-200 rounded-3xl shadow-2xl z-[999] overflow-hidden py-3"

                >
                  <div className="px-6 py-2 border-b border-slate-50 mb-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Suggestions de médicaments</span>
                  </div>
                  {quickSuggestions.map((s, i) => (
                    <button
                      key={s}
                      onClick={() => {
                        const parts = quickVal.split(' ');
                        parts[0] = s;
                        const final = parts.join(' ');
                        const newDrug = parseQuickEntry(final);
                        setDrugs([newDrug, ...drugs]);
                        setQuickVal('');
                        setQuickSuggestions([]);
                        setStep('PLANNING');
                      }}
                      className={cn(
                        "w-full px-8 py-3 text-left text-sm font-bold transition-all flex items-center justify-between group",
                        i === quickHighlightedIdx ? "bg-primary text-white" : "text-slate-600 hover:bg-primary/5 hover:text-primary"
                      )}
                    >
                      <span>{s}</span>
                      <ChevronRight size={14} className={cn("transition-transform", i === quickHighlightedIdx ? "translate-x-1" : "opacity-0 group-hover:opacity-100")} />
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>

            <div className="absolute right-6 top-1/2 -translate-y-1/2 flex items-center gap-2">
              <span className="text-[8px] font-black text-slate-300 uppercase tracking-widest border border-slate-200 px-2 py-1 rounded-lg">↵ ENTER POUR AJOUTER</span>
            </div>
          </div>

        {/* SPEED-PILLS : Favoris du Docteur */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-hide px-2">
          {['DOLIPRANE 1G', 'AUGMENTIN 1G', 'ANTADYS 100MG', 'SOLUPRED 20MG', 'HEXTRIL'].map(fav => (
            <button
              key={fav}
              onClick={() => {
                const [name, dose] = fav.split(' ');
                setDrugs([{
                  id: Date.now(),
                  name,
                  dosage: dose || '',
                  forme: fav.includes('HEXTRIL') ? 'BAIN DE BOUCHE' : 'COMPRIMÉS',
                  posologie: '',
                  type: 'MEDICAMENT',
                  quantite: 1
                }, ...drugs]);
                setStep('PLANNING');
              }}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-[9px] font-black text-slate-600 uppercase hover:bg-primary hover:text-white hover:border-primary transition-all whitespace-nowrap shadow-sm group"
            >
              <Pill size={10} className="group-hover:rotate-12 transition-transform" />
              {fav}
            </button>
          ))}
        </div>
      </div>

      {/* PRESETS BAR */}
      <AnimatePresence>
        {presets.length > 0 && showPresets && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide"
          >
            <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest shrink-0 ml-4">Presets :</span>
            {presets.map(p => (
              <button
                key={p.id}
                onClick={() => {
                  const newDrugs = p.drugs.map((d: any, i: number) => ({
                    id: Date.now() + i,
                    name: d.name,
                    dosage: d.dosage,
                    forme: d.forme || 'COMPRIMÉS',
                    posologie: d.posologie,
                    type: 'MEDICAMENT',
                    quantite: 1
                  }));
                  setDrugs(newDrugs);
                }}
                className="px-4 py-2 bg-white border border-slate-200 rounded-2xl text-[9px] font-black text-slate-600 uppercase hover:border-primary hover:text-primary hover:bg-primary/5 transition-all whitespace-nowrap shadow-sm active:scale-95 flex items-center gap-2 group/chip"
              >
                <div className="w-1 h-1 rounded-full bg-slate-300 group-hover/chip:bg-primary transition-colors" />
                {p.act_context}
              </button>
            ))}
            <button onClick={() => setShowPresets(false)} className="p-1.5 text-slate-300 hover:text-slate-500"><BadgeMinus size={14} /></button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {step === 'RESEARCH' && (
          <motion.div
            key="research"
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            className="p-16 flex flex-col items-center justify-center text-center space-y-8 bg-white/30 rounded-[3rem] border border-dashed border-primary/30 backdrop-blur-sm"
          >
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full animate-pulse scale-150" />
              <div className="w-20 h-20 bg-white rounded-3xl flex items-center justify-center shadow-2xl relative z-10 border border-primary/10">
                <RefreshCcw size={40} className="text-primary animate-spin" style={{ color: 'var(--primary)' }} />
              </div>
            </div>
            <div className="max-w-sm">
              <h4 className="text-xl font-black text-slate-800 mb-3">Analyse du dossier clinique...</h4>
              <p className="text-xs text-slate-500 font-bold leading-relaxed">
                Apprentissage de vos habitudes, calcul des doses et validation des interactions médicamenteuses.
              </p>
            </div>
          </motion.div>
        )}

        {step === 'ASSESSMENT' && assessment && (
          <motion.div
            key="assessment"
            initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7 space-y-6">
                <div className="bg-white/60 p-8 rounded-[2.5rem] border border-white/60 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
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
                    {assessment.risques_identifies?.length > 0 ? (
                      <div className="p-4 bg-red-50 rounded-2xl border border-red-100">
                        <span className="text-[9px] font-black text-red-600 uppercase tracking-widest block mb-2">Risques Détectés</span>
                        <ul className="space-y-1.5">
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
                      {assessment.dosage_note && <p className="text-[10px] text-primary/60 font-black mt-2 uppercase">{assessment.dosage_note}</p>}
                    </div>
                  </div>
                </div>
              </div>

              <div className="lg:col-span-5 space-y-6">
                <div className="bg-slate-900 p-8 rounded-[2.5rem] text-white shadow-2xl shadow-primary/20 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-12 bg-primary/20 blur-[100px] rounded-full group-hover:scale-150 transition-transform duration-1000" />
                  <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-6">
                      <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                        <Stethoscope size={20} className="text-blue-300" />
                      </div>
                      <h4 className="text-xs font-black uppercase tracking-widest">Suggestions</h4>
                    </div>
                    <div className="space-y-3 mb-8">
                      {assessment.recommandations_moleculaires?.map((m: any, i: number) => (
                        <button
                          key={i}
                          onClick={() => addMolecule(m.molecule)}
                          className="w-full text-left bg-white/5 p-3 rounded-2xl border border-white/10 hover:bg-primary hover:border-primary hover:shadow-lg hover:shadow-primary/20 transition-all group/sugg"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-[10px] font-black text-blue-300 uppercase group-hover/sugg:text-white transition-colors">{m.molecule}</span>
                            <div className="flex gap-1">
                              {m.noms_commerciaux?.slice(0, 2).map((n: string) => (
                                <span key={n} className="px-1.5 py-0.5 bg-white/10 rounded text-[7px] font-black uppercase group-hover/sugg:bg-white/20">{n}</span>
                              ))}
                            </div>
                          </div>
                          <p className="text-[9px] text-white/40 font-bold leading-tight group-hover/sugg:text-white/70">{m.justification}</p>
                        </button>
                      ))}
                    </div>
                    <button
                      onClick={designTreatmentPlan}
                      className="w-full py-4 bg-primary text-white rounded-2xl text-[11px] font-black uppercase tracking-[0.2em] shadow-xl shadow-primary/40 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3"
                      style={{ backgroundColor: 'var(--primary)' }}
                    >
                      Établir l'Ordonnance <ChevronRight size={18} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {(step === 'PLANNING' || step === 'IDLE' || (step === 'ASSESSMENT' && drugs.some(d => d.name))) && (
          <motion.div key="planning" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
            {step === 'PLANNING' && loading && (
              <div className="p-20 text-center bg-white/40 rounded-[3rem] border border-dashed border-primary/20 flex flex-col items-center gap-6 backdrop-blur-sm">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                  <Zap size={32} className="text-primary animate-bounce" style={{ color: 'var(--primary)' }} />
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
                    key={drug.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={cn(
                      'bg-white/60 p-4 rounded-[1.8rem] border transition-all group relative backdrop-blur-xl',
                      fieldError ? 'border-red-200 bg-red-50/10' : 'border-white/80 hover:bg-white hover:shadow-xl hover:shadow-slate-200/20',
                      isRadio && 'border-amber-100 bg-amber-50/5',
                    )}
                  >
                    <div className="grid grid-cols-12 gap-3 items-center">
                      {/* Toggle Compact */}
                      <div className="col-span-12 lg:col-span-2 flex items-center gap-1.5 p-1 bg-slate-100/50 rounded-xl w-fit border border-slate-200/30">
                        <button
                          type="button"
                          onClick={() => { onUpdateDrug(drug.id, 'type', 'MEDICAMENT'); if (!drug.forme) onUpdateDrug(drug.id, 'forme', 'COMPRIMÉS'); }}
                          className={cn(
                            'p-2 rounded-lg transition-all',
                            !isRadio ? 'bg-white text-primary shadow-sm' : 'text-slate-400 hover:text-slate-500',
                          )}
                          title="Médicament"
                        >
                          <Pill size={14} style={!isRadio ? { color: 'var(--primary)' } : {}} />
                        </button>
                        <button
                          type="button"
                          onClick={() => { onUpdateDrug(drug.id, 'type', 'EXAMEN'); onUpdateDrug(drug.id, 'dosage', ''); onUpdateDrug(drug.id, 'forme', ''); onUpdateDrug(drug.id, 'posologie', ''); }}
                          className={cn(
                            'p-2 rounded-lg transition-all',
                            isRadio ? 'bg-white text-amber-600 shadow-sm' : 'text-slate-400 hover:text-slate-500',
                          )}
                          title="Radio / Examen"
                        >
                          <Microscope size={14} />
                        </button>
                      </div>

                      {/* Nom & Forme/Dose */}
                      <div className={cn('relative', isRadio ? 'col-span-12 lg:col-span-10' : 'col-span-12 lg:col-span-4')}>
                        <div className="space-y-1">
                          <input
                            type="text"
                            data-tour="prescription-name-input"
                            className="w-full bg-transparent border-none p-0 focus:ring-0 font-black text-slate-800 text-sm uppercase placeholder:text-slate-400 tracking-tight"
                            placeholder={isRadio ? "NOM DE L'EXAMEN..." : 'MÉDICAMENT...'}
                            value={drug.name}
                            onChange={e => handleSearch(drug.id, 'name', e.target.value.toUpperCase())}
                            onFocus={() => { if (drug.name.length >= 1) handleSearch(drug.id, 'name', drug.name); }}
                            onKeyDown={e => handleKeyDown(e, drug.id, 'name')}
                            onBlur={() => setTimeout(() => setActiveSearchId(null), 200)}
                          />

                          {!isRadio && (
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={e => handleFormeOpen(e, drug.id)}
                                className="bg-slate-100/50 px-2 py-1 rounded-lg text-[8px] font-black text-primary uppercase tracking-widest border border-transparent hover:bg-white hover:border-primary/20 transition-all flex items-center gap-1.5"
                                style={{ color: 'var(--primary)' }}
                              >
                                {getFormeIcon(drug.forme)}
                                {drug.forme.startsWith('AUTRE') ? 'AUTRE' : (drug.forme || 'FORME')}
                              </button>
                              
                              {drug.forme.startsWith('AUTRE') && (
                                <input
                                  type="text"
                                  className="w-24 bg-white/50 border border-slate-200 px-2 py-1 rounded-lg focus:ring-0 text-[9px] font-black text-slate-700 uppercase tracking-widest placeholder:text-slate-400 focus:border-primary/40 transition-colors"
                                  placeholder="PRÉCISER..."
                                  value={drug.forme.includes(':') ? drug.forme.split(':')[1].trim() : ''}
                                  onChange={e => onUpdateDrug(drug.id, 'forme', `AUTRE: ${e.target.value}`)}
                                />
                              )}
                              
                              <div className="flex items-center gap-1 bg-white/50 px-2 py-1 rounded-lg border border-slate-100">
                                <span className="text-[7px] font-black text-slate-500 uppercase tracking-widest">Dose :</span>
                                <input
                                  type="text"
                                  className="w-20 bg-transparent border-none p-0 focus:ring-0 text-[9px] font-black text-slate-600 uppercase tracking-widest placeholder:text-slate-400"
                                  placeholder="500MG..."
                                  value={drug.dosage}
                                  onFocus={() => handleSearch(drug.id, 'dosage', drug.dosage)}
                                  onChange={e => handleSearch(drug.id, 'dosage', e.target.value)}
                                />
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Autocomplete nom */}
                        <AnimatePresence>
                          {activeSearchId?.id === drug.id && activeSearchId?.field === 'name' && (suggestions.medications.length > 0) && (
                            <motion.div
                              initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
                              className="absolute left-0 top-full mt-2 w-full min-w-[200px] bg-white border border-slate-100 rounded-xl shadow-2xl z-[100] overflow-hidden py-1 max-h-[300px] overflow-y-auto custom-scrollbar"
                            >
                              {suggestions.medications.map((m, i) => (
                                <button
                                  key={m}
                                  onClick={() => applySuggestion(drug.id, 'name', m)}
                                  className={cn(
                                    'w-full px-4 py-2 text-left text-[10px] font-black text-slate-600 transition-colors flex items-center justify-between',
                                    i === highlightedIdx ? 'bg-primary/10 text-primary' : 'hover:bg-primary/5 hover:text-primary',
                                  )}
                                >
                                  {m}
                                  <ChevronRight size={12} className="opacity-40" />
                                </button>
                              ))}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>

                      {/* Posologie */}
                      <div className={cn('relative h-full', isRadio ? 'hidden' : 'col-span-12 lg:col-span-5')}>
                        <div className="bg-slate-50/50 p-2.5 rounded-xl border border-slate-100 group-hover:bg-white transition-all focus-within:shadow-md focus-within:shadow-primary/5">
                          <textarea
                            rows={1}
                            className="w-full bg-transparent border-none p-0 text-[11px] font-bold text-slate-600 focus:ring-0 resize-none placeholder:text-slate-400 leading-tight"
                            placeholder="Posologie..."
                            value={drug.posologie}
                            onFocus={() => handleSearch(drug.id, 'posologie', drug.posologie)}
                            onChange={e => {
                              handleSearch(drug.id, 'posologie', e.target.value);
                              e.target.style.height = 'auto';
                              e.target.style.height = `${e.target.scrollHeight}px`;
                            }}
                          />
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="col-span-12 lg:col-span-1 flex justify-end">
                        <button
                          onClick={() => onRemoveDrug(drug.id)}
                          className="p-2 text-slate-200 hover:text-red-500 transition-all opacity-0 group-hover:opacity-100"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* ELITE DOUBLE CHECK / AUDIT SECTION */}
            <div className="mt-8 bg-slate-900 rounded-[2.5rem] p-8 text-white relative overflow-hidden shadow-2xl shadow-slate-900/20">
              <div className="absolute top-0 right-0 p-20 bg-primary/10 blur-[100px] rounded-full" />
              
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                      <ShieldCheck size={22} className={coherenceWarnings.length > 0 ? "text-amber-400" : "text-emerald-400"} />
                    </div>
                    <div>
                      <h4 className="text-xs font-black uppercase tracking-widest">Audit de Cohérence Final</h4>
                      <p className="text-[10px] font-bold text-slate-400">Vérification croisée avec le dossier patient</p>
                    </div>
                  </div>
                  {coherenceWarnings.length === 0 && (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/20 border border-emerald-500/30 rounded-xl">
                      <CheckCircle2 size={12} className="text-emerald-400" />
                      <span className="text-[9px] font-black uppercase text-emerald-400 tracking-widest">Validation de sécurité ok</span>
                    </div>
                  )}
                </div>

                {coherenceWarnings.length > 0 ? (
                  <div className="space-y-3">
                    {coherenceWarnings.map((w, i) => (
                      <div key={i} className="flex items-start gap-4 p-4 bg-white/5 rounded-2xl border border-white/10 hover:bg-white/10 transition-all">
                        <AlertCircle size={18} className={w.level === 'critical' ? "text-red-400" : "text-amber-400"} />
                        <p className="text-[11px] font-bold text-slate-200 leading-relaxed">{w.message}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-white/5 rounded-2xl border border-white/5 italic">
                    <p className="text-[10px] text-slate-400 font-medium">Aucune interaction ou risque majeur détecté pour cette sélection. Le plan de traitement respecte les standards de sécurité IAmina.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Actions bas de formulaire */}
            <div className="flex gap-4 mt-6">
              <button
                onClick={onAddDrug}
                className="flex-1 py-5 border-2 border-dashed border-slate-200 text-slate-400 rounded-[2.5rem] flex items-center justify-center gap-3 hover:border-primary hover:text-primary hover:bg-primary/5 transition-all font-black text-xs uppercase tracking-widest"
              >
                <Plus size={20} /> Ajouter une ligne
              </button>

              <button
                onClick={handleBatchSave}
                disabled={savingHabits}
                className="ml-auto px-8 py-5 bg-white text-slate-800 border border-slate-200 rounded-[2.5rem] flex items-center justify-center gap-3 hover:bg-slate-50 transition-all font-black text-xs uppercase tracking-widest shadow-lg shadow-slate-200/50 disabled:opacity-50"
                title="Action globale : enregistre vos habitudes en base de données"
              >
                <Brain size={20} className="text-primary" style={{ color: 'var(--primary)' }} />
                {savingHabits ? 'Mémorisation...' : 'Mémoriser mes habitudes'}
              </button>
            </div>

          </motion.div>
        )}
      </AnimatePresence>

      {/* Dropdown Forme — position: fixed pour échapper aux overflow-y-auto parents */}
      <AnimatePresence>
        {activeSearchId?.field === 'forme_dropdown' && formeDropdownCoords && (() => {
          const activeDrug = drugs.find(d => d.id === activeSearchId.id);
          return (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 8 }}
              style={{
                position: 'fixed',
                top: formeDropdownCoords.top,
                left: formeDropdownCoords.left,
                width: Math.max(formeDropdownCoords.width, 208),
                zIndex: 200,
              }}
              className="bg-white border border-slate-100 rounded-2xl shadow-2xl overflow-hidden py-2"
            >
              {FORMES.map(f => {
                const Icon = f.icon;
                return (
                  <button
                    key={f.l}
                    onClick={() => {
                      onUpdateDrug(activeSearchId.id, 'forme', f.l === 'AUTRE' ? 'AUTRE: ' : f.l);
                      setActiveSearchId(null);
                      setFormeDropdownCoords(null);
                    }}
                    className={cn(
                      'w-full px-5 py-2.5 text-left text-[10px] font-black uppercase tracking-widest flex items-center gap-3 transition-colors',
                      activeDrug?.forme.startsWith(f.l) ? 'bg-primary/10 text-primary' : 'text-slate-500 hover:bg-slate-50 hover:text-primary',
                    )}
                  >
                    <Icon size={14} /> {f.l}
                  </button>
                );
              })}
            </motion.div>
          );
        })()}
      </AnimatePresence>

      {/* Overlay fermeture dropdowns */}
      {(suggestions.medications.length > 0 || suggestions.dosages.length > 0 || suggestions.posologies.length > 0 || activeSearchId?.field === 'forme_dropdown') && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setSuggestions({ medications: [], dosages: [], posologies: [] });
            setActiveSearchId(null);
            setFormeDropdownCoords(null);
          }}
        />
      )}
    </div>
  );
};
