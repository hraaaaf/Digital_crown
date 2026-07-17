import type { AppUser } from '../../types';

export type PartnerProductCategory = string;

export type PartnerProduct = {
  id: string;
  supplierId?: string;
  supplierName?: string;
  name: string;
  category: PartnerProductCategory;
  specialty?: string;
  sku: string;
  unit: string;
  price: number;
  originalPrice?: number;
  availability: 'Disponible' | 'Sur commande' | 'Discontinué';
  description: string;
  longDescription: string;
  benefits: string[];
  audience?: string;
  imageUrl?: string;
  gallery?: string[];
};

export type PartnerProfile = {
  id: string;
  name: string;
  badge: string;
  description: string;
  promise: string;
  coverage: string[];
  logistics: string[];
  support: string[];
  heroImageUrl?: string;
};

export type PartnerCatalogSupplier = {
  id: number;
  supplierKey: string;
  name: string;
  badge?: string | null;
  description?: string | null;
  promise?: string | null;
  apiBaseUrl?: string | null;
  syncMode?: string | null;
  isActive: boolean;
  productCount: number;
};

export type PartnerCatalogProduct = {
  id: number;
  supplierId: number;
  supplierName?: string | null;
  externalProductId?: string | null;
  name: string;
  sku: string;
  dentalCategory: string;
  dentalSpecialty: string;
  unit: string;
  price: number;
  availability: string;
  shortDescription?: string | null;
  longDescription?: string | null;
  benefits: string[];
  isFeatured: boolean;
  sortOrder: number;
};

export const STORAGE_CART_KEY = 'digitalcrown_partner_cart_v1';
const STORAGE_MARKETPLACE_CACHE_PREFIX = 'digitalcrown_partner_marketplace_cache_v1';

export type CartState = Record<string, number>;
export type PartnerMarketplaceStrategyPreset = {
  key: string;
  label: string;
  settlementBasis: string;
  revenueModel: string;
  commissionRate: number;
  discountRate: number;
  fixedFeeAmount: number;
  description: string;
};

export type PartnerMarketplaceCatalogMeta = {
  categories: string[];
  specialties: string[];
  availability: string[];
};

export type PartnerMarketplaceCache = {
  version: 1;
  scopeKey: string;
  syncedAt: string;
  strategyPresets: PartnerMarketplaceStrategyPreset[];
  catalogMeta: PartnerMarketplaceCatalogMeta | null;
  suppliers: PartnerCatalogSupplier[];
  products: PartnerProduct[];
};

const noActiveSupplierProfile: PartnerProfile = {
  id: 'aucun-fournisseur',
  name: 'Aucun fournisseur actif',
  badge: 'Configuration requise',
  description: "Aucun fournisseur partenaire n'est encore configuré pour ce cabinet.",
  promise: "Une fois un fournisseur ajouté depuis le dashboard administrateur, son catalogue apparaîtra ici pour vos commandes.",
  coverage: [],
  logistics: [],
  support: [],
};

export const partnerCategories = ['Toutes', 'Consommables', 'Restauration', 'Endodontie', 'Instrumentation'] as const;

