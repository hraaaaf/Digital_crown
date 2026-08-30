import type { AppUser } from '../../types';

export type PartnerProductCategory = string;

export type PartnerTemplateMetric = {
  label: string;
  value: string;
  tone?: 'dark' | 'light' | 'emerald' | 'amber' | 'blue';
};

export type PartnerTemplateBlock = {
  eyebrow: string;
  title: string;
  description: string;
  bullets: string[];
};

export type PartnerProductSpec = {
  label: string;
  value: string;
};

export type PartnerProductPageTemplate = {
  summary: string;
  clinicalApplications: string[];
  whatsIncluded: string[];
  technicalSpecs: PartnerProductSpec[];
  assurances: string[];
};

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
  isFeatured?: boolean;
  sortOrder?: number;
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
  metrics: PartnerTemplateMetric[];
  sections: PartnerTemplateBlock[];
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
export const STORAGE_MARKETPLACE_CACHE_PREFIX = 'digitalcrown_partner_marketplace_cache_v1';
export const MARKETPLACE_CACHE_TTL_MS = 15 * 60 * 1000;
const AUTH_STORAGE_KEY = 'auth-storage';

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

const emptyMetrics: PartnerTemplateMetric[] = [
  { label: 'Références', value: '0', tone: 'dark' },
  { label: 'Spécialités', value: '0', tone: 'light' },
  { label: 'Mode', value: 'Préparation', tone: 'amber' },
];

const noActiveSupplierProfile: PartnerProfile = {
  id: 'aucun-fournisseur',
  name: 'Aucun fournisseur actif',
  badge: 'Configuration requise',
  description: "Aucun fournisseur partenaire n'est encore configuré pour ce cabinet.",
  promise: "Une fois un fournisseur ajouté depuis le dashboard administrateur, son catalogue apparaîtra ici pour vos commandes.",
  coverage: [],
  logistics: [],
  support: [],
  metrics: emptyMetrics,
  sections: [
    {
      eyebrow: 'Mise en route',
      title: 'Préparer le premier catalogue',
      description: 'Activez un fournisseur, ajoutez ses produits, puis laissez DigitalCrown exposer une expérience catalogue prête pour la commande.',
      bullets: ['Créer la fiche fournisseur', 'Classer les produits par catégorie', 'Renseigner les prix et les références'],
    },
  ],
};

export const partnerCategories = ['Toutes', 'Consommables', 'Restauration', 'Endodontie', 'Instrumentation'] as const;

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
  imageUrl: undefined,
  gallery: [],
  isFeatured: product.isFeatured,
  sortOrder: product.sortOrder,
});

export const buildPartnerProfile = (supplier?: PartnerCatalogSupplier | null): PartnerProfile => {
  if (!supplier) {
    return noActiveSupplierProfile;
  }

  const supplierMode = supplier.syncMode || 'Manuelle + API prête';

  return {
    id: String(supplier.id),
    name: supplier.name,
    badge: supplier.badge || 'Partenaire actif',
    description: supplier.description || 'Fournisseur partenaire connectable à DigitalCrown via catalogue, commandes envoyées et futur import API.',
    promise: supplier.promise || 'DigitalCrown capte la commande, la structure et l’envoie ensuite au fournisseur pour exécution logistique.',
    coverage: [
      'Catalogue classé par catégorie dentaire',
      'Produits filtrés par spécialité clinique',
      'Base compatible avec import automatique fournisseur',
    ],
    logistics: [
      'Commande enregistrée puis envoyée au partenaire',
      'Référence partenaire conservée pour suivi commercial',
      'Réconciliation possible si la commande change ou s’annule',
    ],
    support: [
      'Commission sur commande envoyée ou confirmée selon accord',
      'Mode remise fournisseur ou revente déjà préparé',
      'Architecture extensible à plusieurs partenaires',
    ],
    heroImageUrl: supplier.apiBaseUrl || undefined,
    metrics: [
      { label: 'Références prêtes', value: String(Math.max(0, supplier.productCount)), tone: 'dark' },
      { label: 'Intégration', value: supplierMode, tone: 'emerald' },
      { label: 'Statut', value: supplier.isActive ? 'Actif' : 'Préparation', tone: supplier.isActive ? 'blue' : 'amber' },
    ],
    sections: [
      {
        eyebrow: 'Approvisionnement',
        title: 'Un catalogue pensé pour le fauteuil, pas pour un simple tableur',
        description: 'La navigation met en avant les familles de soins, les références critiques et un tunnel de commande piloté depuis DigitalCrown.',
        bullets: ['Catégories visibles dès l’arrivée', 'Spécialités filtrables rapidement', 'Références et prix lisibles sur chaque carte'],
      },
      {
        eyebrow: 'Pilotage',
        title: 'Une base propre pour les futurs imports fournisseur',
        description: 'Les champs métier, les blocs éditoriaux et les surfaces catalogue servent de gabarit pour brancher ensuite un flux API sans refaire l’interface.',
        bullets: ['Fiche fournisseur enrichie', 'Fiche produit modulaire', 'Cache local-first pour consultation fluide'],
      },
      {
        eyebrow: 'Monétisation',
        title: 'Le suivi commercial reste compatible avec plusieurs accords',
        description: 'Que vous soyez rémunéré sur la commande envoyée, confirmée ou sur un modèle de remise, la structure de l’expérience est déjà prête.',
        bullets: ['Commande transmise et historisée', 'Cas d’annulation prévus', 'Évolution multi-partenaires déjà cadrée'],
      },
    ],
  };
};

