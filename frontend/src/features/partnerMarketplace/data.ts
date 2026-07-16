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
  availability: 'Disponible' | 'Sur commande';
  description: string;
  longDescription: string;
  benefits: string[];
  audience?: string;
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

export type CartState = Record<string, number>;

export const partnerProfile: PartnerProfile = {
  id: 'dental-supply-atlas',
  name: 'Dental Supply Atlas',
  badge: 'Partenaire pilote',
  description: 'Fournisseur pilote integre dans DigitalCrown pour tester un parcours catalogue, commande et remuneration sans casser les flux coeur du cabinet.',
  promise: 'DigitalCrown capte la commande, structure le panier et transmet ensuite au fournisseur pour traitement, disponibilite et logistique.',
  coverage: [
    'Consommables de rotation rapide',
    'Materiaux de restauration et d endodontie',
    'Instrumentation standard du cabinet',
  ],
  logistics: [
    'Confirmation fournisseur sous 24h cible',
    'Commande envoyee depuis DigitalCrown puis reconciliee si elle change',
    'Reference partenaire stockee pour audit commercial et suivi de commission',
  ],
  support: [
    'Gestion des cas annules ou modifies apres envoi',
    'Scenarios commission, remise ou forfait deja prepares',
    'Surface extensible a plusieurs partenaires sans refaire l architecture',
  ],
};

export const partnerProducts: PartnerProduct[] = [
  {
    id: 'MKT-001',
    supplierId: 'dental-supply-atlas',
    supplierName: 'Dental Supply Atlas',
    name: 'Gants nitrile premium',
    category: 'Consommables',
    specialty: 'General Dentistry',
    sku: 'GN-PREM-100',
    unit: 'boite',
    price: 185,
    originalPrice: 210,
    availability: 'Disponible',
    description: 'Boite de 100 gants non poudres pour usage quotidien.',
    longDescription: 'Une reference de base pour l activite quotidienne du cabinet. Produit pertinent pour les scenarios de reapprovisionnement rapide et d alertes de stock.',
    benefits: ['Rotation rapide', 'Commande recurrente', 'Bonne reference pour mesurer l adoption'],
    audience: 'Cabinets generalistes et omnipratiques',
  },
  {
    id: 'MKT-002',
    supplierId: 'dental-supply-atlas',
    supplierName: 'Dental Supply Atlas',
    name: 'Masques chirurgicaux type IIR',
    category: 'Consommables',
    specialty: 'General Dentistry',
    sku: 'MASK-IIR-50',
    unit: 'boite',
    price: 95,
    originalPrice: 110,
    availability: 'Disponible',
    description: 'Protection standard pour le cabinet et l accueil patient.',
    longDescription: 'Produit simple et frequemment commande, utile pour valider le tunnel de commande partenaire sur des montants modestes mais recurrents.',
    benefits: ['Faible friction achat', 'Usage recurrent', 'Ideal pour onboarding fournisseur'],
    audience: 'Accueil, soins et sterilisation',
  },
  {
    id: 'MKT-003',
    supplierId: 'dental-supply-atlas',
    supplierName: 'Dental Supply Atlas',
    name: 'Composite universel nano-hybride A2',
    category: 'Restauration',
    specialty: 'Prosthodontics',
    sku: 'COMP-A2-4G',
    unit: 'seringue',
    price: 420,
    originalPrice: 480,
    availability: 'Sur commande',
    description: 'Composite polyvalent pour restaurations anterieures et posterieures.',
    longDescription: 'Reference a valeur unitaire plus elevee, interessante pour tester les scenarios de commission et les modifications de commande apres envoi.',
    benefits: ['Valeur unitaire plus forte', 'Scenario de marge ou commission pertinent', 'Peut subir des ajustements fournisseur'],
    audience: 'Restauration directe et omnipratique',
  },
  {
    id: 'MKT-004',
    supplierId: 'dental-supply-atlas',
    supplierName: 'Dental Supply Atlas',
    name: 'Adhesif photopolymerisable',
    category: 'Restauration',
    specialty: 'Prosthodontics',
    sku: 'ADH-5ML',
    unit: 'flacon',
    price: 310,
    originalPrice: 345,
    availability: 'Disponible',
    description: 'Adhesif compatible avec les protocoles courants du cabinet.',
    longDescription: 'Produit connexe au composite, adapte aux logiques de bundle et de recommandation commerciale dans une V2.',
    benefits: ['Vente complementaire', 'Compatible bundles', 'Stock facile a suivre'],
    audience: 'Protocoles adhesifs quotidiens',
  },
  {
    id: 'MKT-005',
    supplierId: 'dental-supply-atlas',
    supplierName: 'Dental Supply Atlas',
    name: 'Limes rotatives NiTi assortiment',
    category: 'Endodontie',
    specialty: 'Endodontics',
    sku: 'NITI-ROT-6',
    unit: 'kit',
    price: 780,
    originalPrice: 860,
    availability: 'Sur commande',
    description: 'Assortiment de limes pour la preparation canalaire.',
    longDescription: 'Produit plus technique, adapte a des variations de tarif ou de disponibilite et utile pour valider les cas de recalcul apres modification.',
    benefits: ['Ticket eleve', 'Cas de recalcul interessant', 'Lien fort avec l activite clinique'],
    audience: 'Endodontistes et omnipraticiens equipes',
  },
  {
    id: 'MKT-006',
    supplierId: 'dental-supply-atlas',
    supplierName: 'Dental Supply Atlas',
    name: 'Ciment verre ionomere',
    category: 'Endodontie',
    specialty: 'Endodontics',
    sku: 'GIC-FIX-SET',
    unit: 'kit',
    price: 260,
    originalPrice: 290,
    availability: 'Disponible',
    description: 'Kit de scellement a prise rapide.',
    longDescription: 'Reference simple a maintenir dans le catalogue partenaire avec une fiche produit claire et un historique de commande interpretable.',
    benefits: ['Bon candidat V1', 'Catalogue lisible', 'Facile a recommander'],
    audience: 'Scellement et restauration courante',
  },
  {
    id: 'MKT-007',
    supplierId: 'dental-supply-atlas',
    supplierName: 'Dental Supply Atlas',
    name: 'Cassette de sterilisation inox',
    category: 'Instrumentation',
    specialty: 'General Dentistry',
    sku: 'STER-CASE-M',
    unit: 'piece',
    price: 540,
    originalPrice: 590,
    availability: 'Sur commande',
    description: 'Cassette moyenne pour instrumentation standard.',
    longDescription: 'Produit instrumentation avec cycle de remplacement moins frequent mais valeur percue plus elevee, bon test pour les commandes non recurrentes.',
    benefits: ['Valeur percue haute', 'Bon test instrument', 'Peut justifier une fiche detaillee'],
    audience: 'Sterilisation et organisation du plateau',
  },
  {
    id: 'MKT-008',
    supplierId: 'dental-supply-atlas',
    supplierName: 'Dental Supply Atlas',
    name: 'Insert ultrasonique detartrage',
    category: 'Instrumentation',
    specialty: 'Periodontics',
    sku: 'ULTRA-INS-1',
    unit: 'piece',
    price: 690,
    originalPrice: 745,
    availability: 'Disponible',
    description: 'Insert polyvalent pour detartrage supra-gingival.',
    longDescription: 'Produit clinique clair pour une fiche produit plus complete et une navigation catalogue coherente.',
    benefits: ['Produit lisible', 'Ticket moyen utile', 'Bonne demonstration du flux produit'],
    audience: 'Parodontie et prophylaxie',
  },
];

