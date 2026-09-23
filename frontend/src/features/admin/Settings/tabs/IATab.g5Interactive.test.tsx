import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { IATab } from './IATab';

const state = vi.hoisted(() => ({
  profile: {
    performance_mode: false,
    clinical_tips_enabled: true,
    show_patient_badges: true,
  },
  staged: [] as any[],
}));

vi.mock('../hooks/useSettingsStore', () => ({
  useSettingsStore: (selector: any) => selector({ profile: state.profile }),
  __esModule: true,
}));

vi.mock('../runtimePreferences', () => ({
  stageRuntimePreferences: (updates: any) => state.staged.push(updates),
}));

vi.mock('../../../../hooks/useLocalStorage', () => ({
  safeStorage: { get: vi.fn(() => null) },
}));

beforeEach(() => {
  state.profile = {
    performance_mode: false,
    clinical_tips_enabled: true,
    show_patient_badges: true,
  };
  state.staged = [];
});

afterEach(() => cleanup());

describe('IATab G5 runtime preference controls', () => {
  it('stages performance mode instead of persisting immediately', () => {
    render(<IATab />);
    fireEvent.click(screen.getByRole('button', { name: 'Mode Performance' }));
    expect(state.staged).toContainEqual({ performance_mode: true });
  });

  it('stages AI activity animation preference without immediate backend mutation', () => {
    render(<IATab />);
    fireEvent.click(screen.getByRole('button', { name: 'Animation d’activité IA' }));
    expect(state.staged).toContainEqual({ clinical_tips_enabled: false });
  });

  it('stages patient indicators without immediate backend mutation', () => {
    render(<IATab />);
    fireEvent.click(screen.getByRole('button', { name: 'Indicateurs de suivi patient' }));
    expect(state.staged).toContainEqual({ show_patient_badges: false });
  });

  it('reflects current profile truth through aria-pressed state', () => {
    render(<IATab />);
    expect(screen.getByRole('button', { name: 'Mode Performance' }).getAttribute('aria-pressed')).toBe('false');
    expect(screen.getByRole('button', { name: 'Animation d’activité IA' }).getAttribute('aria-pressed')).toBe('true');
    expect(screen.getByRole('button', { name: 'Indicateurs de suivi patient' }).getAttribute('aria-pressed')).toBe('true');
  });
});
