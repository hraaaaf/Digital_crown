import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import type { StepId } from '../cephaloShared';

type Palette = {
  accent: string;
  border: string;
  textMuted: string;
  accentSuccess: string;
  accentError: string;
  [key: string]: string;
};

interface StepTabProps {
  id: StepId;
  label: string;
  isActive: boolean;
  isCompleted: boolean;
  hasError?: boolean;
  onClick: () => void;
  P: Palette;
}

export const StepTab: React.FC<StepTabProps> = ({ id, label, isActive, isCompleted, hasError, onClick, P }) => (
  <motion.button
    whileHover={{ y: -1 }} whileTap={{ scale: 0.98 }}
    onClick={onClick}
    className="relative px-4 py-3 rounded-lg transition-all"
    style={{
      background: isActive ? `${P.accent}15` : 'transparent',
      border: `1px solid ${isActive ? P.accent : P.border}`,
      color: isActive ? P.accent : P.textMuted,
    }}
  >
    <div className="flex items-center gap-2 text-xs font-mono font-semibold tracking-wide">
      {isCompleted && !isActive && !hasError && <CheckCircle2 size={12} style={{ color: P.accentSuccess }} />}
      {hasError && !isActive && <AlertCircle size={12} style={{ color: P.accentError }} />}
      <span className="opacity-40">{id}.</span>
      <span>{label}</span>
    </div>
    {isActive && (
      <motion.div
        layoutId="step-active"
        className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full"
        style={{ background: `linear-gradient(90deg, ${P.accent}, ${P.accentSuccess})` }}
      />
    )}
  </motion.button>
);
