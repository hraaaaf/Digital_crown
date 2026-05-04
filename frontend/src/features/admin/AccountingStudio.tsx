import React from 'react';
import { 
  Calculator, 
  Plus, 
  Trash2, 
  Search,
  Zap,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils/cn';
import { Odontogram } from '../../components/odontogram';
import { OdontogramSVG } from '../../components/odontogram/OdontogramSVG';
import type { SelectedSurfaceData } from '../../components/odontogram/types';
import { api } from '../../services/api';

interface PriceItem { 
  id: number; 
  description: string; 
  dent: string; 
  price: number;
  toothNumbers?: number[];
  _odontogramKey?: string;
}

export interface InstallmentItem {
  id: number;
  date: string;
  amount: number;
  label: string;
}

interface AccountingStudioProps {
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
  calculateTotal: () => number;
  installments: InstallmentItem[];
  setInstallments: (val: InstallmentItem[]) => void;
  validationErrors?: ValidationError[];
  coherenceWarnings?: CoherenceWarning[];
}

import type { ValidationError, CoherenceWarning } from './DocumentStudio/useDocumentGenerator';
import { AlertCircle, AlertTriangle } from 'lucide-react';

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
    calculateTotal,
    installments,
    setInstallments,
    validationErrors = [],
    coherenceWarnings = []
  } = props;

  // Dynamics Quick Acts state (Habit-based)
  const [quickActs, setQuickActs] = React.useState<{ name: string; price: number; category: string }[]>([]);

  React.useEffect(() => {
    fetchQuickActs();
  }, []);

  const fetchQuickActs = async () => {
    try {
      const res = await api.get('/accounting/frequent-acts');
      if (res.data && res.data.length > 0) {
        setQuickActs(res.data);
      } else {
        // Elite Default Fallback
        setQuickActs([
          { name: 'Consultation', price: 300, category: 'CONS' },
          { name: 'Détartrage', price: 500, category: 'PREV' },
          { name: 'Composite 1 face', price: 400, category: 'CONS' },
          { name: 'Extraction simple', price: 600, category: 'CHIR' },
        ]);
      }
    } catch (err) {
      console.error("Erreur chargement habitudes acts:", err);
    }
  };

  const saveActAsHabit = async (name: string, price: number, category?: string) => {
    try {
      await api.post('/accounting/record-act', { name, price, category });
      fetchQuickActs(); // Refresh shortcuts
    } catch (err) {
      console.error(err);
    }
  };

  const inputClass = "w-full px-4 py-3 bg-white/70 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-300 shadow-sm font-medium text-slate-800";
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1";
  const addButtonClass = "w-full py-4 border-2 border-dashed border-slate-200 text-slate-400 rounded-2xl flex items-center justify-center gap-2 hover:border-primary hover:text-primary hover:bg-primary/5 transition-all font-bold mt-2";

  // Check for high total warning
  const highTotalWarning = coherenceWarnings.find(w => w.message.includes('Total élevé'));
  // Check for empty items error
  const globalItemsError = validationErrors.find(e => e.field === 'items');

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* Global Alerts Center */}
      {(highTotalWarning || globalItemsError) && (
        <div className="space-y-2">
          {globalItemsError && (
            <div className="px-6 py-3 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-600 font-bold flex items-center gap-3 animate-in slide-in-from-top-2">
              <AlertCircle size={16} /> {globalItemsError.message}
            </div>
          )}
          {highTotalWarning && (
            <div className="px-6 py-3 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-600 font-bold flex items-center gap-3 animate-in slide-in-from-top-2">
              <AlertTriangle size={16} /> {highTotalWarning.message}
            </div>
          )}
        </div>
      )}
      
      {/* QUICK ACTIONS BAR (Phase 3) - LIGHT ELITE */}
      <div className="flex flex-wrap gap-3 p-6 bg-white/40 backdrop-blur-xl rounded-[2.5rem] border border-white/60 shadow-[0_20px_50px_rgba(0,51,128,0.04)] relative overflow-hidden group/bar">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] -mr-32 -mt-32 rounded-full" />
        
        <div className="flex items-center gap-4 px-4 mr-4 border-r border-slate-200 relative z-10">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/10 shadow-sm">
            <Zap size={20} />
          </div>
          <div className="hidden sm:block">
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 block leading-none mb-1">Raccourcis</span>
            <span className="text-xs font-black uppercase tracking-widest" style={{ color: 'var(--primary)' }}>Actes Rapides</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 relative z-10">
          {quickActs.map((act, idx) => (
            <button
              key={`${act.name}-${idx}`}
              onClick={() => {
                const newId = Date.now();
                const newItem = { id: newId, description: act.name, price: act.price, dent: '', category: act.category };
                props.setItems([...props.items, newItem as any]);
              }}
              className={cn(
                "group px-5 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 border flex items-center gap-3",
                act.category === 'CHIR' 
                  ? "bg-rose-50 border-rose-100 text-rose-600 hover:bg-rose-600 hover:text-white" 
                  : act.category === 'PROTH'
                  ? "bg-blue-50 border-blue-100 text-blue-600 hover:bg-blue-600 hover:text-white"
                  : act.category === 'CONS'
                  ? "bg-emerald-50 border-emerald-100 text-emerald-600 hover:bg-emerald-600 hover:text-white"
                  : "bg-slate-50 border-slate-100 text-slate-500 hover:bg-slate-600 hover:text-white"
              )}
            >
              <div className="w-1.5 h-1.5 rounded-full bg-current opacity-40 group-hover:opacity-100" />
              {act.name}
              <span className="opacity-40 group-hover:opacity-100 text-[8px] ml-1 font-bold">+{act.price}</span>
            </button>
          ))}
        </div>
      </div>

      {/* DYNAMIC PANORAMIC SECTION */}
      {showOdontoPanoramique && (
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-slate-50/50 rounded-[2.5rem] border border-slate-100 p-8 shadow-inner relative"
        >
          <div className="flex bg-slate-200/50 p-1.5 rounded-2xl gap-1 w-fit mb-8 transition-all">
            <button
              onClick={() => setOdontogramMode('individual')}
              className={cn(
                "px-6 py-2.5 rounded-xl text-[10px] font-black uppercase transition-all",
                odontogramMode === 'individual' ? "bg-white shadow-md" : "text-slate-500"
              )}
              style={odontogramMode === 'individual' ? { color: 'var(--primary)' } : {}}
            >
              Acte Unitaire
            </button>
            <button
              onClick={() => setOdontogramMode('group')}
              className={cn(
                "px-6 py-2.5 rounded-xl text-[10px] font-black uppercase transition-all",
                odontogramMode === 'group' ? "bg-white text-emerald-600 shadow-md" : "text-slate-500"
              )}
            >
              Bridge / PAP
            </button>
            <button
              onClick={() => {
                setOdontogramMode('ortho');
                if (!groupTreatmentName) setGroupTreatmentName('Traitement Orthodontique');
              }}
              className={cn(
                "px-6 py-2.5 rounded-xl text-[10px] font-black uppercase transition-all",
                odontogramMode === 'ortho' ? "bg-white text-primary shadow-md" : "text-slate-500"
              )}
              style={odontogramMode === 'ortho' ? { color: 'var(--primary)' } : {}}
            >
              Orthodontie
            </button>
          </div>

          {odontogramMode === 'ortho' ? (
            <div className="space-y-8 py-2">
               {/* SMART ORTHO DASHBOARD */}
               <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="md:col-span-1 bg-white/60 p-6 rounded-[2.5rem] border border-white shadow-sm flex flex-col items-center justify-center">
                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center text-primary mb-3 shadow-inner">
                      <Calculator size={28} />
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Mode</span>
                    <span className="text-sm font-black text-slate-800">ORTHO ELITE</span>
                  </div>
                  
                  <div className="md:col-span-3 bg-white/40 backdrop-blur-md p-8 rounded-[2.5rem] border border-white/60 shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 blur-3xl rounded-full" />
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-8 relative z-10">
                      <div className="flex-1 w-full">
                        <div className="flex justify-between items-end mb-3">
                          <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Progression du règlement</span>
                          <span className="text-xs font-black text-emerald-600">
                            {groupTreatmentPrice ? Math.round((installments.reduce((s, i) => s + i.amount, 0) / Number(groupTreatmentPrice)) * 100) : 0}%
                          </span>
                        </div>
                        <div className="h-3 w-full bg-slate-200/50 rounded-full overflow-hidden border border-white">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${groupTreatmentPrice ? Math.min(100, (installments.reduce((s, i) => s + i.amount, 0) / Number(groupTreatmentPrice)) * 100) : 0}%` }}
                            className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]"
                          />
                        </div>
                      </div>
                      <div className="flex gap-8 border-l border-slate-200 pl-8">
                        <div className="text-right">
                          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">Déjà Réglé</span>
                          <span className="text-xl font-black text-emerald-600">{installments.reduce((s, i) => s + i.amount, 0).toLocaleString('fr-FR')} <span className="text-[10px] opacity-60 font-bold">MAD</span></span>
                        </div>
                        <div className="text-right">
                          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">Reste à percevoir</span>
                          <span className="text-xl font-black text-amber-500">{(Number(groupTreatmentPrice || 0) - installments.reduce((s, i) => s + i.amount, 0)).toLocaleString('fr-FR')} <span className="text-[10px] opacity-60 font-bold">MAD</span></span>
                        </div>
                      </div>
                    </div>
                  </div>
               </div>

               {/* ORTHO CONFIGURATION & GENERATOR */}
               <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                  <div className="lg:col-span-8 bg-white/40 p-10 rounded-[2.5rem] border border-white/60 space-y-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <div>
                        <label className={labelClass}>Libellé du traitement global</label>
                        <input
                          type="text"
                          className={inputClass}
                          placeholder="Ex: Traitement Ortho - Semestre 1"
                          value={groupTreatmentName}
                          onChange={(e) => setGroupTreatmentName(e.target.value)}
                        />
                      </div>
                      <div>
                        <label className={labelClass}>Total Contrat (MAD)</label>
                        <input
                          type="number"
                          className={cn(inputClass, "font-black text-xl")}
                          value={groupTreatmentPrice}
                          onChange={(e) => setGroupTreatmentPrice(e.target.value === '' ? '' : Number(e.target.value))}
                          style={{ color: 'var(--primary)' }}
                        />
                      </div>
                    </div>

                    <div className="pt-6 border-t border-white/40 flex flex-wrap items-end gap-4">
                      <div className="flex-1 min-w-[200px]">
                        <label className={labelClass} style={{ color: '#059669' }}>Avance Initiale immédiate</label>
                        <div className="relative">
                          <input
                            type="number"
                            id="ortho-advance"
                            className={cn(inputClass, "border-emerald-100 focus:ring-emerald-500/20 focus:border-emerald-500 font-bold")}
                            placeholder="Ex: 2000"
                          />
                          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[9px] font-black text-emerald-400 uppercase">MAD</span>
                        </div>
                      </div>
                      
                      <button
                        onClick={() => {
                          if (!groupTreatmentName.trim()) return;
                          const advance = Number((document.getElementById('ortho-advance') as HTMLInputElement)?.value) || 0;
                          
                          // 1. Mise à jour de l'acte principal
                          const existingMain = props.items.find(i => i.description === groupTreatmentName);
                          if (existingMain) {
                            props.updateItem(existingMain.id, 'price', Number(groupTreatmentPrice) || 0);
                          } else {
                            props.setItems([{ 
                              id: Date.now(), 
                              description: groupTreatmentName, 
                              dent: '-', 
                              price: Number(groupTreatmentPrice) || 0 
                            }, ...props.items]);
                          }

                          // 2. Ajouter l'avance si présente
                          if (advance > 0) {
                            setInstallments([...installments, { 
                              id: Date.now() + 1, 
                              date: new Date().toISOString().split('T')[0], 
                              amount: advance, 
                              label: 'Avance initiale' 
                            }]);
                          }
                          if (document.getElementById('ortho-advance')) (document.getElementById('ortho-advance') as HTMLInputElement).value = '';
                        }}
                        className="px-8 py-5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-black uppercase tracking-widest flex items-center justify-center gap-3 transition-all shadow-xl shadow-emerald-500/20 active:scale-95"
                      >
                        <Zap size={20} /> Appliquer
                      </button>
                    </div>
                  </div>

                  <div className="lg:col-span-4 bg-primary/5 p-8 rounded-[2.5rem] border border-primary/10 flex flex-col justify-center items-center text-center space-y-4 group">
                    <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center text-primary group-hover:scale-110 transition-transform duration-500">
                      <Zap size={24} />
                    </div>
                    <div>
                      <h4 className="text-[11px] font-black uppercase tracking-widest text-primary">Smart Generator</h4>
                      <p className="text-[9px] font-bold text-slate-500 mt-2 px-4 italic leading-relaxed">Étaler automatiquement le reste à payer sur les mois à venir.</p>
                    </div>
                    <div className="flex items-center gap-2 w-full pt-2">
                       <input 
                         type="number" 
                         id="spread-months" 
                         className="w-16 px-2 py-3 bg-white border border-primary/20 rounded-xl text-center text-xs font-black text-primary outline-none focus:ring-2 focus:ring-primary/20" 
                         defaultValue={6} 
                       />
                       <button
                         onClick={() => {
                           const months = Number((document.getElementById('spread-months') as HTMLInputElement)?.value) || 6;
                           const remaining = Number(groupTreatmentPrice || 0) - installments.reduce((s, i) => s + i.amount, 0);
                           if (remaining <= 0) return;
                           
                           const monthly = Math.round(remaining / months);
                           const newInst = [];
                           for (let i = 1; i <= months; i++) {
                             const d = new Date();
                             d.setMonth(d.getMonth() + i);
                             newInst.push({
                               id: Date.now() + i + Math.random(),
                               date: d.toISOString().split('T')[0],
                               amount: monthly,
                               label: `Mensualité ${installments.filter(inst => inst.label.includes('Mensualité')).length + i}`
                             });
                           }
                           setInstallments([...installments, ...newInst]);
                         }}
                         className="flex-1 py-3 bg-primary text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-primary/20 hover:bg-primary-hover active:scale-95 transition-all"
                         style={{ backgroundColor: 'var(--primary)' }}
                       >
                         Étaler le Reste
                       </button>
                    </div>
                  </div>
               </div>
            </div>
          ) : odontogramMode === 'individual' ? (
            <div className="flex-1 flex justify-center items-center py-2">
              <div className="w-full max-w-[500px] mx-auto px-4">
                <Odontogram
                  patientId={parseInt(patientId || '0', 10)}
                  mode="SELECT_FOR_DOCUMENT"
                  onChange={handleTeethFromOdontogram}
                  showLegend={false}
                  compact={true}
                  className="border-0 shadow-none bg-transparent"
                />
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 py-2">
              <div className="bg-white p-6 rounded-[2.5rem] border border-slate-100 shadow-sm flex flex-col justify-center min-h-[220px] max-w-[450px] mx-auto w-full group">
                <div className="transition-transform group-hover:scale-105 duration-700">
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
                <div className="flex flex-wrap gap-2 mt-6 justify-center">
                  {(['all', 'maxillaire', 'mandibule', 'none'] as const).map((g) => (
                    <button
                      key={g}
                      onClick={() => selectTeethGroup(g)}
                      className="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest border border-emerald-100 text-emerald-600 hover:bg-emerald-50 bg-white transition-all shadow-sm active:scale-95"
                    >
                      {g === 'none' ? 'Réinitialiser' : g}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-6 flex flex-col justify-center bg-white/40 p-10 rounded-[2.5rem] border border-white/60">
                <div>
                  <label className={labelClass}>Libellé du soin groupé</label>
                  <input
                    type="text"
                    className={inputClass}
                    placeholder="Ex: Bridge 3-éléments céramo-métallique"
                    value={groupTreatmentName}
                    onChange={(e) => setGroupTreatmentName(e.target.value)}
                  />
                </div>
                <div>
                  <label className={labelClass}>Honoraires globaux (MAD)</label>
                  <input
                    type="number"
                    className={cn(inputClass, "font-mono text-right font-black text-2xl")}
                    value={groupTreatmentPrice}
                    onChange={(e) => setGroupTreatmentPrice(e.target.value === '' ? '' : Number(e.target.value))}
                    style={{ color: 'var(--primary)' }}
                  />
                </div>

                <button
                  onClick={applyGroupTreatment}
                  disabled={!groupTreatmentName.trim() || groupSelectedTeeth.length === 0}
                  className="w-full py-5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white rounded-2xl font-black uppercase tracking-widest flex items-center justify-center gap-3 transition-all shadow-xl shadow-emerald-500/20 active:scale-95"
                >
                  <Plus size={24} />
                  Valider {groupSelectedTeeth.length} dent{groupSelectedTeeth.length > 1 ? 's' : ''}
                </button>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* FEES TABLE */}
      <div className="space-y-4">
        <div className="grid grid-cols-12 gap-4 px-6">
          <div className="col-span-6"><label className={labelClass}>Acte / Traitement</label></div>
          <div className="col-span-2 text-center"><label className={labelClass}>Dent(s)</label></div>
          <div className="col-span-3 text-right"><label className={labelClass}>Honoraires (MAD)</label></div>
          <div className="col-span-1"></div>
        </div>

        <div className="space-y-3">
          <AnimatePresence>
            {items.map((item, idx) => {
              const descError = validationErrors.find(e => e.field === `item_${idx}`);
              const priceError = validationErrors.find(e => e.field === `item_price_${idx}`);
              const hasError = !!(descError || priceError);

              return (
                <motion.div 
                  layout
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  key={item.id} 
                  className={cn(
                    "grid grid-cols-12 gap-4 items-center bg-white/40 p-4 rounded-[2.2rem] border transition-all group relative overflow-hidden",
                    hasError ? "border-red-200 bg-red-50/20" : "border-white/60 hover:bg-white hover:border-primary/20 hover:shadow-[0_20px_60px_rgba(0,51,128,0.06)]"
                  )}
                >
                  <div className={cn("absolute left-0 top-0 bottom-0 w-1.5 transition-all duration-500", hasError ? "bg-red-500" : "bg-primary/0 group-hover:bg-primary")} />
                  <div className="col-span-6 relative">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-primary/40 group-focus-within:text-primary transition-colors">
                      <Search size={16} />
                    </div>
                    <div className="relative">
                      <input
                        type="text"
                        className={cn(inputClass, "pl-12 border-transparent bg-transparent shadow-none font-black text-primary placeholder:text-slate-300", descError && "placeholder:text-red-300")}
                        style={{ color: descError ? '#ef4444' : 'var(--primary)' }}
                        placeholder={descError ? descError.message : "Désignation de l'acte médical..."}
                        value={item.description}
                        onChange={(e) => handleActSearch(e.target.value, item.id)}
                      />
                      {descError && (
                        <div className="absolute -bottom-1 left-12 text-[8px] font-black text-red-500 uppercase tracking-widest flex items-center gap-1">
                          <AlertCircle size={8} /> Description Requise
                        </div>
                      )}
                    </div>
                    
                    {/* Act Suggestions */}
                    {activeActSearchId === item.id && actSuggestions.length > 0 && (
                      <div className="absolute top-full left-0 right-0 z-50 bg-white/95 backdrop-blur-md border border-slate-200 rounded-[2rem] shadow-2xl mt-4 overflow-hidden animate-in fade-in zoom-in-95 duration-300">
                        <div className="p-4 bg-slate-50/50 border-b border-slate-100 flex items-center justify-between">
                           <div className="flex items-center gap-2">
                             <Zap size={14} className="text-amber-500" />
                             <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">IA Suggestions</span>
                           </div>
                           <div className="text-[9px] font-bold text-slate-300 italic">SANINOVA Intelligent Engine</div>
                        </div>
                        <div className="max-h-[300px] overflow-y-auto custom-scrollbar">
                          {actSuggestions.length > 0 ? (
                            actSuggestions.map((act) => (
                              <button
                                key={act.id}
                                onClick={() => applyActSuggestion(item.id, act)}
                                className="w-full text-left px-6 py-5 hover:bg-primary/5 border-b border-slate-50 last:border-0 transition-all flex items-center justify-between group/item"
                              >
                                <div className="flex flex-col gap-1">
                                  <div className="font-black text-slate-800 text-sm group-hover/item:text-primary transition-colors tracking-tight">{act.name}</div>
                                  <div className="flex items-center gap-2">
                                    <span className={cn("px-2 py-0.5 rounded-md text-[8px] font-black uppercase tracking-tighter border", getCategoryColor(act.category))}>
                                      {act.category || 'Général'}
                                    </span>
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-sm font-black text-primary" style={{ color: 'var(--primary)' }}>{act.base_price} <span className="text-[10px] opacity-60">MAD</span></div>
                                  <div className="text-[9px] text-slate-400 font-bold uppercase">Prix Conseillé</div>
                                </div>
                              </button>
                            ))
                          ) : item.description.length >= 2 ? (
                            <button
                              onClick={() => {
                                saveActAsHabit(item.description, item.price);
                                setActiveActSearchId(null);
                              }}
                              className="w-full text-left px-6 py-5 hover:bg-emerald-50 border-b border-slate-50 last:border-0 transition-all flex items-center justify-between group/item"
                            >
                              <div className="flex flex-col gap-1">
                                <div className="font-black text-emerald-700 text-sm tracking-tight italic">"{item.description}"</div>
                                <div className="text-[9px] font-black text-emerald-600/60 uppercase tracking-widest">Nouvel Acte Personnalisé</div>
                              </div>
                              <div className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-emerald-600/20">
                                <Plus size={14} /> Enregistrer comme habitude
                              </div>
                            </button>
                          ) : null}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="col-span-2">
                    <div className="flex items-center justify-center">
                      <input
                        type="text"
                        className={cn(
                          "w-full bg-slate-100/50 px-2 py-2.5 rounded-xl font-black text-slate-700 border border-slate-200/50 text-center outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all",
                          !item.dent && "placeholder:text-slate-300"
                        )}
                        placeholder="-"
                        value={item.dent}
                        onChange={(e) => updateItem(item.id, 'dent', e.target.value)}
                      />
                    </div>
                  </div>
  
                  <div className="col-span-3">
                    <div className="relative">
                      <input
                        type="number"
                        className={cn(inputClass, "text-right font-black text-lg pr-12 border-transparent bg-slate-50/50 shadow-none", priceError && "text-red-500")}
                        style={{ color: priceError ? '#ef4444' : 'var(--primary)' }}
                        value={item.price}
                        onChange={(e) => updateItem(item.id, 'price', e.target.value)}
                      />
                      <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-black text-primary/40 uppercase">MAD</span>
                      {priceError && (
                        <div className="absolute -bottom-1 right-12 text-[8px] font-black text-red-500 uppercase tracking-widest flex items-center gap-1">
                          <AlertCircle size={8} /> Prix Invalide
                        </div>
                      )}
                    </div>
                  </div>
  
                  <div className="col-span-1 flex justify-center">
                    <button
                      onClick={() => removeItem(item.id)}
                      className="p-3 text-slate-300 hover:text-white hover:bg-rose-500 rounded-2xl transition-all opacity-0 group-hover:opacity-100 shadow-lg shadow-rose-500/20 active:scale-90"
                    >
                      <Trash2 size={20} />
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        <button onClick={addEmptyRow} className={addButtonClass}>
          <Plus size={20} />
          Ajouter une ligne personnalisée
        </button>
      </div>

      {/* PAYMENT TRACKER (INSTALLMENTS) - Elite Section */}
      <div className="bg-white/40 backdrop-blur-xl rounded-[2.5rem] p-8 border border-white/60 shadow-[0_20px_50px_rgba(0,51,128,0.04)] space-y-6">
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-600 border border-emerald-100 shadow-sm">
              <Calculator size={20} />
            </div>
            <div>
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 block leading-none mb-1">Échéancier</span>
              <span className="text-xs font-black uppercase tracking-widest text-emerald-600">Suivi des Versements (Ortho)</span>
            </div>
          </div>
          <button 
            onClick={() => setInstallments([...installments, { id: Date.now(), date: new Date().toISOString().split('T')[0], amount: 0, label: installments.length === 0 ? 'Avance' : `Versement ${installments.length + 1}` }])}
            className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-emerald-700 transition-all flex items-center gap-2 shadow-lg shadow-emerald-600/20"
          >
            <Plus size={14} /> Ajouter un versement
          </button>
        </div>

        {installments.length > 0 && (
          <div className="space-y-3">
            <div className="grid grid-cols-12 gap-4 px-6">
              <div className="col-span-4"><label className={labelClass}>Désignation</label></div>
              <div className="col-span-4"><label className={labelClass}>Date de règlement</label></div>
              <div className="col-span-3 text-right"><label className={labelClass}>Montant (MAD)</label></div>
              <div className="col-span-1"></div>
            </div>
            {installments.map((inst) => {
              const isPast = new Date(inst.date) < new Date(new Date().setHours(0,0,0,0));
              const isToday = new Date(inst.date).toDateString() === new Date().toDateString();
              
              return (
                <motion.div 
                  key={inst.id}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    "grid grid-cols-12 gap-4 items-center p-4 rounded-2xl border shadow-sm group transition-all",
                    isPast ? "bg-rose-50/30 border-rose-100" : isToday ? "bg-emerald-50/30 border-emerald-100" : "bg-white border-slate-100"
                  )}
                >
                  <div className="col-span-4 flex items-center gap-3">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      isPast ? "bg-rose-400 animate-pulse" : isToday ? "bg-emerald-400" : "bg-slate-300"
                    )} />
                    <input
                      type="text"
                      className="w-full bg-transparent border-none p-0 text-xs font-bold text-slate-700 focus:ring-0"
                      value={inst.label}
                      onChange={(e) => setInstallments(installments.map(i => i.id === inst.id ? { ...i, label: e.target.value } : i))}
                    />
                  </div>
                  <div className="col-span-4">
                    <div className="flex items-center gap-2">
                       <input
                        type="date"
                        className={cn(
                          "w-full bg-transparent border-none p-0 text-xs font-black focus:ring-0",
                          isPast ? "text-rose-600" : "text-slate-400"
                        )}
                        value={inst.date}
                        onChange={(e) => setInstallments(installments.map(i => i.id === inst.id ? { ...i, date: e.target.value } : i))}
                      />
                      {isPast && <span className="text-[8px] font-black text-rose-500 uppercase px-2 py-0.5 bg-rose-100 rounded-md">Retard</span>}
                    </div>
                  </div>
                  <div className="col-span-3">
                    <input
                      type="number"
                      className="w-full bg-transparent border-none p-0 text-right text-sm font-black text-emerald-600 focus:ring-0"
                      value={inst.amount}
                      onChange={(e) => setInstallments(installments.map(i => i.id === inst.id ? { ...i, amount: Number(e.target.value) } : i))}
                    />
                  </div>
                  <div className="col-span-1 flex justify-center">
                    <button 
                      onClick={() => setInstallments(installments.filter(i => i.id !== inst.id))}
                      className="p-2 text-slate-300 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </motion.div>
              );
            })}

            {/* REST TO PAY SUMMARY */}
            <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
               <button
                 onClick={async () => {
                   try {
                     const total = calculateTotal();
                     await api.post('/accounting/plans', {
                       patient_id: parseInt(patientId),
                       title: `Plan de paiement - ${new Date().toLocaleDateString('fr-FR')}`,
                       total_amount: total,
                       installments: installments.map(i => ({
                         label: i.label,
                         amount: i.amount,
                         due_date: i.date,
                         status: 'EN_ATTENTE'
                       }))
                     });
                     alert('✅ Plan de paiement persistant enregistré avec succès !');
                   } catch (err) {
                     console.error(err);
                     alert('❌ Erreur lors de la sauvegarde du plan.');
                   }
                 }}
                 className="px-6 py-3 bg-white border border-emerald-200 text-emerald-600 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-emerald-50 transition-all flex items-center gap-2 shadow-sm active:scale-95"
               >
                 <Calculator size={14} />
                 Enregistrer comme Plan de Suivi
               </button>

               <div className="bg-emerald-50 px-8 py-5 rounded-[2rem] border border-emerald-100 flex items-center gap-8 shadow-inner">
                  <div className="text-right">
                    <span className="text-[9px] font-black text-emerald-600/60 uppercase tracking-widest block mb-1">Total Versé</span>
                    <span className="text-lg font-black text-emerald-700">{installments.reduce((sum, i) => sum + i.amount, 0).toLocaleString('fr-FR')} MAD</span>
                  </div>
                  <div className="w-px h-10 bg-emerald-200/50" />
                  <div className="text-right">
                    <span className="text-[9px] font-black text-amber-600 uppercase tracking-widest block mb-1">Reste à payer</span>
                    <span className="text-lg font-black text-amber-600">{(calculateTotal() - installments.reduce((sum, i) => sum + i.amount, 0)).toLocaleString('fr-FR')} MAD</span>
                  </div>
               </div>
            </div>
          </div>
        )}
      </div>

      {/* FOOTER TOTAL & PAIEMENT ELITE (LIGHT EDITION) */}
      <div className="mt-12 bg-white/60 backdrop-blur-2xl rounded-[3.5rem] p-12 text-slate-900 shadow-[0_40px_120px_rgba(0,51,128,0.08)] border border-white relative overflow-hidden animate-in zoom-in-95 duration-1000">
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 blur-[120px] -mr-48 -mt-48 rounded-full pointer-events-none" />
        
        <div className="flex flex-col lg:flex-row justify-between items-center gap-10 relative z-10">
          <div className="flex flex-col gap-6 w-full lg:w-auto">
            <div className="flex items-center gap-3">
              <div className="w-1.5 h-6 bg-primary rounded-full shadow-[0_0_15px_rgba(0,102,255,0.3)]" />
              <label className="text-[11px] font-black uppercase tracking-[0.3em] text-slate-400">Règlement Patient</label>
            </div>
            
            <div className="flex flex-wrap bg-slate-100/50 backdrop-blur-md p-2 rounded-[2rem] gap-2 border border-slate-200/50">
              {['Espèces', 'Chèque', 'TPE', 'Virement'].map((m) => (
                <button
                  key={m}
                  onClick={() => setPaymentMode(m)}
                  className={cn(
                    "px-8 py-3.5 rounded-[1.2rem] text-[10px] font-black uppercase tracking-widest transition-all",
                    paymentMode === m 
                      ? "bg-primary text-white shadow-xl shadow-primary/20 scale-105" 
                      : "text-slate-500 hover:text-slate-900 hover:bg-white"
                  )}
                  style={paymentMode === m ? { backgroundColor: 'var(--primary)' } : {}}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col items-center lg:items-end w-full lg:w-auto">
            <div className="flex items-center gap-3 mb-2 opacity-60">
               <Calculator size={18} className="text-primary" />
               <span className="text-[11px] font-black text-slate-400 uppercase tracking-[0.4em]">Honoraires Totaux</span>
            </div>
            <div className="flex items-baseline gap-4">
              <motion.span 
                key={calculateTotal()}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-7xl font-black tracking-tighter text-slate-900"
              >
                {calculateTotal().toLocaleString('fr-FR')}
              </motion.span>
              <span className="text-2xl font-black text-primary uppercase tracking-widest" style={{ color: 'var(--primary)' }}>MAD</span>
            </div>
            <div className="mt-4 px-5 py-2 bg-slate-900 rounded-full flex items-center gap-2 shadow-lg shadow-slate-900/10">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[9px] font-black text-white uppercase tracking-widest">Poste de Saisie Certifié Elite</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
