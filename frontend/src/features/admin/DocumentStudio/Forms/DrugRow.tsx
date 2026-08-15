import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, ChevronDown, ChevronRight, ChevronUp, Microscope, Pill, Trash2 } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import type { DrugItem } from './prescriptionTypes';
import { getFormeIcon } from './prescriptionTypes';
import type { ValidationError } from '../useDocumentGenerator';

export interface DrugRowProps {
  drug: DrugItem;
  idx: number;
  drugsCount: number;
  assessment: any;
  validationErrors: ValidationError[];
  forcedDrugs: number[];
  activeSearchId: { id: number; field: string } | null;
  suggestions: { medications: string[]; dosages: string[]; posologies: string[] };
  highlightedIdx: number;
  medChecks: Record<number, { known: boolean; exists?: boolean; available_mg?: number[]; dci?: string }>;
  onUpdateDrug: (id: number, field: keyof DrugItem, val: any) => void;
  onRemoveDrug: (id: number) => void;
  onMove: (id: number, direction: 'up' | 'down') => void;
  onSearch: (id: number, field: string, val: string) => void;
  onKeyDown: (e: React.KeyboardEvent, id: number, field: string) => void;
  onApplySuggestion: (id: number, field: string, val: string) => void;
  onFormeOpen: (e: React.MouseEvent<HTMLButtonElement>, drugId: number) => void;
  onForceAllergy: (id: number) => void;
  onToggleType: (id: number, type: 'MEDICAMENT' | 'EXAMEN') => void;
}

