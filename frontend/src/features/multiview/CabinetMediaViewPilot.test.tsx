import React from 'react';
import { act, cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CabinetMediaViewPilot } from './CabinetMediaViewPilot';

// Existing real clinical module is mocked ONLY in this unit test.
// The real authenticated browser gate must exercise its actual API and UI.
vi.mock('../patients/components/PatientMediaTimeline', () => ({
  PatientMediaTimeline: ({ patientId }: { patientId: number }) => (
    <div data-testid="media-authentique">Patient courant : {patientId}</div>
  ),
}));

const listeners = new Set<() => void>();
let matches = false;

beforeEach(() => {
  listeners.clear();
  matches = false;
  vi.stubEnv('VITE_V15_07_G1_MEDIA_FRAME_PILOT', '1');
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    value: vi.fn().mockImplementation(() => ({
      get matches() { return matches; },
      media: '(min-width: 1280px)',
      addEventListener: (_: string, listener: () => void) => listeners.add(listener),
      removeEventListener: (_: string, listener: () => void) => listeners.delete(listener),
    })),
  });
});

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
});

describe('Vues multiples — enveloppe du module clinique existant', () => {
  it('préserve le module original sur petit écran', () => {
    render(<CabinetMediaViewPilot patientId={47} />);
    expect(screen.queryByRole('region', { name: 'Médiathèque clinique' })).toBeNull();
    expect(screen.getAllByTestId('media-authentique')).toHaveLength(1);
  });

  it('utilise un seul module réel sous le thème actif sur bureau et conserve le patient', () => {
    matches = true;
    const { rerender } = render(<CabinetMediaViewPilot patientId={47} />);
    expect(screen.getByRole('region', { name: 'Médiathèque clinique' })).toBeTruthy();
    expect(screen.getAllByTestId('media-authentique')).toHaveLength(1);
    rerender(<CabinetMediaViewPilot patientId={48} />);
    expect(screen.getByTestId('media-authentique').textContent).toContain('48');
    expect(screen.getByTestId('media-authentique').textContent).not.toContain('47');
  });

  it('retire le cadre lors du passage en largeur mobile et conserve le module', () => {
    matches = true;
    render(<CabinetMediaViewPilot patientId={47} />);
    expect(screen.getByRole('region', { name: 'Médiathèque clinique' })).toBeTruthy();
    act(() => { matches = false; listeners.forEach(callback => callback()); });
    expect(screen.queryByRole('region', { name: 'Médiathèque clinique' })).toBeNull();
    expect(screen.getAllByTestId('media-authentique')).toHaveLength(1);
  });

  it('ne crée jamais de cadre lorsque le drapeau est désactivé', () => {
    vi.stubEnv('VITE_V15_07_G1_MEDIA_FRAME_PILOT', '0');
    matches = true;
    render(<CabinetMediaViewPilot patientId={47} />);
    expect(screen.queryByRole('region', { name: 'Médiathèque clinique' })).toBeNull();
    expect(screen.getAllByTestId('media-authentique')).toHaveLength(1);
  });
});