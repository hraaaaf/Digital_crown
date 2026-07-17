import React, { useEffect, useMemo, useState } from 'react';
import {
  ShoppingCart,
  Search,
  Package,
  PackageOpen,
  Store,
  ShieldCheck,
  Truck,
  Plus,
  Minus,
  CheckCircle2,
  ClipboardList,
  Calculator,
  RefreshCw,
  Settings2,
  Sparkles,
  Tags,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '../utils/cn';
import { api } from '../services/api';
import { useAuthStore } from '../stores/useAuthStore';
import {
  type CartState,
  type PartnerCatalogProduct,
  type PartnerCatalogSupplier,
  type PartnerMarketplaceCatalogMeta,
  type PartnerMarketplaceStrategyPreset,
  type PartnerProduct,
  availabilityBadgeClass,
  buildPartnerProfile,
  formatMoney,
  getPartnerProductFromList,
  readMarketplaceCache,
  normalizePartnerProduct,
  partnerCategories,
  readStoredCart,
  writeMarketplaceCache,
  writeStoredCart,
} from '../features/partnerMarketplace/data';

type MetaPayload = {
  strategyPresets: PartnerMarketplaceStrategyPreset[];
};

const buildStrategyPreview = (preset: PartnerMarketplaceStrategyPreset, amount: number) => {
  if (preset.revenueModel === 'COMMISSION_PERCENT') {
    return amount * (preset.commissionRate / 100);
  }
  if (preset.revenueModel === 'DISCOUNT_RESALE') {
    return amount * (preset.discountRate / 100);
  }
  return amount > 0 ? preset.fixedFeeAmount : 0;
};

const fallbackCategories = [...partnerCategories];

export const PartnerMarketplacePage: React.FC = () => {
  const user = useAuthStore((state) => state.user);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('Toutes');
  const [cart, setCart] = useState<CartState>({});
  const [meta, setMeta] = useState<MetaPayload | null>(null);
  const [selectedStrategyKey, setSelectedStrategyKey] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState(false);
  const [catalogMeta, setCatalogMeta] = useState<PartnerMarketplaceCatalogMeta | null>(null);
  const [suppliers, setSuppliers] = useState<PartnerCatalogSupplier[]>([]);
  const [catalogProducts, setCatalogProducts] = useState<PartnerProduct[]>([]);
  const [customer, setCustomer] = useState({
    fullName: '',
    clinic: '',
    phone: '',
    email: '',
    city: '',
    note: ''
  });

  useEffect(() => {
    setCart(readStoredCart());
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    writeStoredCart(cart);
  }, [cart]);

  const hydrateFromCache = () => {
    const cached = readMarketplaceCache(user);
    if (!cached) return false;
    setMeta({ strategyPresets: cached.strategyPresets });
    setCatalogMeta(cached.catalogMeta);
    setSuppliers(cached.suppliers);
    setCatalogProducts(cached.products);
    if (cached.strategyPresets.length > 0) {
      setSelectedStrategyKey((current) => current || cached.strategyPresets[0].key);
    }
    return true;
  };

  const loadCatalog = async () => {
    setCatalogLoading(true);
    setCatalogError(false);
    const hadCache = hydrateFromCache();
    try {
      const [ordersMetaRes, metaRes, suppliersRes, productsRes] = await Promise.all([
        api.get('/partner-orders/meta'),
        api.get('/partner-catalog/meta'),
        api.get('/partner-catalog/suppliers'),
        api.get('/partner-catalog/products'),
      ]);
      const strategyPresets = (ordersMetaRes.data?.strategyPresets || []) as PartnerMarketplaceStrategyPreset[];
      setMeta({ strategyPresets });
      if (strategyPresets.length > 0) {
        setSelectedStrategyKey((current) => current || strategyPresets[0].key);
      }
      const nextCatalogMeta = (metaRes.data || null) as PartnerMarketplaceCatalogMeta | null;
      setCatalogMeta(nextCatalogMeta);
      const nextSuppliers = (suppliersRes.data || []) as PartnerCatalogSupplier[];
      const nextProducts = ((productsRes.data || []) as PartnerCatalogProduct[]).map(normalizePartnerProduct);
      setSuppliers(nextSuppliers);
      setCatalogProducts(nextProducts);
      writeMarketplaceCache(user, {
        strategyPresets,
        catalogMeta: nextCatalogMeta,
        suppliers: nextSuppliers,
        products: nextProducts,
      });
    } catch {
      if (!hadCache) {
        setMeta((current) => current ?? { strategyPresets: [] });
        setCatalogMeta(null);
        setSuppliers([]);
        setCatalogProducts([]);
      }
      setCatalogError(true);
    } finally {
      setCatalogLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    const bootstrap = async () => {
      hydrateFromCache();
      if (!active) return;
      await loadCatalog();
    };

    bootstrap();
    return () => {
      active = false;
    };
  }, [user?.employer_id, user?.id]);

  const activeSupplier = useMemo(() => {
    return suppliers.find((supplier) => supplier.isActive) || suppliers[0] || null;
  }, [suppliers]);

  const partnerProfile = useMemo(() => buildPartnerProfile(activeSupplier), [activeSupplier]);

  const categoryOptions = useMemo(() => {
    const liveCategories = catalogMeta?.categories?.length ? catalogMeta.categories : fallbackCategories.slice(1);
    return ['Toutes', ...liveCategories];
  }, [catalogMeta]);

  const specialtyOptions = useMemo(() => {
    const liveSpecialties = catalogMeta?.specialties?.length
      ? catalogMeta.specialties
      : Array.from(new Set(catalogProducts.map((product) => product.specialty).filter(Boolean) as string[]));
    return liveSpecialties.slice(0, 4);
  }, [catalogMeta, catalogProducts]);

  const featuredProducts = useMemo(() => {
    return [...catalogProducts].sort((a, b) => b.price - a.price).slice(0, 3);
  }, [catalogProducts]);

  const filteredProducts = useMemo(() => {
    const query = search.trim().toLowerCase();
    return catalogProducts.filter((product) => {
      const matchCategory = category === 'Toutes' || product.category === category;
      const haystack = `${product.name} ${product.category} ${product.sku} ${product.description} ${product.specialty || ''}`.toLowerCase();
      const matchSearch = !query || haystack.includes(query);
      return matchCategory && matchSearch;
    });
  }, [search, category, catalogProducts]);

  const cartLines = useMemo(() => {
    return Object.entries(cart)
      .filter(([, quantity]) => quantity > 0)
      .map(([productId, quantity]) => {
        const product = getPartnerProductFromList(catalogProducts, productId);
        if (!product) return null;
        return {
          ...product,
          quantity,
          lineTotal: product.price * quantity
        };
      })
      .filter(Boolean) as Array<PartnerProduct & { quantity: number; lineTotal: number }>;
  }, [cart, catalogProducts]);

  const estimatedTotal = cartLines.reduce((sum, line) => sum + line.lineTotal, 0);
  const totalUnits = cartLines.reduce((sum, line) => sum + line.quantity, 0);
  const selectedStrategy = meta?.strategyPresets.find((preset) => preset.key === selectedStrategyKey) ?? null;
  const previewRevenue = selectedStrategy ? buildStrategyPreview(selectedStrategy, estimatedTotal) : 0;

  const adjustQty = (productId: string, delta: number) => {
    setSuccessMessage('');
    setCart((current) => {
      const next = { ...current };
      const currentQty = next[productId] ?? 0;
      const target = Math.max(0, currentQty + delta);
      if (target === 0) {
        delete next[productId];
      } else {
        next[productId] = target;
      }
      return next;
    });
  };

  const submitOrder = async (event: React.FormEvent) => {
    event.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');
    if (!cartLines.length) {
      setSuccessMessage('Ajoutez au moins un produit avant de préparer la commande.');
      return;
    }
    if (!selectedStrategy) {
      setErrorMessage("Choisissez une stratégie de rémunération avant d'enregistrer la commande.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        partnerId: activeSupplier ? String(activeSupplier.id) : partnerProfile.id,
        partnerName: activeSupplier?.name || partnerProfile.name,
        strategyLabel: selectedStrategy.label,
        settlementBasis: selectedStrategy.settlementBasis,
        revenueModel: selectedStrategy.revenueModel,
        commissionRate: selectedStrategy.commissionRate,
        discountRate: selectedStrategy.discountRate,
        fixedFeeAmount: selectedStrategy.fixedFeeAmount,
        customer,
        lines: cartLines.map((line) => ({
          productId: line.id,
          name: line.name,
          sku: line.sku,
          quantity: line.quantity,
          unitPrice: line.price,
          lineTotal: line.lineTotal
        })),
        estimatedTotal,
      };

      const response = await api.post('/partner-orders', payload);
      const order = response.data;
      if (!order?.orderNumber) {
        throw new Error("La commande n'a pas pu être enregistrée correctement.");
      }

      setCart({});
      setCustomer({ fullName: '', clinic: '', phone: '', email: '', city: '', note: '' });
      setSuccessMessage(`Commande ${order.orderNumber} enregistrée avec la stratégie "${order.strategyLabel}".`);
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || error?.message || "Impossible d'enregistrer la commande partenaire.");
    } finally {
      setSubmitting(false);
    }
  };

  const hasSupplier = Boolean(activeSupplier);
  const showNoCatalogState = !catalogLoading && !catalogError && catalogProducts.length === 0;
  const showNoResultsState = !catalogLoading && !catalogError && catalogProducts.length > 0 && filteredProducts.length === 0;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <section className="relative overflow-hidden rounded-elite-lg border border-border-main bg-card-bg shadow-elite">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.12),transparent_36%),radial-gradient(circle_at_top_right,rgba(16,185,129,0.10),transparent_28%),linear-gradient(135deg,rgba(255,255,255,0.96),rgba(248,250,252,0.94))]" />
        <div className="relative p-8 lg:p-10 grid grid-cols-1 xl:grid-cols-[1.25fr_0.75fr] gap-6">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary border border-primary/10 text-[10px] font-black uppercase tracking-widest">
              <Sparkles size={13} />
              Marketplace fournisseur intégrée
            </div>
            <div className="space-y-3 max-w-3xl">
              <h1 className="font-outfit text-3xl md:text-4xl font-black tracking-tight text-slate-900">Un espace catalogue haut de gamme, sans sortir de DigitalCrown.</h1>
              <p className="text-slate-600 font-medium leading-relaxed">
                Cette vitrine garde les repères de l'application, mais adopte une lecture plus catalogue : catégories, spécialités dentaires, fiches produit, panier et commande partenaire.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <InfoTile icon={<ShieldCheck size={14} />} tone="emerald" title="Intégration sûre" text="Le module reste isolé du cœur patient, agenda et comptabilité." />
              <InfoTile icon={<Package size={14} />} tone="blue" title="Catalogue extensible" text="Ajout manuel aujourd'hui, import API fournisseur demain." />
              <InfoTile icon={<Truck size={14} />} tone="amber" title="Suivi commercial" text="Les commandes envoyées sont réconciliées côté administration pour le calcul de revenu." />
            </div>
            {specialtyOptions.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {specialtyOptions.map((item) => (
                  <span key={item} className="inline-flex items-center gap-2 px-3 py-2 rounded-full border border-border-main bg-card-bg/85 text-xs font-black text-slate-600 uppercase tracking-widest shadow-sm">
                    <Tags size={12} className="text-primary" />
                    {item}
                  </span>
                ))}
              </div>
            )}
          </div>

          <aside className="rounded-elite-lg border border-slate-800 bg-slate-950 text-white p-6 lg:p-7 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-elite bg-white/10 flex items-center justify-center">
                <ClipboardList size={22} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-widest font-black text-slate-400">{partnerProfile.badge}</p>
                <h2 className="font-outfit text-xl font-black">{partnerProfile.name}</h2>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <MetricCard label="Références" value={String(catalogProducts.length)} />
              <MetricCard label="Catégories" value={String(Math.max(0, categoryOptions.length - 1))} />
              <MetricCard label="Panier" value={String(totalUnits)} />
            </div>
            {selectedStrategy && (
              <div className="rounded-elite bg-white/5 border border-white/10 p-4">
                <p className="text-[10px] uppercase tracking-widest font-black text-slate-400 mb-2">Stratégie active</p>
                <p className="font-black">{selectedStrategy.label}</p>
                <p className="text-sm text-slate-300 mt-2 leading-relaxed">{selectedStrategy.description}</p>
              </div>
            )}
            <div className={cn('grid gap-3', user?.is_superadmin ? 'grid-cols-1 md:grid-cols-3' : 'grid-cols-1 md:grid-cols-2')}>
              <Link to={`/approvisionnement/partenaire/${partnerProfile.id}`} className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-elite border border-white/10 bg-white/5 text-sm font-black hover:bg-white/10 transition-colors">
                <Store size={15} />
                Fournisseur
              </Link>
              {user?.is_superadmin && (
                <Link to="/approvisionnement/admin" className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-elite border border-white/10 bg-white/5 text-sm font-black hover:bg-white/10 transition-colors">
                  <Settings2 size={15} />
                  Administration
                </Link>
              )}
              <button type="button" onClick={loadCatalog} className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-elite border border-white/10 bg-white/5 text-sm font-black hover:bg-white/10 transition-colors">
                <RefreshCw size={15} />
                Actualiser la vue
              </button>
            </div>
          </aside>
        </div>
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-[0.95fr_1.45fr_0.7fr] gap-6">
        <aside className="space-y-5">
          <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-5 space-y-4 sticky top-6">
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-2">Recherche produit</p>
              <div className="relative">
                <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  type="text"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Référence, catégorie, spécialité"
                  className="w-full pl-11 pr-4 py-3 border border-border-main rounded-elite text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-card-bg"
                />
              </div>
            </div>
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-2">Catégories</p>
              <div className="flex flex-wrap gap-2">
                {categoryOptions.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setCategory(item)}
                    className={cn(
                      'px-3 py-2 rounded-full text-[11px] font-black uppercase tracking-widest border transition-all',
                      category === item
                        ? 'bg-slate-900 text-white border-slate-900 shadow-lg'
                        : 'bg-card-bg text-text-muted border-border-main hover:border-slate-300'
                    )}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
            {partnerProfile.promise && (
              <div className="rounded-elite border border-emerald-200 bg-emerald-50 p-4 space-y-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-emerald-700">Promesse fournisseur</p>
                <p className="text-sm font-semibold text-emerald-900 leading-relaxed">{partnerProfile.promise}</p>
                {partnerProfile.coverage.length > 0 && (
                  <div className="space-y-2">
                    {partnerProfile.coverage.slice(0, 3).map((item) => (
                      <div key={item} className="text-sm text-emerald-900/85 font-medium flex items-start gap-2">
                        <CheckCircle2 size={14} className="shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </aside>

        <section className="space-y-5">
          {!catalogLoading && !catalogError && featuredProducts.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {featuredProducts.map((product, index) => (
                <Link key={product.id} to={`/approvisionnement/produits/${product.id}`} className={cn(
                  'relative overflow-hidden rounded-elite-lg border shadow-elite p-5 transition-all hover:-translate-y-1 hover:shadow-elite-hover',
                  index === 0 ? 'bg-slate-950 text-white border-slate-900' : 'bg-card-bg border-border-main'
                )}>
                  <div className={cn('absolute inset-0 opacity-70 pointer-events-none', index === 0 ? 'bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.28),transparent_30%)]' : 'bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.08),transparent_28%)]')} />
                  <div className="relative space-y-3">
                    {product.imageUrl && (
                      <div className="overflow-hidden rounded-elite border border-white/10 bg-white/5">
                        <img src={product.imageUrl} alt={product.name} className="h-44 w-full object-cover" />
                      </div>
                    )}
                    <div className="flex items-center justify-between gap-3">
                      <span className={cn('px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border', index === 0 ? 'border-white/10 bg-white/10 text-white' : 'border-border-main bg-slate-50 text-text-muted')}>
                        {index === 0 ? 'Sélection premium' : 'Top ventes'}
                      </span>
                      <ArrowRight size={16} className={index === 0 ? 'text-white/70' : 'text-text-muted'} />
                    </div>
                    <div>
                      <p className={cn('text-[10px] font-black uppercase tracking-widest mb-2', index === 0 ? 'text-slate-300' : 'text-text-muted')}>
                        {product.category} | {product.specialty || 'Omnipratique'}
                      </p>
                      <h3 className={cn('font-outfit text-lg font-black leading-tight', index === 0 ? 'text-white' : 'text-slate-900')}>{product.name}</h3>
                      <p className={cn('text-sm mt-2 leading-relaxed min-h-[42px]', index === 0 ? 'text-slate-300' : 'text-text-muted')}>{product.description}</p>
                    </div>
                    <div className="flex items-end justify-between gap-3">
                      <div>
                        <p className={cn('text-2xl font-black', index === 0 ? 'text-white' : 'text-slate-900')}>{formatMoney(product.price)}</p>
                      </div>
                      <span className={cn('px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border whitespace-nowrap', availabilityBadgeClass(product.availability))}>
                        {product.availability}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {catalogLoading ? (
              <p className="col-span-full text-sm text-text-muted">Chargement du catalogue partenaire...</p>
            ) : catalogError ? (
              <div className="col-span-full flex flex-col items-center text-center gap-3 rounded-elite-lg border border-dashed border-border-main bg-card-bg px-6 py-12">
                <div className="w-12 h-12 rounded-elite-sm bg-rose-50 text-rose-600 flex items-center justify-center">
                  <RefreshCw size={20} />
                </div>
                <div>
                  <p className="font-black text-slate-900">Impossible de charger le catalogue</p>
                  <p className="text-sm text-text-muted mt-1 max-w-sm mx-auto">Le service catalogue fournisseur n'est pas joignable pour le moment. Réessayez dans un instant.</p>
                </div>
                <button type="button" onClick={loadCatalog} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-elite bg-slate-900 text-white text-xs font-black uppercase tracking-widest hover:bg-black transition-colors">
                  <RefreshCw size={13} />
                  Réessayer
                </button>
              </div>
            ) : showNoCatalogState ? (
              <div className="col-span-full flex flex-col items-center text-center gap-3 rounded-elite-lg border border-dashed border-border-main bg-card-bg px-6 py-12">
                <div className="w-12 h-12 rounded-elite-sm bg-primary/10 text-primary flex items-center justify-center">
                  <PackageOpen size={20} />
                </div>
                <div>
                  <p className="font-black text-slate-900">
                    {hasSupplier ? 'Catalogue en cours de mise en place' : 'Aucun fournisseur configuré'}
                  </p>
                  <p className="text-sm text-text-muted mt-1 max-w-sm mx-auto">
                    {hasSupplier
                      ? `${partnerProfile.name} n'a pas encore de produits publiés dans DigitalCrown.`
                      : "Aucun fournisseur partenaire n'est encore actif pour ce cabinet."}
                  </p>
                </div>
                {user?.is_superadmin ? (
                  <Link to="/approvisionnement/admin" className="inline-flex items-center gap-2 px-4 py-2.5 rounded-elite bg-slate-900 text-white text-xs font-black uppercase tracking-widest hover:bg-black transition-colors">
                    <Settings2 size={13} />
                    {hasSupplier ? 'Ajouter des produits' : 'Configurer un fournisseur'}
                  </Link>
                ) : (
                  <p className="text-xs font-black uppercase tracking-widest text-text-muted">Contactez votre administrateur pour l'activer.</p>
                )}
              </div>
            ) : showNoResultsState ? (
              <div className="col-span-full flex flex-col items-center text-center gap-3 rounded-elite-lg border border-dashed border-border-main bg-card-bg px-6 py-12">
                <div className="w-12 h-12 rounded-elite-sm bg-primary/10 text-primary flex items-center justify-center">
                  <Search size={20} />
                </div>
                <div>
                  <p className="font-black text-slate-900">Aucun produit ne correspond à ces filtres</p>
                  <p className="text-sm text-text-muted mt-1 max-w-sm mx-auto">Essayez une autre catégorie ou modifiez votre recherche.</p>
                </div>
                <button
                  type="button"
                  onClick={() => { setSearch(''); setCategory('Toutes'); }}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-elite border border-border-main text-slate-700 text-xs font-black uppercase tracking-widest hover:bg-slate-50 transition-colors"
                >
                  Réinitialiser les filtres
                </button>
              </div>
            ) : (
              filteredProducts.map((product) => {
                const isDiscontinued = product.availability === 'Discontinué';
                return (
                  <article key={product.id} className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6 space-y-4 transition-all hover:-translate-y-1 hover:shadow-elite-hover">
                    {product.imageUrl && (
                      <Link to={`/approvisionnement/produits/${product.id}`} className="block overflow-hidden rounded-elite border border-border-main bg-slate-100">
                        <img src={product.imageUrl} alt={product.name} className="h-48 w-full object-cover transition-transform duration-300 hover:scale-[1.02]" />
                      </Link>
                    )}
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-2">
                          {product.category} | {product.specialty || 'Omnipratique'}
                        </p>
                        <Link to={`/approvisionnement/produits/${product.id}`} className="font-outfit text-lg font-black text-slate-900 leading-tight hover:text-primary transition-colors">
                          {product.name}
                        </Link>
                        <p className="text-xs text-text-muted font-bold uppercase tracking-widest mt-2">{product.sku}</p>
                      </div>
                      <span className={cn('px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border whitespace-nowrap', availabilityBadgeClass(product.availability))}>
                        {product.availability}
                      </span>
                    </div>
                    <p className="text-sm text-text-muted leading-relaxed min-h-[42px]">{product.description}</p>
                    <div className="rounded-elite bg-slate-50 border border-border-main p-4">
                      <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">Pour qui</p>
                      <p className="text-sm font-semibold text-slate-700">{product.audience || product.specialty || 'Cabinet dentaire'}</p>
                    </div>
                    <div className="flex items-end justify-between gap-4">
                      <div>
                        <p className="text-2xl font-black text-slate-900">{formatMoney(product.price)}</p>
                        <p className="text-xs font-bold text-text-muted uppercase tracking-widest mt-1">Prix indicatif | unité {product.unit}</p>
                      </div>
                      {isDiscontinued ? (
                        <p className="text-xs font-black uppercase tracking-widest text-slate-400">Retiré du catalogue</p>
                      ) : (
                        <div className="flex items-center gap-2">
                          <button type="button" onClick={() => adjustQty(product.id, -1)} className="w-9 h-9 rounded-elite border border-border-main text-slate-600 flex items-center justify-center hover:bg-slate-50 transition-colors">
                            <Minus size={14} />
                          </button>
                          <div className="w-10 text-center font-black text-slate-900">{cart[product.id] ?? 0}</div>
                          <button type="button" onClick={() => adjustQty(product.id, 1)} className="w-9 h-9 rounded-elite bg-primary text-white flex items-center justify-center hover:brightness-110 transition-all">
                            <Plus size={14} />
                          </button>
                        </div>
                      )}
                    </div>
                    <Link to={`/approvisionnement/produits/${product.id}`} className="inline-flex items-center text-sm font-black text-primary hover:underline">
                      Voir la fiche produit
                    </Link>
                  </article>
                );
              })
            )}
          </div>
        </section>

        <aside className="space-y-5">
          <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-11 h-11 rounded-elite bg-primary/10 text-primary flex items-center justify-center">
                <ShoppingCart size={20} />
              </div>
              <div>
                <h2 className="font-outfit text-lg font-black text-slate-900">Commande partenaire</h2>
                <p className="text-xs font-bold uppercase tracking-widest text-text-muted">Panier, contact et stratégie</p>
              </div>
            </div>

            <div className="p-4 rounded-elite border border-amber-200 bg-amber-50 text-amber-800 text-sm font-medium leading-relaxed mb-4">
              La commande est d'abord créée en brouillon, puis suivie et réconciliée par l'administrateur du cabinet.
            </div>

            <div className="space-y-3 mb-5">
              {cartLines.length === 0 ? (
                <div className="text-sm text-text-muted bg-slate-50 border border-border-main rounded-elite p-4">
                  Aucun produit sélectionné pour le moment.
                </div>
              ) : (
                cartLines.map((line) => (
                  <div key={line.id} className="border border-border-main rounded-elite p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-black text-slate-900">{line.name}</p>
                        <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mt-1">{line.sku}</p>
                      </div>
                      <p className="font-black text-slate-900">{formatMoney(line.lineTotal)}</p>
                    </div>
                    <div className="flex items-center justify-between mt-3 text-sm text-text-muted">
                      <span>{line.quantity} x {formatMoney(line.price)}</span>
                      <span>{line.unit}</span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="space-y-2 pb-5 border-b border-border-main">
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-muted">Lignes</span>
                <span className="font-black text-slate-900">{cartLines.length}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-muted">Unités</span>
                <span className="font-black text-slate-900">{totalUnits}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-muted">Total estimé</span>
                <span className="text-xl font-black text-slate-900">{formatMoney(estimatedTotal)}</span>
              </div>
            </div>

            <form onSubmit={submitOrder} className="space-y-3 pt-5">
              <div>
                <label className="block text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">Stratégie partenaire</label>
                <select
                  value={selectedStrategyKey}
                  onChange={(event) => setSelectedStrategyKey(event.target.value)}
                  className="w-full px-4 py-3 border border-border-main rounded-elite text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-card-bg"
                >
                  {(meta?.strategyPresets || []).map((preset) => (
                    <option key={preset.key} value={preset.key}>{preset.label}</option>
                  ))}
                </select>
              </div>

              {selectedStrategy && (
                <div className="rounded-elite border border-border-main bg-slate-50 p-4 space-y-2">
                  <div className="flex items-center gap-2 text-slate-700 text-xs font-black uppercase tracking-widest">
                    <Calculator size={14} />
                    Simulation de revenu
                  </div>
                  <p className="text-sm text-text-muted">{selectedStrategy.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-muted">Base choisie</span>
                    <span className="font-black text-slate-900">{selectedStrategy.settlementBasis}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-text-muted">Revenu théorique</span>
                    <span className="font-black text-slate-900">{formatMoney(previewRevenue)}</span>
                  </div>
                </div>
              )}

              <InputField label="Nom complet" value={customer.fullName} onChange={(value) => setCustomer((prev) => ({ ...prev, fullName: value }))} required />
              <InputField label="Cabinet" value={customer.clinic} onChange={(value) => setCustomer((prev) => ({ ...prev, clinic: value }))} required />
              <div className="grid grid-cols-2 gap-3">
                <InputField label="Téléphone" value={customer.phone} onChange={(value) => setCustomer((prev) => ({ ...prev, phone: value }))} required />
                <InputField label="Ville" value={customer.city} onChange={(value) => setCustomer((prev) => ({ ...prev, city: value }))} required />
              </div>
              <InputField label="Email" type="email" value={customer.email} onChange={(value) => setCustomer((prev) => ({ ...prev, email: value }))} required />
              <div>
                <label className="block text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">Note</label>
                <textarea
                  value={customer.note}
                  onChange={(event) => setCustomer((prev) => ({ ...prev, note: event.target.value }))}
                  rows={3}
                  className="w-full px-4 py-3 border border-border-main rounded-elite text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-card-bg resize-none"
                  placeholder="Instruction de commande ou précision utile"
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3 rounded-elite bg-slate-900 text-white font-black uppercase tracking-widest text-xs hover:bg-black transition-colors disabled:opacity-60"
              >
                {submitting ? 'Enregistrement...' : 'Enregistrer la commande partenaire'}
              </button>
              {successMessage && (
                <div className="rounded-elite border border-emerald-200 bg-emerald-50 text-emerald-800 p-4 text-sm font-medium leading-relaxed flex gap-3">
                  <CheckCircle2 size={18} className="shrink-0 mt-0.5" />
                  <span>{successMessage}</span>
                </div>
              )}
              {errorMessage && (
                <div className="rounded-elite border border-rose-200 bg-rose-50 text-rose-800 p-4 text-sm font-medium leading-relaxed">
                  {errorMessage}
                </div>
              )}
            </form>
          </div>
        </aside>
      </div>
    </div>
  );
};

const MetricCard = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-elite bg-white/5 border border-white/10 px-4 py-4">
    <p className="text-[10px] uppercase tracking-widest font-black text-slate-400">{label}</p>
    <p className="text-2xl font-black mt-2">{value}</p>
  </div>
);

const InfoTile = ({
  icon,
  tone,
  title,
  text
}: {
  icon: React.ReactNode;
  tone: 'emerald' | 'blue' | 'amber';
  title: string;
  text: string;
}) => {
  const tones = {
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    blue: 'border-blue-200 bg-blue-50 text-blue-700',
    amber: 'border-amber-200 bg-amber-50 text-amber-700'
  };

  return (
    <div className={cn('rounded-elite px-4 py-4 border', tones[tone])}>
      <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest">
        {icon}
        {title}
      </div>
      <p className="text-sm font-semibold text-slate-900 mt-2">{text}</p>
    </div>
  );
};

const InputField = ({
  label,
  value,
  onChange,
  type = 'text',
  required = false
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
}) => (
  <div>
    <label className="block text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">{label}</label>
    <input
      type={type}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      required={required}
      className="w-full px-4 py-3 border border-border-main rounded-elite text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-card-bg"
    />
  </div>
);

export default PartnerMarketplacePage;
