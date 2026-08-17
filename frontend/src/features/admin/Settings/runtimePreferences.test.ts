import { beforeEach, describe, expect, it } from 'vitest';

import { useSettingsStore } from './hooks/useSettingsStore';
import { commitRuntimePreferences, stageRuntimePreferences } from './runtimePreferences';

describe('Settings runtime preference truth contract', () => {
  beforeEach(() => {
    localStorage.clear();
    useSettingsStore.setState({
      profile: {
        ...useSettingsStore.getState().profile,
        show_patient_badges: true,
        performance_mode: false,
        clinical_tips_enabled: true,
      },
      isDirty: false,
    });
  });

  it('stages profile changes without mutating persisted runtime preferences', () => {
    stageRuntimePreferences({ performance_mode: true, clinical_tips_enabled: false });

    const state = useSettingsStore.getState();
    expect(state.profile.performance_mode).toBe(true);
    expect(state.profile.clinical_tips_enabled).toBe(false);
    expect(state.isDirty).toBe(true);
    expect(localStorage.getItem('performanceMode')).toBeNull();
    expect(localStorage.getItem('clinical_tips_enabled')).toBeNull();
  });

  it('commits runtime preferences only when explicitly called after persistence', () => {
    stageRuntimePreferences({
      show_patient_badges: false,
      performance_mode: true,
      clinical_tips_enabled: false,
    });

    commitRuntimePreferences(useSettingsStore.getState().profile);

    expect(localStorage.getItem('show_patient_badges')).toBe('false');
    expect(localStorage.getItem('performanceMode')).toBe('true');
    expect(localStorage.getItem('clinical_tips_enabled')).toBe('false');
    expect(localStorage.getItem('clinicalTipsEnabled')).toBe('false');
  });
});
