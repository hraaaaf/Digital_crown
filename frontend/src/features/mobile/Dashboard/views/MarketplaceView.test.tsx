import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import type { MarketplacePreviewData } from '../../../partnerMarketplace/usePartnerMarketplace';
import { MarketplaceView } from './MarketplaceView';

const preview: MarketplacePreviewData = {
  strategyPresets: [{ key: 'sent_commission_10', label: 'Commission', settlementBasis: 'SENT_TO_PARTNER', revenueModel: 'COMMISSION_PERCENT', commissionRate: 10, discountRate: 0, fixedFeeAmount: 0, description: 'Test' }],
  catalogMeta: { categories: ['Restauration', 'Endodontie'], specialties: ['Omnipratique'], availability: ['AVAILABLE'] },
  suppliers: [{ id: 11, supplierKey: 'atlas', name: 'Atlas', isActive: true, productCount: 2 }],
  products: [
    { id: '101', supplierId: '11', supplierName: 'Atlas', name: 'Composite universel', category: 'Restauration', specialty: 'Omnipratique', sku: 'CMP-101', unit: 'seringue', price: 390, availability: 'Disponible', description: 'Composite', longDescription: 'Composite', benefits: [] },
    { id: '102', supplierId: '11', supplierName: 'Atlas', name: 'Limes NiTi', category: 'Endodontie', specialty: 'Endodontie', sku: 'ENDO-22', unit: 'blister', price: 295, availability: 'Disponible', description: 'Limes', longDescription: 'Limes', benefits: [] },
  ],
  customer: { fullName: 'Dr Baseline', clinic: 'Cabinet Atlas', email: 'baseline@example.test', phone: '0600000000', city: 'Rabat' },
};

afterEach(() => cleanup());

describe('MarketplaceView', () => {
  it('searches by SKU, adds to cart and opens a prefilled DRAFT checkout', async () => {
    render(<MarketplaceView previewData={preview} />);

    expect(screen.getByRole('heading', { name: 'Marketplace' })).toBeTruthy();
    const search = screen.getByRole('searchbox', { name: 'Rechercher par nom ou SKU' });
    fireEvent.change(search, { target: { value: 'ENDO-22' } });
    expect(screen.getByText('Limes NiTi')).toBeTruthy();
    expect(screen.queryByText('Composite universel')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Ajouter une unité de Limes NiTi' }));
    expect(screen.getAllByText(/Panier · 1/).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir le panier, 1 unité' }));
    expect(screen.getByRole('dialog')).toBeTruthy();
    expect((screen.getByLabelText('Nom complet') as HTMLInputElement).value).toBe('Dr Baseline');
    expect((screen.getByLabelText('Cabinet') as HTMLInputElement).value).toBe('Cabinet Atlas');
    expect((screen.getByLabelText('Email') as HTMLInputElement).value).toBe('baseline@example.test');
    expect(screen.getByText(/Rien n’est transmis au fournisseur/)).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer le brouillon' }));
    expect(await screen.findByRole('status')).toHaveTextContent('Aucune donnée réelle n’a été envoyée');
  });
});
