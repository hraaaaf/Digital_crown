import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Plus, Zap } from 'lucide-react';

export interface AccountingQuickAct {
  name: string;
  price: number;
  category: string;
}

interface AccountingQuickActionsProps {
  acts: AccountingQuickAct[];
  onSelect: (act: AccountingQuickAct) => void;
  onAddManual: () => void;
}

export const AccountingQuickActions: React.FC<AccountingQuickActionsProps> = ({
  acts,
  onSelect,
  onAddManual,
}) => {
  const [open, setOpen] = useState(false);

  return (
    <section className="rounded-2xl border border-slate-100 bg-white shadow-sm">
      <button
        type="button"
        aria-expanded={open}
        aria-controls="accounting-quick-actions-panel"
        onClick={() => setOpen(value => !value)}
        className="flex w-full items-center gap-3 px-5 py-4 text-left"
      >
        <Zap size={18} className="text-amber-500" />
        <span className="flex-1 text-xs font-black uppercase tracking-widest text-slate-600">
          Actes rapides
        </span>
        {open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
      </button>

      {open && (
        <div id="accounting-quick-actions-panel" className="flex flex-wrap gap-2 border-t border-slate-100 p-4">
          {acts.map(act => (
            <button
              key={`${act.category}:${act.name}`}
              type="button"
              onClick={() => onSelect(act)}
              className="rounded-xl border border-slate-100 bg-white px-4 py-2.5 text-left text-xs font-bold text-slate-700 hover:border-primary/30 hover:bg-slate-50"
            >
              <span>{act.name}</span>
              <span className="ml-2 font-black text-primary">{act.price} MAD</span>
            </button>
          ))}
          <button
            type="button"
            onClick={onAddManual}
            className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-xs font-black text-white"
          >
            <Plus size={14} /> Nouvel acte
          </button>
        </div>
      )}
    </section>
  );
};
