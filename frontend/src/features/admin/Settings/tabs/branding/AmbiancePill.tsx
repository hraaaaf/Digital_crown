import React from 'react';
import type { Preset } from './types';
import { BRAND_IDENTITIES } from '../../../constants';
import { ChevronRight } from 'lucide-react';

interface AmbiancePillProps {
  currentPreset: Preset | null;
  onClick: () => void;
}

export const AmbiancePill: React.FC<AmbiancePillProps> = ({ currentPreset, onClick }) => {
  const palette = currentPreset 
    ? BRAND_IDENTITIES.find(p => p.id === currentPreset.palette)
    : null;

  return (
    <button 
      onClick={onClick}
      className="flex flex-col gap-1 px-4 py-2 bg-[var(--card-bg)] border border-[var(--border-color)] rounded-xl hover:border-[var(--text-main)] transition-colors text-left"
    >
      <span className="font-bold text-[11px] text-[var(--text-muted)] tracking-[0.12em] uppercase">
        Ambiance active
      </span>
      <div className="flex items-center gap-3">
        <span className="font-semibold text-[13px] text-[var(--text-main)]">
          {currentPreset ? currentPreset.name : 'Personnalisé'}
        </span>
        
        {palette && (
          <div className="flex w-[36px] h-[22px] rounded-md overflow-hidden border border-[var(--border-color)]">
            <div className="flex-1" style={{ backgroundColor: palette.primary }} />
            <div className="flex-1" style={{ backgroundColor: palette.secondary }} />
            <div className="flex-1" style={{ backgroundColor: palette.accent }} />
          </div>
        )}

        <ChevronRight size={14} className="text-[var(--text-muted)]" />
      </div>
    </button>
  );
};
