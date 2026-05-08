import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { 
  Calculator, 
  Plus, 
  Trash2, 
  Search,
  Zap,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Banknote
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils/cn';
import { useClinicalRef } from '../clinical-ref/useClinicalRef';
import { ClinicalRefSidebar } from '../clinical-ref/ClinicalRefSidebar';
import { Brain } from 'lucide-react';
import { Odontogram } from '../../components/odontogram';
import { OdontogramSVG } from '../../components/odontogram/OdontogramSVG';
import type { SelectedSurfaceData } from '../../components/odontogram/types';
import { api } from '../../services/api';
import type { ValidationError, CoherenceWarning } from './DocumentStudio/useDocumentGenerator';

interface PriceItem { 
  id: number; 
  description: string; 
  dent: string; 
  price: number;
  toothNumbers?: number[];
  _odontogramKey?: string;
  category?: string;
}

export interface InstallmentItem {
  id: number;
  date: string;
  amount: number;
  label: string;
}

interface AccountingStudioProps {
  isDevis?: boolean;
  patientId: string;
  items: PriceItem[];
  setItems: (items: PriceItem[]) => void;
  paymentMode: string;
  setPaymentMode: (mode: string) => void;
  showOdontoPanoramique: boolean;
  odontogramMode: 'individual' | 'group' | 'ortho';
  setOdontogramMode: (mode: 'individual' | 'group' | 'ortho') => void;
  groupSelectedTeeth: number[];
  handleToothDirectClick: (toothNumber: number) => void;
  selectTeethGroup: (group: 'all' | 'maxillaire' | 'mandibule' | 'none') => void;
  groupTreatmentName: string;
  setGroupTreatmentName: (val: string) => void;
  groupTreatmentPrice: number | '';
  setGroupTreatmentPrice: (val: number | '') => void;
  applyGroupTreatment: () => void;
  handleTeethFromOdontogram: (teeth: SelectedSurfaceData[]) => void;
  addEmptyRow: () => void;
  removeItem: (id: number) => void;
  updateItem: (id: number, field: keyof PriceItem, value: string | number) => void;
  handleActSearch: (query: string, itemId: number) => void;
  activeActSearchId: number | null;
  setActiveActSearchId: (id: number | null) => void;
  actSuggestions: any[];
  applyActSuggestion: (itemId: number, act: any) => void;
  installments: InstallmentItem[];
  setInstallments: (val: InstallmentItem[]) => void;
  validationErrors?: ValidationError[];
  coherenceWarnings?: CoherenceWarning[];
}

const getCategoryColor = (cat: string) => {
  switch (cat) {
    case 'CHIR': return 'bg-rose-50 text-rose-600 border-rose-100';
    case 'PROTH': return 'bg-blue-50 text-blue-600 border-blue-100';
    case 'CONS': return 'bg-emerald-50 text-emerald-600 border-emerald-100';
    case 'PREV': return 'bg-amber-50 text-amber-600 border-amber-100';
    default: return 'bg-slate-50 text-slate-500 border-slate-100';
  }
};

export const AccountingStudio: React.FC<AccountingStudioProps> = (props) => {
  const {
    isDevis = false,
    patientId,
    items,
    paymentMode,
    setPaymentMode,
    showOdontoPanoramique,
    odontogramMode,
    setOdontogramMode,
    groupSelectedTeeth,
    handleToothDirectClick,
    selectTeethGroup,
    groupTreatmentName,
    setGroupTreatmentName,
    groupTreatmentPrice,
    setGroupTreatmentPrice,
    applyGroupTreatment,
    handleTeethFromOdontogram,
    addEmptyRow,
    removeItem,
    updateItem,
    handleActSearch,
    activeActSearchId,
    setActiveActSearchId,
    actSuggestions,
    applyActSuggestion,
    installments,
    setInstallments,
    validationErrors = [],
    coherenceWarnings = [],
  } = props;

  // Zen-Elite state: Collapsible Odontogram
  const [isOdontoOpen, setIsOdontoOpen] = useState(items.length === 0);
  const [quickActs, setQuickActs] = useState<{ name: string; price: number; category: string }[]>([]);
  
  const [activeGuideAct, setActiveGuideAct] = useState<string | null>(null);
  const protocol = useClinicalRef(activeGuideAct || undefined);

  useEffect(() => {
    fetchQuickActs();
  }, []);

  const fetchQuickActs = async () => {
    try {
      const res = await api.get('/accounting/frequent-acts');
      if (res.data && res.data.length > 0) {
        setQuickActs(res.data);
      } else {
        setQuickActs([
          { name: 'Consultation', price: 300, category: 'CONS' },
          { name: 'Détartrage', price: 500, category: 'PREV' },
          { name: 'Composite 1 face', price: 400, category: 'CONS' },
          { name: 'Extraction simple', price: 600, category: 'CHIR' },
        ]);
      }
    } catch (err) {
      console.error("Erreur habitudes acts:", err);
    }
  };

  const saveActAsHabit = async (name: string, price: number, category?: string) => {
    try {
      await api.post('/accounting/record-act', { name, price, category });
      fetchQuickActs();
    } catch (err) { console.error(err); }
  };

  // Ensure at least one empty line if items is empty
  useEffect(() => {
    if (items.length === 0) {
      addEmptyRow();
    }
  }, [items.length, addEmptyRow]);

  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-2 ml-1";
  const inputClass = "w-full px-5 py-4 bg-white/70 border border-slate-100 rounded-2xl text-sm outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all duration-300 shadow-sm font-bold text-slate-800";

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-1000 pb-32">

      {/* Erreurs de validation */}
      {validationErrors.length > 0 && (
        <div className="space-y-2">
          {validationErrors.map((err, idx) => (
            <div key={idx} className="px-6 py-3 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-600 font-bold flex items-center gap-3 animate-in slide-in-from-top-2">
              <AlertCircle size={16} /> {err.message}
            </div>
          ))}
        </div>
      )}

      {/* Alertes de cohérence (1.2) */}
      {coherenceWarnings.length > 0 && (
        <div className="space-y-2">
          {coherenceWarnings.map((w, idx) => (
            <div key={idx} className={cn(
              "px-6 py-3 rounded-2xl text-xs font-bold flex items-center gap-3 animate-in slide-in-from-top-2",
              w.level === 'warning' ? "bg-amber-50 border border-amber-200 text-amber-700"
                : w.level === 'critical' ? "bg-red-50 border border-red-200 text-red-600"
                : "bg-blue-50 border border-blue-200 text-blue-600"
            )}>
              <AlertCircle size={16} className="shrink-0" /> {w.message}
            </div>
          ))}
        </div>
      )}

      {/* 1. RACCOURCIS RAPIDES */}
      <div className="flex flex-wrap gap-3 p-6 bg-white/60 backdrop-blur-2xl rounded-[2rem] border border-white/80 shadow-[0_8px_30px_rgba(0,0,0,0.03)] items-center relative z-20">
        <div className="flex items-center gap-3 pr-6 border-r border-slate-200">
          <div className="w-9 h-9 bg-amber-500/10 text-amber-600 rounded-xl flex items-center justify-center border border-amber-100">
            <Zap size={18} />
          </div>
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Rapide</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {quickActs.map((act, i) => (
            <motion.button
              key={i}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                props.setItems([...items, { id: Date.now()+i, description: act.name, price: act.price, dent: '-', category: act.category }]);
                saveActAsHabit(act.name, act.price, act.category);
              }}
              className={cn(
                "px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest border transition-all flex items-center gap-2",
                getCategoryColor(act.category || '')
              )}
            >
              {act.name} <span className="opacity-40 font-bold">+{act.price}</span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* 2. ASSISTANT CLINIQUE (Sélecteur de Dents) */}
      {showOdontoPanoramique && (
        <motion.div 
          layout
          className="bg-slate-50/50 rounded-[2rem] border border-slate-200/50 overflow-hidden transition-all duration-500"
        >
          <button 
            onClick={() => setIsOdontoOpen(!isOdontoOpen)}
            className="w-full px-8 py-4 flex items-center justify-between hover:bg-white/40 transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                <Calculator size={16} />
              </div>
              <span className="text-[10px] font-black uppercase tracking-widest block text-slate-500">
                {odontogramMode === 'ortho' ? 'Configuration Globale' : 'Sélecteur de Dents / Odontogramme'}
              </span>
            </div>
            <div className="flex items-center gap-3">
              {!isOdontoOpen && odontogramMode !== 'ortho' && groupSelectedTeeth.length > 0 && (
                <span className="px-3 py-1 bg-primary/10 text-primary rounded-lg text-[9px] font-black">
                  {groupSelectedTeeth.length} dent(s) sélectionnée(s)
                </span>
              )}
              {isOdontoOpen ? <ChevronUp size={16} className="text-slate-300" /> : <ChevronDown size={16} className="text-slate-300" />}
            </div>
          </button>

          <AnimatePresence>
            {isOdontoOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="px-6 pb-6 space-y-6"
              >
                <div className="flex bg-slate-200/40 p-1 rounded-xl gap-1 w-fit transition-all border border-slate-200/20 mx-auto">
                  {(['individual', 'group', 'ortho'] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setOdontogramMode(mode)}
                      className={cn(
                        "px-6 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all",
                        odontogramMode === mode ? "bg-white shadow-md text-primary" : "text-slate-400 hover:text-slate-600"
                      )}
                      style={odontogramMode === mode ? { color: 'var(--primary)' } : {}}
                    >
                      {mode === 'individual' ? 'Unitaire' : mode === 'group' ? 'Multi-Dents' : 'Global'}
                    </button>
                  ))}
                </div>

                {odontogramMode === 'ortho' ? (
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in zoom-in-95 duration-500">
                    <div className="lg:col-span-8 space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <label className={labelClass}>Libellé</label>
                          <input type="text" className={cn(inputClass, "py-3 text-xs")} value={groupTreatmentName} onChange={(e) => setGroupTreatmentName(e.target.value)} placeholder="Traitement..." />
                        </div>
                        <div className="space-y-1">
                          <label className={labelClass}>Prix</label>
                          <input type="number" className={cn(inputClass, "py-3 text-xs font-black text-primary")} style={{ color: 'var(--primary)' }} value={groupTreatmentPrice} onChange={(e) => setGroupTreatmentPrice(e.target.value === '' ? '' : Number(e.target.value))} />
                        </div>
                      </div>
                      <div className="p-5 bg-emerald-50/50 rounded-2xl border border-emerald-100/50 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-emerald-500/20 rounded-xl flex items-center justify-center text-emerald-600">
                             <Banknote size={20} />
                          </div>
                          <div>
                            <span className="text-[9px] font-black text-emerald-600/60 uppercase tracking-widest block">Flexible</span>
                            <span className="text-xs font-black text-emerald-800">Échéancier auto</span>
                          </div>
                        </div>
                        <button 
                          onClick={() => {
                            applyGroupTreatment();
                            setIsOdontoOpen(false);
                          }}
                          className="px-6 py-3 bg-emerald-600 text-white rounded-xl font-black uppercase tracking-widest text-[9px] shadow-lg shadow-emerald-600/20 hover:-translate-y-0.5 transition-all"
                        >
                          Valider
                        </button>
                      </div>
                    </div>
                    <div className="lg:col-span-4 bg-white/50 rounded-2xl border border-slate-100 p-6 flex flex-col justify-center text-center">
                       <span className="text-3xl font-black text-slate-800 tracking-tighter mb-1">{installments.reduce((s, i) => s + i.amount, 0)} <span className="text-[10px] uppercase opacity-30">MAD</span></span>
                       <span className={labelClass}>Planifié</span>
                       <button 
                        onClick={() => setInstallments([...installments, { id: Date.now(), date: new Date().toISOString().split('T')[0], amount: 0, label: `Versement ${installments.length + 1}` }])}
                        className="mt-3 text-[8px] font-black uppercase tracking-widest text-emerald-600 hover:underline"
                       >
                         + Échéance
                       </button>
                    </div>
                  </div>
                ) : (
                  <div className="animate-in fade-in zoom-in-95 duration-500 max-w-xl mx-auto">
                    {odontogramMode === 'individual' ? (
                      <div className="transform scale-90 origin-top transition-transform duration-500">
                        <Odontogram 
                          patientId={parseInt(patientId, 10)} 
                          mode="SELECT_FOR_DOCUMENT"
                          onChange={handleTeethFromOdontogram}
                          compact={true}
                          naked={true}
                        />
                      </div>
                    ) : (
                      <div className="animate-in fade-in duration-500">
                        <div className="transform scale-90 origin-top transition-transform duration-500">
                          <OdontogramSVG 
                            type="ADULT" 
                            teethSurfaces={{}}
                            selectedTooth={null}
                            selectedSurface={null}
                            onSurfaceClick={() => {}}
                            multiSelectedTeeth={groupSelectedTeeth} 
                            onToothDirectClick={handleToothDirectClick} 
                            showNumbers={false}
                          />
                        </div>
                        <div className="flex justify-center gap-2 mt-[-60px] pb-6">
                          {(['maxillaire', 'mandibule', 'none'] as const).map(g => (
                            <button 
                              key={g} 
                              onClick={() => selectTeethGroup(g)} 
                              className="px-5 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest border border-slate-200 bg-white shadow-sm hover:shadow-md hover:text-primary transition-all text-slate-400"
                            >
                              {g === 'none' ? 'Effacer' : g}
                            </button>
                          ))}
                        </div>
                      </div>
                     )}
                    {odontogramMode === 'group' && groupSelectedTeeth.length > 0 && (
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-6 p-5 bg-white/80 rounded-2xl border border-primary/20 shadow-xl shadow-primary/5 flex flex-col lg:flex-row items-center gap-4"
                      >
                        <div className="flex-1 w-full grid grid-cols-1 md:grid-cols-2 gap-4">
                          <input 
                            type="text" 
                            className={cn(inputClass, "py-3 text-xs")} 
                            placeholder="Acte pour ce groupe..." 
                            value={groupTreatmentName}
                            onChange={(e) => setGroupTreatmentName(e.target.value)}
                          />
                          <div className="relative">
                            <input 
                              type="number" 
                              className={cn(inputClass, "py-3 text-xs pr-12 font-black text-primary")} 
                              style={{ color: 'var(--primary)' }}
                              placeholder="Prix total..." 
                              value={groupTreatmentPrice}
                              onChange={(e) => setGroupTreatmentPrice(e.target.value === '' ? '' : Number(e.target.value))}
                            />
                            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[8px] font-black text-slate-300 uppercase">MAD</span>
                          </div>
                        </div>
                        <button 
                          onClick={() => {
                            applyGroupTreatment();
                            setIsOdontoOpen(false);
                          }}
                          className="w-full lg:w-auto px-8 py-3.5 bg-primary text-white rounded-xl font-black uppercase tracking-widest text-[9px] shadow-lg shadow-primary/20 hover:-translate-y-0.5 transition-all"
                        >
                          Appliquer au groupe
                        </button>
                      </motion.div>
                    )}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}

      {/* 2. LISTE DES SOINS */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-black uppercase tracking-[0.3em] text-slate-400">Détail des actes</h3>
          <button
            onClick={addEmptyRow}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary/10 text-primary rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-primary/20 transition-all"
            style={{ color: 'var(--primary)' }}
          >
            <Plus size={14} /> Ajouter un acte
          </button>
        </div>

        <div className="space-y-3">
          <AnimatePresence mode="popLayout">
            {items.map((item, idx) => (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="group flex items-center gap-4 bg-white/50 hover:bg-white backdrop-blur-sm p-5 rounded-[2rem] border border-white/60 hover:border-primary/20 hover:shadow-xl hover:shadow-primary/5 transition-all duration-300"
              >
                <div className="w-10 h-10 bg-slate-100/50 rounded-xl flex items-center justify-center text-slate-400 group-hover:text-primary group-hover:bg-primary/10 transition-all font-black text-xs">
                  {idx + 1}
                </div>
                <div className="flex-1 relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 pointer-events-none group-focus-within:text-primary transition-colors">
                    <Search size={16} />
                  </div>
                  <input
                    type="text"
                    className={cn(inputClass, "pl-12 border-transparent bg-transparent shadow-none hover:bg-slate-50/50 transition-colors")}
                    value={item.description}
                    onChange={(e) => {
                      const isLast = idx === items.length - 1;
                      const wasEmpty = !item.description.trim();
                      handleActSearch(e.target.value, item.id);
                      
                      // Smart Add: Only add if last, previously empty, now filled, AND no empty row follows
                      const hasNextEmpty = items[idx + 1] && !items[idx + 1].description.trim();
                      if (isLast && wasEmpty && e.target.value.trim() && !hasNextEmpty) {
                        addEmptyRow();
                      }
                    }}
                    onBlur={() => setTimeout(() => setActiveActSearchId(null), 150)}
                    placeholder="Désignation du soin..."
                  />
                  {activeActSearchId === item.id && actSuggestions.length > 0 && (
                    <div className="absolute top-full left-0 right-0 z-[100] bg-white/95 backdrop-blur-xl border border-slate-100 rounded-[1.5rem] shadow-2xl mt-3 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                      {actSuggestions.map((act) => (
                        <button
                          key={act.id}
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={() => applyActSuggestion(item.id, act)}
                          className="w-full text-left px-6 py-4 hover:bg-primary/5 border-b border-slate-50 last:border-0 transition-all flex items-center justify-between group/suggest"
                        >
                          <div className="flex flex-col">
                            <span className="font-black text-sm group-hover/suggest:text-primary transition-colors">{act.name}</span>
                            <span className="text-[8px] font-black uppercase text-slate-300 tracking-widest">{act.category}</span>
                          </div>
                          <span className="text-sm font-black" style={{ color: 'var(--primary)' }}>{act.base_price} MAD</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <div className="w-24">
                  <input
                    type="text"
                    className={cn(inputClass, "text-center px-2 border-transparent bg-transparent shadow-none hover:bg-slate-50/50")}
                    value={item.dent}
                    onChange={(e) => updateItem(item.id, 'dent', e.target.value)}
                    placeholder="Dent"
                  />
                </div>
                <div className="w-36 relative">
                  <input
                    type="number"
                    className={cn(inputClass, "text-right pr-12 border-transparent bg-transparent shadow-none hover:bg-slate-50/50 text-primary")}
                    style={{ color: 'var(--primary)' }}
                    value={item.price}
                    onChange={(e) => updateItem(item.id, 'price', e.target.value)}
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[9px] font-black text-slate-300 uppercase">MAD</span>
                </div>
                
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                  <button
                    onClick={() => {
                      if (!item.description.trim()) {
                        toast.error("Veuillez saisir un acte pour consulter le guide.");
                        return;
                      }
                      setActiveGuideAct(item.description);
                      toast.success(`Chargement du guide : ${item.description.substring(0, 20)}...`, { icon: '🧠', duration: 2000 });
                    }}
                    className="p-3 text-slate-300 hover:text-primary hover:bg-primary/5 rounded-xl transition-all group/brain relative"
                    title="Guide Clinique IA"
                  >
                    <Brain size={18} className={cn(activeGuideAct === item.description ? "text-primary animate-pulse" : "")} />
                  </button>
                  <button
                    onClick={() => removeItem(item.id)}
                    className="p-3 text-slate-300 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-all"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* 2.5 MODE DE RÈGLEMENT (Intégré) */}
      {!isDevis && (
        <div className="p-6 bg-white/40 backdrop-blur-xl rounded-[2rem] border border-white/60 shadow-sm flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-slate-100 text-slate-500 rounded-xl flex items-center justify-center border border-slate-200">
              <Banknote size={18} />
            </div>
            <div>
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest block">Règlement</span>
              <span className="text-xs font-black text-slate-700">Mode de paiement principal</span>
            </div>
          </div>
          <div className="flex bg-slate-200/50 p-1 rounded-xl gap-1">
            {['Espèces', 'Chèque', 'TPE', 'Virement'].map(m => (
              <button
                key={m}
                onClick={() => setPaymentMode(m as any)}
                className={cn(
                  "px-5 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all",
                  paymentMode === m ? "bg-white shadow-md text-primary" : "text-slate-400 hover:text-slate-600"
                )}
                style={paymentMode === m ? { color: 'var(--primary)' } : {}}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      )}


      {protocol && (
        <ClinicalRefSidebar 
          protocol={protocol} 
          isOpen={!!activeGuideAct} 
          onClose={() => setActiveGuideAct(null)} 
        />
      )}
    </div>
  );
};
