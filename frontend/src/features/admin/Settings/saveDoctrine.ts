import type { Tab } from './types';

export const PROFILE_BACKED_TABS: readonly Tab[] = ['profil', 'branding', 'ia'];
export const ATOMIC_SETTINGS_TABS: readonly Tab[] = ['catalogue', 'agenda', 'securite', 'equipe'];

export const isProfileBackedTab = (tab: Tab) => PROFILE_BACKED_TABS.includes(tab);
export const isAtomicSettingsTab = (tab: Tab) => ATOMIC_SETTINGS_TABS.includes(tab);

export const shouldShowSharedSaveBar = (
  tab: Tab,
  state: { isDirty: boolean; saving: boolean; saveSuccess: boolean },
) => isProfileBackedTab(tab) && (state.isDirty || state.saveSuccess);

export const shouldShowPendingConfigNotice = (tab: Tab, isDirty: boolean) =>
  isDirty && isAtomicSettingsTab(tab);

export const shouldWarnBeforeUnload = (isDirty: boolean) => isDirty;