export const buildPartnerProductTemplate = (product: PartnerProduct): PartnerProductPageTemplate => ({
  summary: `${product.name} est présenté comme une référence premium du catalogue ${product.category.toLowerCase()}, avec une lecture rapide du bénéfice clinique, des usages et des éléments de commande.`,
  clinicalApplications: [
    `Usage principal en ${product.specialty || 'omnipratique'}`,
    `Référence adaptée à un parcours d’achat rapide pour ${product.audience || 'le cabinet dentaire'}`,
    'Supporte une présentation catalogue avec prix, arguments et commande partenaire',
  ],
  whatsIncluded: [
    `Conditionnement : ${product.unit}`,
    `Référence fournisseur : ${product.sku}`,
    'Fiche exploitable pour import ou synchronisation API future',
  ],
  technicalSpecs: [
    { label: 'Catégorie', value: product.category },
    { label: 'Spécialité', value: product.specialty || 'Omnipratique' },
    { label: 'Conditionnement', value: product.unit },
    { label: 'Disponibilité', value: product.availability },
  ],
  assurances: [
    'Commande préparée dans DigitalCrown avant envoi au partenaire',
    'Ajustement possible en cas de changement fournisseur',
    'Base de fiche prête pour photos réelles et données enrichies',
  ],
});

export const getPartnerProductFromList = (products: PartnerProduct[], productId: string) =>
  products.find((product) => product.id === productId) ?? null;

export const formatMoney = (value: number) =>
  `${value.toLocaleString('fr-MA', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} MAD`;

export const getMarketplaceScopeKey = (user?: Pick<AppUser, 'employer_id' | 'id'> | null) => {
  if (user?.employer_id) return `employer:${user.employer_id}`;
  if (user?.id) return `user:${user.id}`;
  return 'anonymous';
};

export const getMarketplaceCacheStorageKey = (user?: Pick<AppUser, 'employer_id' | 'id'> | null) =>
  `${STORAGE_MARKETPLACE_CACHE_PREFIX}:${getMarketplaceScopeKey(user)}`;

const getPersistedAuthUser = (): Pick<AppUser, 'employer_id' | 'id'> | null => {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { state?: { user?: AppUser | null; isAuthenticated?: boolean } };
    if (!parsed?.state?.isAuthenticated || !parsed.state.user?.id) return null;
    return parsed.state.user;
  } catch {
    return null;
  }
};

export const getMarketplaceCartScopeKey = (user?: Pick<AppUser, 'employer_id' | 'id'> | null) => {
  const resolved = user ?? getPersistedAuthUser();
  if (!resolved?.id) return 'anonymous';
  if (resolved.employer_id) return `employer:${resolved.employer_id}:user:${resolved.id}`;
  return `user:${resolved.id}`;
};

export const getMarketplaceCartStorageKey = (user?: Pick<AppUser, 'employer_id' | 'id'> | null) =>
  `${STORAGE_CART_KEY}:${getMarketplaceCartScopeKey(user)}`;

export const readMarketplaceCache = (user?: Pick<AppUser, 'employer_id' | 'id'> | null): PartnerMarketplaceCache | null => {
  if (typeof window === 'undefined') return null;
  const storageKey = getMarketplaceCacheStorageKey(user);
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PartnerMarketplaceCache;
    const expectedScope = getMarketplaceScopeKey(user);
    const syncedAtMs = Date.parse(parsed?.syncedAt || '');
    if (
      !parsed ||
      parsed.version !== 1 ||
      parsed.scopeKey !== expectedScope ||
      !Number.isFinite(syncedAtMs) ||
      Date.now() - syncedAtMs > MARKETPLACE_CACHE_TTL_MS
    ) {
      window.localStorage.removeItem(storageKey);
      return null;
    }
    return parsed;
  } catch {
    window.localStorage.removeItem(storageKey);
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

export const readStoredCart = (user?: Pick<AppUser, 'employer_id' | 'id'> | null): CartState => {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.localStorage.getItem(getMarketplaceCartStorageKey(user));
    return raw ? (JSON.parse(raw) as CartState) : {};
  } catch {
    return {};
  }
};

export const writeStoredCart = (cart: CartState, user?: Pick<AppUser, 'employer_id' | 'id'> | null) => {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(getMarketplaceCartStorageKey(user), JSON.stringify(cart));
};
