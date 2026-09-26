import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { 
  Plus, 
  Trash2, 
  Zap,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Banknote,
  Brain,
  History,
  LayoutGrid,
  ArrowLeft,
  ArrowUp,
  ArrowDown,
  Sparkles,
  Wand2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils/cn';
import { PremiumOdontogramSVG } from '../../components/odontogram/PremiumOdontogramSVG';
import { TreatmentSelector } from '../../components/odontogram/TreatmentSelector';
import { createPortal } from 'react-dom';
import type { SelectedSurfaceData, ToothSurface, ToothTreatment } from '../../components/odontogram/types';
import { api } from '../../services/api';
import type { ValidationError, CoherenceWarning } from './DocumentStudio/useDocumentGenerator';
import { PriceBrain } from '../../components/odontogram/PriceBrain';
import { useAccountingStore, type PriceItem, type InstallmentItem } from './store/useAccountingStore';
import { useCatalogStore } from './Settings/hooks/useCatalogStore';
import { AccountingQuickActions } from './DocumentStudio/AccountingQuickActions';
import { groupAccountingItemsByPhase, isAccountingPhaseSeparator } from './DocumentStudio/AccountingPhasePolicy';
import { replaceOdontogramToothSelections } from './DocumentStudio/AccountingOdontogramPolicy';
import { odontogramGroupSelection, odontogramQuickGroupKeys } from './DocumentStudio/AccountingOdontogramModePolicy';
import { resolveAccountingBundles, type ResolvedAccountingBundle } from './DocumentStudio/AccountingBundlePolicy';
import { moveAccountingLine } from './DocumentStudio/AccountingLineOrderPolicy';
import { accountingDocumentTotal } from './DocumentStudio/AccountingTotalPolicy';
import { resolveNamedDevisActPrice } from './DocumentStudio/AccountingNamedActPricePolicy';
import { suggestedCatalogActs } from './DocumentStudio/AccountingActApplicabilityPolicy';

const detectRegion = (teeth: number[]): string => {
  if (teeth.length === 0) return 'Général';
  const first = teeth[0];
  const q = Math.floor(first / 10);
  const qName = q === 1 ? 'Sup. Droit' : q === 2 ? 'Sup. Gauche' : q === 3 ? 'Inf. Gauche' : q === 4 ? 'Inf. Droit' : q === 5 ? 'Prim. Sup. Droit' : q === 6 ? 'Prim. Sup. Gauche' : q === 7 ? 'Prim. Inf. Gauche' : 'Prim. Inf. Droit';
  const isAnterior = teeth.every(t => [1,2,3].includes(t % 10));
  if (isAnterior) return q <= 2 || q === 5 || q === 6 ? 'Sextant Antérieur Sup.' : 'Sextant Antérieur Inf.';
  const isPosterior = teeth.every(t => [4,5,6,7,8].includes(t % 10));
  if (isPosterior) return `Sextant ${qName}`;
  return `Quadrant ${q}`;
};

interface AccountingStudioProps {
  isDevis?: boolean;
  patientId: string;
  coherenceWarnings?: CoherenceWarning[];
  validationErrors?: { message: string }[];
  setSelectedTeethFromOdontogram: (teeth: SelectedSurfaceData[]) => void;
}

export const AccountingStudio: React.FC<AccountingStudioProps> = ({
  isDevis = false,
  patientId,
  coherenceWarnings = [],
  validationErrors = [],
}) => {
  const {
    items, setItems,
    paymentMode, setPaymentMode,
    showOdontoPanoramique, setShowOdontoPanoramique,
    groupSelectedTeeth, setGroupSelectedTeeth,
    actSuggestions, setActSuggestions,
    activeActSearchId, setActiveActSearchId,
    installments, setInstallments,
    isAccounted, setIsAccounted,
    paymentStatus, setPaymentStatus,
    paymentStatusGuardMessage, clearPaymentStatusGuard,
    isGlobalNote, setIsGlobalNote,
    groupTreatmentName, setGroupTreatmentName,
    groupTreatmentPrice, setGroupTreatmentPrice
  } = useAccountingStore();

  const { specialties, fetchCatalog, createAct, updateAct } = useCatalogStore();
  
  React.useEffect(() => {
    if (specialties.length === 0) {
      fetchCatalog();
    }
  }, [fetchCatalog, specialties.length]);

  const TREATMENT_TEMPLATES = React.useMemo(() => {
    return specialties.flatMap(s => s.acts.map(act => ({
      id: act.id.toString(),
      name: act.name,
      category: s.name,
      base_price: act.base_price,
      catalogActId: act.id,
    })));
  }, [specialties]);

  const handleToothDirectClick = (n: number) => setGroupSelectedTeeth(groupSelectedTeeth.includes(n) ? groupSelectedTeeth.filter(x => x !== n) : [...groupSelectedTeeth, n]);

  const groupSuggestedActs = React.useMemo(
    () => suggestedCatalogActs(
      specialties,
      { selectedTeeth: groupSelectedTeeth, selectionMode: groupSelectedTeeth.length > 1 ? 'GROUP' : 'INDIVIDUAL' },
      6,
    ),
    [groupSelectedTeeth, specialties],
  );

  const generalSuggestedActs = React.useMemo(
    () => suggestedCatalogActs(
      specialties,
      { selectedTeeth: [], selectionMode: 'GENERAL' },
      10,
    ),
    [specialties],
  );

  const [isOdontoOpen, setIsOdontoOpen] = useState(items.length === 0);
  const [quickActs, setQuickActs] = useState<{ name: string; price: number; category: string }[]>([]);
  const [suggestedBundles, setSuggestedBundles] = useState<ResolvedAccountingBundle[]>([]);
  const [odontogramType, setOdontogramType] = useState<'ADULT' | 'PEDIATRIC'>('ADULT');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [isTreasuryModalOpen, setIsTreasuryModalOpen] = useState(false);
  const [isNewCatalogActOpen, setIsNewCatalogActOpen] = useState(false);
  const [newCatalogActName, setNewCatalogActName] = useState('');
  const [newCatalogActPrice, setNewCatalogActPrice] = useState('');
  const [newCatalogActSpecialtyId, setNewCatalogActSpecialtyId] = useState<number | ''>('');
  const replaceToothTreatmentsFromSelector = React.useCallback((
    toothNumber: number,
    treatments: ToothTreatment[],
    surfaces: ToothSurface[],
  ) => {
    const dentLabel = surfaces.length > 0 ? toothNumber.toString() + ` (${surfaces.join('')})` : undefined;
    setItems((prev: PriceItem[]) => replaceOdontogramToothSelections(
      prev,
      toothNumber,
      treatments.map(treatment => ({
        toothNumber,
        treatmentId: treatment.id,
        name: treatment.name,
        price: treatment.price,
        category: treatment.category,
        catalogActId: treatment.catalogActId,
        dent: dentLabel,
      })),
    ));
  }, [setItems]);

  const [activeTooth, setActiveTooth] = useState<number | null>(null);

  const activeToothTreatments = React.useMemo<ToothTreatment[]>(() => {
    if (!activeTooth) return [];
    const prefix = `${activeTooth}::`;
    return items.flatMap(item => {
      if (!item._odontogramKey?.startsWith(prefix) || !item.category) return [];
      return [{
        id: item._odontogramKey.slice(prefix.length),
        name: item.description,
        price: Number(item.price) || 0,
        category: item.category as ToothTreatment['category'],
        catalogActId: item.catalogActId,
        scope: 'UNITAIRE' as const,
      }];
    });
  }, [activeTooth, items]);

  const normalizeCatalogName = (value: string) => value.trim().replace(/\s+/g, ' ').toLocaleLowerCase('fr');

  const findCatalogAct = React.useCallback((specialtyId: number, name: string) => {
    const specialty = specialties.find(s => s.id === specialtyId);
    if (!specialty) return null;
    const normalized = normalizeCatalogName(name);
    return specialty.acts.find(act => normalizeCatalogName(act.name) === normalized) || null;
  }, [specialties]);

  const ensureCatalogAct = React.useCallback(async (
    specialtyId: number,
    name: string,
    price: number,
    applicability?: any,
  ) => {
    const cleanName = name.trim().replace(/\s+/g, ' ');
    if (!cleanName) return false;
    const existing = findCatalogAct(specialtyId, cleanName);
    if (existing) {
      if (Number(existing.base_price) <= 0 && price > 0) {
        await updateAct(existing.id, { base_price: price });
      }
      return true;
    }
    return createAct(specialtyId, {
      name: cleanName,
      base_price: price > 0 ? price : 0,
      applicability,
    });
  }, [createAct, findCatalogAct, updateAct]);

  const openNewCatalogAct = () => {
    setNewCatalogActName('');
    setNewCatalogActPrice('');
    setNewCatalogActSpecialtyId(specialties[0]?.id || '');
    setIsNewCatalogActOpen(true);
  };

  const addCatalogActLine = async () => {
    if (!newCatalogActName.trim() || !newCatalogActSpecialtyId) {
      toast.error('Choisissez une spécialité et renseignez le nom de l’acte.');
      return;
    }
    const specialtyId = Number(newCatalogActSpecialtyId);
    const specialty = specialties.find(s => s.id === specialtyId);
    const existing = findCatalogAct(specialtyId, newCatalogActName);
    const enteredPrice = Number(newCatalogActPrice) || 0;
    const effectivePrice = enteredPrice > 0 ? enteredPrice : Number(existing?.base_price) || 0;
    const ok = await ensureCatalogAct(specialtyId, newCatalogActName, enteredPrice);
    if (!ok) return;
    setItems((prev: any) => [...prev, {
      id: Date.now(),
      description: existing?.name || newCatalogActName.trim().replace(/\s+/g, ' '),
      dent: '0',
      price: effectivePrice,
      category: specialty?.name,
    }]);
    setIsNewCatalogActOpen(false);
    setNewCatalogActName('');
    setNewCatalogActPrice('');
    setNewCatalogActSpecialtyId('');
  };
  const removeItem = (id: number) => setItems((prev: any) => prev.filter((i: any) => i.id !== id));
  const moveItem = (id: number, direction: 'UP' | 'DOWN') => setItems((prev: PriceItem[]) => moveAccountingLine(prev, id, direction));
  
  const updateItem = (id: number, f: string, v: string | number) => {
    const newItems = items.map(i => i.id === id ? { ...i, [f]: f === 'price' ? Number(v) : v } : i);
    setItems(newItems);
    const item = newItems.find(i => i.id === id);
    if (item && item.description && item.price > 0 && (f === 'price' || f === 'description')) {
      PriceBrain.recordAct(item.description, item.price, item.category || 'CONSERVATRICE');
    }
  };

  const handleActSearch = async (q: string, id: number) => {
    setItems(items.map(i => i.id === id ? { ...i, description: q } : i));
    if (q.length < 2) { setActSuggestions([]); setActiveActSearchId(null); return; }
    setActiveActSearchId(id);
    
    const localMatches = TREATMENT_TEMPLATES.filter((t: any) => 
      t.name.toLowerCase().includes(q.toLowerCase()) || 
      t.category.toLowerCase().includes(q.toLowerCase())
    ).map((t: any) => ({ 
      id: `template_${t.id}`, 
      name: t.name,
      base_price: t.base_price,
      category: t.category,
      catalogActId: t.catalogActId,
      isLocal: true,
      is_habit: false
    }));

    try {
      const res = await api.get(`/actes/search?q=${encodeURIComponent(q)}`);
      const apiMatches = res.data.map((m: any) => ({ ...m, is_habit: true }));
      
      const merged = [...localMatches];
      apiMatches.forEach((am: any) => {
        if (!merged.find(lm => lm.name.toLowerCase() === am.name.toLowerCase())) {
          merged.push(am);
        }
      });
      setActSuggestions(merged);
    } catch {
      setActSuggestions(localMatches);
    }
  };

  const applyActSuggestion = (itemId: number, act: any) => {
    const resolved = resolveNamedDevisActPrice(act.name, TREATMENT_TEMPLATES);
    setItems(items.map(i => i.id === itemId ? {
      ...i,
      description: act.name,
      price: resolved.price,
      category: resolved.category || act.category,
      catalogActId: act.catalogActId
    } : i));
    setActSuggestions([]);
    setActiveActSearchId(null);
    if (resolved.source === 'UNRESOLVED') {
      toast.error('Tarif catalogue absent : renseignez le prix avant archivage.');
    }
  };

  const handlePhaseSequencing = () => {
    const groups = groupAccountingItemsByPhase(items);
    let currentId = Date.now();
    const newItems: PriceItem[] = [];

    groups.forEach(group => {
      newItems.push({
        id: currentId++,
        description: `--- ${group.label.toUpperCase()} ---`,
        dent: '',
        price: 0,
        toothNumbers: [],
      });
      newItems.push(...group.items);
    });

    setItems(newItems);
    toast.success('Organisation par phases appliquée au devis.');
  };
  
  const fetchQuickActs = async () => {
    try {
      const res = await api.get('/accounting/frequent-acts');
      const source = Array.isArray(res.data) && res.data.length > 0
        ? res.data
        : TREATMENT_TEMPLATES.slice(0, 8).map(t => ({ name: t.name, category: t.category }));
      const repriced = source
        .map((act: any) => {
          const resolved = resolveNamedDevisActPrice(act.name, TREATMENT_TEMPLATES);
          return {
            name: act.name,
            price: resolved.price,
            category: resolved.category || act.category || 'CONSERVATRICE',
          };
        })
        .filter((act: any) => act.price > 0)
        .slice(0, 4);
      setQuickActs(repriced);
    } catch (err) {
      console.error("Erreur habitudes acts:", err);
      setQuickActs(
        TREATMENT_TEMPLATES
          .map(t => ({ name: t.name, price: Number(t.base_price) || 0, category: t.category }))
          .filter(t => t.price > 0)
          .slice(0, 4)
      );
    }
  };

  useEffect(() => {
    if (TREATMENT_TEMPLATES.length > 0) fetchQuickActs();
  }, [TREATMENT_TEMPLATES]);

  useEffect(() => {
    const lastItem = items[items.length - 1];
    if (lastItem && lastItem.description.trim().length > 2) {
      const timer = setTimeout(async () => {
        try {
          const res = await api.post('/actes/catalog/bundles', { act_names: [lastItem.description] });
          const catalogActs = TREATMENT_TEMPLATES.map(t => ({
            name: t.name,
            base_price: t.base_price,
            category: t.category,
          }));
          setSuggestedBundles(resolveAccountingBundles(res.data || [], catalogActs));
        } catch (err) {
          console.error("Erreur fetching bundles:", err);
        }
      }, 500);
      return () => clearTimeout(timer);
    } else {
      setSuggestedBundles([]);
    }
  }, [items, TREATMENT_TEMPLATES]);

  const rememberActPrice = (name: string, price: number, category?: string) => {
    if (!name.trim() || !Number.isFinite(price) || price <= 0) return;
    PriceBrain.recordAct(name, price, category || 'CONSERVATRICE');
  };

  useEffect(() => {
    if (items.length === 0) {
      setIsOdontoOpen(true);
    }
  }, [items.length]);

  const labelClass = "text-[9px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-1.5 ml-1";

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20 max-w-[95rem] mx-auto">
      {(validationErrors.length > 0 || coherenceWarnings.length > 0) && (
        <div className="space-y-2 px-2 mb-6">
          {validationErrors.map((err, idx) => (
            <div key={`v-${idx}`} className="px-6 py-3 bg-red-50 border border-red-100 rounded-2xl text-[11px] text-red-600 font-black flex items-center gap-3 animate-in slide-in-from-top-2">
              <AlertCircle size={16} /> {err.message}
            </div>
          ))}
          {coherenceWarnings.map((w, idx) => (
            <div key={`c-${idx}`} className={cn(
              "px-6 py-3 rounded-2xl text-[11px] font-black flex items-center gap-3 animate-in slide-in-from-top-2",
              w.level === 'warning' ? "bg-amber-50 border border-amber-100 text-amber-700"
                : w.level === 'critical' ? "bg-red-50 border border-red-100 text-red-600"
                : "bg-blue-50 border border-blue-100 text-blue-600"
            )}>
              <AlertCircle size={16} className="shrink-0" /> {w.message}
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-col gap-10 max-w-5xl mx-auto items-center">
        <div className="w-full space-y-6">
          <div className="flex items-center justify-center gap-1.5 px-1 text-[9px] font-black uppercase tracking-normal text-slate-400 sm:gap-3 sm:px-2 sm:text-[10px] sm:tracking-[0.14em]" aria-label="Parcours du document">
            <span className="text-primary"><span className="sm:hidden">1 · Clinique</span><span className="hidden sm:inline">1 · Sélection clinique</span></span>
            <ChevronDown size={11} className="-rotate-90 text-slate-300 sm:size-3" aria-hidden="true" />
            <span>2 · Prestations</span>
            <ChevronDown size={11} className="-rotate-90 text-slate-300 sm:size-3" aria-hidden="true" />
            <span><span className="sm:hidden">3 · Récap.</span><span className="hidden sm:inline">3 · Récapitulatif</span></span>
          </div>

          <AccountingQuickActions
            acts={quickActs}
            onSelect={(act) => {
              setItems([
                ...items.filter(it => it.description.trim()),
                { id: Date.now() + Math.random(), description: act.name, price: act.price, dent: '-', category: act.category },
              ]);
              rememberActPrice(act.name, act.price, act.category);
            }}
            onAddManual={openNewCatalogAct}
          />

          <AnimatePresence>
            {suggestedBundles.length > 0 && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ opacity: 0, height: 0 }}
                className="pt-4 border-t border-slate-100 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <Brain className="w-5 h-5 text-primary animate-pulse" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Suggestions complémentaires :</span>
                  <div className="flex gap-2">
                    {suggestedBundles.map((b, i) => (
                      <span key={i} className="px-2 py-1 bg-slate-50 rounded-lg text-[9px] font-bold text-slate-500">
                        +{b.name}{b.priceSource === 'UNRESOLVED' ? ' • prix à saisir' : ''}
                      </span>
                    ))}
                  </div>
                </div>
                <button 
                  type="button"
                  onClick={() => {
                    const newItems = [...items];
                    suggestedBundles.forEach(b => {
                      if (!newItems.find(it => it.description.toLowerCase() === b.name.toLowerCase())) {
                        newItems.push({ id: Date.now() + Math.random(), description: b.name, price: b.price, dent: '-', category: b.category });
                      }
                    });
                    const unresolved = suggestedBundles.filter(b => b.priceSource === 'UNRESOLVED').length;
                    setItems(newItems);
                    setSuggestedBundles([]);
                    if (unresolved > 0) {
                      toast.error(`${unresolved} suggestion(s) ajoutée(s) sans tarif catalogue : prix à renseigner.`);
                    } else {
                      toast.success("Suggestions ajoutées avec les tarifs catalogue");
                    }
                  }}
                  className="px-6 py-2 bg-primary/10 text-primary border border-primary/20 rounded-xl font-black uppercase text-[9px] tracking-[0.2em] hover:bg-primary hover:text-white transition-all"
                >
                  Appliquer le Pack
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {showOdontoPanoramique && (
          <div data-testid="document-plan-of-care" className="bg-white rounded-2xl sm:rounded-[2.5rem] border border-slate-100 shadow-sm overflow-hidden group">
            <button 
              type="button"
              onClick={() => setIsOdontoOpen(!isOdontoOpen)}
              className="w-full px-4 py-4 sm:px-8 sm:py-5 flex items-center justify-between gap-3 hover:bg-slate-50 transition-all"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-500 group-hover:bg-primary/10 group-hover:text-primary transition-all">
                  <LayoutGrid size={20} />
                </div>
                <div className="text-left">
                  <h4 className="text-sm font-black text-slate-800 tracking-tight">Plan de soins</h4>
                  <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Odontogramme & catalogue</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {groupSelectedTeeth.length > 0 && !isOdontoOpen && (
                  <span className="px-4 py-1.5 bg-primary text-white rounded-full text-[9px] font-black uppercase tracking-widest" style={{ backgroundColor: 'var(--primary)' }}>
                    {groupSelectedTeeth.length} Sélectionnée(s)
                  </span>
                )}
                {isOdontoOpen ? <ChevronUp size={20} className="text-slate-300" /> : <ChevronDown size={20} className="text-slate-300" />}
              </div>
            </button>
            {isOdontoOpen && (
              <div className="flex justify-stretch sm:justify-end border-t border-slate-100 bg-slate-50/40 px-4 py-2 sm:px-8">
                <button
                  type="button"
                  onClick={() => {
                    setIsOdontoOpen(false);
                    requestAnimationFrame(() => document.getElementById('document-prestations')?.scrollIntoView?.({ behavior: 'smooth', block: 'start' }));
                  }}
                  className="inline-flex w-full sm:w-auto items-center justify-center gap-1.5 rounded-xl bg-primary px-3 py-2.5 sm:py-2 text-[9px] font-black uppercase tracking-widest text-white shadow-sm transition hover:opacity-90"
                >
                  Continuer vers les prestations <ChevronDown size={14} />
                </button>
              </div>
            )}

            <AnimatePresence>
              {isOdontoOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="px-3 pb-3 sm:px-4 sm:pb-4"
                >
                  <div className="bg-white/60 backdrop-blur-xl rounded-2xl sm:rounded-[2.5rem] border border-white/80 shadow-xl sm:shadow-2xl overflow-hidden relative min-h-[330px] sm:min-h-[360px] flex flex-col">
                    <div className="p-3 sm:p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 sm:gap-4 shrink-0 bg-white/20">
                      <div className="grid grid-cols-2 w-full sm:w-auto bg-slate-100/50 p-1 rounded-xl border border-slate-100">
                        {(['ADULT', 'PEDIATRIC'] as const).map(type => (
                          <button
                            key={type}
                            type="button"
                            onClick={() => {
                              setOdontogramType(type);
                              setGroupSelectedTeeth([]);
                              setActiveTooth(null);
                            }}
                            className={cn(
                              "w-full sm:w-auto px-3 sm:px-4 py-2 rounded-lg text-[9px] font-black uppercase tracking-wider sm:tracking-widest transition-all",
                              odontogramType === type ? "bg-white text-slate-900 shadow-sm border border-slate-100" : "text-slate-400 hover:text-slate-600"
                            )}
                          >{type === 'ADULT' ? 'Adulte' : 'Enfant'}</button>
                        ))}
                      </div>

                      <div className="hidden sm:flex flex-1" aria-hidden="true" />

                      <div className="hidden sm:flex w-24 justify-end">
                        <Zap size={14} className="text-primary" />
                      </div>
                    </div>

                    <div className="relative flex-1 flex flex-col p-2.5 sm:p-4 bg-slate-50/20 overflow-hidden">
                      <div className="relative sm:absolute sm:top-4 sm:left-1/2 sm:-translate-x-1/2 z-30 mb-2 sm:mb-0 px-1 sm:px-0">
                        <div className="w-full sm:w-auto px-3 sm:px-5 py-2 sm:py-2.5 bg-primary/5 backdrop-blur-md text-primary rounded-xl sm:rounded-2xl text-[9px] sm:text-[10px] font-black uppercase tracking-normal sm:tracking-widest flex items-center justify-center gap-2 sm:gap-3 border border-primary/20 shadow-sm text-center">
                          Sélectionnez une ou plusieurs dents
                        </div>
                      </div>

                      <div className="flex-1 flex flex-col items-center justify-center relative">
                        <div className="w-full flex justify-center items-center">
                          <PremiumOdontogramSVG
                            type={odontogramType}
                            selectedTooth={activeTooth}
                            multiSelectedTeeth={groupSelectedTeeth}
                            onToothClick={handleToothDirectClick}
                            showNumbers
                            className="w-full max-w-[760px]"
                          />
                        </div>

                        {groupSelectedTeeth.length > 0 && (
                          <motion.div 
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            className="relative sm:absolute sm:bottom-6 sm:left-1/2 sm:-translate-x-1/2 mt-2 sm:mt-0 w-full max-w-2xl px-1 sm:px-6 z-20 pointer-events-auto"
                          >
                            <div className="bg-slate-900/95 backdrop-blur-2xl rounded-2xl sm:rounded-[2rem] p-3 sm:p-5 border border-white/10 shadow-xl sm:shadow-2xl flex flex-col gap-3 sm:gap-4">
                              <>
                                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                                    <div className="flex min-w-0 items-center gap-2 sm:gap-3">
                                      <div className="flex -space-x-2">
                                        {groupSelectedTeeth.slice(0, 4).map(n => (
                                          <div key={n} className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-[10px] font-black text-white border-2 border-slate-900">{n}</div>
                                        ))}
                                        {groupSelectedTeeth.length > 4 && (
                                          <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-[10px] font-black text-white border-2 border-slate-900">+{groupSelectedTeeth.length - 4}</div>
                                        )}
                                      </div>
                                      <span className="truncate text-[9px] sm:text-[10px] font-black text-slate-300 uppercase tracking-wide sm:tracking-widest">{groupSelectedTeeth.length} dent(s) sélectionnée(s)</span>
                                    </div>
                                    <button type="button" onClick={() => selectTeethGroup('none')} className="text-[9px] font-black text-rose-400 uppercase tracking-widest hover:text-rose-300">Réinitialiser</button>
                                  </div>

                                  {groupSuggestedActs.length > 0 ? (
                                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                      {groupSuggestedActs.map(({ act, specialty }) => (
                                        <button
                                          key={act.id}
                                          type="button"
                                          onClick={() => {
                                            const price = Number(act.base_price) || 0;
                                            setGroupTreatmentName(act.name);
                                            if (price <= 0) {
                                              setGroupTreatmentPrice('');
                                              toast.error('Tarif catalogue absent : renseignez un prix avant d’ajouter cet acte.');
                                              return;
                                            }
                                            const sorted = [...groupSelectedTeeth].sort((a, b) => a - b);
                                            setItems([...items, {
                                              id: Date.now() + Math.random(),
                                              description: act.name,
                                              dent: sorted.join('-'),
                                              price,
                                              toothNumbers: sorted,
                                              category: specialty,
                                              catalogActId: act.id,
                                            }]);
                                            selectTeethGroup('none');
                                            setGroupTreatmentName('');
                                            setGroupTreatmentPrice('');
                                            toast.success(`Ajouté : ${act.name}`);
                                          }}
                                          className="px-2.5 sm:px-3 py-2 rounded-xl text-[8px] sm:text-[9px] font-black uppercase tracking-wide sm:tracking-widest transition-all text-left truncate bg-white/10 text-slate-300 hover:bg-white/20 hover:text-white"
                                        >
                                          {act.name}
                                        </button>
                                      ))}
                                    </div>
                                  ) : (
                                    <p className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-[10px] font-bold text-slate-400">
                                      Aucun acte suggéré pour cette sélection. Retrouvez l’acte dans le catalogue.
                                    </p>
                                  )}

                                  <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-white/10">
                                    <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">Sélection rapide</span>
                                    {odontogramQuickGroupKeys(odontogramType).slice(0, 4).map(group => (
                                      <button key={group} type="button" onClick={() => selectTeethGroup(group)} className="px-2.5 py-1.5 bg-white/10 text-slate-300 hover:bg-white/20 rounded-lg text-[9px] font-black tracking-widest">{group}</button>
                                    ))}
                                    <button type="button" onClick={() => selectTeethGroup('none')} className="ml-auto px-2.5 py-1.5 text-[9px] font-black text-rose-400 hover:text-rose-300">Effacer</button>
                                  </div>
                                </>
                            </div>
                          </motion.div>
                        )}
                      </div>

                      <AnimatePresence>
                        {activeTooth && (
                          <TreatmentSelector
                            toothNumber={activeTooth}
                            currentTreatments={activeToothTreatments}
                            allowEmptyConfirm={activeToothTreatments.length > 0}
                            onConfirm={(treatments, surfaces, notes) => {
                              replaceToothTreatmentsFromSelector(activeTooth, treatments, surfaces);
                              treatments.forEach(t => {
                                if (t.price && t.price > 0) {
                                  PriceBrain.recordAct(t.name, t.price, t.category, t.id);
                                }
                              });
                              setActiveTooth(null);
                            }}
                            onCancel={() => setActiveTooth(null)}
                            embedded={false}
                          />
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        <div id="document-prestations" className="w-full space-y-6 scroll-mt-4">
          <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-xl shadow-slate-200/20 overflow-hidden">
            <div className="px-10 py-6 border-b border-slate-50 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-3">
                <History className="w-5 h-5 text-slate-400" />
                <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Détail des prestations</h3>
              </div>
              <div className="flex items-center gap-4">
                {isDevis && items.length > 0 && (
                  <button
                    type="button"
                    onClick={handlePhaseSequencing}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-500/10 text-indigo-500 rounded-lg text-[10px] font-black uppercase tracking-widest hover:bg-indigo-500/20 transition-all"
                  >
                    <Wand2 size={12} /> Organiser par phases
                  </button>
                )}
                <button
                  type="button"
                  onClick={openNewCatalogAct}
                  className="text-[10px] font-black text-primary uppercase tracking-widest hover:underline"
                >+ Ligne Manuelle</button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50/50">
                    <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest w-16 text-center">#</th>
                    <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Description de l'acte</th>
                    <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest w-32 text-center">Dent</th>
                    <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest w-44 text-right">Honoraires (MAD)</th>
                    <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest w-32"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  <AnimatePresence mode="popLayout">
                    {items.map((item, idx) => {
                      const isPhaseSeparator = isAccountingPhaseSeparator(item.description);
                      return (
                        <motion.tr
                          key={item.id}
                          layout
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0, x: -20 }}
                          className={cn(
                            "group transition-colors",
                            isPhaseSeparator ? "bg-indigo-50/70" : "hover:bg-slate-50/50"
                          )}
                        >
                          <td className="px-8 py-4 text-center font-black text-slate-300 text-xs">{idx + 1}</td>
                          <td className="px-8 py-4 relative">
                            <div className="relative group/search">
                              <input
                                type="text"
                                disabled={isPhaseSeparator}
                                className={cn(
                                  "w-full border rounded-xl px-4 py-3 text-sm font-bold outline-none transition-all",
                                  isPhaseSeparator
                                    ? "bg-transparent border-transparent text-indigo-600 cursor-default"
                                    : "bg-white border-slate-100 focus:border-primary/50 text-slate-800"
                                )}
                                value={item.description}
                                onChange={(e) => handleActSearch(e.target.value, item.id)}
                                onBlur={() => {
                                  setTimeout(() => setActiveActSearchId(null), 200);
                                  const exact = TREATMENT_TEMPLATES.find(t => normalizeCatalogName(t.name) === normalizeCatalogName(item.description));
                                  if (!exact && item.description.trim()) {
                                    setNewCatalogActName(item.description.trim());
                                    setNewCatalogActPrice(item.price > 0 ? String(item.price) : '');
                                    setNewCatalogActSpecialtyId(
                                      specialties.find(s => s.name === item.category)?.id || specialties[0]?.id || '',
                                    );
                                    setIsNewCatalogActOpen(true);
                                    setItems(prev => prev.filter(row => row.id !== item.id));
                                  }
                                }}
                                placeholder="Rechercher un acte du catalogue..."
                              />
                              {!isPhaseSeparator && activeActSearchId === item.id && actSuggestions.length > 0 && (
                                <div className="absolute top-full left-0 right-0 z-[100] bg-white border border-slate-100 rounded-2xl shadow-2xl mt-2 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                                  {actSuggestions.map((act) => (
                                    <button
                                      key={act.id}
                                      type="button"
                                      onMouseDown={(e) => e.preventDefault()}
                                      onClick={() => applyActSuggestion(item.id, act)}
                                      className="w-full text-left px-5 py-3.5 hover:bg-slate-50 flex items-center justify-between group/suggest border-b border-slate-50 last:border-0"
                                    >
                                      <div>
                                        <p className="font-bold text-sm text-slate-800">{act.name}</p>
                                        <p className="text-[9px] font-black text-slate-400 uppercase tracking-tighter">{act.category || 'GÉNÉRAL'}</p>
                                      </div>
                                      <span className="font-black text-primary text-sm">{act.base_price} <span className="text-[9px] opacity-40">MAD</span></span>
                                    </button>
                                  ))}
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="px-8 py-4">
                            <input
                              type="text"
                              disabled={isPhaseSeparator}
                              className="w-full bg-slate-50/50 border border-transparent focus:border-slate-200 rounded-xl px-3 py-3 text-center text-sm font-black text-slate-600 outline-none transition-all disabled:opacity-30 disabled:cursor-default"
                              value={item.dent}
                              onChange={(e) => updateItem(item.id, 'dent', e.target.value)}
                              placeholder="--"
                            />
                          </td>
                          <td className="px-8 py-4">
                            <div className="relative">
                              <input
                                type="number"
                                disabled={isPhaseSeparator}
                                className="w-full bg-slate-50/50 border border-transparent focus:border-primary/30 rounded-xl px-4 py-3 text-right text-sm font-black text-primary outline-none transition-all disabled:opacity-30 disabled:cursor-default"
                                style={{ color: 'var(--primary)' }}
                                value={item.price || ''}
                                onFocus={e => e.target.select()}
                                onChange={(e) => updateItem(item.id, 'price', e.target.value)}
                                placeholder="0.00"
                              />
                            </div>
                          </td>
                          <td className="px-8 py-4 text-right">
                            <div className="flex items-center justify-end gap-1 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                              <button
                                type="button"
                                onClick={() => moveItem(item.id, 'UP')}
                                disabled={idx === 0}
                                aria-label={`Monter ${item.description || `la ligne ${idx + 1}`}`}
                                className="p-2 text-slate-300 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-all disabled:opacity-20 disabled:pointer-events-none"
                              >
                                <ArrowUp size={14} />
                              </button>
                              <button
                                type="button"
                                onClick={() => moveItem(item.id, 'DOWN')}
                                disabled={idx === items.length - 1}
                                aria-label={`Descendre ${item.description || `la ligne ${idx + 1}`}`}
                                className="p-2 text-slate-300 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-all disabled:opacity-20 disabled:pointer-events-none"
                              >
                                <ArrowDown size={14} />
                              </button>
                              <button
                                type="button"
                                onClick={() => removeItem(item.id)}
                                aria-label={`Supprimer ${item.description || `la ligne ${idx + 1}`}`}
                                className="p-2.5 text-slate-300 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-all"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </td>
                        </motion.tr>
                      );
                    })}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>

            <div className="px-10 py-6 border-t border-slate-50 bg-slate-50/30 flex flex-col items-end gap-4">
              <div className="flex items-center justify-between w-full">
                <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Total</span>
                <span className="text-xl font-black text-primary">{accountingDocumentTotal(items)} MAD</span>
              </div>
              {!isDevis && (
                <button 
                  type="button"
                  onClick={() => setIsTreasuryModalOpen(true)}
                  className="w-full py-4 bg-primary text-white rounded-2xl font-black uppercase tracking-widest hover:scale-[1.02] active:scale-95 transition-all shadow-xl shadow-primary/20 flex justify-center items-center gap-2"
                >
                  <Banknote size={20} /> Procéder à l'Encaissement
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {!isDevis && isTreasuryModalOpen && (
          <div className="fixed inset-0 z-[400] flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="p-6 sm:p-10 bg-white rounded-[2rem] sm:rounded-[3rem] border border-white shadow-2xl space-y-6 sm:space-y-10 relative overflow-hidden max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            >
              <button 
                type="button"
                onClick={() => setIsTreasuryModalOpen(false)}
                className="absolute top-6 right-6 w-10 h-10 bg-slate-50 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full flex items-center justify-center transition-all z-20"
              >
                <Plus size={24} className="rotate-45" />
              </button>

              <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[120px] rounded-full pointer-events-none" />

              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between relative z-10 gap-6 sm:gap-0">
                <div className="flex items-center gap-5">
                  <div className="w-14 h-14 bg-primary/10 text-primary rounded-[1.25rem] flex items-center justify-center border border-primary/20 shadow-inner">
                    <Banknote size={28} />
                  </div>
                  <div>
                    <h4 className="text-lg font-black text-slate-800 tracking-tight uppercase">Encaissement</h4>
                    <p className="text-[10px] text-slate-400 font-black uppercase tracking-[0.2em]">Règlement et échéances</p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="flex flex-col items-end gap-2">
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-[0.3em]">Comptabiliser CA</span>
                    <button 
                      type="button"
                      onClick={() => setIsAccounted(!isAccounted)}
                      className={cn(
                        "relative w-14 h-7 rounded-full transition-all duration-500",
                        isAccounted ? "bg-primary" : "bg-slate-100"
                      )}
                    >
                      <div className={cn(
                        "absolute top-1 w-5 h-5 bg-white rounded-full shadow-lg transition-all duration-500",
                        isAccounted ? "left-8" : "left-1"
                      )} />
                    </button>
                  </div>
                </div>
              </div>

              {paymentStatusGuardMessage && (
                <div
                  role="alert"
                  className="relative z-20 flex items-start justify-between gap-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900"
                >
                  <div>
                    <div className="text-xs font-black uppercase tracking-wider">Paiement partiel</div>
                    <div className="mt-1 text-xs font-semibold">{paymentStatusGuardMessage}</div>
                  </div>
                  <button
                    type="button"
                    onClick={clearPaymentStatusGuard}
                    className="shrink-0 rounded-xl border border-amber-300 bg-white px-3 py-2 text-[10px] font-black uppercase tracking-wider"
                  >
                    Compris
                  </button>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 pt-4 relative z-10">
                <div className="space-y-4">
                  <label className={cn(labelClass, "text-slate-400")}>Statut de Règlement</label>
                  <div className="flex bg-slate-50/50 p-1.5 rounded-[1.5rem] border border-slate-100 gap-1">
                    {[
                      { id: 'EN_ATTENTE', label: 'Attente', color: 'text-amber-600 bg-white shadow-sm border border-slate-100' },
                      { id: 'PARTIEL', label: 'Partiel', color: 'text-blue-600 bg-white shadow-sm border border-slate-100' },
                      { id: 'PAYE', label: 'Réglé', color: 'text-emerald-600 bg-white shadow-sm border border-slate-100' }
                    ].map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => setPaymentStatus(s.id)}
                        className={cn(
                          "flex-1 py-3.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all",
                          paymentStatus === s.id ? s.color : "text-slate-400 hover:text-slate-600"
                        )}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-4">
                  <label className={cn(labelClass, "text-slate-400")}>Mode d'Encaissement</label>
                  <div className="flex bg-slate-50/50 p-1.5 rounded-[1.5rem] border border-slate-100 gap-1 overflow-x-auto no-scrollbar">
                    {['Espèces', 'Chèque', 'TPE', 'Virement'].map((m) => (
                      <button
                        key={m}
                        type="button"
                        onClick={() => setPaymentMode(m as any)}
                        className={cn(
                          "flex-1 px-4 py-3.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all whitespace-nowrap",
                          paymentMode === m ? "bg-white text-slate-800 shadow-sm border border-slate-100" : "text-slate-400 hover:text-slate-600"
                        )}
                      >
                        {m === 'Espèces' ? 'Cash' : m}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-4">
                  <label className={cn(labelClass, "text-slate-400")}>Structure de Facturation</label>
                  <div className="flex bg-slate-50/50 p-1.5 rounded-[1.5rem] border border-slate-100 gap-1">
                    <button
                      type="button"
                      onClick={() => setIsGlobalNote(false)}
                      className={cn(
                        "flex-1 py-3.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all",
                        !isGlobalNote ? "bg-white text-indigo-600 shadow-sm border border-slate-100" : "text-slate-400 hover:text-slate-600"
                      )}
                    >Unique</button>
                    <button
                      type="button"
                      onClick={() => setIsGlobalNote(true)}
                      className={cn(
                        "flex-1 py-3.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all",
                        isGlobalNote ? "bg-white text-purple-600 shadow-sm border border-slate-100" : "text-slate-400 hover:text-slate-600"
                      )}
                    >Global / Planifié</button>
                  </div>
                </div>
              </div>

              <AnimatePresence>
                {isGlobalNote && (
                  <motion.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="p-8 bg-slate-50/50 rounded-[2.5rem] border border-slate-100 border-dashed space-y-6 relative z-10"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em] flex items-center gap-3">
                        <History className="w-4 h-4 text-primary" /> Configuration des Échéances
                      </span>
                      <button 
                        type="button"
                        onClick={() => setInstallments([...installments, { id: Date.now(), date: new Date().toISOString().split('T')[0], amount: 0, label: `Versement ${installments.length + 1}` }])}
                        className="px-4 py-2 bg-white border border-slate-100 rounded-xl text-[9px] font-black text-slate-600 uppercase tracking-widest transition-all hover:bg-slate-50 shadow-sm"
                      >+ Nouvelle Échéance</button>
                    </div>

                    <div className="space-y-4">
                      {installments.map((inst) => (
                        <div key={inst.id} className="flex flex-col sm:grid sm:grid-cols-12 gap-4 sm:gap-4 items-center bg-white p-4 sm:p-0 rounded-2xl sm:bg-transparent">
                          <div className="w-full sm:col-span-5">
                            <input 
                              type="text" 
                              className="w-full px-5 py-3 bg-white sm:bg-white border border-slate-100 rounded-xl text-xs font-bold text-slate-700 outline-none focus:border-primary/30 transition-all"
                              value={inst.label}
                              onChange={(e) => setInstallments(installments.map(i => i.id === inst.id ? { ...i, label: e.target.value } : i))}
                            />
                          </div>
                          <div className="w-full sm:col-span-3">
                            <input 
                              type="date" 
                              className="w-full px-4 py-3 bg-white border border-slate-100 rounded-xl text-xs font-bold text-slate-700 outline-none focus:border-primary/30 transition-all"
                              value={inst.date}
                              onChange={(e) => setInstallments(installments.map(i => i.id === inst.id ? { ...i, date: e.target.value } : i))}
                            />
                          </div>
                          <div className="w-full sm:col-span-3 relative">
                            <input 
                              type="number"
                              className="w-full px-5 py-3 bg-slate-50 border border-slate-100 rounded-xl text-xs font-black text-primary outline-none focus:border-primary/50 text-right pr-12"
                              value={inst.amount}
                              onFocus={e => e.target.select()}
                              onChange={(e) => setInstallments(installments.map(i => i.id === inst.id ? { ...i, amount: Number(e.target.value) } : i))}
                            />
                            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[9px] font-black text-slate-300">MAD</span>
                          </div>
                          <div className="w-full sm:col-span-1 flex justify-end sm:justify-center">
                            <button 
                              type="button"
                              onClick={() => setInstallments(installments.filter(i => i.id !== inst.id))}
                              className="p-3 text-slate-300 hover:text-rose-400 transition-all bg-rose-50 sm:bg-transparent rounded-xl sm:rounded-none w-full sm:w-auto"
                            >
                              <Trash2 size={16} className="mx-auto" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="pt-6 border-t border-slate-100 relative z-10">
                <p className="mb-4 text-xs font-semibold text-slate-500">
                  Ces réglages seront enregistrés avec la note lors de son enregistrement.
                </p>
                <div className="flex flex-col sm:flex-row justify-end gap-4">
                <button 
                  type="button"
                  onClick={() => setIsTreasuryModalOpen(false)}
                  className="w-full sm:w-auto px-8 py-3 bg-slate-100 text-slate-500 rounded-xl font-black uppercase tracking-widest hover:bg-slate-200 transition-all text-xs"
                >Fermer</button>
                <button
                  type="button"
                  onClick={() => setIsTreasuryModalOpen(false)}
                  className="w-full sm:w-auto px-8 py-3 bg-primary text-white rounded-xl font-black uppercase tracking-widest shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all text-xs"
                >Appliquer à la note</button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
      {isNewCatalogActOpen && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center bg-slate-950/35 p-4 backdrop-blur-sm">
          <div role="dialog" aria-modal="true" aria-label="Ajouter un acte au catalogue" className="w-full max-w-lg rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl">
            <div className="mb-5">
              <h3 className="text-lg font-black text-slate-900">Ajouter un acte au catalogue</h3>
              <p className="mt-1 text-sm text-slate-500">L’acte sera enregistré dans le catalogue central puis ajouté à ce document.</p>
            </div>
            <div className="space-y-4">
              <label className="block space-y-1.5">
                <span className="text-xs font-black uppercase tracking-wide text-slate-500">Spécialité</span>
                <select
                  value={newCatalogActSpecialtyId}
                  onChange={(e) => setNewCatalogActSpecialtyId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm font-bold text-slate-800"
                >
                  <option value="">Choisir une spécialité</option>
                  {specialties.map(specialty => (
                    <option key={specialty.id} value={specialty.id}>{specialty.name}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-1.5">
                <span className="text-xs font-black uppercase tracking-wide text-slate-500">Acte</span>
                <input
                  value={newCatalogActName}
                  onChange={(e) => setNewCatalogActName(e.target.value)}
                  placeholder="Nom de l'acte"
                  className="w-full rounded-xl border border-slate-200 px-3 py-3 text-sm font-bold text-slate-800"
                />
              </label>
              <label className="block space-y-1.5">
                <span className="text-xs font-black uppercase tracking-wide text-slate-500">Tarif catalogue (facultatif)</span>
                <input
                  type="number"
                  min="0"
                  value={newCatalogActPrice}
                  onChange={(e) => setNewCatalogActPrice(e.target.value)}
                  placeholder="Tarif à définir"
                  className="w-full rounded-xl border border-slate-200 px-3 py-3 text-sm font-bold text-slate-800"
                />
              </label>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button type="button" onClick={() => setIsNewCatalogActOpen(false)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-bold text-slate-600">Annuler</button>
              <button type="button" onClick={addCatalogActLine} className="rounded-xl bg-primary px-4 py-2.5 text-sm font-black text-white">Créer et ajouter</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};