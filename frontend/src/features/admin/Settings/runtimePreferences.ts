import { safeStorage } from '../../../hooks/useLocalStorage';
import { useSettingsStore } from './hooks/useSettingsStore';
import type { CabinetProfile } from './types';

type RuntimePreferences = Pick<
  CabinetProfile,
  'show_patient_badges' | 'performance_mode' | 'clinical_tips_enabled'
>;

export const stageRuntimePreferences = (updates: Partial<RuntimePreferences>) => {
  useSettingsStore.setState((state) => ({
    profile: { ...state.profile, ...updates },
    isDirty: true,
  }));
};

export const commitRuntimePreferences = (profile: RuntimePreferences) => {
  safeStorage.set('show_patient_badges', String(profile.show_patient_badges ?? true));
  safeStorage.set('performanceMode', String(profile.performance_mode ?? false));
  safeStorage.set('clinical_tips_enabled', String(profile.clinical_tips_enabled ?? true));
  safeStorage.set('clinicalTipsEnabled', String(profile.clinical_tips_enabled ?? true));
  window.dispatchEvent(new Event('settings_updated'));
  window.dispatchEvent(new Event('clinical-tips-changed'));
};
