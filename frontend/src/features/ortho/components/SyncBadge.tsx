import React from 'react';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import type { SyncState } from '../cephaloShared';

type Palette = {
  accent: string;
  accentSuccess: string;
  accentError: string;
  [key: string]: string;
};

interface SyncBadgeProps {
  state: SyncState;
  P: Palette;
}

export const SyncBadge: React.FC<SyncBadgeProps> = ({ state, P }) => {
  if (state === 'idle') return null;
  const cfg = {
    syncing: { color: P.accent, icon: <Loader2 size={12} className="animate-spin" />, label: 'Synchronisation…' },
    success: { color: P.accentSuccess, icon: <CheckCircle2 size={12} />, label: 'Synchronisé' },
    error: { color: P.accentError, icon: <AlertCircle size={12} />, label: 'Erreur sync' },
  }[state];
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
      className="absolute bottom-4 right-4 z-30 px-3 py-2 rounded-lg text-xs font-mono flex items-center gap-2 pointer-events-none"
      style={{ background: `${cfg.color}15`, border: `1px solid ${cfg.color}40`, color: cfg.color }}
    >
      {cfg.icon}{cfg.label}
    </motion.div>
  );
};
