import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain, CheckCircle2, AlertCircle, Zap, RefreshCcw, ChevronRight,
  ShieldCheck, Stethoscope, Loader2, Plus, ChevronDown,
} from 'lucide-react';
import { cn } from '../../../../utils/cn';
import { api } from '../../../../services/api';
import toast from 'react-hot-toast';
import type { ValidationError } from '../useDocumentGenerator';
import type { MedicationInputSource } from '../normalizeMedicationForPatient';
import {
  pharmacologyReviewMessage,
  resolveAndNormalizeMedication,
} from '../PrescriptionPharmacologyPipeline';

import type { DrugItem } from './prescriptionTypes';
import { FORMES, KIN_PRESET, DEFAULT_MOROCCO_PRESETS, fuzzyMatch } from './prescriptionTypes';
import { DrugRow } from './DrugRow';
import { QuickEntryBar } from './QuickEntryBar';
import { PrescriptionGuideModal } from './PrescriptionGuideModal';

export type { DrugItem };

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

function useDebounce<T extends (...args: any[]) => void>(fn: T, delay: number): T {
  const fnRef = useRef(fn);
  useEffect(() => { fnRef.current = fn; }, [fn]);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  return useCallback((...args: Parameters<T>) => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => { fnRef.current(...args); }, delay);
  }, [delay]) as T;
}

