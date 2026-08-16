import { Clock } from 'lucide-react';
import { motion } from 'framer-motion';
import { dashboardItemVariants } from '../animations';
import type { DashboardStats } from '../types';

export const RecentActivity = ({ visible, stats }: { visible: boolean; stats: DashboardStats | null }) => {
  if (!visible) return null;
  return (
    <motion.section variants={dashboardItemVariants} data-tour="dashboard-agenda" className="space-y-5">
      <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-2 px-4 flex items-center gap-2">
        <Clock size={16} /> Activité Récente
      </h2>
      <div data-tour="dashboard-activity" className="bg-card-bg/80 backdrop-blur-xl border border-border-main rounded-elite-lg p-4 shadow-elite">
        <span className="sr-only">{stats?.recent_patients.length ?? 0}</span>
      </div>
    </motion.section>
  );
};
