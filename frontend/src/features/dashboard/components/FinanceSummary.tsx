import { AlertCircle, Banknote, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '../../../utils/cn';
import { dashboardItemVariants } from '../animations';
import type { FinanceToday } from '../types';

export const FinanceSummary = ({
  visible,
  finance,
}: {
  visible: boolean;
  finance: FinanceToday | null;
}) => {
  if (!visible || !finance) return null;

  return (
    <motion.section variants={dashboardItemVariants}>
      <h2 className="text-[11px] font-black uppercase tracking-[0.15em] text-text-muted mb-4">
        Finances du Cabinet — Aujourd'hui
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 bg-emerald-500/10 rounded-elite-sm flex items-center justify-center border border-emerald-500/20">
              <Banknote size={18} className="text-emerald-400" />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">CA du Jour</span>
          </div>
          <div className="text-3xl font-black font-outfit text-emerald-400">
            {finance.today_revenue.toLocaleString('fr-MA')}
          </div>
          <div className="text-[10px] font-bold text-text-muted mt-1">MAD encaissés aujourd'hui</div>
        </div>

        <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 bg-blue-500/10 rounded-elite-sm flex items-center justify-center border border-blue-500/20">
              <TrendingUp size={18} className="text-blue-400" />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Mois en Cours</span>
          </div>
          <div className="text-3xl font-black font-outfit text-blue-400">
            {finance.month_revenue.toLocaleString('fr-MA')}
          </div>
          <div className="text-[10px] font-bold text-text-muted mt-1">MAD encaissés ce mois</div>
        </div>

        <div className={cn(
          'rounded-elite-lg border shadow-elite p-6',
          finance.total_debt > 0 ? 'bg-red-50 border-red-100' : 'bg-card-bg border-border-main',
        )}>
          <div className="flex items-center gap-3 mb-4">
            <div className={cn(
              'w-9 h-9 rounded-elite-sm flex items-center justify-center',
              finance.total_debt > 0
                ? 'bg-red-500/10 border border-red-500/20'
                : 'bg-emerald-500/10 border border-emerald-500/20',
            )}>
              <AlertCircle size={18} className={finance.total_debt > 0 ? 'text-red-400' : 'text-emerald-400'} />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Impayés Globaux</span>
          </div>
          <div className={cn(
            'text-3xl font-black font-outfit',
            finance.total_debt > 0 ? 'text-red-500' : 'text-emerald-400',
          )}>
            {finance.total_debt.toLocaleString('fr-MA')}
          </div>
          <div className="text-[10px] font-bold text-text-muted mt-1">MAD non encaissés (total cabinet)</div>
        </div>
      </div>
    </motion.section>
  );
};
