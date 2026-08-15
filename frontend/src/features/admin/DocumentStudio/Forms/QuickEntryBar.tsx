import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, Clock3, TrendingUp, Zap } from 'lucide-react';
import { api } from '../../../../services/api';
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

interface QuickPicksResponse {
  recent_medications?: string[];
  frequent_medications?: string[];
}

export const QuickEntryBar: React.FC<QuickEntryBarProps> = ({
  quickVal, setQuickVal, quickSuggestions, quickHighlightedIdx,
  setQuickHighlightedIdx, onSearchChange, onAddDrug, onSetStep,
  hydrateMedicationDetails, parseQuickEntry,
}) => {
  const [recentMedications, setRecentMedications] = useState<string[]>([]);
  const [frequentMedications, setFrequentMedications] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const submittingRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    api.get('/prescriptions/habits/suggest', { params: { q: '' } })
      .then(response => {
        if (cancelled) return;
        const data = (response.data || {}) as QuickPicksResponse;
        setRecentMedications(Array.isArray(data.recent_medications) ? data.recent_medications.slice(0, 5) : []);
        setFrequentMedications(Array.isArray(data.frequent_medications) ? data.frequent_medications.slice(0, 5) : []);
      })
      .catch(() => {
        if (!cancelled) {
          setRecentMedications([]);
          setFrequentMedications([]);
        }
      });
    return () => { cancelled = true; };
  }, []);

  const submitDrug = async (text: string) => {
    if (!text.trim() || submittingRef.current) return;
    submittingRef.current = true;
    setSubmitting(true);
    try {
      const newDrug = await hydrateMedicationDetails(parseQuickEntry(text));
      onAddDrug(newDrug);
      setQuickVal('');
      setQuickHighlightedIdx(-1);
      onSetStep('PLANNING');
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  };

  const visibleRecent = recentMedications.slice(0, 4);
  const visibleFrequent = frequentMedications.filter(name => !visibleRecent.includes(name)).slice(0, 4);
  const showQuickPicks = !quickVal.trim() && (visibleRecent.length > 0 || visibleFrequent.length > 0);

  return (
    <div className="relative group space-y-3">
      <div className="relative">
        <div className="absolute inset-y-0 left-6 flex items-center text-primary/40 group-focus-within:text-primary transition-colors">
          <Zap size={18} />
        </div>
        <input
          type="text"
          value={quickVal}
          disabled={submitting}
          aria-busy={submitting}
          onChange={e => {
            const v = e.target.value;
            setQuickVal(v);
            onSearchChange(v);
          }}
          className="w-full bg-white/70 border border-white/90 backdrop-blur-xl rounded-[2rem] pl-16 pr-32 py-5 text-base font-bold text-slate-800 focus:bg-white focus:border-primary/30 focus:shadow-2xl focus:shadow-primary/5 transition-all outline-none placeholder:text-slate-300 disabled:opacity-60"
          placeholder="Médicament, dosage, forme, posologie…"
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

        <div className="absolute right-6 top-1/2 -translate-y-1/2 flex items-center gap-2">
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest border border-slate-200 px-2 py-1 rounded-lg bg-white/70">
            {submitting ? 'AJOUT…' : '↵ AJOUTER'}
          </span>
        </div>

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
                  disabled={submitting}
                  onMouseDown={async e => {
                    e.preventDefault();
                    const parts = quickVal.split(' ');
                    parts[0] = s;
                    await submitDrug(parts.join(' '));
                  }}
                  className={cn(
                    'w-full px-8 py-3 text-left text-sm font-bold transition-all flex items-center justify-between group disabled:opacity-50',
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
      </div>

      {showQuickPicks && (
        <div className="flex flex-wrap items-center gap-2 px-2" aria-label="Accès rapides aux médicaments habituels">
          {visibleRecent.map(name => (
            <button
              key={`recent-${name}`}
              type="button"
              disabled={submitting}
              onClick={() => void submitDrug(name)}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-[10px] font-black uppercase tracking-wide text-slate-600 transition-colors hover:border-primary/30 hover:text-primary disabled:opacity-50"
              title="Médicament récent"
            >
              <Clock3 size={11} />
              {name}
            </button>
          ))}
          {visibleFrequent.map(name => (
            <button
              key={`frequent-${name}`}
              type="button"
              disabled={submitting}
              onClick={() => void submitDrug(name)}
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-[10px] font-black uppercase tracking-wide text-slate-600 transition-colors hover:border-primary/30 hover:text-primary disabled:opacity-50"
              title="Médicament fréquent"
            >
              <TrendingUp size={11} />
              {name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
