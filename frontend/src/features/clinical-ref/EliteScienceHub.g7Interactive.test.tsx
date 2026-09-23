import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { EliteScienceHub } from './EliteScienceHub';

const articles = vi.hoisted(() => [
  {
    id: 'endo-1',
    category: 'ENDODONTIE',
    year: 2025,
    title: 'Endodontic outcomes',
    authors: 'Smith et al.',
    journal: 'Dental Journal',
    summary: 'Evidence endo',
    url: 'https://example.org/endo',
  },
  {
    id: 'ortho-1',
    category: 'ORTHODONTIE',
    year: 2024,
    title: 'Orthodontic evidence',
    authors: 'Jones et al.',
    journal: 'Ortho Journal',
    summary: 'Evidence ortho',
    url: 'https://example.org/ortho',
  },
]);

vi.mock('../../data/science_articles', () => ({ scienceArticles: articles }));

function Probe() {
  const l = useLocation();
  return <div data-testid="loc">{l.pathname}</div>;
}

function renderHub() {
  return render(
    <MemoryRouter initialEntries={['/bibliotheque','/science-hub']} initialIndex={1}>
      <Routes>
        <Route path="/bibliotheque" element={<><div>Library destination</div><Probe /></>} />
        <Route path="/science-hub" element={<><EliteScienceHub /><Probe /></>} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => cleanup());

describe('EliteScienceHub G7 interactive matrix', () => {
  it('filters by title and author without mutating anything', async () => {
    renderHub();
    const search = screen.getByPlaceholderText('Rechercher un article...');

    fireEvent.change(search, { target: { value: 'Endodontic' } });
    expect(screen.getByText('Endodontic outcomes')).toBeTruthy();
    await waitFor(() => expect(screen.queryByText('Orthodontic evidence')).toBeNull());

    fireEvent.change(search, { target: { value: 'Jones' } });
    expect(screen.getByText('Orthodontic evidence')).toBeTruthy();
    await waitFor(() => expect(screen.queryByText('Endodontic outcomes')).toBeNull());
  });

  it('filters by scientific category and exposes truthful no-result state', async () => {
    renderHub();

    fireEvent.click(screen.getByRole('button', { name: 'ENDODONTIE' }));
    expect(screen.getByText('Endodontic outcomes')).toBeTruthy();
    await waitFor(() => expect(screen.queryByText('Orthodontic evidence')).toBeNull());

    const search = screen.getByPlaceholderText('Rechercher un article...');
    fireEvent.change(search, { target: { value: 'absent' } });
    await waitFor(() => expect(screen.getByText('Aucun article ne correspond à votre recherche.')).toBeTruthy());
  });

  it('links to the exact external study with safe new-tab attributes', () => {
    renderHub();
    const link = screen.getAllByRole('link', { name: /Consulter l'étude complète/i })[0];
    expect(link.getAttribute('href')).toBe('https://example.org/endo');
    expect(link.getAttribute('target')).toBe('_blank');
    expect(link.getAttribute('rel')).toContain('noopener');
    expect(link.getAttribute('rel')).toContain('noreferrer');
  });

  it('returns through router history using the back control', () => {
    renderHub();
    const back = screen.getAllByRole('button')[0];
    fireEvent.click(back);
    expect(screen.getByText('Library destination')).toBeTruthy();
    expect(screen.getByTestId('loc').textContent).toBe('/bibliotheque');
  });
});
