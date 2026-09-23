import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PartnerMarketplacePage } from './PartnerMarketplacePage';

const s = vi.hoisted(() => ({
  totalUnits: 2,
  estimatedTotal: 780,
  search: '',
  availableOnly: false,
  category: 'Toutes',
  categoryOptions: ['Toutes','Restauration'],
  catalogLoading: false,
  catalogError: false,
  products: [] as any[],
  filteredProducts: [] as any[],
  cart: { '101': 2 } as Record<string,number>,
  cartLines: [] as any[],
  customer: { fullName:'Dr Test', clinic:'Cabinet Test', phone:'0600000000', email:'test@example.com', city:'Rabat', note:'' },
  submitting: false,
  successMessage: '',
  errorMessage: '',
  previewMode: false,
  setSearch: vi.fn(),
  setAvailableOnly: vi.fn(),
  setCategory: vi.fn(),
  adjustQty: vi.fn(),
  loadCatalog: vi.fn(),
  updateCustomer: vi.fn(),
  submitDraft: vi.fn(),
}));

vi.mock('../features/partnerMarketplace/usePartnerMarketplace', () => ({
  usePartnerMarketplace: () => s,
}));

const product = {
  id:'101', name:'Composite universel', sku:'CMP-101', category:'Restauration',
  specialty:'Omnipratique', price:390, unit:'seringue', availability:'Disponible',
  description:'Composite', supplierId:'11', supplierName:'Atlas Dental', benefits:[], isFeatured:true, sortOrder:1,
};

beforeEach(() => {
  vi.clearAllMocks();
  s.totalUnits=2; s.estimatedTotal=780; s.search=''; s.availableOnly=false; s.category='Toutes';
  s.catalogLoading=false; s.catalogError=false; s.products=[product]; s.filteredProducts=[product];
  s.cart={'101':2}; s.cartLines=[{...product,quantity:2,lineTotal:780}];
  s.submitting=false; s.successMessage=''; s.errorMessage=''; s.previewMode=false;
  s.submitDraft.mockResolvedValue(true);
});
afterEach(()=>cleanup());

function renderPage(){ return render(<MemoryRouter><PartnerMarketplacePage /></MemoryRouter>); }

describe('PartnerMarketplacePage G7 visible controls',()=>{
  it('delegates search, refresh, availability and category filters',()=>{
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('Nom, référence ou SKU…'),{target:{value:'CMP'}});
    expect(s.setSearch).toHaveBeenCalledWith('CMP');
    fireEvent.click(screen.getByRole('button',{name:'Actualiser'}));
    expect(s.loadCatalog).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button',{name:'Disponibles'}));
    expect(s.setAvailableOnly).toHaveBeenCalledWith(true);
    fireEvent.click(screen.getByRole('button',{name:'Restauration'}));
    expect(s.setCategory).toHaveBeenCalledWith('Restauration');
  });

  it('delegates plus/minus quantity controls to the canonical controller',()=>{
    renderPage();
    fireEvent.click(screen.getByRole('button',{name:'Ajouter une unité de Composite universel'}));
    expect(s.adjustQty).toHaveBeenCalledWith(product,1);
    fireEvent.click(screen.getByRole('button',{name:'Retirer une unité de Composite universel'}));
    expect(s.adjustQty).toHaveBeenCalledWith(product,-1);
  });

  it('opens checkout only with a non-empty cart and closes explicitly',()=>{
    renderPage();
    fireEvent.click(screen.getByRole('button',{name:/Ouvrir le panier, 2 unités/i}));
    expect(screen.getByRole('dialog',{name:/Préparer le brouillon/i})).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Fermer'}));
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('delegates customer edits and submits draft, closing only on real success',async()=>{
    renderPage();
    fireEvent.click(screen.getByRole('button',{name:/Ouvrir le panier, 2 unités/i}));
    const phone=screen.getByDisplayValue('0600000000');
    fireEvent.change(phone,{target:{value:'0611111111'}});
    expect(s.updateCustomer).toHaveBeenCalledWith('phone','0611111111');

    fireEvent.click(screen.getByRole('button',{name:'Enregistrer le brouillon'}));
    await waitFor(()=>expect(s.submitDraft).toHaveBeenCalledTimes(1));
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('keeps checkout open when draft submission is refused',async()=>{
    s.submitDraft.mockResolvedValueOnce(false);
    renderPage();
    fireEvent.click(screen.getByRole('button',{name:/Ouvrir le panier, 2 unités/i}));
    fireEvent.click(screen.getByRole('button',{name:'Enregistrer le brouillon'}));
    await waitFor(()=>expect(s.submitDraft).toHaveBeenCalledTimes(1));
    expect(screen.getByRole('dialog',{name:/Préparer le brouillon/i})).toBeTruthy();
  });

  it('renders catalog failure separately from empty catalog and retries',()=>{
    s.catalogError=true; s.products=[]; s.filteredProducts=[]; s.cart={}; s.cartLines=[]; s.totalUnits=0; s.estimatedTotal=0;
    renderPage();
    expect(screen.getByText('Catalogue indisponible')).toBeTruthy();
    expect(screen.queryByText('Aucun produit publié')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Réessayer'}));
    expect(s.loadCatalog).toHaveBeenCalledTimes(1);
  });

  it('disables cart entry when cart is empty',()=>{
    s.totalUnits=0; s.cart={}; s.cartLines=[]; s.estimatedTotal=0;
    renderPage();
    expect((screen.getByRole('button',{name:/Ouvrir le panier, 0 unité/i}) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole('button',{name:'Préparer le brouillon'}) as HTMLButtonElement).disabled).toBe(true);
  });
});
