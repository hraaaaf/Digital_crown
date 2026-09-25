import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PartnerCatalogAdminPage } from './PartnerCatalogAdminPage';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}));

const meta = {
  categories: ['Restauration'],
  specialties: ['Omnipratique'],
  availability: ['AVAILABLE', 'ON_REQUEST'],
};

const supplier = {
  id: 11,
  supplierKey: 'atlas',
  name: 'Atlas Dental',
  badge: 'Local',
  description: 'Supplier',
  promise: '24h',
  apiBaseUrl: null,
  syncMode: 'manual',
  isActive: true,
  productCount: 1,
};

const product = {
  id: 101,
  supplierId: 11,
  supplierName: 'Atlas Dental',
  externalProductId: 'P101',
  name: 'Composite universel',
  sku: 'CMP-101',
  dentalCategory: 'Restauration',
  dentalSpecialty: 'Omnipratique',
  unit: 'seringue',
  price: 390,
  availability: 'AVAILABLE',
  shortDescription: 'Composite test',
  longDescription: 'Long',
  benefits: ['Facile'],
  isFeatured: true,
  sortOrder: 1,
};

const order = {
  id: 55,
  orderNumber: 'CMD-055',
  partnerName: 'Atlas Dental',
  strategyLabel: 'Commission',
  status: 'DRAFT',
  estimatedTotal: 780,
  currentTotal: 780,
  recognizedRevenueAmount: 0,
  partnerReference: null,
  statusNote: null,
};

function installReads() {
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/partner-catalog/meta') return { data: meta } as never;
    if (url === '/partner-catalog/suppliers') return { data: [supplier] } as never;
    if (url === '/partner-catalog/products') return { data: [product] } as never;
    if (url === '/partner-orders') return { data: [order] } as never;
    if (url === '/partner-orders/meta') return { data: { supportedStatuses: ['DRAFT','CONFIRMED','FULFILLED','CANCELLED'] } } as never;
    throw new Error('unexpected GET '+url);
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  installReads();
  vi.mocked(api.post).mockResolvedValue({ data: {} } as never);
  vi.mocked(api.patch).mockResolvedValue({ data: {} } as never);
});
afterEach(() => cleanup());

async function renderPage() {
  render(<MemoryRouter><PartnerCatalogAdminPage /></MemoryRouter>);
  await screen.findByText('Composite universel');
}

