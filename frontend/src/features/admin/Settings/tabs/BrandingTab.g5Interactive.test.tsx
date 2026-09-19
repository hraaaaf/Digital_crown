import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { BrandingTab } from './BrandingTab';

const state = vi.hoisted(() => ({
  profile: { selected_theme: 'elite', primary_color: '#003380' } as any,
  updateProfile: vi.fn(),
  stored: new Map<string,string>(),
}));

vi.mock('../hooks/useSettingsStore', () => ({
  useSettingsStore: () => ({ profile: state.profile, updateProfile: state.updateProfile }),
}));

vi.mock('../../../../hooks/useLocalStorage', () => ({
  safeStorage: {
    get: (key: string) => state.stored.get(key) ?? null,
    set: (key: string, value: string) => state.stored.set(key, value),
  },
}));

vi.mock('./branding/presets', () => ({
  PRESETS: [
    { id: 'royal_prestige', name: 'Royal Prestige', profile: { selected_theme: 'prestige' } },
    { id: 'clean', name: 'Clean', profile: { selected_theme: 'elite', primary_color: '#ffffff' } },
  ],
  detectPreset: () => ({ id: 'clean', name: 'Clean' }),
  presetToProfilePatch: (preset: any) => preset.profile,
}));

vi.mock('./branding/AmbiancePill', () => ({
  AmbiancePill: ({ onClick }: { onClick: () => void }) => <button onClick={onClick}>Open presets</button>,
}));
vi.mock('./branding/PresetsModal', () => ({
  PresetsModal: ({ open, onClose, onApply }: any) => open ? (
    <div>
      <span>Presets modal</span>
      <button onClick={() => onApply({ id:'clean', profile:{ selected_theme:'elite', primary_color:'#ffffff' } })}>Apply Clean</button>
      <button onClick={onClose}>Close presets</button>
    </div>
  ) : null,
}));
vi.mock('./branding/StudioControls', () => ({
  StudioControls: () => <div>Studio controls</div>,
}));
vi.mock('./branding/StudioPreview', () => ({
  StudioPreview: ({ scope }: { scope: string }) => <div>Preview {scope}</div>,
}));
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn() } }));

beforeEach(() => {
  vi.clearAllMocks();
  state.stored = new Map();
  localStorage.clear();
  state.profile = { selected_theme: 'elite', primary_color: '#003380' };
  vi.spyOn(window, 'confirm').mockReturnValue(true);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('BrandingTab G5 interactive matrix', () => {
  it('changes preview scope locally without mutating profile', () => {
    render(<BrandingTab />);
    expect(screen.getByText('Preview app')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Document' }));

    expect(screen.getByText('Preview doc')).toBeTruthy();
    expect(localStorage.getItem('branding_preview_scope')).toBe('doc');
    expect(state.updateProfile).not.toHaveBeenCalled();
  });

  it('applies a preset only into staged profile configuration', () => {
    render(<BrandingTab />);
    fireEvent.click(screen.getByRole('button', { name: 'Open presets' }));
    expect(screen.getByText('Presets modal')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Apply Clean' }));
    expect(state.updateProfile).toHaveBeenCalledWith({ selected_theme: 'elite', primary_color: '#ffffff' });
    expect(screen.queryByText('Presets modal')).toBeNull();
  });

  it('requires confirmation before resetting ambiance to the default preset', () => {
    render(<BrandingTab />);

    vi.mocked(window.confirm).mockReturnValueOnce(false);
    fireEvent.click(screen.getByRole('button', { name: /Réinitialiser/i }));
    expect(state.updateProfile).not.toHaveBeenCalled();

    vi.mocked(window.confirm).mockReturnValueOnce(true);
    fireEvent.click(screen.getByRole('button', { name: /Réinitialiser/i }));
    expect(state.updateProfile).toHaveBeenCalledWith({ selected_theme: 'prestige' });
  });

  it('applies animated background immediately as a runtime-only preference', () => {
    const dispatch = vi.spyOn(window, 'dispatchEvent');
    render(<BrandingTab />);

    const toggle = screen.getByRole('button', { name: 'Arrière-plan animé' });
    expect(toggle.getAttribute('aria-pressed')).toBe('false');
    fireEvent.click(toggle);

    expect(state.stored.get('app_background_animated')).toBe('true');
    expect(dispatch).toHaveBeenCalledWith(expect.objectContaining({ type: 'settings_updated' }));
    expect(state.updateProfile).not.toHaveBeenCalled();
  });
});
