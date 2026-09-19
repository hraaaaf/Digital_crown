import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PartnerSupplierPage } from './PartnerSupplierPage';
import { PartnerProductPage } from './PartnerProductPage';
import { api } from '../services/api';

const data = vi.hoisted(() => ({
  cache: null as any,
  cart: {} as Record<string,number>,
  writeCart: vi.fn(),
  writeCache: vi.fn(),
}));

vi.mock('../services/api', () => ({ api: { get: vi.fn() } }));
vi.mock('../stores/useAuthStore', () => ({
  useAuthStore: (selector:any) => selector({ user:{ id:7, employer_id:null, role:'ADMIN' } }),
}));

const normalized = {
  id:'101', supplierId:'11', supplierName:'Atlas Dental', name:'Composite universel',
  category:'Restauration', specialty:'Omnipratique', sku:'CMP-101', unit:'seringue',
  price:390, availability:'Disponible', description:'Composite test', longDescription:'Longue description',
  benefits:['Résistant'], audience:'Cabinet', isFeatured:true, sortOrder:1,
};
const stopped = { ...normalized, id:'102', sku:'OLD-102', name:'Produit arrêté', availability:'Discontinué' };

vi.mock('../features/partnerMarketplace/data', () => ({
  partnerCategories:['Toutes','Restauration'],
  readMarketplaceCache: () => data.cache,
  writeMarketplaceCache: (...args:any[]) => data.writeCache(...args),
  readStoredCart: () => data.cart,
  writeStoredCart: (cart:any) => { data.cart={...cart}; data.writeCart(cart); },
  normalizePartnerProduct: (raw:any) => raw.id===102 || raw.id==='102' ? stopped : normalized,
  buildPartnerProfile: (supplier:any) => ({
    id: supplier?.id || '11',
    name: supplier?.name || 'Atlas Dental',
    badge:'Partenaire',
    description:'Description fournisseur',
    promise:'Livraison fiable',
    metrics:[],
    coverage:[],
    logistics:[],
    sections:[],
  }),
  buildPartnerProductTemplate: () => ({
    summary:'Résumé premium',
    clinicalApplications:['Application'],
    whatsIncluded:['Inclus'],
    technicalSpecs:[['SKU','CMP-101']],
    assurances:['Traçabilité'],
  }),
  formatMoney: (n:number) => n+' MAD',
  availabilityBadgeClass: () => 'badge',
}));

const supplier={ id:11, supplierKey:'atlas', name:'Atlas Dental', isActive:true, productCount:2 };
const meta={ categories:['Restauration','Endodontie'], specialties:['Omnipratique','Endodontie'], availability:['AVAILABLE'] };

beforeEach(()=>{
  vi.clearAllMocks();
  data.cache=null; data.cart={};
  vi.mocked(api.get).mockImplementation(async(url:string)=>{
    if(url==='/partner-catalog/meta') return {data:meta} as never;
    if(url==='/partner-catalog/suppliers') return {data:[supplier]} as never;
    if(url==='/partner-catalog/products') return {data:[{id:101},{id:102}]} as never;
    if(url==='/partner-catalog/products/101') return {data:{id:101}} as never;
    if(url==='/partner-catalog/products/102') return {data:{id:102}} as never;
    if(url==='/partner-catalog/suppliers/11') return {data:supplier} as never;
    throw new Error('unexpected GET '+url);
  });
});
afterEach(()=>cleanup());

function supplierPage(){
 return render(<MemoryRouter initialEntries={['/approvisionnement/partenaire/11']}><Routes>
  <Route path="/approvisionnement/partenaire/:partnerId" element={<PartnerSupplierPage/>}/>
  <Route path="/approvisionnement/produits/:productId" element={<div>Product destination</div>}/>
  <Route path="/approvisionnement" element={<div>Marketplace destination</div>}/>
 </Routes></MemoryRouter>);
}
function productPage(id='101'){
 return render(<MemoryRouter initialEntries={['/approvisionnement/produits/'+id]}><Routes>
  <Route path="/approvisionnement/produits/:productId" element={<PartnerProductPage/>}/>
  <Route path="/approvisionnement" element={<div>Marketplace destination</div>}/>
  <Route path="/approvisionnement/partenaire/:partnerId" element={<div>Supplier destination</div>}/>
 </Routes></MemoryRouter>);
}

