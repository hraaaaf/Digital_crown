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
    <section
      data-ordonnance-quick-entry
      aria-label="Saisie rapide de l'ordonnance"
      className="relative min-w-0 space-y-3 rounded-[1.75rem] border border-slate-200/70 bg-white/60 p-3 shadow-lg shadow-slate-900/[0.03] backdrop-blur-2xl dark:border-white/10 dark:bg-slate-900/50 sm:p-4"
    >
      <div className="flex items-center justify-between gap-3 px-1">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-primary/10 bg-primary/10 text-primary">
            <Zap size={15} />
          </div>
          <div className="min-w-0">
            <div className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-800 dark:text-slate-100">Saisie rapide</div>
            <div className="hidden text-[9px] font-semibold text-slate-400 dark:text-slate-500 sm:block">Médicament, dosage, forme et posologie en une ligne.</div>
          </div>
        </div>
        <span className="hidden shrink-0 rounded-lg border border-slate-200/70 bg-white/70 px-2.5 py-1 text-[9px] font-black uppercase tracking-wider text-slate-400 dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-500 sm:inline-flex">
          {submitting ? 'Ajout…' : '↵ Ajouter'}
        </span>
      </div>

      <div className="relative min-w-0 group">
        <div className="absolute inset-y-0 left-4 flex items-center text-primary/45 transition-colors group-focus-within:text-primary sm:left-5">
          <Zap size={18} />
        </div>
        <input
          type="text"
          value={quickVal}
          disabled={submitting}
          aria-busy={submitting}
          aria-label="Médicament, dosage, forme, posologie"
          onChange={e => {
            const v = e.target.value;
            setQuickVal(v);
            onSearchChange(v);
          }}
          className="min-h-14 w-full min-w-0 rounded-2xl border border-slate-200/80 bg-white/85 py-3.5 pl-12 pr-4 text-sm font-bold text-slate-800 outline-none shadow-sm backdrop-blur-xl transition-all placeholder:text-slate-300 focus:border-primary/30 focus:bg-white focus:ring-4 focus:ring-primary/10 disabled:opacity-60 dark:border-white/10 dark:bg-slate-950/60 dark:text-slate-100 dark:placeholder:text-slate-600 dark:focus:bg-slate-950 sm:pl-14 sm:pr-4 sm:text-base"
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

        <AnimatePresence>
          {quickSuggestions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="absolute left-1 right-1 top-full z-[999] mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-white py-2 shadow-2xl dark:border-white/10 dark:bg-slate-950 sm:left-3 sm:right-3"
            >
              <div className="mb-1 border-b border-slate-100 px-4 py-2 dark:border-white/10 sm:px-5">
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Suggestions de médicaments</span>
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
                    'flex min-h-11 w-full items-center justify-between px-5 py-2.5 text-left text-sm font-bold transition-all group disabled:opacity-50',
                    i === quickHighlightedIdx
                      ? 'bg-primary text-white'
                      : 'text-slate-600 hover:bg-primary/5 hover:text-primary dark:text-slate-300 dark:hover:bg-white/5',
                  )}
                >
                  <span>{s}</span>
                  <ChevronRight size={14} className={cn('transition-transform', i === quickHighlightedIdx ? 'translate-x-1' : 'opacity-0 group-hover:opacity-100')} />
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {showQuickPicks && (
        <div className="flex flex-wrap items-center gap-2 px-1" aria-label="Accès rapides aux médicaments habituels">
          {visibleRecent.map(name => (
            <button
              key={`recent-${name}`}
              type="button"
              disabled={submitting}
              onClick={() => void submitDrug(name)}
              className="inline-flex min-h-11 items-center gap-1.5 rounded-xl border border-slate-200/80 bg-white/75 px-3 py-2 text-[10px] font-black uppercase tracking-wide text-slate-600 shadow-sm transition-colors hover:border-primary/30 hover:bg-white hover:text-primary disabled:opacity-50 dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-300 dark:hover:bg-slate-900"
              title="Médicament récent"
            >
              <Clock3 size={11} />{name}
            </button>
          ))}
          {visibleFrequent.map(name => (
            <button
              key={`frequent-${name}`}
              type="button"
              disabled={submitting}
              onClick={() => void submitDrug(name)}
              className="inline-flex min-h-11 items-center gap-1.5 rounded-xl border border-slate-200/80 bg-white/75 px-3 py-2 text-[10px] font-black uppercase tracking-wide text-slate-600 shadow-sm transition-colors hover:border-primary/30 hover:bg-white hover:text-primary disabled:opacity-50 dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-300 dark:hover:bg-slate-900"
              title="Médicament fréquent"
            >
              <TrendingUp size={11} />{name}
            </button>
          ))}
        </div>
      )}
    </section>
  );
};
