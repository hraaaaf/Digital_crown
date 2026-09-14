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

const MOBILE_LABELS: Record<StepId, string> = {
  1: 'Céphalo',
  2: 'Moulages',
  3: 'Synthèse',
  4: 'Documents',
};

export const StepTab: React.FC<StepTabProps> = ({ id, label, isActive, isCompleted, hasError, onClick, P }) => (
  <>
    {id === 1 && (
      <style>{`
        @media (max-width: 639px) {
          [data-tour="cephalo-stepper"] {
            gap: 0.25rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
            overflow-x: visible;
          }
          [data-tour="cephalo-stepper"] > svg {
            display: none;
          }
          [data-tour="cephalo-stepper"] > button {
            flex: 1 1 0%;
            min-width: 0;
            padding-left: 0.375rem;
            padding-right: 0.375rem;
          }
          [data-tour="cephalo-stepper"] > button > div:first-child {
            justify-content: center;
            gap: 0.25rem;
          }
        }
      `}</style>
    )}
    <motion.button
      type="button"
      aria-current={isActive ? 'step' : undefined}
      aria-label={`${id}. ${label}`}
      whileHover={{ y: -1 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="relative min-h-11 shrink-0 whitespace-nowrap rounded-xl px-2.5 py-2.5 transition-all sm:px-3.5"
      style={{
        background: isActive ? `${P.accent}10` : 'transparent',
        border: `1px solid ${isActive ? `${P.accent}80` : P.border}`,
        color: isActive ? P.accent : P.textMuted,
        boxShadow: isActive ? `0 4px 14px ${P.accent}12` : 'none',
      }}
    >
      <div className="flex items-center gap-1.5 text-[10px] font-semibold tracking-wide sm:gap-2 sm:text-[11px]">
        {isCompleted && !isActive && !hasError && <CheckCircle2 size={12} style={{ color: P.accentSuccess }} />}
        {hasError && !isActive && <AlertCircle size={12} style={{ color: P.accentError }} />}
        <span className="text-[9px] font-black opacity-50 sm:text-[10px]">{id}</span>
        <span className="sm:hidden">{MOBILE_LABELS[id]}</span>
        <span className="hidden sm:inline">{label}</span>
      </div>
      {isActive && (
        <motion.div
          layoutId="step-active"
          className="absolute inset-x-2 bottom-0 h-0.5 rounded-full"
          style={{ background: P.accent }}
        />
      )}
    </motion.button>
  </>
);
