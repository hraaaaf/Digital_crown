import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { EliteLibrary } from './EliteLibrary';

const clinicalFixtures = vi.hoisted(() => ({ protocols: [
  {
    act_code: 'DET',
    act_names: ['Détartrage'],
    category: 'Parodontologie',
    difficulty: 'routine',
    checklist: [{ label: 'A', critical: false }],
    pitfalls: [],
  },
  {
    act_code: 'ENDO',
    act_names: ['Traitement endodontique'],
    category: 'Endodontie',
    difficulty: 'complex',
    checklist: [{ label: 'A', critical: true }, { label: 'B', critical: false }],
    pitfalls: [{ label: 'Risque' }],
  },
  {
    act_code: 'AVUL',
    act_names: ['Avulsion'],
    category: 'Chirurgie',
    difficulty: 'specialist',
    checklist: [{ label: 'A', critical: true }],
    pitfalls: [{ label: 'R1' }, { label: 'R2' }],
  },
] }));

vi.mock('../../data/clinical-protocols', () => ({ CLINICAL_PROTOCOLS: clinicalFixtures.protocols }));
vi.mock('./ClinicalRefContent', () => ({
  ClinicalRefContent: ({ protocol }: { protocol: any }) => <div>Protocol content {protocol.act_code}</div>,
}));
vi.mock('./ClinicalSoinMode', () => ({
  ClinicalSoinMode: ({ protocol, onClose }: { protocol: any; onClose: () => void }) => (
    <div><span>Soin mode {protocol.act_code}</span><button onClick={onClose}>Close soin</button></div>
  ),
}));

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
}

function renderLibrary(entry = '/bibliotheque') {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/bibliotheque" element={<><EliteLibrary /><LocationProbe /></>} />
        <Route path="/bibliotheque/:code" element={<><EliteLibrary /><LocationProbe /></>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  localStorage.clear();
  vi.spyOn(window, 'print').mockImplementation(() => undefined);
  vi.spyOn(window, 'open').mockImplementation(() => null);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('EliteLibrary G7 interactive matrix', () => {
  it('filters by search and resets filters without mutation', () => {
    renderLibrary();
    const input = screen.getByPlaceholderText('Avulsion, composite, blanchiment…');

    fireEvent.change(input, { target: { value: 'ENDO' } });
    expect(screen.getByText('Traitement endodontique')).toBeTruthy();
    expect(screen.queryByText('Détartrage')).toBeNull();

    fireEvent.change(input, { target: { value: 'absent' } });
    expect(screen.getByText('Aucun protocole trouvé')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Réinitialiser les filtres/i }));
    expect(screen.getByText('Détartrage')).toBeTruthy();
  });

  it('filters favorites and persists favorite state locally', () => {
    renderLibrary();

    const card = screen.getByText('Détartrage').closest('button')!;
    const star = withinButtonStar(card as HTMLElement);
    fireEvent.click(star);

    expect(JSON.parse(localStorage.getItem('dc_favs') || '[]')).toContain('DET');
    fireEvent.click(screen.getByRole('button', { name: /Favoris/i }));
    expect(screen.getByText('Détartrage')).toBeTruthy();
    expect(screen.queryByText('Avulsion')).toBeNull();
  });

  it('switches grid/list and sorting controls locally', () => {
    renderLibrary();
    fireEvent.click(screen.getByTitle('Vue liste'));
    expect(screen.getByTitle('Vue liste')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Difficulté' }));
    let protocolOrder = Array.from(document.querySelectorAll('button'))
      .map(button => button.textContent?.replace(/\s+/g, ' ').trim())
      .filter(text => ['Détartrage', 'Traitement endodontique', 'Avulsion'].includes(text || ''));
    expect(protocolOrder).toEqual(['Détartrage', 'Traitement endodontique', 'Avulsion']);

    fireEvent.click(screen.getByRole('button', { name: 'Discipline' }));
    protocolOrder = Array.from(document.querySelectorAll('button'))
      .map(button => button.textContent?.replace(/\s+/g, ' ').trim())
      .filter(text => ['Détartrage', 'Traitement endodontique', 'Avulsion'].includes(text || ''));
    expect(protocolOrder).toEqual(['Avulsion', 'Traitement endodontique', 'Détartrage']);
  });

  it('opens protocol deep-link, records recent, navigates next/previous and closes to library root', () => {
    renderLibrary();
    fireEvent.click(screen.getByText('Détartrage').closest('button')!);

    expect(screen.getByTestId('location').textContent).toBe('/bibliotheque/DET');
    expect(screen.getByText('Protocol content DET')).toBeTruthy();
    expect(JSON.parse(localStorage.getItem('dc_recents') || '[]')[0]).toBe('DET');

    fireEvent.click(screen.getByTitle('Suivant (→)'));
    expect(screen.getByTestId('location').textContent).toBe('/bibliotheque/ENDO');
    expect(screen.getByText('Protocol content ENDO')).toBeTruthy();

    fireEvent.click(screen.getByTitle('Précédent (←)'));
    expect(screen.getByTestId('location').textContent).toBe('/bibliotheque/DET');

    fireEvent.click(screen.getByTitle('Fermer (Esc)'));
    expect(screen.getByTestId('location').textContent).toBe('/bibliotheque');
  });

  it('hydrates a protocol directly from /bibliotheque/:code', () => {
    renderLibrary('/bibliotheque/ENDO');
    expect(screen.getByText('Protocol content ENDO')).toBeTruthy();
  });

  it('prints and opens/closes immersive soin mode explicitly', () => {
    renderLibrary('/bibliotheque/DET');

    fireEvent.click(screen.getByTitle('Imprimer (P)'));
    expect(window.print).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: /Ouvrir en mode Soin/i }));
    expect(screen.getByText('Soin mode DET')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Close soin' }));
    expect(screen.queryByText('Soin mode DET')).toBeNull();
  });

  it('opens command palette by button and keyboard, searches, then opens selected protocol', () => {
    renderLibrary();

    fireEvent.click(screen.getAllByRole('button', { name: /Rechercher/i })[0]);
    const cmd = screen.getByPlaceholderText('Rechercher un protocole ou une spécialité...');
    fireEvent.change(cmd, { target: { value: 'Avulsion' } });
    fireEvent.keyDown(cmd, { key: 'Enter' });

    expect(screen.getByTestId('location').textContent).toBe('/bibliotheque/AVUL');

    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    expect(screen.getByPlaceholderText('Rechercher un protocole ou une spécialité...')).toBeTruthy();
  });

  it('clears recent history explicitly', () => {
    localStorage.setItem('dc_recents', JSON.stringify(['DET']));
    renderLibrary();
    expect(screen.getByText('Récemment consultés')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Effacer' }));
    expect(JSON.parse(localStorage.getItem('dc_recents') || '[]')).toEqual([]);
    expect(screen.queryByText('Récemment consultés')).toBeNull();
  });
});

function withinButtonStar(button: HTMLElement) {
  const candidates = Array.from(button.querySelectorAll('span'));
  const star = candidates.find(el => el.textContent === '☆' || el.textContent === '★');
  if (!star) throw new Error('favorite control missing');
  return star;
}
