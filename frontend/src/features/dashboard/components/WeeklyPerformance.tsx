import { useState } from 'react';
import { ChevronRight, TrendingUp } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { cn } from '../../../utils/cn';
import { dashboardItemVariants } from '../animations';
import type { DashboardStats } from '../types';

const getPast7DaysLabels = () => {
  const labels: string[] = [];
  const today = new Date();
  for (let i = 6; i >= 0; i -= 1) {
    const day = new Date();
    day.setDate(today.getDate() - i);
    labels.push(day.toLocaleDateString('fr-FR', { weekday: 'short' }));
  }
  return labels;
};

export const WeeklyPerformance = ({
  visible,
  stats,
}: {
  visible: boolean;
  stats: DashboardStats | null;
}) => {
  const [expanded, setExpanded] = useState(false);
  if (!visible) return null;

  const labels = getPast7DaysLabels();

  return (
    <motion.section variants={dashboardItemVariants} className="lg:col-span-2 space-y-5">
      <button
        onClick={() => setExpanded(value => !value)}
        className="w-full text-[10px] font-black text-text-muted uppercase tracking-widest mb-2 px-4 flex items-center justify-between hover:text-primary transition-colors"
      >
        <span className="flex items-center gap-2"><TrendingUp size={16} /> Performance Hebdomadaire</span>
        <ChevronRight size={14} className={cn('transition-transform', expanded && 'rotate-90')} />
      </button>
      <div data-tour="dashboard-stats" className="bg-card-bg/85 backdrop-blur-xl rounded-elite-lg border border-border-main shadow-elite relative overflow-hidden">
        <AnimatePresence initial={false}>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="p-8 h-[410px] flex flex-col justify-between relative">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />

                <div className="relative z-10 flex items-center justify-between border-b border-border-main pb-4">
                  <div>
                    <p className="font-black text-[9px] uppercase tracking-[0.2em] text-text-muted">Intelligence Analytique</p>
                    <h4 className="text-xl font-black text-primary font-outfit mt-1">Activité Clinique</h4>
                  </div>
                  <div className="flex gap-4">
                    <div className="text-right">
                      <span className="text-[8px] font-black text-text-muted uppercase tracking-wider block">Volume Hebdo</span>
                      <span className="text-xs font-black text-main">
                        {stats?.weekly_patients !== undefined ? stats.weekly_patients : 0} Dossier{stats?.weekly_patients !== 1 ? 's' : ''}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[8px] font-black text-text-muted uppercase tracking-wider block">IA / Patient</span>
                      <span className="font-black text-xs text-emerald-500 flex items-center justify-end gap-1">
                        {stats?.total_patients ? (stats.total_analyses / stats.total_patients).toFixed(1) : '0'} analyses
                      </span>
                    </div>
                  </div>
                </div>

                <div className="relative z-10 flex-1 flex items-end justify-between gap-3 pt-8 pb-4 h-[220px]">
                  <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
                    {[1, 2, 3, 4].map(value => (
                      <div key={value} className="w-full border-t border-dashed border-text-muted/40" />
                    ))}
                  </div>

                  {stats?.weekly_activity?.map((value, index) => {
                    const label = labels[index]
                      ? labels[index].charAt(0).toUpperCase() + labels[index].slice(1)
                      : '';
                    const patientCount = stats.weekly_patient_counts?.[index];

                    return (
                      <div key={index} className="flex-1 flex flex-col items-center gap-2 group/bar relative z-10 h-full justify-end">
                        {patientCount !== undefined && (
                          <div className="absolute bottom-[calc(100%-10px)] left-1/2 -translate-x-1/2 opacity-0 group-hover/bar:opacity-100 transition-all duration-300 pointer-events-none bg-slate-900/95 dark:bg-black/90 border border-border-main text-white px-2.5 py-1.5 rounded-xl text-[9px] font-black shadow-xl whitespace-nowrap mb-2 z-[20]">
                            <div className="text-[7px] text-white/70 uppercase tracking-widest">Nouveaux dossiers</div>
                            <div className="text-sm font-black text-accent mt-0.5">{patientCount} Patient{patientCount > 1 ? 's' : ''}</div>
                          </div>
                        )}
                        <div className="w-full relative rounded-t-xl overflow-hidden bg-slate-100 dark:bg-white/5 border border-transparent group-hover/bar:border-primary/20 transition-all h-full flex items-end">
                          <motion.div
                            initial={{ height: 0 }}
                            animate={{ height: `${value}%` }}
                            transition={{ duration: 0.8, ease: 'easeOut', delay: index * 0.05 }}
                            className="w-full rounded-t-xl bg-gradient-to-t from-primary/30 to-primary relative group-hover/bar:from-primary/50 group-hover/bar:to-primary/90 transition-all"
                          >
                            {value > 5 && <div className="absolute top-0 left-0 right-0 h-1 bg-white/40 shadow-[0_0_10px_#fff]" />}
                          </motion.div>
                        </div>
                        <span className="text-[9px] font-black text-text-muted uppercase tracking-wider group-hover/bar:text-primary transition-colors">
                          {label}
                        </span>
                      </div>
                    );
                  })}
                </div>

                <div className="relative z-10 border-t border-border-main pt-4 flex items-center justify-between text-[9px] font-bold text-text-muted uppercase tracking-wider">
                  <span className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" /> Nouveaux dossiers / 7 jours
                  </span>
                  <span>Mise à jour à chaque chargement</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.section>
  );
};
