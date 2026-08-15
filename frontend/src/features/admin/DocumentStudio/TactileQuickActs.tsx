import React from 'react';
import { Plus, Zap } from 'lucide-react';
import type { QuickActInput } from './QuickActsPolicy';

interface TactileQuickActsProps {
  acts: QuickActInput[];
  onSelect: (act: QuickActInput) => void;
  onAddCustom: () => void;
}

export const TactileQuickActs: React.FC<TactileQuickActsProps> = ({ acts, onSelect, onAddCustom }) => (
  <section
    aria-label="Actes rapides"
    className="mx-auto w-full max-w-5xl rounded-2xl border border-slate-100 bg-white/80 p-3 shadow-sm backdrop-blur-sm"
  >
    <div className="mb-2 flex items-center gap-2 px-1">
      <Zap className="h-4 w-4 text-amber-500" aria-hidden="true" />
      <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Actes rapides</span>
    </div>
    <div className="flex gap-2 overflow-x-auto pb-1 sm:flex-wrap">
      {acts.map((act, index) => (
        <button
          key={`${act.name}-${index}`}
          type="button"
          onClick={() => onSelect(act)}
          className="min-h-11 shrink-0 rounded-xl border border-slate-200 bg-white px-4 py-2 text-left text-[10px] font-black uppercase tracking-wider text-slate-700 transition-colors hover:border-primary/30 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
        >
          <span>{act.name}</span>
          <span className="ml-2 text-primary">+{act.price} MAD</span>
        </button>
      ))}
      <button
        type="button"
        onClick={onAddCustom}
        className="min-h-11 shrink-0 rounded-xl bg-primary px-4 py-2 text-[10px] font-black uppercase tracking-wider text-white shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
      >
        <span className="flex items-center gap-2"><Plus size={14} aria-hidden="true" /> Nouvel acte</span>
      </button>
    </div>
  </section>
);
