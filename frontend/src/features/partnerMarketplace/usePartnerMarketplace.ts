import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../../services/api';
import { useAuthStore } from '../../stores/useAuthStore';
import type { AppUser } from '../../types';
import {
  type CartState,
  type PartnerCatalogProduct,
  type PartnerCatalogSupplier,
  type PartnerMarketplaceCatalogMeta,
  type PartnerMarketplaceStrategyPreset,
  type PartnerProduct,
  getPartnerProductFromList,
  normalizePartnerProduct,
  partnerCategories,
  readMarketplaceCache,
  readStoredCart,
  writeMarketplaceCache,
  writeStoredCart,
} from './data';

export type MarketplaceCustomer = {
  fullName: string;
  clinic: string;
  phone: string;
  email: string;
  city: string;
  note: string;
};

export type MarketplacePreviewData = {
  strategyPresets: PartnerMarketplaceStrategyPreset[];
  catalogMeta: PartnerMarketplaceCatalogMeta | null;
  suppliers: PartnerCatalogSupplier[];
  products: PartnerProduct[];
};

export type MarketplaceCartLine = PartnerProduct & {
  quantity: number;
  lineTotal: number;
};

const emptyCustomer: MarketplaceCustomer = {
  fullName: '',
  clinic: '',
  phone: '',
  email: '',
  city: '',
  note: '',
};

export function buildMarketplaceCustomer(user?: AppUser | null): MarketplaceCustomer {
  return {
    ...emptyCustomer,
    fullName: user?.full_name || user?.nom_complet || '',
    clinic: user?.cabinet_name || '',
    email: user?.email || '',
  };
}

