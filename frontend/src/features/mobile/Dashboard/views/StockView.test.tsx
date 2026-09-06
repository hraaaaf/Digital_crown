import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { StockView } from './StockView';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
    patch: vi.fn(),
    post: vi.fn(),
  },
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
  it('loads the shared stock endpoint and exposes rupture/alert/search contracts', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: items } as any);
    render(<StockView />);

    expect(await screen.findByText('Gants nitrile M')).toBeTruthy();
    expect(api.get).toHaveBeenCalledWith('/stock/items');
    expect(screen.getByText('Composite universel')).toBeTruthy();
    expect(screen.getByText('Masques')).toBeTruthy();

    fireEvent.click(screen.getByText('À traiter'));
    expect(screen.getByText('Gants nitrile M')).toBeTruthy();
    expect(screen.getByText('Composite universel')).toBeTruthy();
    expect(screen.queryByText('Masques')).toBeNull();

    fireEvent.click(screen.getByText('Tous'));
    fireEvent.change(screen.getByPlaceholderText('Rechercher un article…'), { target: { value: 'Fournisseur test' } });
    expect(screen.getByText('Gants nitrile M')).toBeTruthy();
    expect(screen.queryByText('Composite universel')).toBeNull();
  });

  it('persists +1 and never exposes a decrement below zero', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: items } as any);
    vi.mocked(api.patch).mockResolvedValue({ data: { ...items[1], quantite: 3, alerte: true } } as any);
    render(<StockView />);

    expect(await screen.findByText('Composite universel')).toBeTruthy();
    const ruptureMinus = screen.getByRole('button', { name: 'Retirer une boîtes de Gants nitrile M' });
    expect(ruptureMinus.hasAttribute('disabled')).toBe(true);

    fireEvent.click(screen.getByRole('button', { name: 'Ajouter une seringues à Composite universel' }));
    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/stock/items/2', { quantite: 3 }));
  });

  it('creates a quick item with the existing stock API and no delete action', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] } as any);
    vi.mocked(api.post).mockResolvedValue({ data: { id: 9, nom: 'Compresses', categorie: 'CONSOMMABLE', quantite: 10, seuil_alerte: 4, unite: 'paquets', alerte: false } } as any);
    render(<StockView />);

    expect(await screen.findByText('Aucun article')).toBeTruthy();
    expect(screen.queryByText(/supprimer/i)).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter un article' }));
    fireEvent.change(screen.getByPlaceholderText('Nom de l’article'), { target: { value: 'Compresses' } });
    fireEvent.change(screen.getByLabelText('Quantité'), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText("Seuil d'alerte"), { target: { value: '4' } });
    fireEvent.change(screen.getByLabelText('Unité'), { target: { value: 'paquets' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/stock/items', {
      nom: 'Compresses', categorie: 'CONSOMMABLE', quantite: 10, seuil_alerte: 4, unite: 'paquets',
    }));
    expect(await screen.findByText('Compresses')).toBeTruthy();
  });
});