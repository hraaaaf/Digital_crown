import { describe, expect, it } from 'vitest';

import {
  isAtomicSettingsTab,
  isProfileBackedTab,
  shouldShowPendingConfigNotice,
  shouldShowSharedSaveBar,
  shouldWarnBeforeUnload,
} from './saveDoctrine';

describe('Settings R1 save doctrine', () => {
  it('classifies only profile-backed tabs as staged configuration', () => {
    expect(['profil', 'branding', 'ia'].every((tab) => isProfileBackedTab(tab as any))).toBe(true);
    expect(['catalogue', 'agenda', 'securite', 'equipe'].every((tab) => isAtomicSettingsTab(tab as any))).toBe(true);
    expect(isProfileBackedTab('catalogue')).toBe(false);
    expect(isAtomicSettingsTab('profil')).toBe(false);
  });

  it('shows the shared save bar only for staged dirty/success state, never for atomic upload saving alone', () => {
    expect(shouldShowSharedSaveBar('profil', { isDirty: true, saving: false, saveSuccess: false })).toBe(true);
    expect(shouldShowSharedSaveBar('branding', { isDirty: true, saving: true, saveSuccess: false })).toBe(true);
    expect(shouldShowSharedSaveBar('ia', { isDirty: false, saving: false, saveSuccess: true })).toBe(true);
    expect(shouldShowSharedSaveBar('profil', { isDirty: false, saving: false, saveSuccess: false })).toBe(false);
    expect(shouldShowSharedSaveBar('branding', { isDirty: false, saving: true, saveSuccess: false })).toBe(false);
    expect(shouldShowSharedSaveBar('agenda', { isDirty: true, saving: false, saveSuccess: false })).toBe(false);
  });

  it('keeps atomic tabs free of global save actions while surfacing pending staged work', () => {
    expect(shouldShowPendingConfigNotice('catalogue', true)).toBe(true);
    expect(shouldShowPendingConfigNotice('agenda', true)).toBe(true);
    expect(shouldShowPendingConfigNotice('securite', true)).toBe(true);
    expect(shouldShowPendingConfigNotice('equipe', true)).toBe(true);
    expect(shouldShowPendingConfigNotice('profil', true)).toBe(false);
    expect(shouldShowPendingConfigNotice('catalogue', false)).toBe(false);
  });

  it('warns before browser unload only when staged configuration is dirty', () => {
    expect(shouldWarnBeforeUnload(true)).toBe(true);
    expect(shouldWarnBeforeUnload(false)).toBe(false);
  });
});