export const PrescriptionAgenticStudio: React.FC<PrescriptionAgenticStudioProps> = ({
  patientId, drugs, setDrugs, onUpdateDrug, onRemoveDrug, onAddDrug,
  validationErrors, coherenceWarnings = [],
}) => {
  const [step, setStep] = useState<'IDLE' | 'RESEARCH' | 'ASSESSMENT' | 'PLANNING'>('IDLE');
  const [assessment, setAssessment] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [activeSearchId, setActiveSearchId] = useState<{ id: number; field: string } | null>(null);
  const [suggestions, setSuggestions] = useState<{ medications: string[]; dosages: string[]; posologies: string[] }>({
    medications: [], dosages: [], posologies: [],
  });
  const [medChecks, setMedChecks] = useState<Record<number, { known: boolean; exists?: boolean; available_mg?: number[]; dci?: string }>>({});
  const [pharmacologyReviews, setPharmacologyReviews] = useState<Record<number, string[]>>({});
  const [formeDropdownCoords, setFormeDropdownCoords] = useState<{ top: number; left: number; width: number } | null>(null);
  const [presets, setPresets] = useState<any[]>([]);
  const [showPresets, setShowPresets] = useState(true);
  const [selectedUserPreset, setSelectedUserPreset] = useState('');
  const [savingAsPreset, setSavingAsPreset] = useState(false);
  const [showSavePresetModal, setShowSavePresetModal] = useState(false);
  const [newPresetName, setNewPresetName] = useState('');
  const [patientAdvice, setPatientAdvice] = useState('');
  const [showPatientAdvice, setShowPatientAdvice] = useState(false);
  const [forcedDrugs, setForcedDrugs] = useState<number[]>([]);
  const [showGuideModal, setShowGuideModal] = useState(false);
  const [guideWeight, setGuideWeight] = useState(0);
  const [guideAge, setGuideAge] = useState(0);
  const [guideCategory, setGuideCategory] = useState<string>('TOUS');
  const [guideSearch, setGuideSearch] = useState('');
  const [guideNationalResults, setGuideNationalResults] = useState<Array<{ nom: string; dci: string; dosage: string; unite: string; forme: string }>>([]);
  const [guideSearching, setGuideSearching] = useState(false);
  const [quickVal, setQuickVal] = useState('');
  const [quickSuggestions, setQuickSuggestions] = useState<string[]>([]);
  const [quickHighlightedIdx, setQuickHighlightedIdx] = useState(-1);
  const [highlightedIdx, setHighlightedIdx] = useState(-1);
  const [quickExpanded, setQuickExpanded] = useState(true);

  const rememberPharmacologyResult = useCallback((id: number, result: Awaited<ReturnType<typeof resolveAndNormalizeMedication>>) => {
    if (result.dictionaryResult) {
      setMedChecks(prev => ({ ...prev, [id]: result.dictionaryResult }));
    }
    const reviewMessage = pharmacologyReviewMessage(result);
    setPharmacologyReviews(prev => {
      const next = { ...prev };
      if (reviewMessage) next[id] = [reviewMessage];
      else delete next[id];
      return next;
    });
  }, []);

  const normalizeCandidate = useCallback(async (
    drug: DrugItem,
    source: MedicationInputSource,
    practitionerExplicit?: { dosage?: boolean; posology?: boolean },
  ): Promise<DrugItem> => {
    const result = await resolveAndNormalizeMedication({
      drug,
      source,
      assessment,
      practitionerExplicit,
    });
    rememberPharmacologyResult(drug.id, result);
    return result.drug;
  }, [assessment, rememberPharmacologyResult]);

  // --- Silent clinical assessment ---
  useEffect(() => {
    if (!patientId) return;
    const silentResearch = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/prescriptions/agentic/assessment/${patientId}`);
        setAssessment(res.data);
        if (res.data?.age != null) {
          setGuideAge(res.data.age);
          const w = res.data.weight ?? res.data.poids;
          setGuideWeight(typeof w === 'number' && Number.isFinite(w) && w > 0 ? w : 0);
        }
      } catch (err) {
        console.error('Assessment Error:', err);
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
      const normalized = await Promise.all(res.data.prescriptions.map(async (p: any, idx: number) => {
        const candidate: DrugItem = {
          id: Date.now() + idx,
          name: p.medicament, dosage: p.dosage,
          forme: p.forme, posologie: p.posologie,
          type: 'MEDICAMENT', quantite: 1, non_substituable: false,
        };
        return normalizeCandidate(candidate, 'assessment');
      }));
      setDrugs(normalized);
    } catch {
      setStep('ASSESSMENT');
    } finally {
      setLoading(false);
    }
  };

  // --- Presets ---
  const fetchPresets = useCallback(async () => {
    try {
      const res = await api.get('/prescriptions/habits/presets');
      setPresets(res.data);
    } catch (err) {
      console.error('Erreur presets:', err);
    }
  }, []);

  useEffect(() => { fetchPresets(); }, [fetchPresets]);

  const deletePreset = async (actCode: string) => {
    if (!window.confirm(`Supprimer le preset "${actCode}" ?`)) return;
    try {
      await api.delete(`/prescriptions/preferences/${encodeURIComponent(actCode)}`);
      toast.success('Preset supprimé');
      fetchPresets();
    } catch {
      toast.error('Erreur lors de la suppression');
    }
  };

  const saveCurrentAsPreset = async () => {
    if (!newPresetName.trim()) return;
    setSavingAsPreset(true);
    try {
      await api.post('/prescriptions/preferences', {
        act_code: newPresetName.toUpperCase(),
        drugs: drugs.map(d => ({ name: d.name, dosage: d.dosage, forme: d.forme, posologie: d.posologie })),
      });
      setShowSavePresetModal(false);
      setNewPresetName('');
      fetchPresets();
      toast.success(`Preset "${newPresetName}" enregistré !`);
    } catch {
      toast.error("Erreur lors de l'enregistrement du preset.");
    } finally {
      setSavingAsPreset(false);
    }
  };

  // --- Helpers ---
  const getDefaultMedicationDetails = useCallback((name: string) => {
    const upperName = name.trim().toUpperCase();
    if (upperName.includes('KIN')) return KIN_PRESET;
    return DEFAULT_MOROCCO_PRESETS.flatMap(p => p.drugs).find(d => d.name.toUpperCase() === upperName);
  }, []);

  const hydrateMedicationDetails = useCallback(async (drug: DrugItem): Promise<DrugItem> => {
    if (drug.type === 'EXAMEN') return drug;

    const explicitDosage = Boolean((drug as any).__r1ExplicitDosage);
    const explicitPosology = Boolean((drug as any).__r1ExplicitPosology);
    const cleanDrug: DrugItem = { ...drug };
    delete (cleanDrug as any).__r1ExplicitDosage;
    delete (cleanDrug as any).__r1ExplicitPosology;

    const preset = getDefaultMedicationDetails(cleanDrug.name);
    let candidate: DrugItem = preset
      ? {
          ...cleanDrug,
          name: preset.name,
          dosage: cleanDrug.dosage || preset.dosage,
          forme: cleanDrug.forme || preset.forme,
          posologie: cleanDrug.posologie || preset.posologie,
        }
      : cleanDrug;

    if (!candidate.dosage || !candidate.posologie) {
      try {
        const res = await api.get(`/prescriptions/habits/details?med_name=${encodeURIComponent(candidate.name)}`);
        candidate = {
          ...candidate,
          dosage: candidate.dosage || res.data.dosages?.[0] || '',
          posologie: candidate.posologie || res.data.posologies?.[0] || '',
        };
      } catch { /* local/offline fallback stays empty */ }
    }

    return normalizeCandidate(candidate, 'quick_entry', {
      dosage: explicitDosage,
      posology: explicitPosology,
    });
  }, [getDefaultMedicationDetails, normalizeCandidate]);

  const addDrugAtEnd = useCallback((drug: DrugItem) => {
    const hasOnlyEmptyPlaceholder = drugs.length === 1 && !drugs[0].name.trim() && !drugs[0].posologie.trim();
    setDrugs(hasOnlyEmptyPlaceholder ? [drug] : [...drugs, drug]);
    setQuickExpanded(false);
  }, [drugs, setDrugs]);

  const addMolecule = useCallback(async (
    molecule: string,
    forcedDosage?: string,
    forcedPosology?: string,
    forme?: string,
    source: MedicationInputSource = 'assessment',
  ) => {
    const newId = Date.now();
    let candidate: DrugItem = {
      id: newId, name: molecule, dosage: forcedDosage || '', forme: forme || 'COMPRIMÉS',
      posologie: forcedPosology || '', type: 'MEDICAMENT', quantite: 1, non_substituable: false,
    };

    if (!forcedDosage || !forcedPosology) {
      try {
        const res = await api.get(`/prescriptions/habits/details?med_name=${encodeURIComponent(molecule)}`);
        candidate = {
          ...candidate,
          dosage: forcedDosage || res.data.dosages?.[0] || '',
          posologie: forcedPosology || res.data.posologies?.[0] || '',
        };
      } catch { /* habits are optional, never evidence */ }
    }

    const normalized = await normalizeCandidate(candidate, source);
    setDrugs([...drugs, normalized]);
  }, [drugs, setDrugs, normalizeCandidate]);

  const moveDrug = useCallback((id: number, direction: 'up' | 'down') => {
    const idx = drugs.findIndex(d => d.id === id);
    if (idx === -1) return;
    if (direction === 'up' && idx === 0) return;
    if (direction === 'down' && idx === drugs.length - 1) return;
    const newDrugs = [...drugs];
    const targetIdx = direction === 'up' ? idx - 1 : idx + 1;
    [newDrugs[idx], newDrugs[targetIdx]] = [newDrugs[targetIdx], newDrugs[idx]];
    setDrugs(newDrugs);
  }, [drugs, setDrugs]);

  // --- National med check ---
  const runMedCheck = useDebounce(async (id: number, name: string, dosage: string) => {
    if (!name?.trim()) {
      setMedChecks(prev => { const n = { ...prev }; delete n[id]; return n; });
      return;
    }
    try {
      const res = await api.get('/medications/validate', { params: { name, dosage: dosage || undefined } });
      setMedChecks(prev => ({ ...prev, [id]: res.data }));
    } catch { /* silent — offline or unknown */ }
  }, 350);

  const searchGuideNational = useDebounce(async (q: string) => {
    if (q.trim().length < 2) { setGuideNationalResults([]); setGuideSearching(false); return; }
    try {
      const res = await api.get('/medications/search', { params: { q } });
      setGuideNationalResults(res.data || []);
    } catch {
      setGuideNationalResults([]);
    } finally {
      setGuideSearching(false);
    }
  }, 300);

  // --- Autocomplete ---
  const fetchSuggestions = useCallback(async (id: number, field: string, val: string) => {
    try {
      if (field === 'name' && val.length >= 1) {
        const res = await api.get(`/prescriptions/habits/suggest?q=${encodeURIComponent(val)}`);
        const data = res.data;
        if (!data.medications || data.medications.length === 0) {
          const pool = [...new Set([
            ...DEFAULT_MOROCCO_PRESETS.flatMap(p => p.drugs.map(d => d.name)),
            'KIN',
          ])];
          const fuzzyHits = pool.filter(n => fuzzyMatch(val, n));
          if (fuzzyHits.length > 0) { setSuggestions({ medications: fuzzyHits, dosages: [], posologies: [] }); return; }
        }
        setSuggestions(data);
      } else if (field === 'dosage' || field === 'posologie') {
        const drug = drugs.find(d => d.id === id);
        if (drug?.name) {
          const res = await api.get(`/prescriptions/habits/details?med_name=${encodeURIComponent(drug.name)}`);
          setSuggestions({ medications: [], ...res.data });
        }
      }
    } catch (err: any) {
      if (err.name === 'CanceledError') return;
      console.error('Fetch suggestions error:', err);
    }
  }, [drugs]);

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
    if (field === 'name' || field === 'dosage') {
      const d = drugs.find(x => x.id === id);
      const name = field === 'name' ? val : (d?.name || '');
      const dosage = field === 'dosage' ? val : (d?.dosage || '');
      runMedCheck(id, name, dosage);
    }
  };

  const applySuggestion = useCallback(async (id: number, field: string, val: string) => {
    setSuggestions({ medications: [], dosages: [], posologies: [] });
    setActiveSearchId(null);

    if (field !== 'name') {
      onUpdateDrug(id, field as keyof DrugItem, val);
      return;
    }

    const current = drugs.find(d => d.id === id);
    if (!current) return;
    const preset = getDefaultMedicationDetails(val);
    let candidate: DrugItem = {
      ...current,
      name: val,
      dosage: preset?.dosage || '',
      forme: preset?.forme || current.forme || 'COMPRIMÉS',
      posologie: preset?.posologie || '',
    };

    if (!candidate.dosage || !candidate.posologie) {
      try {
        const res = await api.get(`/prescriptions/habits/details?med_name=${encodeURIComponent(val)}`);
        candidate = {
          ...candidate,
          dosage: candidate.dosage || res.data.dosages?.[0] || '',
          posologie: candidate.posologie || res.data.posologies?.[0] || '',
        };
      } catch { /* optional habit suggestions */ }
    }

    const normalized = await normalizeCandidate(candidate, 'line_autocomplete');
    onUpdateDrug(id, 'name', normalized.name);
    onUpdateDrug(id, 'dosage', normalized.dosage);
    onUpdateDrug(id, 'forme', normalized.forme);
    onUpdateDrug(id, 'posologie', normalized.posologie);
    runMedCheck(id, normalized.name, normalized.dosage);
  }, [drugs, getDefaultMedicationDetails, normalizeCandidate, onUpdateDrug, runMedCheck]);

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
    if (e.key === 'Enter' && highlightedIdx >= 0) { e.preventDefault(); void applySuggestion(id, field, list[highlightedIdx]); }
    if (e.key === 'Escape') { setSuggestions({ medications: [], dosages: [], posologies: [] }); setActiveSearchId(null); }
  };

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

  useEffect(() => {
    if (!formeDropdownCoords) return;
    const close = () => { setActiveSearchId(null); setFormeDropdownCoords(null); };
    window.addEventListener('scroll', close, true);
    window.addEventListener('resize', close);
    return () => { window.removeEventListener('scroll', close, true); window.removeEventListener('resize', close); };
  }, [formeDropdownCoords]);

  // --- Preset application through R1 arbiter ---
  const applyPresetWithSafety = useCallback(async (
    presetDrugs: any[],
    presetLabel?: string,
    source: MedicationInputSource = 'system_protocol',
  ) => {
    const normalized = await Promise.all(presetDrugs.map(async (d: any, i: number) => {
      const candidate: DrugItem = {
        ...d,
        id: Date.now() + i,
        type: 'MEDICAMENT',
        quantite: 1,
        non_substituable: false,
      };
      return normalizeCandidate(candidate, source);
    }));

    const PARACETAMOL_NAMES = ['paracetamol', 'doliprane', 'efferalgan', 'dafalgan', 'perfalgan'];
    const isParacetamol = (name: string) => PARACETAMOL_NAMES.some(n => name.toLowerCase().includes(n));
    const deduplicatedDrugs = normalized.reduce((acc: DrugItem[], drug: DrugItem) => {
      if (isParacetamol(drug.name) && acc.find(d => isParacetamol(d.name))) return acc;
      acc.push(drug);
      return acc;
    }, []);

    setDrugs(deduplicatedDrugs);
    setNewPresetName(presetLabel || '');
    setStep('PLANNING');

    const reviews = deduplicatedDrugs.filter(d => pharmacologyReviews[d.id]?.length > 0).length;
    if (reviews > 0) {
      toast(`Protocole chargé : ${reviews} ligne(s) nécessitent une revue pharmacologique.`, { icon: '⚠️', duration: 5000 });
    } else {
      toast.success(presetLabel ? `Protocole "${presetLabel}" normalisé.` : 'Protocole normalisé.');
    }
  }, [normalizeCandidate, setDrugs, pharmacologyReviews]);

  // --- Quick entry parse ---
  const parseQuickEntry = (text: string): DrugItem => {
    const lowerText = text.toLowerCase();
    const parts = text.trim().split(/\s+/);
    const radioKeywords = ['radio', 'télé-radio', 'teleradio', 'conebeam', 'scanner', 'irm', 'panoramique', 'rvg', 'bitewing', 'status', 'dentoscan', 'cbct', 'examen'];
    const isExamen = radioKeywords.some(k => lowerText.includes(k));
    const preset = getDefaultMedicationDetails(parts[0]);
    const drug: DrugItem = {
      id: Date.now(),
      name: (preset?.name || parts[0]).toUpperCase(),
      dosage: preset?.dosage || '',
      forme: isExamen ? '' : (preset?.forme || 'COMPRIMÉS'),
      posologie: preset?.posologie || '',
      type: isExamen ? 'EXAMEN' : 'MEDICAMENT',
      quantite: 1, non_substituable: false,
    };
    if (isExamen) {
      if (parts.length <= 3) { drug.name = text.toUpperCase().trim(); drug.posologie = ''; }
      else { drug.name = parts.slice(0, 2).join(' ').toUpperCase(); drug.posologie = parts.slice(2).join(' ').trim(); }
      return drug;
    }
    const formesMap: Record<string, string> = {
      'sachet': 'SACHETS', 'gelule': 'GÉLULES', 'gélule': 'GÉLULES', 'bain': 'BAIN DE BOUCHE', 'kin': 'BAIN DE BOUCHE',
      'sirop': 'SIROP', 'pommade': 'POMMADE', 'crème': 'CRÈME', 'creme': 'CRÈME', 'goutte': 'GOUTTES',
      'ampoule': 'AMPOULES', 'spray': 'SPRAY', 'comprimé': 'COMPRIMÉS', 'comprime': 'COMPRIMÉS', 'cp': 'COMPRIMÉS',
    };
    let poso = text;
    let formeTextFound = '';
    for (const [key, value] of Object.entries(formesMap)) {
      const m = text.match(new RegExp(`\\b${key}s?\\b`, 'i'));
      if (m) { drug.forme = value; formeTextFound = m[0]; break; }
    }
    let dosageTextFound = '';
    const dosageMatch = text.match(/\b\d+(\s?)(g|mg|mcg|ml|l|ui)\b/i);
    if (dosageMatch) { drug.dosage = dosageMatch[0].toUpperCase().replace(/\s/g, ''); dosageTextFound = dosageMatch[0]; }
    let qtyTextFound = '';
    const qtyMatch = text.match(/(qsp|x|qty|qté|qte)\s*(\d+)/i) || text.match(/\b(\d+)\s*(boite|boîte|pack|unité)s?\b/i);
    if (qtyMatch) { const num = qtyMatch[2] || qtyMatch[1]; drug.quantite = parseInt(num); qtyTextFound = qtyMatch[0]; }
    if (poso.toUpperCase().startsWith(drug.name)) poso = poso.substring(drug.name.length);
    if (dosageTextFound) poso = poso.replace(dosageTextFound, '');
    if (formeTextFound) poso = poso.replace(formeTextFound, '');
    if (qtyTextFound) poso = poso.replace(qtyTextFound, '');
    const parsedPosologie = poso.replace(/\s+/g, ' ').trim();
    if (parsedPosologie) drug.posologie = parsedPosologie;
    (drug as any).__r1ExplicitDosage = Boolean(dosageMatch);
    (drug as any).__r1ExplicitPosology = Boolean(parsedPosologie);
    return drug;
  };

  const handleQuickSearch = useDebounce(async (val: string) => {
    const searchPart = val.trim().split(' ')[0];
    if (searchPart.length < 1) { setQuickSuggestions([]); return; }
    try {
      const res = await api.get(`/prescriptions/habits/suggest?q=${encodeURIComponent(searchPart)}`);
      setQuickSuggestions(res.data.medications || []);
    } catch { /* silent */ }
  }, 300);

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex items-center justify-between bg-white/40 p-4 rounded-[2rem] border border-white/60 backdrop-blur-2xl shadow-lg shadow-primary/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary to-blue-600 text-white rounded-xl flex items-center justify-center shadow-md shadow-primary/30">
            <Brain size={20} className={loading ? 'animate-pulse' : ''} />
          </div>
          <div>
            <h3 className="text-[11px] font-black text-slate-800 uppercase tracking-[0.2em] leading-none mb-1 flex items-center gap-2">
              IAmina Intelligence
              <span className="bg-primary/10 text-primary text-[7px] px-1.5 py-0.5 rounded-full">v4.8</span>
            </h3>
            {drugs.length > 0 && (
              <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">
                {drugs.length} médicament{drugs.length > 1 ? 's' : ''}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className={cn(
            'px-3 py-1.5 rounded-xl border transition-all flex items-center gap-2',
            coherenceWarnings.length === 0
              ? 'bg-emerald-50/50 border-emerald-100 text-emerald-600'
              : 'bg-amber-50/50 border-amber-100 text-amber-600 animate-pulse',
          )}>
            <ShieldCheck size={12} className={coherenceWarnings.length > 0 ? 'hidden' : ''} />
            <AlertCircle size={12} className={coherenceWarnings.length === 0 ? 'hidden' : ''} />
            <span className="text-[8px] font-black uppercase tracking-widest">
              {coherenceWarnings.length === 0 ? 'Cohérence OK' : 'Audit Requis'}
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
            onClick={() => setShowGuideModal(true)}
            className="px-3 py-1.5 bg-indigo-500/10 text-indigo-600 border border-indigo-500/20 rounded-xl hover:bg-indigo-500 hover:text-white transition-all flex items-center gap-2 shadow-sm"
          >
            <Stethoscope size={14} />
            <span className="text-[9px] font-black uppercase tracking-widest hidden sm:inline">Médicaments</span>
          </button>
          <button
            onClick={() => { setStep('IDLE'); setAssessment(null); }}
            className="p-2 bg-slate-100 text-slate-400 rounded-xl hover:bg-slate-200 transition-all"
          >
            <RefreshCcw size={14} />
          </button>
        </div>
      </div>

      {/* ALLERGY BANNER */}
      {assessment && (assessment?.patient_context?.antecedents || assessment?.antecedents) && (
        <motion.div
          initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 border border-red-200 p-4 rounded-[1.5rem] flex items-start gap-3 shadow-sm relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />
          <AlertCircle className="text-red-500 shrink-0 mt-0.5" size={20} />
          <div className="relative z-10">
            <h4 className="text-[11px] font-black text-red-800 uppercase tracking-widest mb-1">Contexte Médical</h4>
            <p className="text-xs font-bold text-red-700">
              {assessment?.patient_context?.antecedents || assessment?.antecedents}
            </p>
          </div>
        </motion.div>
      )}

      {/* QUICK ENTRY */}
      <AnimatePresence initial={false}>
        {quickExpanded ? (
          <motion.div
            key="quick-open"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <QuickEntryBar
              quickVal={quickVal}
              setQuickVal={setQuickVal}
              quickSuggestions={quickSuggestions}
              quickHighlightedIdx={quickHighlightedIdx}
              setQuickHighlightedIdx={setQuickHighlightedIdx}
              onSearchChange={handleQuickSearch}
              onAddDrug={addDrugAtEnd}
              onSetStep={setStep}
              hydrateMedicationDetails={hydrateMedicationDetails}
              parseQuickEntry={parseQuickEntry}
            />
          </motion.div>
        ) : (
          <motion.button
            key="quick-closed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setQuickExpanded(true)}
            className="w-full flex items-center gap-3 px-6 py-3 bg-primary/5 border border-dashed border-primary/20 rounded-[2rem] text-primary/60 hover:text-primary hover:border-primary/40 hover:bg-primary/10 transition-all text-[10px] font-black uppercase tracking-widest"
          >
            <Zap size={14} />
            Saisie rapide…
          </motion.button>
        )}
      </AnimatePresence>

      {/* PRESETS BAR */}
      <AnimatePresence>
        {showPresets && (
          <motion.div
            initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
            className="flex flex-col gap-3"
          >
            <div className="flex items-center justify-between px-4 mb-2">
              <div className="flex items-center gap-2">
                <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Protocoles Cliniques</span>
                <span className="w-1 h-1 rounded-full bg-slate-300" />
                <span className="text-[8px] font-bold text-slate-300 uppercase italic">Arbitrage pharmaco actif</span>
              </div>
              <button onClick={() => setShowPresets(false)} className="text-[9px] font-black text-slate-300 hover:text-slate-500 uppercase tracking-tighter transition-colors">Masquer</button>
            </div>
            <div className="px-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <span className="text-[8px] font-black text-slate-400 uppercase tracking-widest block">Protocoles Système</span>
                <div className="relative">
                  <select
                    className="w-full appearance-none bg-white border border-slate-200 rounded-2xl px-4 py-2.5 pr-8 text-[9px] font-black text-slate-600 uppercase tracking-widest cursor-pointer hover:border-primary/30 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                    value=""
                    onChange={e => {
                      const p = DEFAULT_MOROCCO_PRESETS.find(p => p.label === e.target.value);
                      if (p) void applyPresetWithSafety(p.drugs, p.label, 'system_protocol');
                      e.currentTarget.value = '';
                    }}
                  >
                    <option value="" disabled>— Choisir un protocole —</option>
                    {DEFAULT_MOROCCO_PRESETS.map(p => (
                      <option key={p.label} value={p.label}>{p.label} ({p.drugs.length} méd.)</option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-slate-400"><ChevronDown size={12} /></div>
                </div>
              </div>

              <div className="space-y-1.5">
                <span className="text-[8px] font-black text-slate-400 uppercase tracking-widest block">Mes Ordonnances</span>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <select
                      className="w-full appearance-none bg-white border border-slate-200 rounded-2xl px-4 py-2.5 pr-8 text-[9px] font-black text-slate-600 uppercase tracking-widest cursor-pointer hover:border-primary/30 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      value={selectedUserPreset}
                      disabled={presets.length === 0}
                      onChange={e => {
                        setSelectedUserPreset(e.target.value);
                        const p = presets.find(p => p.act_context === e.target.value);
                        if (p) void applyPresetWithSafety(p.drugs, p.act_context, 'user_protocol');
                      }}
                    >
                      <option value="">{presets.length === 0 ? '— Aucune ordonnance sauvegardée —' : '— Choisir une ordonnance —'}</option>
                      {presets.map(p => (
                        <option key={p.id} value={p.act_context}>{p.act_context}{p.drugs?.length > 0 ? ` (${p.drugs.length})` : ''}</option>
                      ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-slate-400"><ChevronDown size={12} /></div>
                  </div>
                  {selectedUserPreset && (
                    <button
                      onClick={() => { deletePreset(selectedUserPreset); setSelectedUserPreset(''); }}
                      className="w-9 h-9 flex-shrink-0 bg-red-50 border border-red-100 text-red-400 rounded-2xl flex items-center justify-center hover:bg-red-500 hover:text-white transition-all text-sm font-black"
                    >×</button>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* STEP VIEWS */}
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
                Chargement du contexte patient et des vérifications pharmacologiques disponibles.
              </p>
            </div>
          </motion.div>
        )}

        {step === 'ASSESSMENT' && assessment && (
          <motion.div key="assessment" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7 space-y-6">
                <div className="bg-white/60 p-8 rounded-[2.5rem] border border-white/60 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-emerald-500/10 text-emerald-600 rounded-xl flex items-center justify-center">
                      <ShieldCheck size={22} />
                    </div>
                    <div>
                      <h4 className="text-xs font-black text-slate-800 uppercase tracking-widest">Bilan Clinique</h4>
                      <p className="text-[10px] font-bold text-slate-400">Moteur déterministe local</p>
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
                        <span className="text-xs font-bold text-emerald-700 uppercase tracking-widest">Aucun risque signalé par ce contrôle</span>
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
                        <button key={i} onClick={() => void addMolecule(m.molecule, undefined, undefined, undefined, 'assessment')}
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
                  <p className="text-[10px] font-bold text-slate-400">Normalisation pharmacologique et structuration finale.</p>
                </div>
              </div>
            )}

            <div className="space-y-3">
              {drugs.map((drug, idx) => (
                <div key={drug.id} className="space-y-2">
                  <DrugRow
                    drug={drug}
                    idx={idx}
                    drugsCount={drugs.length}
                    assessment={assessment}
                    validationErrors={validationErrors}
                    forcedDrugs={forcedDrugs}
                    activeSearchId={activeSearchId}
                    suggestions={suggestions}
                    highlightedIdx={highlightedIdx}
                    medChecks={medChecks}
                    onUpdateDrug={onUpdateDrug}
                    onRemoveDrug={onRemoveDrug}
                    onMove={moveDrug}
                    onSearch={handleSearch}
                    onKeyDown={handleKeyDown}
                    onApplySuggestion={(id, field, val) => { void applySuggestion(id, field, val); }}
                    onFormeOpen={handleFormeOpen}
                    onForceAllergy={id => setForcedDrugs(prev => [...prev, id])}
                    onToggleType={(id, type) =>
                      setDrugs(drugs.map(d => d.id === id
                        ? { ...d, type, forme: type === 'MEDICAMENT' ? (d.forme || 'COMPRIMÉS') : '', dosage: type === 'EXAMEN' ? '' : d.dosage, posologie: type === 'EXAMEN' ? '' : d.posologie }
                        : d))
                    }
                  />
                  {pharmacologyReviews[drug.id]?.length > 0 && (
                    <div className="mx-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-[11px] font-bold text-amber-800 flex items-start gap-2">
                      <AlertCircle size={14} className="shrink-0 mt-0.5" />
                      <span><strong>Revue pharmacologique requise :</strong> {pharmacologyReviews[drug.id].join(' ')}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Safety badge */}
            <div className="flex items-center justify-end px-4">
              <div
                className={cn(
                  'flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all cursor-help',
                  coherenceWarnings.length > 0 || Object.keys(pharmacologyReviews).length > 0
                    ? 'bg-amber-500/10 border-amber-500/20 text-amber-600'
                    : 'bg-slate-500/10 border-slate-500/20 text-slate-600',
                )}
                title="État partiel des contrôles locaux. Le moteur safety complet est traité au lot R3."
              >
                {coherenceWarnings.length > 0 || Object.keys(pharmacologyReviews).length > 0 ? <AlertCircle size={12} /> : <ShieldCheck size={12} />}
                <span className="text-[8px] font-black uppercase tracking-widest">
                  {coherenceWarnings.length > 0 || Object.keys(pharmacologyReviews).length > 0
                    ? `${coherenceWarnings.length + Object.keys(pharmacologyReviews).length} Revue(s)`
                    : 'Contrôles locaux sans alerte'}
                </span>
              </div>
            </div>

            {/* Add line */}
            <div className="flex flex-wrap justify-center gap-4 mt-6">
              <button
                onClick={onAddDrug}
                className="flex-1 min-w-[200px] py-5 border-2 border-dashed border-slate-200 text-slate-400 rounded-[2.5rem] flex items-center justify-center gap-3 hover:border-primary hover:text-primary hover:bg-primary/5 transition-all font-black text-xs uppercase tracking-widest"
              >
                <Plus size={20} /> Ajouter une ligne
              </button>
            </div>

            {/* Patient advice */}
            <div className="mt-4">
              <button
                type="button"
                onClick={() => setShowPatientAdvice(v => !v)}
                className="flex items-center gap-2 text-[9px] font-black text-slate-400 hover:text-primary uppercase tracking-widest transition-colors px-2"
              >
                <div className={cn('w-3 h-3 rounded-full border-2 border-current transition-colors', showPatientAdvice ? 'bg-primary border-primary' : 'border-slate-300')} />
                Conseils au Patient
                {patientAdvice.trim() && <span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-[7px]">✓</span>}
              </button>
              <AnimatePresence>
                {showPatientAdvice && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                    className="mt-3 overflow-hidden"
                  >
                    <div className="bg-blue-50/50 border border-blue-100 rounded-[1.5rem] p-4 focus-within:ring-2 focus-within:ring-primary/10 focus-within:border-primary/20 transition-all">
                      <textarea
                        rows={3}
                        className="w-full bg-transparent border-none p-0 text-[11px] font-bold text-slate-600 focus:ring-0 resize-none placeholder:text-slate-300 leading-relaxed"
                        placeholder="Ex : Éviter les aliments durs pendant 48h. Ne pas fumer. Rincer avec le bain de bouche après chaque repas..."
                        value={patientAdvice}
                        onChange={e => setPatientAdvice(e.target.value)}
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* SAVE PRESET MODAL */}
      <AnimatePresence>
        {showSavePresetModal && (
          <div className="fixed inset-0 z-[30000] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-md"
              onClick={() => setShowSavePresetModal(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="relative bg-white rounded-[3rem] p-10 w-full max-w-md shadow-2xl border border-white/20"
            >
              <div className="flex items-center gap-4 mb-8">
                <div className="w-14 h-14 bg-primary/10 rounded-[1.5rem] flex items-center justify-center text-primary">
                  <Brain size={28} />
                </div>
                <div>
                  <h3 className="text-lg font-black text-slate-800 uppercase tracking-tight">Mémoriser le Preset</h3>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Protocole personnel</p>
                </div>
              </div>
              <div className="space-y-6">
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3 ml-2">Nom de l'Acte (Ex: Implantologie)</label>
                  <input
                    type="text" value={newPresetName}
                    onChange={e => setNewPresetName(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-6 py-4 text-sm font-bold text-slate-800 outline-none focus:ring-4 focus:ring-primary/10 focus:border-primary/30 transition-all placeholder:text-slate-300"
                    placeholder="Saisissez le contexte clinique..."
                    autoFocus
                    onKeyDown={e => e.key === 'Enter' && saveCurrentAsPreset()}
                  />
                </div>
                <div className="flex gap-4 pt-4">
                  <button onClick={() => setShowSavePresetModal(false)} className="flex-1 py-4 bg-slate-50 text-slate-500 rounded-2xl text-[11px] font-black uppercase tracking-widest hover:bg-slate-100 transition-all">Annuler</button>
                  <button
                    onClick={saveCurrentAsPreset}
                    disabled={savingAsPreset || !newPresetName.trim()}
                    className="flex-1 py-4 bg-primary text-white rounded-2xl text-[11px] font-black uppercase tracking-widest shadow-xl shadow-primary/30 hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                    style={{ backgroundColor: 'var(--primary)' }}
                  >
                    {savingAsPreset ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                    Enregistrer
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* FORME DROPDOWN (fixed position to escape overflow) */}
      <AnimatePresence>
        {activeSearchId?.field === 'forme_dropdown' && formeDropdownCoords && (() => {
          const activeDrug = drugs.find(d => d.id === activeSearchId.id);
          return (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 8 }}
              style={{ position: 'fixed', top: formeDropdownCoords.top, left: formeDropdownCoords.left, width: Math.max(formeDropdownCoords.width, 208), zIndex: 200 }}
              className="bg-white border border-slate-100 rounded-2xl shadow-2xl overflow-hidden py-2"
            >
              {FORMES.map(f => {
                const Icon = f.icon;
                return (
                  <button
                    key={f.l}
                    onClick={() => { onUpdateDrug(activeSearchId.id, 'forme', f.l === 'AUTRE' ? 'AUTRE: ' : f.l); setActiveSearchId(null); setFormeDropdownCoords(null); }}
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

      {/* Overlay to close dropdowns */}
      {(suggestions.medications.length > 0 || suggestions.dosages.length > 0 || suggestions.posologies.length > 0 || activeSearchId?.field === 'forme_dropdown') && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => { setSuggestions({ medications: [], dosages: [], posologies: [] }); setActiveSearchId(null); setFormeDropdownCoords(null); }}
        />
      )}

      {/* GUIDE MODAL */}
      <PrescriptionGuideModal
        show={showGuideModal}
        onClose={() => setShowGuideModal(false)}
        guideAge={guideAge}
        setGuideAge={setGuideAge}
        guideWeight={guideWeight}
        setGuideWeight={setGuideWeight}
        guideCategory={guideCategory}
        setGuideCategory={setGuideCategory}
        guideSearch={guideSearch}
        setGuideSearch={setGuideSearch}
        guideNationalResults={guideNationalResults}
        guideSearching={guideSearching}
        setGuideSearching={setGuideSearching}
        onNationalSearch={searchGuideNational}
        assessment={assessment}
        onAddMolecule={(molecule, dosage, posology, forme) => {
          void addMolecule(molecule, dosage, posology, forme, 'drug_library');
        }}
      />
    </div>
  );
};
