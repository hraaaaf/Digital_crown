import React from 'react';
import { Activity, Gauge, ShieldCheck, Zap } from 'lucide-react';
import { useSettingsStore } from '../hooks/useSettingsStore';
import { SettingsSection } from '../components/SharedUI';
import { cn } from '../../../../utils/cn';
import { safeStorage } from '../../../../hooks/useLocalStorage';
import { stageRuntimePreferences } from '../runtimePreferences';

const ToggleRow = ({ icon, title, description, state, onToggle, activeColorClass, style }: any) => (
  <div className="bg-slate-50 p-5 sm:p-8 rounded-3xl border border-slate-200 grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 sm:gap-8 min-w-0">
    <div className="min-w-0">
      <div className="flex items-start sm:items-center gap-3 mb-1">
        <span className="mt-0.5 sm:mt-0 shrink-0">{icon}</span>
        <h4 className="font-black text-slate-800 leading-snug">{title}</h4>
      </div>
      <p className="text-sm text-slate-500 font-medium leading-relaxed">{description}</p>
    </div>
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={Boolean(state)}
      aria-label={title}
      className={cn("w-14 h-7 shrink-0 rounded-full transition-all relative flex items-center px-1", state ? activeColorClass : "bg-slate-300")}
      style={style}
    >
      <div className={cn("w-5 h-5 bg-white rounded-full shadow-lg transition-all", state ? "translate-x-7" : "translate-x-0")} />
    </button>
  </div>
);

export const IATab: React.FC = () => {
  const profile = useSettingsStore((state) => state.profile);
  const performanceMode = profile.performance_mode ?? safeStorage.get('performanceMode') === 'true';
  const clinicalTipsEnabled = profile.clinical_tips_enabled ?? safeStorage.get('clinical_tips_enabled') !== 'false';
  const patientIndicatorsEnabled = profile.show_patient_badges ?? true;

  const togglePerformanceMode = () => {
    stageRuntimePreferences({ performance_mode: !performanceMode });
  };

  const toggleClinicalTips = () => {
    stageRuntimePreferences({ clinical_tips_enabled: !clinicalTipsEnabled });
  };

  return (
    <div className="space-y-8 sm:space-y-12 min-w-0">
      <SettingsSection
        title="Performance & Assistance"
        subtitle="Réglez les comportements d’assistance réellement appliqués par l’application."
        icon={<Gauge size={32} />}
      >
        <div className="space-y-4 sm:space-y-6">
          <ToggleRow
            icon={<Zap size={18} className="text-amber-500" />}
            title="Mode Performance"
            description="Réduit certains effets visuels coûteux pour améliorer la fluidité sur les configurations modestes."
            state={performanceMode}
            onToggle={togglePerformanceMode}
            activeColorClass="bg-primary"
            style={{ backgroundColor: performanceMode ? 'var(--primary)' : undefined }}
          />

          <ToggleRow
            icon={<Activity size={18} className="text-emerald-500" />}
            title="Conseils cliniques contextuels"
            description="Affiche les bulles de conseil déjà disponibles dans les écrans compatibles, notamment la céphalométrie et la navigation clinique."
            state={clinicalTipsEnabled}
            onToggle={toggleClinicalTips}
            activeColorClass="bg-emerald-500"
          />

          <ToggleRow
            icon={<ShieldCheck size={18} className="text-indigo-600" />}
            title="Indicateurs de suivi patient"
            description="Affiche un indicateur fondé sur l’assiduité aux rendez-vous (60 %) et le rapport encaissé / facturé (40 %). Le praticien peut l’ajuster manuellement."
            state={patientIndicatorsEnabled}
            onToggle={() => stageRuntimePreferences({ show_patient_badges: !patientIndicatorsEnabled })}
            activeColorClass="bg-indigo-600"
          />
        </div>
      </SettingsSection>
    </div>
  );
};