export const partnerCategories = ['Toutes', 'Consommables', 'Restauration', 'Endodontie', 'Instrumentation'] as const;

export const availabilityLabel = (availability: string) =>
  availability === 'AVAILABLE' ? 'Disponible' : 'Sur commande';

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
  originalPrice: Math.round(product.price * 1.12),
  availability: availabilityLabel(product.availability),
  description: product.shortDescription || product.longDescription || 'Produit catalogue partenaire.',
  longDescription: product.longDescription || product.shortDescription || 'Produit catalogue partenaire.',
  benefits: product.benefits?.length ? product.benefits : ['Produit catalogue partenaire', 'Importable depuis API fournisseur'],
  audience: product.dentalSpecialty || 'Cabinet dentaire',
});

export const buildPartnerProfile = (supplier?: PartnerCatalogSupplier | null): PartnerProfile => {
  if (!supplier) {
    return partnerProfile;
  }

  return {
    id: String(supplier.id),
    name: supplier.name,
    badge: supplier.badge || 'Partenaire actif',
    description: supplier.description || 'Fournisseur partenaire connectable a DigitalCrown via catalogue et import API.',
    promise: supplier.promise || 'DigitalCrown capte la commande puis la transmet au fournisseur pour traitement.',
    coverage: [
      'Catalogue classe par categorie dentaire',
      'Produits filtres par specialite clinique',
      'Base compatible avec import automatique fournisseur',
    ],
    logistics: [
      'Commande enregistree puis envoyee au partenaire',
      'Reference partenaire conservee pour suivi commercial',
      'Reconciliation possible si la commande change ou s annule',
    ],
    support: [
      'Commission sur envoye ou confirmee selon accord',
      'Mode remise fournisseur ou revente deja prepare',
      'Architecture extensible a plusieurs partenaires',
    ],
  };
};

export const getPartnerProductFromList = (products: PartnerProduct[], productId: string) =>
  products.find((product) => product.id === productId) ?? null;

export const formatMoney = (value: number) =>
  `${value.toLocaleString('fr-MA', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} MAD`;

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

export const getPartnerProduct = (productId: string) =>
  partnerProducts.find((product) => product.id === productId) ?? null;