describe('PartnerCatalogAdminPage G7 interactive matrix', () => {
  it('loads catalog and order truth from all canonical endpoints', async () => {
    await renderPage();
    for (const url of [
      '/partner-catalog/meta',
      '/partner-catalog/suppliers',
      '/partner-catalog/products',
      '/partner-orders',
      '/partner-orders/meta',
    ]) {
      expect(api.get).toHaveBeenCalledWith(url);
    }
    expect(screen.getByText('CMD-055')).toBeTruthy();
  });

  it('creates a supplier with normalized null/default fields and reloads catalog after ACK', async () => {
    await renderPage();
    const section = screen.getByText('Ajouter un fournisseur').closest('section')!;
    const scoped = within(section as HTMLElement);
    const textInputs = scoped.getAllByRole('textbox');
    fireEvent.change(textInputs[0], { target: { value: 'medix' } });
    fireEvent.change(textInputs[1], { target: { value: 'Medix Dental' } });

    const before = vi.mocked(api.get).mock.calls.filter(([url]) => url === '/partner-catalog/suppliers').length;
    fireEvent.click(scoped.getByRole('button', { name: 'Ajouter fournisseur' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/partner-catalog/suppliers', {
      supplierKey: 'medix',
      name: 'Medix Dental',
      badge: null,
      description: null,
      promise: null,
      apiBaseUrl: null,
      syncMode: 'manual',
      isActive: true,
    }));
    await waitFor(() => expect(
      vi.mocked(api.get).mock.calls.filter(([url]) => url === '/partner-catalog/suppliers').length,
    ).toBeGreaterThan(before));
    expect(screen.getByText('Fournisseur partenaire ajouté.')).toBeTruthy();
  });

  it('surfaces supplier creation refusal without false success', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({ response: { data: { detail: 'Clé fournisseur déjà utilisée' } } });
    await renderPage();
    const section = screen.getByText('Ajouter un fournisseur').closest('section')!;
    const scoped = within(section as HTMLElement);
    const inputs = scoped.getAllByRole('textbox');
    fireEvent.change(inputs[0], { target: { value: 'atlas' } });
    fireEvent.change(inputs[1], { target: { value: 'Duplicate' } });
    fireEvent.click(scoped.getByRole('button', { name: 'Ajouter fournisseur' }));

    expect(await screen.findByText('Clé fournisseur déjà utilisée')).toBeTruthy();
    expect(screen.queryByText('Fournisseur partenaire ajouté.')).toBeNull();
  });

  it('creates a product with numeric fields and newline-normalized benefits', async () => {
    await renderPage();
    const section = screen.getByText('Ajouter un produit').closest('section')!;
    const scoped = within(section as HTMLElement);
    const textboxes = scoped.getAllByRole('textbox');
    const selects = scoped.getAllByRole('combobox');
    const spinboxes = scoped.getAllByRole('spinbutton');

    fireEvent.change(selects[0], { target: { value: '11' } });
    fireEvent.change(textboxes[0], { target: { value: 'EXT-9' } });
    fireEvent.change(textboxes[1], { target: { value: 'Gants premium' } });
    fireEvent.change(textboxes[2], { target: { value: 'GLV-9' } });
    fireEvent.change(selects[1], { target: { value: 'Restauration' } });
    fireEvent.change(selects[2], { target: { value: 'Omnipratique' } });
    fireEvent.change(textboxes[3], { target: { value: 'boite' } });
    fireEvent.change(spinboxes[0], { target: { value: '125.5' } });
    fireEvent.change(selects[3], { target: { value: 'AVAILABLE' } });
    fireEvent.change(spinboxes[1], { target: { value: '4' } });

    const areas = scoped.getAllByRole('textbox').filter(el => el.tagName === 'TEXTAREA');
    fireEvent.change(areas[0], { target: { value: 'Court' } });
    fireEvent.change(areas[1], { target: { value: 'Longue' } });
    fireEvent.change(areas[2], { target: { value: 'Sans latex\nConfort\n  ' } });

    const checkbox = scoped.getByRole('checkbox');
    fireEvent.click(checkbox);
    fireEvent.click(scoped.getByRole('button', { name: 'Ajouter produit' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/partner-catalog/products', expect.objectContaining({
      supplierId: 11,
      externalProductId: 'EXT-9',
      name: 'Gants premium',
      sku: 'GLV-9',
      dentalCategory: 'Restauration',
      dentalSpecialty: 'Omnipratique',
      unit: 'boite',
      price: 125.5,
      availability: 'AVAILABLE',
      shortDescription: 'Court',
      longDescription: 'Longue',
      benefits: ['Sans latex','Confort'],
      isFeatured: true,
      sortOrder: 4,
    })));
    expect(await screen.findByText('Produit partenaire ajouté.')).toBeTruthy();
  });

  it('filters catalog locally without backend mutation', async () => {
    await renderPage();
    const section = screen.getByText('Catalogue fournisseur').closest('section')!;
    const scoped = within(section as HTMLElement);
    const inputs = scoped.getAllByRole('textbox');
    fireEvent.change(inputs[0], { target: { value: 'absent' } });
    expect(screen.getByText('Aucun produit ne correspond aux filtres')).toBeTruthy();
    expect(api.post).not.toHaveBeenCalled();
    expect(api.patch).not.toHaveBeenCalled();
  });

  it('reconciles partner order with exact status/total/note/reference payload then reloads order truth', async () => {
    await renderPage();
    const card = screen.getByText('CMD-055').closest('div.border')!;
    const scoped = within(card as HTMLElement);
    const selects = scoped.getAllByRole('combobox');
    const inputs = scoped.getAllByRole('textbox');
    const number = scoped.getByRole('spinbutton');

    fireEvent.change(selects[0], { target: { value: 'CONFIRMED' } });
    fireEvent.change(number, { target: { value: '750' } });
    fireEvent.change(inputs[0], { target: { value: 'REF-77' } });
    fireEvent.change(inputs[1], { target: { value: 'Confirmé par fournisseur' } });

    const before = vi.mocked(api.get).mock.calls.filter(([url]) => url === '/partner-orders').length;
    fireEvent.click(scoped.getByRole('button', { name: 'Enregistrer les modifications' }));

    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/partner-orders/55', {
      status: 'CONFIRMED',
      currentTotal: 750,
      note: 'Confirmé par fournisseur',
      partnerReference: 'REF-77',
    }));
    await waitFor(() => expect(
      vi.mocked(api.get).mock.calls.filter(([url]) => url === '/partner-orders').length
    ).toBeGreaterThan(before));
    expect(await screen.findByText(/Commande CMD-055 mise à jour/i)).toBeTruthy();
  });

  it('keeps reconciliation state visible and surfaces backend detail on refusal', async () => {
    vi.mocked(api.patch).mockRejectedValueOnce({ response: { data: { detail: 'Transition de statut refusée' } } });
    await renderPage();
    const card = screen.getByText('CMD-055').closest('div.border')!;
    const scoped = within(card as HTMLElement);

    fireEvent.click(scoped.getByRole('button', { name: 'Enregistrer les modifications' }));

    expect(await screen.findByText('Transition de statut refusée')).toBeTruthy();
    expect(screen.getByText('CMD-055')).toBeTruthy();
  });

  it('explicit Recharger refetches both catalog and partner orders', async () => {
    await renderPage();
    const before = vi.mocked(api.get).mock.calls.length;
    fireEvent.click(screen.getAllByRole('button', { name: 'Recharger' })[0]);
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThan(before));
  });
});
