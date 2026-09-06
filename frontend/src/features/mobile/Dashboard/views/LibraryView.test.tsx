import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { LibraryView } from './LibraryView';

afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

describe('LibraryView MOB-5E', () => {
  it('uses the shared 50-protocol source and searches by existing clinical content', () => {
    render(<LibraryView role="DENTISTE" />);

    expect(screen.getByText('50 protocoles')).toBeTruthy();
    const search = screen.getByPlaceholderText('Rechercher un acte, code, discipline…');
    fireEvent.change(search, { target: { value: 'Extraction molaire' } });

    expect(screen.getByText('1 résultat')).toBeTruthy();
    expect(screen.getByText('Extraction molaire')).toBeTruthy();
    expect(screen.getByText('Chirurgie')).toBeTruthy();
  });

  it('opens existing protocol detail and reuses the existing favorites key', () => {
    render(<LibraryView role="ADMIN" />);
    fireEvent.change(screen.getByPlaceholderText('Rechercher un acte, code, discipline…'), { target: { value: 'Extraction molaire' } });

    const title = screen.getByText('Extraction molaire');
    const openButton = title.closest('button');
    expect(openButton).toBeTruthy();
    fireEvent.click(openButton!);

    expect(screen.getByText('Radio panoramique confirmée')).toBeTruthy();
    expect(screen.getByText('Complexe')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Ajouter Extraction molaire aux favoris' }));
    expect(JSON.parse(window.localStorage.getItem('dc_favs') || '[]')).toContain('extraction-molaire');
  });

  it('fails closed while role is loading and does not expose content to secretary', () => {
    const { rerender } = render(<LibraryView />);
    expect(screen.getByText('Vérification des accès…')).toBeTruthy();
    expect(screen.queryByPlaceholderText('Rechercher un acte, code, discipline…')).toBeNull();

    rerender(<LibraryView role="SECRETAIRE" />);
    expect(screen.getByText('Accès réservé')).toBeTruthy();
    expect(screen.queryByPlaceholderText('Rechercher un acte, code, discipline…')).toBeNull();
  });
});