export function usePartnerMarketplace(options?: { previewData?: MarketplacePreviewData }) {
  const user = useAuthStore((state) => state.user);
  const previewData = options?.previewData;
  const previewMode = Boolean(previewData);

  const [strategyPresets, setStrategyPresets] = useState<PartnerMarketplaceStrategyPreset[]>(previewData?.strategyPresets || []);
  const [catalogMeta, setCatalogMeta] = useState<PartnerMarketplaceCatalogMeta | null>(previewData?.catalogMeta || null);
  const [suppliers, setSuppliers] = useState<PartnerCatalogSupplier[]>(previewData?.suppliers || []);
  const [products, setProducts] = useState<PartnerProduct[]>(previewData?.products || []);
  const [cart, setCart] = useState<CartState>(() => previewMode ? {} : readStoredCart(user));
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('Toutes');
  const [availableOnly, setAvailableOnly] = useState(false);
  const [customer, setCustomer] = useState<MarketplaceCustomer>(() => buildMarketplaceCustomer(user));
  const [catalogLoading, setCatalogLoading] = useState(!previewMode);
  const [catalogError, setCatalogError] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (previewMode) return;
    setCart(readStoredCart(user));
  }, [previewMode, user?.employer_id, user?.id]);

  useEffect(() => {
    if (previewMode) return;
    writeStoredCart(cart, user);
  }, [cart, previewMode, user?.employer_id, user?.id]);

  useEffect(() => {
    setCustomer((current) => ({
      ...current,
      fullName: current.fullName || user?.full_name || user?.nom_complet || '',
      clinic: current.clinic || user?.cabinet_name || '',
      email: current.email || user?.email || '',
    }));
  }, [user?.full_name, user?.nom_complet, user?.cabinet_name, user?.email]);

  const hydrateFromCache = useCallback(() => {
    if (previewMode) return false;
    const cached = readMarketplaceCache(user);
    if (!cached) return false;
    setStrategyPresets(cached.strategyPresets);
    setCatalogMeta(cached.catalogMeta);
    setSuppliers(cached.suppliers);
    setProducts(cached.products);
    return true;
  }, [previewMode, user]);

  const loadCatalog = useCallback(async () => {
    if (previewMode) {
      setStrategyPresets(previewData?.strategyPresets || []);
      setCatalogMeta(previewData?.catalogMeta || null);
      setSuppliers(previewData?.suppliers || []);
      setProducts(previewData?.products || []);
      setCatalogLoading(false);
      setCatalogError(false);
      return;
    }

    setCatalogLoading(true);
    setCatalogError(false);
    const hadCache = hydrateFromCache();
    try {
      const [ordersMetaRes, catalogMetaRes, suppliersRes, productsRes] = await Promise.all([
        api.get('/partner-orders/meta'),
        api.get('/partner-catalog/meta'),
        api.get('/partner-catalog/suppliers'),
        api.get('/partner-catalog/products'),
      ]);

      const nextStrategyPresets = (ordersMetaRes.data?.strategyPresets || []) as PartnerMarketplaceStrategyPreset[];
      const nextCatalogMeta = (catalogMetaRes.data || null) as PartnerMarketplaceCatalogMeta | null;
      const nextSuppliers = (suppliersRes.data || []) as PartnerCatalogSupplier[];
      const nextProducts = ((productsRes.data || []) as PartnerCatalogProduct[]).map(normalizePartnerProduct);

      setStrategyPresets(nextStrategyPresets);
      setCatalogMeta(nextCatalogMeta);
      setSuppliers(nextSuppliers);
      setProducts(nextProducts);
      writeMarketplaceCache(user, {
        strategyPresets: nextStrategyPresets,
        catalogMeta: nextCatalogMeta,
        suppliers: nextSuppliers,
        products: nextProducts,
      });
    } catch {
      if (!hadCache) {
        setStrategyPresets([]);
        setCatalogMeta(null);
        setSuppliers([]);
        setProducts([]);
      }
      setCatalogError(true);
    } finally {
      setCatalogLoading(false);
    }
  }, [hydrateFromCache, previewData, previewMode, user]);

  useEffect(() => {
    hydrateFromCache();
    void loadCatalog();
  }, [hydrateFromCache, loadCatalog]);

  const activeSuppliers = useMemo(() => suppliers.filter((supplier) => supplier.isActive), [suppliers]);
  const categoryOptions = useMemo(() => {
    const live = catalogMeta?.categories?.length ? catalogMeta.categories : partnerCategories.slice(1);
    return ['Toutes', ...live];
  }, [catalogMeta]);

  const orderedProducts = useMemo(() => [...products].sort((a, b) => {
    if (Boolean(a.isFeatured) !== Boolean(b.isFeatured)) return a.isFeatured ? -1 : 1;
    const sortDelta = (a.sortOrder ?? 0) - (b.sortOrder ?? 0);
    if (sortDelta !== 0) return sortDelta;
    return a.name.localeCompare(b.name, 'fr');
  }), [products]);

  const filteredProducts = useMemo(() => {
    const query = search.trim().toLowerCase();
    return orderedProducts.filter((product) => {
      const matchCategory = category === 'Toutes' || product.category === category;
      const matchAvailability = !availableOnly || product.availability === 'Disponible';
      const haystack = `${product.name} ${product.sku} ${product.category} ${product.specialty || ''} ${product.description}`.toLowerCase();
      return matchCategory && matchAvailability && (!query || haystack.includes(query));
    });
  }, [availableOnly, category, orderedProducts, search]);

  const cartLines = useMemo(() => Object.entries(cart)
    .filter(([, quantity]) => quantity > 0)
    .map(([productId, quantity]) => {
      const product = getPartnerProductFromList(products, productId);
      return product ? { ...product, quantity, lineTotal: product.price * quantity } : null;
    })
    .filter(Boolean) as MarketplaceCartLine[], [cart, products]);

  const totalUnits = useMemo(() => cartLines.reduce((sum, line) => sum + line.quantity, 0), [cartLines]);
  const estimatedTotal = useMemo(() => cartLines.reduce((sum, line) => sum + line.lineTotal, 0), [cartLines]);
  const checkoutStrategy = strategyPresets[0] || null;

  const adjustQty = useCallback((product: PartnerProduct, delta: number) => {
    if (product.availability === 'Discontinué') return;
    setSuccessMessage('');
    setErrorMessage('');
    setCart((current) => {
      const next = { ...current };
      const target = Math.max(0, (next[product.id] ?? 0) + delta);
      if (target === 0) delete next[product.id];
      else next[product.id] = target;
      return next;
    });
  }, []);

  const updateCustomer = useCallback((field: keyof MarketplaceCustomer, value: string) => {
    setCustomer((current) => ({ ...current, [field]: value }));
  }, []);

  const submitDraft = useCallback(async () => {
    setSuccessMessage('');
    setErrorMessage('');

    if (!cartLines.length) {
      setErrorMessage('Ajoutez au moins un produit au panier.');
      return false;
    }
    if (!checkoutStrategy) {
      setErrorMessage('La configuration commerciale du Marketplace est indisponible.');
      return false;
    }
    if (!customer.fullName.trim() || !customer.clinic.trim() || !customer.phone.trim() || !customer.email.trim() || !customer.city.trim()) {
      setErrorMessage('Complétez les informations de commande requises.');
      return false;
    }

    if (previewMode) {
      setSuccessMessage('Brouillon de démonstration prêt. Aucune donnée réelle n’a été envoyée.');
      return true;
    }

    setSubmitting(true);
    try {
      const fallbackSupplier = activeSuppliers[0];
      const response = await api.post('/partner-orders', {
        partnerId: fallbackSupplier ? String(fallbackSupplier.id) : 'server-resolved',
        partnerName: fallbackSupplier?.name || 'Server resolved',
        strategyLabel: checkoutStrategy.label,
        settlementBasis: checkoutStrategy.settlementBasis,
        revenueModel: checkoutStrategy.revenueModel,
        commissionRate: checkoutStrategy.commissionRate,
        discountRate: checkoutStrategy.discountRate,
        fixedFeeAmount: checkoutStrategy.fixedFeeAmount,
        customer,
        lines: cartLines.map((line) => ({
          productId: line.id,
          name: line.name,
          sku: line.sku,
          quantity: line.quantity,
          unitPrice: line.price,
          lineTotal: line.lineTotal,
        })),
        estimatedTotal,
      });

      const result = response.data;
      if (!result?.orderNumber) throw new Error("La commande n'a pas été enregistrée correctement.");
      setCart({});
      setCustomer(buildMarketplaceCustomer(user));
      setSuccessMessage(
        result.orderCount && result.orderCount > 1
          ? `${result.orderCount} commandes DRAFT ont été enregistrées pour les fournisseurs concernés.`
          : `Commande ${result.orderNumber} enregistrée en DRAFT.`,
      );
      return true;
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || error?.message || 'Impossible d’enregistrer la commande.');
      return false;
    } finally {
      setSubmitting(false);
    }
  }, [activeSuppliers, cartLines, checkoutStrategy, customer, estimatedTotal, previewMode, user]);

  return {
    user,
    previewMode,
    catalogLoading,
    catalogError,
    products,
    filteredProducts,
    activeSuppliers,
    categoryOptions,
    search,
    setSearch,
    category,
    setCategory,
    availableOnly,
    setAvailableOnly,
    cart,
    cartLines,
    totalUnits,
    estimatedTotal,
    customer,
    updateCustomer,
    submitting,
    successMessage,
    errorMessage,
    adjustQty,
    loadCatalog,
    submitDraft,
  };
}
