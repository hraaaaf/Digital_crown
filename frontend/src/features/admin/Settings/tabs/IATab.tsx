import React, { useState } from 'react';
import { Brain, Shield, Activity, Zap } from 'lucide-react';
import { useSettingsStore } from '../hooks/useSettingsStore';
import { SettingsSection } from '../components/SharedUI';
import { cn } from '../../../../utils/cn';
import { safeStorage } from '../../../../hooks/useLocalStorage';

export const IATab: React.FC = () => {
  const { profile, updateProfile } = useSettingsStore();
  const [performanceMode, setPerformanceMode] = useState(safeStorage.get('performanceMode') === 'true');
  const [clinicalTipsEnabled, setClinicalTipsEnabled] = useState(safeStorage.get('clinicalTipsEnabled') !== 'false');

  const togglePerformanceMode = () => {
    const newVal = !performanceMode;
    setPerformanceMode(newVal);
    safeStorage.set('performanceMode', String(newVal));
    window.dispatchEvent(new Event('performance-mode-changed'));
  };

  const toggleClinicalTips = () => {
    const newVal = !clinicalTipsEnabled;
    setClinicalTipsEnabled(newVal);
    safeStorage.set('clinicalTipsEnabled', String(newVal));
    window.dispatchEvent(new Event('settings-changed'));
  };

  return (
    <div className="space-y-12">
      <SettingsSection 
        title="Intelligence & Performance" 
        subtitle="Optimisez la vitesse et l'intelligence de Ghost Elite."
        icon={<Brain size={32} />}
      >
        <div className="space-y-6">
          <div className="bg-slate-50 p-8 rounded-3xl border border-slate-200 flex items-center justify-between gap-8">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <Zap size={18} className="text-amber-500" />
                <h4 className="font-black text-slate-800">Mode Performance (Ultra-Fluide)</h4>
              </div>
              <p className="text-sm text-slate-500 font-medium">Désactive les effets visuels complexes pour garantir une fluidité maximale sur les configurations modestes.</p>
            </div>
            <button 
              onClick={togglePerformanceMode}
              className={cn(
                "w-14 h-7 rounded-full transition-all relative flex items-center px-1",
                performanceMode ? "bg-primary" : "bg-slate-300"
              )}
              style={{ backgroundColor: performanceMode ? 'var(--primary)' : undefined }}
            >
              <div className={cn("w-5 h-5 bg-white rounded-full shadow-lg transition-all", performanceMode ? "translate-x-7" : "translate-x-0")} />
            </button>
          </div>

          <div className="bg-slate-50 p-8 rounded-3xl border border-slate-200 flex items-center justify-between gap-8">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <Activity size={18} className="text-emerald-500" />
                <h4 className="font-black text-slate-800">Conseils Cliniques (Tips Proactifs)</h4>
              </div>
              <p className="text-sm text-slate-500 font-medium">Affiche des faits scientifiques et des conseils durant l'analyse des dossiers patients.</p>
            </div>
            <button 
              onClick={toggleClinicalTips}
              className={cn("w-14 h-7 rounded-full transition-all relative flex items-center px-1", clinicalTipsEnabled ? "bg-emerald-500" : "bg-slate-300")}
            >
              <div className={cn("w-5 h-5 bg-white rounded-full shadow-lg transition-all", clinicalTipsEnabled ? "translate-x-7" : "translate-x-0")} />
            </button>
          </div>

          <div className="bg-slate-50 p-8 rounded-3xl border border-slate-200 flex items-center justify-between gap-8">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <Shield size={18} className="text-indigo-600" />
                <h4 className="font-black text-slate-800">Badges de Fiabilité Patient</h4>
              </div>
              <p className="text-sm text-slate-500 font-medium">Évaluation automatique de la fidélité et de l'historique de paiement des patients.</p>
            </div>
            <button 
              onClick={() => {
                const newVal = !profile.show_patient_badges;
                updateProfile({ show_patient_badges: newVal });
                localStorage.setItem('show_patient_badges', String(newVal));
                window.dispatchEvent(new Event('patient-badges-changed'));
              }}
              className={cn("w-14 h-7 rounded-full transition-all relative flex items-center px-1", profile.show_patient_badges ? "bg-indigo-600" : "bg-slate-300")}
            >
              <div className={cn("w-5 h-5 bg-white rounded-full shadow-lg transition-all", profile.show_patient_badges ? "translate-x-7" : "translate-x-0")} />
            </button>
          </div>
        </div>
      </SettingsSection>
    </div>
  );
};
