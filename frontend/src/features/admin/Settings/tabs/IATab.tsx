import React, { useState } from 'react';
import { Brain, Shield, Activity, Zap } from 'lucide-react';
import { useSettingsStore } from '../hooks/useSettingsStore';
import { SettingsSection } from '../components/SharedUI';
import { cn } from '../../../../utils/cn';
import { safeStorage } from '../../../../hooks/useLocalStorage';

const ToggleRow = ({ icon, title, description, state, onToggle, activeColorClass, style }: any) => (
  <div className="bg-slate-50 p-8 rounded-3xl border border-slate-200 flex items-center justify-between gap-8">
    <div className="flex-1">
      <div className="flex items-center gap-3 mb-1">
        {icon}
        <h4 className="font-black text-slate-800">{title}</h4>
      </div>
      <p className="text-sm text-slate-500 font-medium">{description}</p>
    </div>
    <button 
      onClick={onToggle}
      className={cn("w-14 h-7 rounded-full transition-all relative flex items-center px-1", state ? activeColorClass : "bg-slate-300")}
      style={style}
    >
      <div className={cn("w-5 h-5 bg-white rounded-full shadow-lg transition-all", state ? "translate-x-7" : "translate-x-0")} />
    </button>
  </div>
);

export const IATab: React.FC = () => {
  const { profile, updateProfile } = useSettingsStore();
  const [performanceMode, setPerformanceMode] = useState(
    profile.performance_mode ?? safeStorage.get('performanceMode') === 'true'
  );
  const [clinicalTipsEnabled, setClinicalTipsEnabled] = useState(
    profile.clinical_tips_enabled ?? safeStorage.get('clinicalTipsEnabled') !== 'false'
  );

  const togglePerformanceMode = () => {
    const newVal = !performanceMode;
    setPerformanceMode(newVal);
    safeStorage.set('performanceMode', String(newVal));
    updateProfile({ performance_mode: newVal });
  };

  const toggleClinicalTips = () => {
    const newVal = !clinicalTipsEnabled;
    setClinicalTipsEnabled(newVal);
    safeStorage.set('clinicalTipsEnabled', String(newVal));
    updateProfile({ clinical_tips_enabled: newVal });
  };

  return (
    <div className="space-y-12">
      <SettingsSection 
        title="Intelligence & Performance" 
        subtitle="Optimisez la vitesse et l'intelligence de Ghost Elite."
        icon={<Brain size={32} />}
      >
        <div className="space-y-6">
          <ToggleRow 
            icon={<Zap size={18} className="text-amber-500" />}
            title="Mode Performance (Ultra-Fluide)"
            description="Désactive les effets visuels complexes pour garantir une fluidité maximale sur les configurations modestes."
            state={performanceMode}
            onToggle={togglePerformanceMode}
            activeColorClass="bg-primary"
            style={{ backgroundColor: performanceMode ? 'var(--primary)' : undefined }}
          />

          <ToggleRow 
            icon={<Activity size={18} className="text-emerald-500" />}
            title="Conseils Cliniques (Tips Proactifs)"
            description="Affiche des faits scientifiques et des conseils durant l'analyse des dossiers patients."
            state={clinicalTipsEnabled}
            onToggle={toggleClinicalTips}
            activeColorClass="bg-emerald-500"
          />

          <ToggleRow 
            icon={<Shield size={18} className="text-indigo-600" />}
            title="Badges de Fiabilité Patient"
            description="Évaluation automatique de la fidélité et de l'historique de paiement des patients."
            state={profile.show_patient_badges}
            onToggle={() => {
              const newVal = !profile.show_patient_badges;
              updateProfile({ show_patient_badges: newVal });
              localStorage.setItem('show_patient_badges', String(newVal));
            }}
            activeColorClass="bg-indigo-600"
          />
        </div>
      </SettingsSection>
    </div>
  );
};
