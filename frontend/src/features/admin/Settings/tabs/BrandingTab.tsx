import React, { useState } from 'react';
import { useSettingsStore } from '../hooks/useSettingsStore';
import { cn } from '../../../../utils/cn';
import toast from 'react-hot-toast';

import type { Scope } from './branding/types';
import { detectPreset, presetToProfilePatch, PRESETS } from './branding/presets';
import { AmbiancePill } from './branding/AmbiancePill';
import { PresetsModal } from './branding/PresetsModal';
import { StudioControls } from './branding/StudioControls';
import { StudioPreview } from './branding/StudioPreview';

export const BrandingTab: React.FC = () => {
  const { profile, updateProfile } = useSettingsStore();
  const [previewScope, setPreviewScope] = useState<Scope>(() => {
    return (
      (localStorage.getItem('branding_preview_scope') as Scope) ||
      (localStorage.getItem('branding_scope') as Scope) ||
      'app'
    );
  });
  const [presetsOpen, setPresetsOpen] = useState(false);

  if (!profile) return null;

  const currentPreset = detectPreset(profile);

  const handlePreviewScopeChange = (newScope: Scope) => {
    setPreviewScope(newScope);
    localStorage.setItem('branding_preview_scope', newScope);
    localStorage.removeItem('branding_scope');
  };

  const handleReset = () => {
    if (window.confirm("Voulez-vous vraiment réinitialiser l'ambiance au preset par défaut ?")) {
      const defaultPreset = PRESETS.find(p => p.id === 'royal_prestige');
      if (defaultPreset) {
        updateProfile(presetToProfilePatch(defaultPreset));
      }
    }
  };

  const handleApplyPreset = (preset: any) => {
    updateProfile(presetToProfilePatch(preset));
    setPresetsOpen(false);
    toast.success("Aperçu appliqué — sauvegardez pour confirmer");
  };

  return (
    <div className="flex flex-col gap-6 animate-in fade-in duration-300 min-w-0">
      {/* Top action row */}
      <div className="flex flex-wrap items-start gap-3 pb-5 border-b border-[var(--border-color)]">
        <AmbiancePill currentPreset={currentPreset} onClick={() => setPresetsOpen(true)} />

        <div className="hidden sm:block sm:flex-1" />

        <div className="flex flex-col gap-1.5 min-w-0">
          <div className="flex items-center gap-2 max-w-full">
            <span className="text-[10px] font-black uppercase tracking-[0.12em] text-[var(--text-muted)] whitespace-nowrap">
              Aperçu
            </span>
            <div
              className="flex max-w-full bg-[var(--bg-medical-pearl)] p-1 rounded-xl border border-[var(--border-color)]"
              aria-label="Choisir l'aperçu du studio"
            >
              {(['app', 'doc'] as Scope[]).map((scope) => (
                <button
                  key={scope}
                  type="button"
                  onClick={() => handlePreviewScopeChange(scope)}
                  aria-pressed={previewScope === scope}
                  className={cn(
                    "px-3 sm:px-4 py-1.5 font-semibold text-[13px] rounded-lg transition-all whitespace-nowrap",
                    previewScope === scope
                      ? "bg-white text-[var(--text-main)] shadow-sm"
                      : "text-[var(--text-muted)] hover:text-[var(--text-main)]"
                  )}
                >
                  {scope === 'app' ? 'Application' : 'Document'}
                </button>
              ))}
            </div>
          </div>
          <p className="text-[10px] text-[var(--text-muted)] leading-tight sm:text-right">
            Ce sélecteur change uniquement l’aperçu affiché.
          </p>
        </div>

        <button
          type="button"
          onClick={handleReset}
          className="px-3 sm:px-4 py-2 font-semibold text-[13px] text-[var(--text-muted)] hover:bg-[var(--bg-medical-pearl)] hover:text-[var(--text-main)] rounded-lg transition-colors border border-transparent hover:border-[var(--border-color)] whitespace-nowrap"
        >
          ↺ Réinitialiser
        </button>
      </div>

      {/* Studio Layout */}
      <div className="grid grid-cols-1 xl:grid-cols-[380px_minmax(0,1fr)] gap-6 min-w-0">
        <div className="min-w-0">
          <StudioControls profile={profile} updateProfile={updateProfile} />
        </div>
        <div className="min-w-0">
          <StudioPreview profile={profile} scope={previewScope} />
        </div>
      </div>

      <PresetsModal
        open={presetsOpen}
        currentPreset={currentPreset}
        onClose={() => setPresetsOpen(false)}
        onApply={handleApplyPreset}
      />
    </div>
  );
};
