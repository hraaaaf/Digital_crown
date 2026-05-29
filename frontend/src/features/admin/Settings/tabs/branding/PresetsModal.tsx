import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Check } from 'lucide-react';
import { PRESETS } from './presets';
import type { Preset } from './types';
import { BRAND_IDENTITIES, PREMIUM_FONTS } from '../../../constants';
import { cn } from '../../../../../utils/cn';

interface PresetsModalProps {
  open: boolean;
  currentPreset: Preset | null;
  onClose: () => void;
  onApply: (preset: Preset) => void;
}

export const PresetsModal: React.FC<PresetsModalProps> = ({ open, currentPreset, onClose, onApply }) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedId(currentPreset?.id ?? null);
    }
  }, [open, currentPreset]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) onClose();
      if (e.key === 'Enter' && open && selectedId) {
        const preset = PRESETS.find(p => p.id === selectedId);
        if (preset) onApply(preset);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, selectedId, onClose, onApply]);

  if (!open) return null;

  const selectedPreset = PRESETS.find(p => p.id === selectedId);

  return createPortal(
    <div 
      className="fixed inset-0 z-[50000] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-[900px] bg-[var(--card-bg)] rounded-2xl shadow-[0_16px_48px_rgba(0,0,0,0.15)] flex flex-col overflow-hidden border border-[var(--border-color)]"
        onClick={e => e.stopPropagation()}
      >
        <div className="p-8 border-b border-[var(--border-color)] flex items-start justify-between">
          <div>
            <h2 className="font-medium text-[26px] text-[var(--text-main)] leading-tight mb-2">
              6 ambiances cohérentes, prêtes à l'emploi
            </h2>
            <p className="text-[14px] text-[var(--text-muted)]">
              Ces préréglages appliquent instantanément la typographie, la palette de couleurs et la densité idéale pour vos documents.
            </p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-[var(--text-muted)] hover:bg-[var(--bg-medical-pearl)] rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-8 bg-[var(--bg-medical-pearl)] grid grid-cols-3 gap-6">
          {PRESETS.map(preset => {
            const palette = BRAND_IDENTITIES.find(p => p.id === preset.palette)!;
            const fontObj = PREMIUM_FONTS.find(f => f.id === preset.font)!;
            const isSelected = selectedId === preset.id;

            return (
              <button
                key={preset.id}
                onClick={() => setSelectedId(preset.id)}
                className={cn(
                  "relative group flex flex-col h-[180px] rounded-2xl overflow-hidden border-2 text-left transition-all",
                  isSelected 
                    ? "border-[var(--primary)] shadow-[0_8px_24px_-16px_rgba(11,15,23,0.18)] -translate-y-0.5" 
                    : "border-[var(--border-color)] hover:border-[var(--text-muted)] hover:shadow-[0_8px_24px_-16px_rgba(11,15,23,0.18)] hover:-translate-y-0.5"
                )}
                style={{
                  background: `linear-gradient(135deg, ${palette.primary}0A 0%, ${palette.secondary}15 100%)`,
                }}
              >
                {/* Miniature document flottante */}
                <div className="absolute right-[-10px] top-[20px] w-[80px] h-[110px] bg-white rounded-md shadow-sm border border-[var(--border-color)] transform rotate-12 opacity-80 group-hover:rotate-6 transition-transform">
                  <div className="absolute top-2 left-2 w-8 h-1" style={{ backgroundColor: palette.primary }} />
                  <div className="absolute top-4 left-2 w-12 h-1 bg-[var(--bg-medical-pearl)]" />
                  <div className="absolute top-6 left-2 w-10 h-1 bg-[var(--bg-medical-pearl)]" />
                </div>

                <div className="p-5 flex flex-col h-full relative z-10">
                  <span className="font-bold text-[11px] tracking-[0.12em] uppercase" style={{ color: palette.primary }}>
                    {preset.vibe}
                  </span>
                  
                  <h3 className="font-medium text-[22px] text-[var(--text-main)] mt-1 mb-auto leading-tight">
                    {preset.name}
                  </h3>

                  <div className="flex items-center gap-3">
                    <div className="flex w-[32px] h-[18px] rounded-md overflow-hidden border border-white/50 shadow-sm">
                      <div className="flex-1" style={{ backgroundColor: palette.primary }} />
                      <div className="flex-1" style={{ backgroundColor: palette.secondary }} />
                    </div>
                    <span className="text-[11px] font-medium text-[var(--text-muted)]">
                      {fontObj.name}
                    </span>
                  </div>
                </div>

                {isSelected && (
                  <div className="absolute top-4 right-4 w-6 h-6 rounded-full bg-[var(--primary)] text-white flex items-center justify-center">
                    <Check size={14} />
                  </div>
                )}
              </button>
            );
          })}
        </div>

        <div className="p-6 border-t border-[var(--border-color)] flex items-center justify-between">
          <span className="text-[13px] text-[var(--text-muted)] font-medium">
            {selectedPreset 
              ? <>Ambiance sélectionnée : <strong className="text-[var(--text-main)]">{selectedPreset.name}</strong> · 6 réglages appliqués</>
              : "Sélectionnez une ambiance"}
          </span>
          <div className="flex items-center gap-3">
            <button 
              onClick={onClose}
              className="px-5 py-2.5 font-semibold text-[13px] text-[var(--text-main)] hover:bg-[var(--bg-medical-pearl)] rounded-lg transition-colors border border-[var(--border-color)]"
            >
              Annuler
            </button>
            <button 
              disabled={!selectedPreset}
              onClick={() => selectedPreset && onApply(selectedPreset)}
              className="px-5 py-2.5 font-semibold text-[13px] bg-[var(--text-main)] text-white hover:bg-black rounded-lg transition-colors disabled:opacity-50"
            >
              Appliquer l'ambiance →
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};
