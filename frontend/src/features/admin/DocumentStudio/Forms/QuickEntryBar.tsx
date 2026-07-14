import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, Zap } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import type { DrugItem } from './prescriptionTypes';

interface QuickEntryBarProps {
  quickVal: string;
  setQuickVal: (v: string) => void;
  quickSuggestions: string[];
  quickHighlightedIdx: number;
  setQuickHighlightedIdx: React.Dispatch<React.SetStateAction<number>>;
  onSearchChange: (val: string) => void;
  onAddDrug: (drug: DrugItem) => void;
  onSetStep: (step: 'IDLE' | 'RESEARCH' | 'ASSESSMENT' | 'PLANNING') => void;
  hydrateMedicationDetails: (drug: DrugItem) => Promise<DrugItem>;
  parseQuickEntry: (text: string) => DrugItem;
}

export const QuickEntryBar: React.FC<QuickEntryBarProps> = ({
  quickVal, setQuickVal, quickSuggestions, quickHighlightedIdx,
  setQuickHighlightedIdx, onSearchChange, onAddDrug, onSetStep,
  hydrateMedicationDetails, parseQuickEntry,
}) => {
  const submitDrug = async (text: string) => {
    if (!text.trim()) return;
    const newDrug = await hydrateMedicationDetails(parseQuickEntry(text));
    onAddDrug(newDrug);
    setQuickVal('');
    setQuickHighlightedIdx(-1);
    onSetStep('PLANNING');
  };

  return (
    <div className="relative group">
      <div className="absolute inset-y-0 left-6 flex items-center text-primary/40 group-focus-within:text-primary transition-colors">
        <Zap size={18} />
      </div>
      <input
        type="text"
        value={quickVal}
        onChange={e => {
          const v = e.target.value;
          setQuickVal(v);
          onSearchChange(v);
        }}
        className="w-full bg-white/60 border border-white/80 backdrop-blur-xl rounded-[2rem] pl-16 pr-8 py-5 text-sm font-bold text-slate-800 focus:bg-white focus:border-primary/30 focus:shadow-2xl focus:shadow-primary/5 transition-all outline-none placeholder:text-slate-300"
        placeholder="Saisie Rapide : Taper un médicament, un dosage ou une posologie... (Ex: Augmentin 1g sachet 2x/j)"
        onKeyDown={async e => {
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
              parts[0] = sugg;
              finalVal = parts.join(' ');
            }
            await submitDrug(finalVal);
            setQuickHighlightedIdx(-1);
          } else if (e.key === 'Escape') {
            setQuickHighlightedIdx(-1);
          }
        }}
        onBlur={() => setTimeout(() => setQuickHighlightedIdx(-1), 200)}
      />

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
                type="button"
                onMouseDown={async e => {
                  // onMouseDown (pas onClick) : le mousedown précède le blur de
                  // l'input dans l'ordre des événements navigateur. preventDefault
                  // empêche l'input de perdre le focus avant que la sélection ne
                  // s'applique — même correctif que DrugRow.tsx pour ce bug.
                  e.preventDefault();
                  const parts = quickVal.split(' ');
                  parts[0] = s;
                  await submitDrug(parts.join(' '));
                }}
                className={cn(
                  'w-full px-8 py-3 text-left text-sm font-bold transition-all flex items-center justify-between group',
                  i === quickHighlightedIdx ? 'bg-primary text-white' : 'text-slate-600 hover:bg-primary/5 hover:text-primary',
                )}
              >
                <span>{s}</span>
                <ChevronRight
                  size={14}
                  className={cn('transition-transform', i === quickHighlightedIdx ? 'translate-x-1' : 'opacity-0 group-hover:opacity-100')}
                />
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="absolute right-6 top-1/2 -translate-y-1/2 flex items-center gap-2">
        <span className="text-[8px] font-black text-slate-300 uppercase tracking-widest border border-slate-200 px-2 py-1 rounded-lg">
          ↵ ENTER POUR AJOUTER
        </span>
      </div>
    </div>
  );
};
