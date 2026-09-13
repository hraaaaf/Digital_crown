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
    type="button"
    aria-current={isActive ? 'step' : undefined}
    whileHover={{ y: -1 }}
    whileTap={{ scale: 0.98 }}
    onClick={onClick}
    className="relative min-h-11 shrink-0 whitespace-nowrap rounded-xl px-3 py-2.5 transition-all sm:px-3.5"
    style={{
      background: isActive ? `${P.accent}10` : 'transparent',
      border: `1px solid ${isActive ? `${P.accent}80` : P.border}`,
      color: isActive ? P.accent : P.textMuted,
      boxShadow: isActive ? `0 4px 14px ${P.accent}12` : 'none',
    }}
  >
    <div className="flex items-center gap-2 text-[11px] font-semibold tracking-wide">
      {isCompleted && !isActive && !hasError && <CheckCircle2 size={13} style={{ color: P.accentSuccess }} />}
      {hasError && !isActive && <AlertCircle size={13} style={{ color: P.accentError }} />}
      <span className="text-[10px] font-black opacity-50">{id}</span>
      <span>{label}</span>
    </div>
    {isActive && (
      <motion.div
        layoutId="step-active"
        className="absolute inset-x-2 bottom-0 h-0.5 rounded-full"
        style={{ background: P.accent }}
      />
    )}
  </motion.button>
);