const buildSvgDataUri = (svg: string) => `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;

const getCategoryPalette = (category: string) => {
  const normalized = category.toLowerCase();
  if (normalized.includes('endo')) {
    return { primary: '#0f766e', secondary: '#99f6e4', accent: '#134e4a', text: '#ecfeff' };
  }
  if (normalized.includes('restauration')) {
    return { primary: '#1d4ed8', secondary: '#bfdbfe', accent: '#1e3a8a', text: '#eff6ff' };
  }
  if (normalized.includes('instrument')) {
    return { primary: '#7c3aed', secondary: '#ddd6fe', accent: '#4c1d95', text: '#f5f3ff' };
  }
  return { primary: '#ea580c', secondary: '#fed7aa', accent: '#9a3412', text: '#fff7ed' };
};

const buildProductImage = (
  product: Pick<PartnerProduct, 'name' | 'category' | 'sku'>,
  variant: 'hero' | 'detail' | 'card' = 'card'
) => {
  const palette = getCategoryPalette(product.category);
  const aspectHeight = variant === 'hero' ? 760 : variant === 'detail' ? 640 : 420;
  const badgeLabel = product.category.slice(0, 22);
  const title = product.name.slice(0, 34);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="${aspectHeight}" viewBox="0 0 1200 ${aspectHeight}">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${palette.primary}" />
          <stop offset="100%" stop-color="${palette.accent}" />
        </linearGradient>
        <linearGradient id="panel" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="rgba(255,255,255,0.14)" />
          <stop offset="100%" stop-color="rgba(255,255,255,0.04)" />
        </linearGradient>
      </defs>
      <rect width="1200" height="${aspectHeight}" fill="url(#bg)" rx="42" />
      <circle cx="1010" cy="132" r="180" fill="rgba(255,255,255,0.12)" />
      <circle cx="155" cy="${aspectHeight - 120}" r="146" fill="rgba(255,255,255,0.08)" />
      <rect x="74" y="72" width="1052" height="${aspectHeight - 144}" rx="34" fill="url(#panel)" stroke="rgba(255,255,255,0.18)" />
      <rect x="118" y="118" width="210" height="52" rx="26" fill="${palette.secondary}" fill-opacity="0.92" />
      <text x="223" y="151" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="${palette.accent}">${badgeLabel}</text>
      <text x="118" y="${variant === 'card' ? 254 : 286}" font-family="Arial, sans-serif" font-size="${variant === 'card' ? 54 : 66}" font-weight="800" fill="${palette.text}">${title}</text>
      <text x="118" y="${variant === 'card' ? 308 : 352}" font-family="Arial, sans-serif" font-size="26" font-weight="600" fill="rgba(255,255,255,0.84)">Ref. ${product.sku}</text>
      <g transform="translate(812, ${variant === 'card' ? 122 : 138})">
        <rect x="0" y="0" width="220" height="220" rx="48" fill="rgba(255,255,255,0.18)" />
        <rect x="28" y="28" width="164" height="164" rx="34" fill="rgba(255,255,255,0.18)" />
        <path d="M108 54c31 0 56 25 56 56v48c0 31-25 56-56 56s-56-25-56-56v-48c0-31 25-56 56-56Z" fill="${palette.secondary}" fill-opacity="0.92" />
        <path d="M108 72c17 0 30 13 30 30v18c0 17-13 30-30 30s-30-13-30-30v-18c0-17 13-30 30-30Z" fill="${palette.accent}" fill-opacity="0.28" />
      </g>
      <g transform="translate(118, ${aspectHeight - 166})">
        <rect x="0" y="0" width="278" height="78" rx="28" fill="rgba(255,255,255,0.14)" />
        <text x="36" y="34" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="rgba(255,255,255,0.78)">Catalogue DigitalCrown</text>
        <text x="36" y="60" font-family="Arial, sans-serif" font-size="26" font-weight="800" fill="${palette.text}">Marketplace dentaire</text>
      </g>
    </svg>
  `;

  return buildSvgDataUri(svg);
};

