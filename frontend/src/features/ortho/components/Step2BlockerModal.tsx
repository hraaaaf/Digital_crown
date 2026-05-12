import React from 'react';
import { createPortal } from 'react-dom';
import { motion } from 'framer-motion';
import { Ruler } from 'lucide-react';

type Palette = {
  bgPanel: string;
  bgCard: string;
  border: string;
  borderFocus: string;
  text: string;
  textMuted: string;
  accent: string;
  accentWarning: string;
  shadowLg: string;
  [key: string]: string;
};

interface Step2BlockerModalProps {
  type: 'calibration' | null;
  onClose: () => void;
  onStartCalibration: () => void;
  P: Palette;
}

export const Step2BlockerModal: React.FC<Step2BlockerModalProps> = ({ type, onClose, onStartCalibration, P }) => {
  if (!type) return null;

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        className="max-w-md w-full rounded-2xl p-6"
        style={{ background: P.bgPanel, border: `1px solid ${P.border}`, boxShadow: P.shadowLg }}
      >
        <div className="flex items-center gap-3 mb-4">
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center"
            style={{ background: `${P.accentWarning}15` }}
          >
            <Ruler size={24} style={{ color: P.accentWarning }} />
          </div>
          <div>
            <h3 className="text-lg font-bold" style={{ color: P.text }}>
              Calibration requise
            </h3>
            <p className="text-xs" style={{ color: P.textMuted }}>Étape préliminaire obligatoire</p>
          </div>
        </div>

        <div className="space-y-3 mb-6">
          <p className="text-sm leading-relaxed" style={{ color: P.textMuted }}>
            Avant de procéder à l'analyse des moulages, vous devez calibrer l'échelle de la radiographie en sélectionnant deux points de référence dont vous connaissez la distance réelle.
          </p>

          <div className="rounded-xl p-4 text-xs space-y-3" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
            {[
              'Cliquez sur "Calibrer maintenant" puis sélectionnez deux points distincts sur l\'image (ex: bords d\'une dent connue)',
              'Entrez la distance réelle entre ces deux points en millimètres',
            ].map((text, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold" style={{ background: P.accent, color: 'white' }}>{i + 1}</span>
                <span style={{ color: P.textMuted }}>{text}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all hover:opacity-80"
            style={{ background: 'transparent', border: `1px solid ${P.border}`, color: P.textMuted }}
          >
            Plus tard
          </button>
          <button
            onClick={() => { onClose(); onStartCalibration(); }}
            className="flex-1 px-4 py-2.5 rounded-xl text-sm font-bold transition-all hover:opacity-90"
            style={{ background: P.accentWarning, color: 'white' }}
          >
            Calibrer maintenant
          </button>
        </div>
      </motion.div>
    </div>,
    document.body
  );
};
