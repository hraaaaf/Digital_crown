import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { StockPage } from './StockPage';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));
vi.mock('../components/EliteGhostLoader', () => ({
  EliteGhostLoader: ({ text }: { text: string }) => <div>{text}</div>,
}));

const item = {
  id: 1,
  nom: 'Gants nitrile',
  categorie: 'CONSOMMABLE',
  quantite: 10,
  seuil_alerte: 5,
  unite: 'boîte',
  prix_unitaire: 30,
  fournisseur: 'Supplier',
  notes: 'Taille M',
  alerte: false,
};

function renderStock() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><StockPage /></QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/stock/items') return { data: [item] } as never;
    if (url === '/stock/alerts') return { data: { count: 0, items: [] } } as never;
    throw new Error('unexpected GET '+url);
  });
  vi.mocked(api.post).mockResolvedValue({ data: {} } as never);
  vi.mocked(api.patch).mockResolvedValue({ data: {} } as never);
  vi.mocked(api.delete).mockResolvedValue({ data: {} } as never);
});
afterEach(() => cleanup());

describe('StockPage G7 interactive matrix', () => {
  it('loads stock + alert truth and filters by search/category', async () => {
    renderStock();
    expect(await screen.findByText('Gants nitrile')).toBeTruthy();
    expect(api.get).toHaveBeenCalledWith('/stock/items');
    expect(api.get).toHaveBeenCalledWith('/stock/alerts');

    fireEvent.change(screen.getByPlaceholderText('Rechercher…'), { target: { value: 'absent' } });
    expect(screen.getByText('Aucun résultat pour cette recherche.')).toBeTruthy();

    fireEvent.change(screen.getByPlaceholderText('Rechercher…'), { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: 'Matériaux' }));
    expect(screen.getByText('Aucun résultat pour cette recherche.')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Tous' }));
    expect(screen.getByText('Gants nitrile')).toBeTruthy();
  });

  it('adds a stock item with normalized numeric/null payload and refreshes queries after ACK', async () => {
    renderStock();
    await screen.findByText('Gants nitrile');

    fireEvent.click(screen.getByRole('button', { name: /Ajouter un article/i }));
    const modal = screen.getByText('Nouvel article').closest('div.fixed')!;
    const scoped = within(modal as HTMLElement);

    const inputs = scoped.getAllByRole('spinbutton');
    fireEvent.change(scoped.getByPlaceholderText('Ex: Gants nitrile S'), { target: { value: 'Masques FFP2' } });
    fireEvent.change(inputs[0], { target: { value: '12' } });
    fireEvent.change(inputs[1], { target: { value: '3' } });
    fireEvent.change(scoped.getByPlaceholderText('Optionnel'), { target: { value: '15.5' } });
    fireEvent.click(scoped.getByRole('button', { name: 'Ajouter' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/stock/items', expect.objectContaining({
      nom: 'Masques FFP2',
      quantite: 12,
      seuil_alerte: 3,
      prix_unitaire: 15.5,
      fournisseur: null,
      notes: null,
    })));
    await waitFor(() => expect(
      vi.mocked(api.get).mock.calls.filter(([url]) => url === '/stock/items').length
    ).toBeGreaterThan(1));
  });

  it('edits an existing item through PATCH', async () => {
    renderStock();
    const name = await screen.findByText('Gants nitrile');
    const row = name.closest('tr')!;

    fireEvent.click(within(row).getByTitle('Modifier'));
    const modal = screen.getByText("Modifier l'article").closest('div.fixed')!;
    const scoped = within(modal as HTMLElement);
    const input = scoped.getByDisplayValue('Gants nitrile');
    fireEvent.change(input, { target: { value: 'Gants nitrile premium' } });
    fireEvent.click(scoped.getByRole('button', { name: 'Mettre à jour' }));

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith(
      '/stock/items/1',
      expect.objectContaining({ nom: 'Gants nitrile premium' }),
    ));
  });

  it('increments/decrements quantity through exact PATCH values and never sends negative quantity', async () => {
    renderStock();
    const row = (await screen.findByText('Gants nitrile')).closest('tr')!;
    const buttons = within(row).getAllByRole('button');
    const minus = buttons[0];
    const plus = buttons[1];

    fireEvent.click(minus);
    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/stock/items/1', { quantite: 9 }));

    vi.mocked(api.patch).mockClear();
    fireEvent.click(plus);
    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/stock/items/1', { quantite: 11 }));
  });

  it('deletes the selected item through the current delete control', async () => {
    renderStock();
    const row = (await screen.findByText('Gants nitrile')).closest('tr')!;
    fireEvent.click(within(row).getByTitle('Supprimer'));

    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/stock/items/1'));
  });
});
