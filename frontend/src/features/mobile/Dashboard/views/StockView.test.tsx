import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { StockView } from './StockView';
import { mobileApiJson } from '../../../../services/zka/mobileApi';

vi.mock('../../../../services/zka/mobileApi', () => ({
  mobileApiJson: vi.fn(),
}));

const items = [
  { id: 1, nom: 'Gants nitrile M', categorie: 'CONSOMMABLE', quantite: 0, seuil_alerte: 4, unite: 'boîtes', fournisseur: 'Fournisseur test', alerte: true },
  { id: 2, nom: 'Composite universel', categorie: 'MATERIAU', quantite: 2, seuil_alerte: 3, unite: 'seringues', fournisseur: null, alerte: true },
  { id: 3, nom: 'Masques', categorie: 'CONSOMMABLE', quantite: 12, seuil_alerte: 5, unite: 'boîtes', fournisseur: null, alerte: false },
];

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('StockView MOB-5D', () => {
  it('loads the Pocket stock endpoint and exposes rupture/alert/search contracts', async () => {
    vi.mocked(mobileApiJson).mockResolvedValue(items as any);
    render(<StockView />);

    expect(await screen.findByText('Gants nitrile M')).toBeTruthy();
    expect(mobileApiJson).toHaveBeenCalledWith('/stock/items');
    expect(screen.getByText('Composite universel')).toBeTruthy();
    fireEvent.click(screen.getByText('À traiter'));
    expect(screen.queryByText('Masques')).toBeNull();

    fireEvent.click(screen.getByText('Tous'));
    fireEvent.change(screen.getByPlaceholderText('Rechercher un article…'), { target: { value: 'Fournisseur test' } });
    expect(screen.getByText('Gants nitrile M')).toBeTruthy();
    expect(screen.queryByText('Composite universel')).toBeNull();
  });

  it('persists +1 and never exposes a decrement below zero', async () => {
    vi.mocked(mobileApiJson)
      .mockResolvedValueOnce(items as any)
      .mockResolvedValueOnce({ ...items[1], quantite: 3, alerte: true } as any);
    render(<StockView />);

    expect(await screen.findByText('Composite universel')).toBeTruthy();
    const ruptureMinus = screen.getByRole('button', { name: 'Retirer une boîtes de Gants nitrile M' });
    expect(ruptureMinus.hasAttribute('disabled')).toBe(true);

    fireEvent.click(screen.getByRole('button', { name: 'Ajouter une seringues à Composite universel' }));
    await waitFor(() => expect(mobileApiJson).toHaveBeenCalledWith('/stock/items/2', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantite: 3 }),
    }));
  });
  it('creates a quick item through the Pocket API and exposes no delete action', async () => {
    vi.mocked(mobileApiJson)
      .mockResolvedValueOnce([] as any)
      .mockResolvedValueOnce({ id: 9, nom: 'Compresses', categorie: 'CONSOMMABLE', quantite: 10, seuil_alerte: 4, unite: 'paquets', alerte: false } as any);
    render(<StockView />);

    expect(await screen.findByText('Aucun article')).toBeTruthy();
    expect(screen.queryByText(/supprimer/i)).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter un article' }));
    fireEvent.change(screen.getByPlaceholderText('Nom de l’article'), { target: { value: 'Compresses' } });
    fireEvent.change(screen.getByLabelText('Quantité'), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText("Seuil d'alerte"), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Unité'), { target: { value: 'paquets' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter' }));

    await waitFor(() => expect(mobileApiJson).toHaveBeenCalledWith('/stock/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nom: 'Compresses', categorie: 'CONSOMMABLE', quantite: 10, seuil_alerte: 4, unite: 'paquets',
      }),
    }));
    expect(await screen.findByText('Compresses')).toBeTruthy();
  });
});