const buildSupplierHeroImage = (supplierName: string) => {
  const safeName = supplierName.slice(0, 30);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="1600" height="860" viewBox="0 0 1600 860">
      <defs>
        <linearGradient id="heroBg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0f172a" />
          <stop offset="52%" stop-color="#1d4ed8" />
          <stop offset="100%" stop-color="#14b8a6" />
        </linearGradient>
      </defs>
      <rect width="1600" height="860" rx="44" fill="url(#heroBg)" />
      <circle cx="1220" cy="180" r="210" fill="rgba(255,255,255,0.10)" />
      <circle cx="1410" cy="650" r="250" fill="rgba(255,255,255,0.08)" />
      <circle cx="230" cy="720" r="180" fill="rgba(255,255,255,0.10)" />
      <rect x="94" y="90" width="1412" height="680" rx="38" fill="rgba(15,23,42,0.12)" stroke="rgba(255,255,255,0.16)" />
      <text x="126" y="188" font-family="Arial, sans-serif" font-size="34" font-weight="700" fill="rgba(255,255,255,0.76)">Partenaire fournisseur</text>
      <text x="126" y="280" font-family="Arial, sans-serif" font-size="78" font-weight="800" fill="#f8fafc">${safeName}</text>
      <text x="126" y="350" font-family="Arial, sans-serif" font-size="28" font-weight="600" fill="rgba(255,255,255,0.82)">Catalogue dentaire, commandes tracees et experience integree dans DigitalCrown.</text>
      <g transform="translate(126, 450)">
        <rect x="0" y="0" width="236" height="120" rx="28" fill="rgba(255,255,255,0.12)" />
        <text x="34" y="46" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="rgba(255,255,255,0.72)">Categories</text>
        <text x="34" y="88" font-family="Arial, sans-serif" font-size="42" font-weight="800" fill="#ffffff">Dentaire</text>
      </g>
      <g transform="translate(392, 450)">
        <rect x="0" y="0" width="286" height="120" rx="28" fill="rgba(255,255,255,0.12)" />
        <text x="34" y="46" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="rgba(255,255,255,0.72)">Mode de vente</text>
        <text x="34" y="88" font-family="Arial, sans-serif" font-size="42" font-weight="800" fill="#ffffff">Commande partenaire</text>
      </g>
      <g transform="translate(1134, 228)">
        <rect x="0" y="0" width="252" height="252" rx="54" fill="rgba(255,255,255,0.16)" />
        <rect x="28" y="28" width="196" height="196" rx="40" fill="rgba(255,255,255,0.18)" />
        <path d="M98 74h56c24 0 44 20 44 44v70c0 24-20 44-44 44H98c-24 0-44-20-44-44v-70c0-24 20-44 44-44Z" fill="#e0f2fe" />
        <path d="M126 104c26 0 48 22 48 48s-22 48-48 48s-48-22-48-48s22-48 48-48Z" fill="#2563eb" fill-opacity="0.22" />
      </g>
    </svg>
  `;

  return buildSvgDataUri(svg);
};

export const availabilityLabel = (availability: string): PartnerProduct['availability'] => {
  if (availability === 'AVAILABLE') return 'Disponible';
  if (availability === 'DISCONTINUED') return 'Discontinué';
  return 'Sur commande';
};

export const availabilityBadgeClass = (availability: PartnerProduct['availability']) => {
  if (availability === 'Disponible') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (availability === 'Discontinué') return 'bg-slate-100 text-slate-500 border-slate-200';
  return 'bg-amber-50 text-amber-700 border-amber-200';
};

export const normalizePartnerProduct = (product: PartnerCatalogProduct): PartnerProduct => ({
  id: String(product.id),
  supplierId: String(product.supplierId),
  supplierName: product.supplierName || undefined,
  name: product.name,
  category: product.dentalCategory as PartnerProductCategory,
  specialty: product.dentalSpecialty,
  sku: product.sku,
  unit: product.unit,
  price: product.price,
  availability: availabilityLabel(product.availability),
  description: product.shortDescription || product.longDescription || 'Produit catalogue partenaire.',
  longDescription: product.longDescription || product.shortDescription || 'Produit catalogue partenaire.',
  benefits: product.benefits?.length ? product.benefits : ['Produit catalogue partenaire', 'Importable depuis API fournisseur'],
  audience: product.dentalSpecialty || 'Cabinet dentaire',
  imageUrl: buildProductImage({ name: product.name, category: product.dentalCategory, sku: product.sku }, 'card'),
  gallery: [
    buildProductImage({ name: product.name, category: product.dentalCategory, sku: product.sku }, 'hero'),
    buildProductImage({ name: product.name, category: product.dentalCategory, sku: product.sku }, 'detail'),
    buildProductImage({ name: product.name, category: product.dentalCategory, sku: product.sku }, 'card'),
  ],
});

export const buildPartnerProfile = (supplier?: PartnerCatalogSupplier | null): PartnerProfile => {
  if (!supplier) {
    return noActiveSupplierProfile;
  }

  return {
    id: String(supplier.id),
    name: supplier.name,
    badge: supplier.badge || 'Partenaire actif',
    description: supplier.description || 'Fournisseur partenaire connectable à DigitalCrown via catalogue et import API.',
    promise: supplier.promise || 'DigitalCrown capte la commande puis la transmet au fournisseur pour traitement.',
    coverage: [
      'Catalogue classé par catégorie dentaire',
      'Produits filtrés par spécialité clinique',
      'Base compatible avec import automatique fournisseur',
    ],
    logistics: [
      'Commande enregistrée puis envoyée au partenaire',
      'Référence partenaire conservée pour suivi commercial',
      "Réconciliation possible si la commande change ou s'annule",
    ],
    support: [
      'Commission sur commande envoyée ou confirmée selon accord',
      'Mode remise fournisseur ou revente déjà préparé',
      'Architecture extensible à plusieurs partenaires',
    ],
    heroImageUrl: buildSupplierHeroImage(supplier.name),
  };
};

export const getPartnerProductFromList = (products: PartnerProduct[], productId: string) =>
  products.find((product) => product.id === productId) ?? null;

export const formatMoney = (value: number) =>
  `${value.toLocaleString('fr-MA', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} MAD`;

export const getMarketplaceScopeKey = (user?: Pick<AppUser, 'employer_id' | 'id'> | null) => {
  if (user?.employer_id) return `employer:${user.employer_id}`;
  if (user?.id) return `user:${user.id}`;
  return 'anonymous';
};

const getMarketplaceCacheStorageKey = (user?: Pick<AppUser, 'employer_id' | 'id'> | null) =>
  `${STORAGE_MARKETPLACE_CACHE_PREFIX}:${getMarketplaceScopeKey(user)}`;

export const readMarketplaceCache = (user?: Pick<AppUser, 'employer_id' | 'id'> | null): PartnerMarketplaceCache | null => {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(getMarketplaceCacheStorageKey(user));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PartnerMarketplaceCache;
    if (!parsed || parsed.version !== 1) return null;
    return parsed;
  } catch {
    return null;
  }
};

export const writeMarketplaceCache = (
  user: Pick<AppUser, 'employer_id' | 'id'> | null | undefined,
  payload: Omit<PartnerMarketplaceCache, 'version' | 'scopeKey' | 'syncedAt'>
) => {
  if (typeof window === 'undefined') return;
  const snapshot: PartnerMarketplaceCache = {
    version: 1,
    scopeKey: getMarketplaceScopeKey(user),
    syncedAt: new Date().toISOString(),
    ...payload,
  };
  window.localStorage.setItem(getMarketplaceCacheStorageKey(user), JSON.stringify(snapshot));
};

export const readStoredCart = (): CartState => {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.localStorage.getItem(STORAGE_CART_KEY);
    return raw ? (JSON.parse(raw) as CartState) : {};
  } catch {
    return {};
  }
};

export const writeStoredCart = (cart: CartState) => {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(STORAGE_CART_KEY, JSON.stringify(cart));
};