describe('Partner detail pages G7 interactive matrix',()=>{
 it('loads supplier truth, filters locally and opens a product detail',async()=>{
   supplierPage();
   expect(await screen.findByText('Composite universel')).toBeTruthy();
   expect(api.get).toHaveBeenCalledWith('/partner-catalog/meta');
   expect(api.get).toHaveBeenCalledWith('/partner-catalog/suppliers');
   expect(api.get).toHaveBeenCalledWith('/partner-catalog/products');

   fireEvent.click(screen.getByRole('button',{name:'Endodontie'}));
   expect(screen.getByText(/Aucun produit ne correspond/i)).toBeTruthy();
   fireEvent.click(screen.getByRole('button',{name:'Réinitialiser les filtres'}));
   expect(screen.getByText('Composite universel')).toBeTruthy();

   fireEvent.click(screen.getByText('Composite universel').closest('a')!);
   expect(await screen.findByText('Product destination')).toBeTruthy();
 });

 it('shows supplier load failure separately and retries',async()=>{
   vi.mocked(api.get).mockRejectedValue(new Error('down'));
   supplierPage();
   expect(await screen.findByText(/Impossible de charger le catalogue de ce fournisseur/i)).toBeTruthy();
   const before=vi.mocked(api.get).mock.calls.length;
   fireEvent.click(screen.getByRole('button',{name:'Réessayer'}));
   await waitFor(()=>expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThan(before));
 });

 it('explicit supplier Recharger performs a fresh canonical load',async()=>{
   supplierPage();
   await screen.findByText('Composite universel');
   const before=vi.mocked(api.get).mock.calls.length;
   fireEvent.click(screen.getByRole('button',{name:'Recharger'}));
   await waitFor(()=>expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThan(before));
 });

 it('loads product and persists plus/minus quantity into shared cart storage',async()=>{
   productPage('101');
   expect(await screen.findByText('Composite universel')).toBeTruthy();
   expect(api.get).toHaveBeenCalledWith('/partner-catalog/products/101');
   expect(api.get).toHaveBeenCalledWith('/partner-catalog/suppliers/11');

   const buttons=screen.getAllByRole('button');
   const plus=buttons.find(b=>b.querySelector('svg') && b.className.includes('text-white'))!;
   fireEvent.click(plus);
   await waitFor(()=>expect(data.writeCart).toHaveBeenCalledWith({'101':1}));
   expect(screen.getByText('1 dans le panier')).toBeTruthy();

   const minus=screen.getAllByRole('button').find(b=>b!==plus && b.querySelector('svg') && b.className.includes('border'))!;
   fireEvent.click(minus);
   await waitFor(()=>expect(data.writeCart).toHaveBeenCalledWith({}));
 });

 it('never exposes quantity controls for a discontinued product',async()=>{
   productPage('102');
   expect(await screen.findByText('Produit arrêté')).toBeTruthy();
   expect(screen.getByText(/ne peut plus être commandé/i)).toBeTruthy();
   expect(screen.queryByText('Retourner à la commande partenaire')).toBeNull();
 });

 it('shows explicit product-unavailable state and returns to catalog when no cache/API truth exists',async()=>{
   vi.mocked(api.get).mockRejectedValue(new Error('down'));
   productPage('101');
   expect(await screen.findByText('Produit introuvable.')).toBeTruthy();
   fireEvent.click(screen.getByRole('button',{name:'Revenir au catalogue'}));
   expect(await screen.findByText('Marketplace destination')).toBeTruthy();
 });
});
