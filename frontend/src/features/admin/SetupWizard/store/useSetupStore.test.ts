import { beforeEach, describe, expect, it } from 'vitest';
import { useSetupStore } from './useSetupStore';

describe('useSetupStore canonical Settings defaults', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    useSetupStore.getState().reset();
  });

  it('starts with the same non-persistent theme and QR defaults as Settings', () => {
    const state = useSetupStore.getState();
    expect(state.selectedTheme).toBe('elite');
    expect(state.selectedTemplate).toBe('swiss');
    expect(state.qrConfig.enabled).toBe(false);
    expect(state.qrConfig.type).toBe('VCARD');
  });

  it('previews a theme without persisting it to localStorage', () => {
    useSetupStore.getState().setSelectedTheme('emerald');
    expect(useSetupStore.getState().selectedTheme).toBe('emerald');
    expect(localStorage.getItem('digitalcrown_theme')).toBeNull();
  });

  it('stores practitioner and establishment INPE separately', () => {
    useSetupStore.getState().setIdentity(prev => ({
      ...prev,
      inpe: 'PRO-42',
      inpeEtablissement: 'EST-42',
    }));
    expect(useSetupStore.getState().identity.inpe).toBe('PRO-42');
    expect(useSetupStore.getState().identity.inpeEtablissement).toBe('EST-42');
  });
});
