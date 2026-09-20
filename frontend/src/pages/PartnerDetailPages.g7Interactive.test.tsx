import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PartnerSupplierPage } from './PartnerSupplierPage';
import { PartnerProductPage } from './PartnerProductPage';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: { get: vi.fn() },
}));

vi.mock('../stores/useAuthStore', () => ({
  useAuthStore: (selector: (state: any) => unknown) =>
    selector({ user: { id: '77', employer_id: 10, role: 'DENTISTE', email: 'dentist@example.test' } }),
}));

const supplier = {
  id: 11,
  supplierKey: 'atlas',
  name: 'Atlas Dental',
  badge: 'Local',
  description: 'Fournisseur test',
  promise: '24h',
  apiBaseUrl: null,
  syncMode: 'manual',
  isActive: true,
  productCount: 2,
};

const rawProducts = [
  {
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
    longDescription: 'Composite test long',
    benefits: ['Facile'],
    isFeatured: true,
    sortOrder: 1,
  },
  {
    id: 102,
    supplierId: 11,
    supplierName: 'Atlas Dental',
    externalProductId: 'P102',
    name: 'Produit arrêté',
    sku: 'OLD-102',
    dentalCategory: 'Endodontie',
    dentalSpecialty: 'Endodontie',
    unit: 'boîte',
    price: 100,
    availability: 'DISCONTINUED',
    shortDescription: 'Ancien',
    longDescription: 'Ancien produit',
    benefits: [],
    isFeatured: false,
    sortOrder: 2,
  },
];

const meta = {
  categories: ['Restauration', 'Endodontie'],
  specialties: ['Omnipratique', 'Endodontie'],
  availability: ['AVAILABLE', 'DISCONTINUED'],
};

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/partner-catalog/meta') return { data: meta } as never;
    if (url === '/partner-catalog/suppliers') return { data: [supplier] } as never;
    if (url === '/partner-catalog/products') return { data: rawProducts } as never;
    if (url === '/partner-catalog/products/101') return { data: rawProducts[0] } as never;
    if (url === '/partner-catalog/products/102') return { data: rawProducts[1] } as never;
    if (url === '/partner-catalog/suppliers/11') return { data: supplier } as never;
    throw new Error('unexpected GET ' + url);
  });
});

afterEach(() => cleanup());

function renderSupplier() {
  return render(
    <MemoryRouter initialEntries={['/approvisionnement/partenaire/11']}>
      <Routes>
        <Route path="/approvisionnement/partenaire/:partnerId" element={<PartnerSupplierPage />} />
        <Route path="/approvisionnement/produits/:productId" element={<div>Product destination</div>} />
        <Route path="/approvisionnement" element={<div>Marketplace destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function renderProduct(id = '101') {
  return render(
    <MemoryRouter initialEntries={[`/approvisionnement/produits/${id}`]}>
      <Routes>
        <Route path="/approvisionnement/produits/:productId" element={<PartnerProductPage />} />
        <Route path="/approvisionnement/partenaire/:partnerId" element={<div>Supplier destination</div>} />
        <Route path="/approvisionnement" element={<div>Marketplace destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('Partner detail pages G7 interactive matrix', () => {
  it('loads supplier/meta/products truth and reloads explicitly', async () => {
    renderSupplier();

    expect(await screen.findByRole('heading', { name: 'Atlas Dental', level: 1 })).toBeTruthy();
    expect(screen.getByRole('link', { name: /Composite universel/i })).toBeTruthy();
    for (const url of ['/partner-catalog/meta','/partner-catalog/suppliers','/partner-catalog/products']) {
      expect(api.get).toHaveBeenCalledWith(url);
    }

    const before = vi.mocked(api.get).mock.calls.length;
    fireEvent.click(screen.getByRole('button', { name: 'Recharger' }));
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThan(before));
  });

  it('filters supplier products by category and specialty without mutation', async () => {
    renderSupplier();
    await screen.findByRole('link', { name: /Composite universel/i });

    fireEvent.click(screen.getAllByRole('button', { name: 'Endodontie' })[0]);
    expect(screen.getByRole('link', { name: /Produit arrêté/i })).toBeTruthy();
    expect(screen.queryByRole('link', { name: /Composite universel/i })).toBeNull();

    const omnicontrol = screen.getByRole('button', { name: 'Omnipratique' });
    fireEvent.click(omnicontrol);
    expect(screen.getByText(/Aucun produit ne correspond/i)).toBeTruthy();
  });

  it('opens the exact product deep-link from supplier catalog', async () => {
    renderSupplier();
    const link = await screen.findByRole('link', { name: /Composite universel/i });
    expect(link.getAttribute('href')).toBe('/approvisionnement/produits/101');

    fireEvent.click(link);
    expect(await screen.findByText('Product destination')).toBeTruthy();
  });

  it('loads product + supplier truth, persists quantity and exposes canonical navigation links', async () => {
    renderProduct('101');

    expect(await screen.findByRole('heading', { name: 'Composite universel' })).toBeTruthy();
    expect(api.get).toHaveBeenCalledWith('/partner-catalog/products/101');
    expect(api.get).toHaveBeenCalledWith('/partner-catalog/suppliers/11');

    const cartBox = screen.getByText('Ajout au panier').parentElement!;
    const quantityButtons = within(cartBox).getAllByRole('button');
    fireEvent.click(quantityButtons[1]);

    await waitFor(() => {
      const values = Array.from({ length: localStorage.length }, (_, i) => localStorage.getItem(localStorage.key(i)!));
      expect(values.some(v => v?.includes('"101":1'))).toBe(true);
    });

    expect(screen.getByRole('link', { name: /Retour catalogue/i }).getAttribute('href')).toBe('/approvisionnement');
    expect(screen.getByRole('link', { name: /Voir fournisseur/i }).getAttribute('href')).toBe('/approvisionnement/partenaire/11');
  });

  it('never exposes quantity controls for a discontinued product', async () => {
    renderProduct('102');

    expect(await screen.findByRole('heading', { name: 'Produit arrêté' })).toBeTruthy();
    expect(screen.getByText(/ne peut plus être commandé/i)).toBeTruthy();
    expect(screen.queryByText('Retourner à la commande partenaire')).toBeNull();
  });

  it('shows not-found truth and returns to marketplace when product load fails without cache', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('missing'));
    renderProduct('999');

    expect(await screen.findByText('Produit introuvable.')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Revenir au catalogue' }));
    expect(await screen.findByText('Marketplace destination')).toBeTruthy();
  });
});