export const DrugRow: React.FC<DrugRowProps> = ({
  drug, idx, drugsCount, validationErrors,
  activeSearchId, suggestions, highlightedIdx, medChecks,
  onUpdateDrug, onRemoveDrug, onMove, onSearch, onKeyDown,
  onApplySuggestion, onFormeOpen, onToggleType,
}) => {
  const fieldError = validationErrors.find(e => e.field === `drug_${idx}`);
  const isRadio = drug.type === 'EXAMEN';
  const hasIdentity = isRadio || Boolean(drug.name.trim());
  const medCheck = medChecks[drug.id];
  const fmtMg = (mg: number) => (mg < 1000 ? `${mg}mg` : `${mg / 1000}g`);
  const nationalMsg = medCheck && medCheck.known && medCheck.exists === false && medCheck.available_mg?.length
    ? `Dosage non répertorié dans le référentiel local${medCheck.dci ? ` (${medCheck.dci})` : ''} — présentations connues : ${medCheck.available_mg.map(fmtMg).join(', ')}.`
    : null;
  const isNameSuggestOpen = activeSearchId?.id === drug.id && activeSearchId?.field === 'name' && suggestions.medications.length > 0;

  return (
    <motion.div
      key={drug.id}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'bg-white/60 p-3 sm:p-4 rounded-[1.8rem] border transition-all group relative backdrop-blur-xl min-w-0',
        fieldError ? 'border-red-200 bg-red-50/10' : 'border-white/80 hover:bg-white hover:shadow-xl hover:shadow-slate-200/20',
        isRadio && 'border-amber-100 bg-amber-50/5',
        isNameSuggestOpen && 'z-50',
      )}
    >
      <div className="grid grid-cols-[auto_minmax(0,1fr)_auto] sm:grid-cols-12 gap-2 sm:gap-3 items-start sm:items-center min-w-0">
        <div className="hidden sm:flex sm:col-span-2 lg:col-span-1 flex-col items-center justify-center self-stretch border-r border-slate-100/50 pr-2">
          <div className="flex flex-col gap-0.5 opacity-50 group-hover:opacity-100 transition-all duration-300">
            <button type="button" onClick={() => onMove(drug.id, 'up')} disabled={idx === 0} className="p-1.5 text-slate-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-all disabled:opacity-0 active:scale-90" title="Monter" aria-label="Monter le médicament"><ChevronUp size={16} strokeWidth={3} /></button>
            <button type="button" onClick={() => onMove(drug.id, 'down')} disabled={idx === drugsCount - 1} className="p-1.5 text-slate-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-all disabled:opacity-0 active:scale-90" title="Descendre" aria-label="Descendre le médicament"><ChevronDown size={16} strokeWidth={3} /></button>
          </div>
        </div>

        <div className="sm:col-span-2 lg:col-span-1 flex flex-col items-center gap-1 p-1 bg-slate-50/50 rounded-2xl border border-slate-100/50 self-stretch justify-center shrink-0">
          <button type="button" onClick={() => onToggleType(drug.id, 'MEDICAMENT')} className={cn('p-2 rounded-xl transition-all', !isRadio ? 'bg-white text-primary shadow-md shadow-primary/5 ring-1 ring-primary/5' : 'text-slate-300 hover:text-slate-400')} title="Médicament" aria-label="Type médicament"><Pill size={15} /></button>
          <button type="button" onClick={() => onToggleType(drug.id, 'EXAMEN')} className={cn('p-2 rounded-xl transition-all', isRadio ? 'bg-white text-amber-600 shadow-md shadow-amber-500/5 ring-1 ring-amber-500/5' : 'text-slate-300 hover:text-slate-400')} title="Radio / Examen" aria-label="Type radio ou examen"><Microscope size={15} /></button>
        </div>

        <div className="relative min-w-0 sm:col-span-7 lg:col-span-9">
          <div className="grid grid-cols-1 sm:grid-cols-10 gap-3 sm:gap-4 items-center min-w-0">
            <div className={cn('space-y-2 min-w-0', !hasIdentity || isRadio ? 'sm:col-span-10' : 'sm:col-span-4')}>
              <input
                type="text"
                className="w-full min-w-0 bg-transparent border-none px-0 py-2.5 focus:ring-0 font-black text-slate-800 text-sm sm:text-base uppercase placeholder:text-slate-400 tracking-tight"
                placeholder={isRadio ? "DÉTAILS DE L'EXAMEN RADIOLOGIQUE..." : 'NOM DU MÉDICAMENT...'}
                value={drug.name}
                onChange={e => onSearch(drug.id, 'name', e.target.value.toUpperCase())}
                onFocus={() => { if (drug.name.length >= 1) onSearch(drug.id, 'name', drug.name); }}
                onKeyDown={e => onKeyDown(e, drug.id, 'name')}
              />

              {!isRadio && hasIdentity && (
                <div className="flex flex-wrap items-center gap-2 animate-in fade-in slide-in-from-left-2">
                  <button type="button" onClick={e => onFormeOpen(e, drug.id)} className="bg-white/80 px-3 py-2 rounded-xl text-[10px] font-black text-primary uppercase tracking-wide border border-slate-100 hover:border-primary/20 hover:shadow-sm transition-all flex items-center gap-1.5" style={{ color: 'var(--primary)' }}>
                    {getFormeIcon(drug.forme)}{drug.forme.startsWith('AUTRE') ? 'AUTRE' : (drug.forme || 'FORME')}
                  </button>
                  {drug.forme.startsWith('AUTRE') && (
                    <input type="text" className="w-28 max-w-full bg-white/50 border border-slate-200 px-3 py-2 rounded-xl focus:ring-0 text-[10px] font-black text-slate-700 uppercase tracking-wide placeholder:text-slate-400 focus:border-primary/40 transition-colors" placeholder="PRÉCISER..." value={drug.forme.includes(':') ? drug.forme.split(':')[1].trim() : ''} onChange={e => onUpdateDrug(drug.id, 'forme', `AUTRE: ${e.target.value}`)} />
                  )}
                  <div className="flex items-center gap-1.5 bg-white/80 px-3 py-2 rounded-xl border border-slate-100 shadow-sm min-w-0">
                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-wide">Dose</span>
                    <input type="text" className="w-20 max-w-[35vw] bg-transparent border-none p-0 focus:ring-0 text-[11px] font-black text-slate-600 uppercase tracking-wide placeholder:text-slate-400" placeholder="500MG" value={drug.dosage} onFocus={() => onSearch(drug.id, 'dosage', drug.dosage)} onChange={e => onSearch(drug.id, 'dosage', e.target.value)} />
                  </div>
                  <button type="button" onClick={() => onUpdateDrug(drug.id, 'non_substituable', !drug.non_substituable)} className={cn('px-3 py-2 rounded-xl border text-[10px] font-black uppercase tracking-wide transition-all select-none', drug.non_substituable ? 'bg-violet-600 text-white border-violet-600 shadow-sm shadow-violet-500/20' : 'bg-white/80 text-slate-400 border-slate-100 hover:border-slate-300 hover:text-slate-600')} title="Non substituable">NS</button>
                </div>
              )}
            </div>

            {!isRadio && hasIdentity && (
              <div className="sm:col-span-6 relative h-full animate-in fade-in slide-in-from-right-2 min-w-0">
                <div className="bg-slate-50/50 px-3 sm:px-4 py-3.5 rounded-2xl border border-slate-100 group-hover:bg-white transition-all focus-within:ring-2 focus-within:ring-primary/5 focus-within:border-primary/20 focus-within:shadow-sm">
                  <textarea rows={2} className="w-full min-w-0 bg-transparent border-none p-0 text-xs font-bold text-slate-600 focus:ring-0 resize-none placeholder:text-slate-300 leading-relaxed min-h-[2.75rem]" placeholder="Ex. 1 gélule × 3/jour pendant 7 jours" value={drug.posologie} onFocus={() => onSearch(drug.id, 'posologie', drug.posologie)} onChange={e => { onSearch(drug.id, 'posologie', e.target.value); e.target.style.height = 'auto'; e.target.style.height = `${e.target.scrollHeight}px`; }} />
                </div>
              </div>
            )}
          </div>

          {!hasIdentity && !isRadio && <p className="mt-1 text-[10px] font-semibold text-slate-400 break-words">Les détails de dose, forme et posologie apparaissent après identification du médicament.</p>}

          {nationalMsg && (
            <div className="mt-2 flex flex-col gap-1 rounded-xl px-3 py-2 border text-[11px] font-bold bg-amber-50 border-amber-200 text-amber-700">
              <div className="flex items-start gap-1.5"><AlertCircle size={12} className="shrink-0 mt-0.5" /><span>{nationalMsg}</span></div>
            </div>
          )}

          <AnimatePresence>
            {isNameSuggestOpen && (
              <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }} className="absolute left-0 top-full mt-2 w-full min-w-0 sm:min-w-[240px] bg-white border border-slate-100 rounded-2xl shadow-2xl z-[100] overflow-hidden py-2 max-h-[300px] overflow-y-auto custom-scrollbar">
                {suggestions.medications.map((m, i) => (
                  <button key={m} type="button" onMouseDown={e => { e.preventDefault(); onApplySuggestion(drug.id, 'name', m); }} className={cn('w-full px-4 sm:px-5 py-3 text-left text-xs font-black text-slate-600 transition-colors flex items-center justify-between', i === highlightedIdx ? 'bg-primary/10 text-primary' : 'hover:bg-primary/5 hover:text-primary')}>
                    <span className="truncate">{m}</span><ChevronRight size={12} className="opacity-40 shrink-0" />
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="sm:col-span-1 flex items-start sm:items-center justify-end">
          <button type="button" onClick={() => onRemoveDrug(drug.id)} className="w-9 h-9 sm:min-w-[44px] sm:min-h-[44px] flex items-center justify-center text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all active:scale-95" title="Supprimer" aria-label="Supprimer le médicament"><Trash2 size={17} /></button>
        </div>
      </div>
    </motion.div>
  );
};
