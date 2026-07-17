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

const heroSurfaceStyle: React.CSSProperties = {
  background: 'radial-gradient(circle at top right, rgba(255,255,255,0.16), transparent 28%), linear-gradient(135deg, var(--primary) 0%, var(--secondary) 55%, var(--accent) 100%)',
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
    note: '',
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
      const nextSuppliers = (suppliersRes.data || []) as PartnerCatalogSupplier[];
      const nextProducts = ((productsRes.data || []) as PartnerCatalogProduct[]).map(normalizePartnerProduct);
      setCatalogMeta(nextCatalogMeta);
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

  const activeSupplier = useMemo(() => suppliers.find((supplier) => supplier.isActive) || suppliers[0] || null, [suppliers]);
  const partnerProfile = useMemo(() => buildPartnerProfile(activeSupplier), [activeSupplier]);

  const categoryOptions = useMemo(() => {
    const liveCategories = catalogMeta?.categories?.length ? catalogMeta.categories : fallbackCategories.slice(1);
    return ['Toutes', ...liveCategories];
  }, [catalogMeta]);

  const specialtyOptions = useMemo(() => {
    const liveSpecialties = catalogMeta?.specialties?.length
      ? catalogMeta.specialties
      : Array.from(new Set(catalogProducts.map((product) => product.specialty).filter(Boolean) as string[]));
    return liveSpecialties.slice(0, 5);
  }, [catalogMeta, catalogProducts]);

  const featuredProducts = useMemo(() => [...catalogProducts].sort((a, b) => b.price - a.price).slice(0, 4), [catalogProducts]);

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
          lineTotal: product.price * quantity,
        };
      })
      .filter(Boolean) as Array<PartnerProduct & { quantity: number; lineTotal: number }>;
  }, [cart, catalogProducts]);

  const estimatedTotal = cartLines.reduce((sum, line) => sum + line.lineTotal, 0);
  const totalUnits = cartLines.reduce((sum, line) => sum + line.quantity, 0);
  const selectedStrategy = meta?.strategyPresets.find((preset) => preset.key === selectedStrategyKey) ?? null;
  const previewRevenue = selectedStrategy ? buildStrategyPreview(selectedStrategy, estimatedTotal) : 0;
  const categoryCounts = useMemo(() => {
    return categoryOptions.slice(1, 5).map((item) => ({
      label: item,
      count: catalogProducts.filter((product) => product.category === item).length,
    }));
  }, [categoryOptions, catalogProducts]);

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
      setErrorMessage('Choisissez une stratégie de rémunération avant d’enregistrer la commande.');
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
          lineTotal: line.lineTotal,
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
      setErrorMessage(error?.response?.data?.detail || error?.message || 'Impossible d’enregistrer la commande partenaire.');
    } finally {
      setSubmitting(false);
    }
  };

  const hasSupplier = Boolean(activeSupplier);
  const showNoCatalogState = !catalogLoading && !catalogError && catalogProducts.length === 0;
  const showNoResultsState = !catalogLoading && !catalogError && catalogProducts.length > 0 && filteredProducts.length === 0;
  const heroProduct = featuredProducts[0] || filteredProducts[0] || null;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <section className="rounded-elite-lg border border-border-main overflow-hidden shadow-elite" style={heroSurfaceStyle}>
        <div className="p-8 lg:p-10 xl:p-12 grid grid-cols-1 xl:grid-cols-[1.08fr_0.92fr] gap-8 text-white">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-4 py-2 text-[11px] font-black uppercase tracking-[0.25em]">
              <Sparkles size={14} />
              Marketplace clinique premium
            </div>
            <div className="space-y-4 max-w-3xl">
              <h1 className="font-outfit text-4xl md:text-5xl xl:text-6xl font-black tracking-tight leading-[0.95]">
                Une vraie vitrine d’achat dentaire, intégrée au thème vivant de DigitalCrown.
              </h1>
              <p className="max-w-2xl text-white/82 text-base md:text-lg font-medium leading-relaxed">
                Inspirée des grands catalogues du secteur, cette landing met en avant les familles de soins, les produits stars,
                le parcours fournisseur et un tunnel de commande propre, sans quitter l’application.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link to={`/approvisionnement/partenaire/${partnerProfile.id}`} className="inline-flex items-center gap-2 rounded-elite border border-white/15 bg-white/10 px-5 py-3 text-sm font-black hover:bg-white/15 transition-colors">
                <Store size={16} />
                Explorer le fournisseur
              </Link>
              {user?.is_superadmin && (
                <Link to="/approvisionnement/admin" className="inline-flex items-center gap-2 rounded-elite border border-white/15 bg-white/10 px-5 py-3 text-sm font-black hover:bg-white/15 transition-colors">
                  <Settings2 size={16} />
                  Gérer le catalogue
                </Link>
              )}
              <button type="button" onClick={loadCatalog} className="inline-flex items-center gap-2 rounded-elite border border-white/15 bg-white px-5 py-3 text-sm font-black hover:brightness-95 transition-all" style={{ color: 'var(--primary)' }}>
                <RefreshCw size={16} />
                Actualiser la vue
              </button>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <HeroMetric label="Références" value={String(catalogProducts.length)} />
              <HeroMetric label="Catégories" value={String(Math.max(0, categoryOptions.length - 1))} />
              <HeroMetric label="Spécialités" value={String(specialtyOptions.length)} />
              <HeroMetric label="Panier" value={String(totalUnits)} />
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr] items-stretch">
            <div className="rounded-elite-lg border border-white/15 bg-white/10 p-5 backdrop-blur-md">
              <MarketplaceArtwork
                eyebrow={partnerProfile.badge}
                title={heroProduct?.name || partnerProfile.name}
                subtitle={heroProduct?.category || 'Catalogue partenaire'}
                caption={heroProduct?.description || partnerProfile.promise}
                badge={heroProduct?.sku || 'Sélection active'}
                compact={false}
              />
            </div>
            <div className="space-y-4">
              <GlassCard title="Pourquoi cette vitrine marche">
                <InfoRow icon={<ShieldCheck size={16} />} text="Les surfaces suivent les tokens du thème, sans casser l’identité de l’application." />
                <InfoRow icon={<Package size={16} />} text="Le modèle prépare déjà la future alimentation automatique par API fournisseur." />
                <InfoRow icon={<Truck size={16} />} text="La commande reste pilotée côté DigitalCrown, avec suivi commercial conservé." />
              </GlassCard>
              {selectedStrategy && (
                <GlassCard title="Stratégie active">
                  <p className="font-outfit text-2xl font-black leading-tight">{selectedStrategy.label}</p>
                  <p className="text-sm text-white/78 mt-2 leading-relaxed">{selectedStrategy.description}</p>
                </GlassCard>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {categoryCounts.map((item) => (
          <button
            key={item.label}
            type="button"
            onClick={() => setCategory(item.label)}
            className="rounded-elite-lg border border-border-main bg-card-bg p-5 text-left shadow-elite transition-all hover:-translate-y-1 hover:shadow-elite-hover"
          >
            <p className="text-[10px] uppercase tracking-[0.28em] font-black text-text-muted">Collection</p>
            <h3 className="font-outfit text-2xl font-black text-text-main mt-2">{item.label}</h3>
            <p className="text-sm text-text-muted mt-2">{item.count} référence(s) disponibles dans ce rayon clinique.</p>
            <div className="mt-4 inline-flex items-center gap-2 text-sm font-black" style={{ color: 'var(--primary)' }}>
              Ouvrir ce rayon
              <ArrowRight size={15} />
            </div>
          </button>
        ))}
      </section>

      {!catalogLoading && !catalogError && featuredProducts.length > 0 && (
        <section className="space-y-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.32em] font-black text-text-muted">Sélection éditoriale</p>
              <h2 className="font-outfit text-3xl font-black text-text-main mt-2">Des produits mis en avant comme sur une vraie marketplace</h2>
            </div>
            <p className="text-sm text-text-muted max-w-md lg:text-right">Grandes cartes, hiérarchie visuelle claire et lecture immédiate du produit, du bénéfice et du prix.</p>
          </div>
          <div className="grid grid-cols-1 xl:grid-cols-[1.1fr_0.9fr] gap-4">
            <FeatureProductCard product={featuredProducts[0]} large onAdd={adjustQty} quantity={cart[featuredProducts[0].id] ?? 0} />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {featuredProducts.slice(1, 4).map((product) => (
                <FeatureProductCard key={product.id} product={product} onAdd={adjustQty} quantity={cart[product.id] ?? 0} />
              ))}
            </div>
          </div>
        </section>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[0.9fr_1.45fr_0.8fr] gap-6 items-start">
        <aside className="space-y-4 xl:sticky xl:top-6">
          <div className="rounded-elite-lg border border-border-main bg-card-bg p-5 shadow-elite space-y-5">
            <div>
              <p className="text-[10px] uppercase tracking-[0.28em] font-black text-text-muted mb-2">Recherche catalogue</p>
              <div className="relative">
                <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  type="text"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Référence, catégorie, spécialité"
                  className="w-full rounded-elite border border-border-main bg-input-field pl-11 pr-4 py-3 text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10"
                />
              </div>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-[0.28em] font-black text-text-muted mb-3">Rayons</p>
              <div className="flex flex-wrap gap-2">
                {categoryOptions.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setCategory(item)}
                    className={cn(
                      'rounded-full border px-3 py-2 text-[11px] font-black uppercase tracking-[0.22em] transition-all',
                      category === item
                        ? 'text-white shadow-lg'
                        : 'bg-card-bg text-text-muted border-border-main hover:border-border-hover'
                    )}
                    style={category === item ? { backgroundColor: 'var(--primary)', borderColor: 'var(--primary)' } : undefined}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
            {specialtyOptions.length > 0 && (
              <div>
                <p className="text-[10px] uppercase tracking-[0.28em] font-black text-text-muted mb-3">Spécialités visibles</p>
                <div className="space-y-2">
                  {specialtyOptions.map((item) => (
                    <div key={item} className="flex items-center gap-3 rounded-elite border border-border-main bg-[var(--glass-bg)] px-4 py-3 text-sm font-semibold text-text-main">
                      <Tags size={15} style={{ color: 'var(--primary)' }} />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="rounded-elite border border-border-main p-4" style={{ background: 'linear-gradient(180deg, var(--glass-bg), var(--card-bg))' }}>
              <p className="text-[10px] uppercase tracking-[0.28em] font-black text-text-muted mb-2">Promesse fournisseur</p>
              <p className="text-sm font-semibold text-text-main leading-relaxed">{partnerProfile.promise}</p>
            </div>
          </div>
        </aside>

        <section className="space-y-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.32em] font-black text-text-muted">Catalogue</p>
              <h2 className="font-outfit text-3xl font-black text-text-main mt-2">Une grille produit plus éditoriale et plus dense</h2>
            </div>
            <div className="text-left lg:text-right">
              <p className="text-sm text-text-muted">{filteredProducts.length} produit(s) affiché(s)</p>
              <p className="text-sm text-text-muted">{hasSupplier ? partnerProfile.name : 'Fournisseur à configurer'}</p>
            </div>
          </div>

          {catalogLoading ? (
            <StateCard title="Chargement du catalogue partenaire..." description="Nous récupérons les produits du fournisseur et le cache local-first." />
          ) : catalogError ? (
            <StateCard title="Impossible de charger le catalogue" description="Le service catalogue n'est pas joignable pour le moment. Réessayez dans un instant." actionLabel="Réessayer" onAction={loadCatalog} />
          ) : showNoCatalogState ? (
            <StateCard
              title={hasSupplier ? 'Catalogue en cours de mise en place' : 'Aucun fournisseur configuré'}
              description={hasSupplier ? `${partnerProfile.name} n'a pas encore de produits publiés dans DigitalCrown.` : "Aucun fournisseur partenaire n'est encore actif pour ce cabinet."}
              actionLabel={user?.is_superadmin ? (hasSupplier ? 'Ajouter des produits' : 'Configurer un fournisseur') : undefined}
              actionHref={user?.is_superadmin ? '/approvisionnement/admin' : undefined}
            />
          ) : showNoResultsState ? (
            <StateCard
              title="Aucun produit ne correspond à ces filtres"
              description="Essayez une autre catégorie ou modifiez votre recherche pour élargir la sélection."
              actionLabel="Réinitialiser les filtres"
              onAction={() => {
                setSearch('');
                setCategory('Toutes');
              }}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredProducts.map((product) => {
                const isDiscontinued = product.availability === 'Discontinué';
                return (
                  <article key={product.id} className="rounded-elite-lg border border-border-main bg-card-bg p-5 shadow-elite transition-all hover:-translate-y-1 hover:shadow-elite-hover">
                    <MarketplaceArtwork
                      eyebrow={product.category}
                      title={product.name}
                      subtitle={product.specialty || 'Omnipratique'}
                      caption={product.description}
                      badge={product.sku}
                      compact
                    />
                    <div className="mt-4 flex items-start justify-between gap-4">
                      <div>
                        <Link to={`/approvisionnement/produits/${product.id}`} className="font-outfit text-xl font-black text-text-main hover:opacity-80 transition-opacity">
                          {product.name}
                        </Link>
                        <p className="mt-2 text-xs font-black uppercase tracking-[0.24em] text-text-muted">{product.sku}</p>
                      </div>
                      <span className={cn('px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.24em] border whitespace-nowrap', availabilityBadgeClass(product.availability))}>
                        {product.availability}
                      </span>
                    </div>
                    <p className="mt-4 text-sm text-text-muted leading-relaxed min-h-[44px]">{product.longDescription}</p>
                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <SpecChip label="Pour" value={product.audience || product.specialty || 'Cabinet dentaire'} />
                      <SpecChip label="Conditionnement" value={product.unit} />
                    </div>
                    <div className="mt-5 flex items-end justify-between gap-4">
                      <div>
                        <p className="text-2xl font-black text-text-main">{formatMoney(product.price)}</p>
                        <p className="mt-1 text-xs font-black uppercase tracking-[0.24em] text-text-muted">Prix indicatif</p>
                      </div>
                      {isDiscontinued ? (
                        <p className="text-xs font-black uppercase tracking-[0.24em] text-text-muted">Retiré du catalogue</p>
                      ) : (
                        <div className="flex items-center gap-2">
                          <button type="button" onClick={() => adjustQty(product.id, -1)} className="w-9 h-9 rounded-elite border border-border-main text-text-main flex items-center justify-center hover:bg-input-field transition-colors">
                            <Minus size={14} />
                          </button>
                          <div className="w-10 text-center font-black text-text-main">{cart[product.id] ?? 0}</div>
                          <button type="button" onClick={() => adjustQty(product.id, 1)} className="w-9 h-9 rounded-elite text-white flex items-center justify-center transition-all hover:brightness-110" style={{ backgroundColor: 'var(--primary)' }}>
                            <Plus size={14} />
                          </button>
                        </div>
                      )}
                    </div>
                    <Link to={`/approvisionnement/produits/${product.id}`} className="mt-4 inline-flex items-center gap-2 text-sm font-black" style={{ color: 'var(--primary)' }}>
                      Voir la fiche produit
                      <ArrowRight size={15} />
                    </Link>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <aside className="space-y-4 xl:sticky xl:top-6">
          <div className="rounded-elite-lg border border-border-main bg-card-bg p-6 shadow-elite">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-11 h-11 rounded-elite flex items-center justify-center text-white" style={{ backgroundColor: 'var(--primary)' }}>
                <ShoppingCart size={20} />
              </div>
              <div>
                <h2 className="font-outfit text-xl font-black text-text-main">Commande partenaire</h2>
                <p className="text-xs font-black uppercase tracking-[0.24em] text-text-muted">Panier, contact, stratégie</p>
              </div>
            </div>

            <div className="rounded-elite border border-border-main p-4 mb-5" style={{ background: 'linear-gradient(180deg, var(--glass-bg), var(--card-bg))' }}>
              <p className="text-sm font-semibold text-text-main leading-relaxed">La commande est préparée dans DigitalCrown, puis envoyée au partenaire selon la stratégie active.</p>
            </div>

            <div className="space-y-3 mb-5">
              {cartLines.length === 0 ? (
                <div className="rounded-elite border border-border-main bg-input-field p-4 text-sm text-text-muted">
                  Aucun produit sélectionné pour le moment.
                </div>
              ) : (
                cartLines.map((line) => (
                  <div key={line.id} className="rounded-elite border border-border-main p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-black text-text-main">{line.name}</p>
                        <p className="mt-1 text-[10px] font-black uppercase tracking-[0.24em] text-text-muted">{line.sku}</p>
                      </div>
                      <p className="font-black text-text-main">{formatMoney(line.lineTotal)}</p>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-sm text-text-muted">
                      <span>{line.quantity} x {formatMoney(line.price)}</span>
                      <span>{line.unit}</span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="space-y-2 border-b border-border-main pb-5">
              <SummaryRow label="Lignes" value={String(cartLines.length)} />
              <SummaryRow label="Unités" value={String(totalUnits)} />
              <SummaryRow label="Total estimé" value={formatMoney(estimatedTotal)} strong />
              {selectedStrategy && <SummaryRow label="Revenu simulé" value={formatMoney(previewRevenue)} />}
            </div>

            <form onSubmit={submitOrder} className="mt-5 space-y-4">
              <div>
                <label className="text-[10px] uppercase tracking-[0.28em] font-black text-text-muted">Stratégie active</label>
                <div className="mt-2 rounded-elite border border-border-main bg-input-field px-4 py-3 text-sm font-semibold text-text-main">
                  {selectedStrategy?.label || 'Aucune stratégie disponible'}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <OrderField label="Nom complet" value={customer.fullName} onChange={(value) => setCustomer((current) => ({ ...current, fullName: value }))} required />
                <OrderField label="Cabinet" value={customer.clinic} onChange={(value) => setCustomer((current) => ({ ...current, clinic: value }))} />
                <OrderField label="Téléphone" value={customer.phone} onChange={(value) => setCustomer((current) => ({ ...current, phone: value }))} required />
                <OrderField label="Email" type="email" value={customer.email} onChange={(value) => setCustomer((current) => ({ ...current, email: value }))} />
              </div>

              <OrderField label="Ville" value={customer.city} onChange={(value) => setCustomer((current) => ({ ...current, city: value }))} />
              <OrderTextArea label="Note de commande" value={customer.note} onChange={(value) => setCustomer((current) => ({ ...current, note: value }))} />

              {successMessage && (
                <div className="rounded-elite border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-800">{successMessage}</div>
              )}
              {errorMessage && (
                <div className="rounded-elite border border-rose-200 bg-rose-50 p-4 text-sm font-semibold text-rose-700">{errorMessage}</div>
              )}

              <button
                type="submit"
                disabled={submitting || !selectedStrategy}
                className="w-full rounded-elite px-5 py-4 text-sm font-black uppercase tracking-[0.28em] text-white transition-all disabled:cursor-not-allowed disabled:opacity-60 hover:brightness-110"
                style={{ backgroundColor: 'var(--primary)' }}
              >
                {submitting ? 'Envoi en cours...' : 'Envoyer la commande au partenaire'}
              </button>
            </form>
          </div>
        </aside>
      </div>
    </div>
  );
};

const HeroMetric: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="rounded-elite border border-white/15 bg-white/10 px-4 py-4 backdrop-blur-md">
    <p className="text-[10px] uppercase tracking-[0.26em] font-black text-white/60">{label}</p>
    <p className="mt-2 font-outfit text-3xl font-black text-white">{value}</p>
  </div>
);

const GlassCard: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="rounded-elite-lg border border-white/15 bg-white/10 p-5 backdrop-blur-md">
    <p className="text-[10px] uppercase tracking-[0.3em] font-black text-white/60 mb-3">{title}</p>
    <div className="space-y-3 text-white">{children}</div>
  </div>
);

const MarketplaceArtwork: React.FC<{
  eyebrow: string;
  title: string;
  subtitle: string;
  caption: string;
  badge: string;
  compact?: boolean;
}> = ({ eyebrow, title, subtitle, caption, badge, compact = false }) => (
  <div
    className={cn('relative overflow-hidden rounded-elite-lg border border-white/10 text-white', compact ? 'p-5 min-h-[220px]' : 'p-6 min-h-[360px]')}
    style={heroSurfaceStyle}
  >
    <div className="absolute inset-0 opacity-35" style={{ background: 'radial-gradient(circle at bottom left, rgba(255,255,255,0.16), transparent 32%)' }} />
    <div className="relative flex h-full flex-col justify-between gap-6">
      <div className="flex items-center justify-between gap-3">
        <span className="inline-flex w-fit items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.25em]">
          {eyebrow}
        </span>
        <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.25em]">
          {badge}
        </span>
      </div>
      <div className="space-y-3">
        <p className="text-sm font-black uppercase tracking-[0.28em] text-white/70">{subtitle}</p>
        <h3 className={cn('font-outfit font-black leading-[0.95]', compact ? 'text-3xl' : 'text-4xl md:text-5xl')}>{title}</h3>
        <p className={cn('max-w-xl text-white/80 leading-relaxed', compact ? 'text-sm' : 'text-base')}>{caption}</p>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <VisualChip label="Catalogue" value="Premium" />
        <VisualChip label="Commande" value="Directe" />
        <VisualChip label="Base" value="API-ready" />
      </div>
    </div>
  </div>
);

const VisualChip: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="rounded-elite border border-white/15 bg-white/10 px-3 py-3 backdrop-blur-md">
    <p className="text-[10px] uppercase tracking-[0.24em] font-black text-white/60">{label}</p>
    <p className="mt-1 text-sm font-black text-white">{value}</p>
  </div>
);

const InfoRow: React.FC<{ icon: React.ReactNode; text: string }> = ({ icon, text }) => (
  <div className="flex items-start gap-3 text-sm leading-relaxed text-white/82">
    <div className="mt-0.5 shrink-0">{icon}</div>
    <span>{text}</span>
  </div>
);

const FeatureProductCard: React.FC<{
  product: PartnerProduct;
  quantity: number;
  onAdd: (productId: string, delta: number) => void;
  large?: boolean;
}> = ({ product, quantity, onAdd, large = false }) => {
  const isDiscontinued = product.availability === 'Discontinué';

  return (
    <article className="rounded-elite-lg border border-border-main bg-card-bg p-5 shadow-elite transition-all hover:-translate-y-1 hover:shadow-elite-hover">
      <MarketplaceArtwork
        eyebrow={large ? 'Produit star' : product.category}
        title={product.name}
        subtitle={product.specialty || 'Omnipratique'}
        caption={product.description}
        badge={product.sku}
        compact={!large}
      />
      <div className="mt-5 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.24em] text-text-muted">{product.category}</p>
          <p className="mt-2 text-2xl font-black text-text-main">{formatMoney(product.price)}</p>
        </div>
        <span className={cn('px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.24em] border whitespace-nowrap', availabilityBadgeClass(product.availability))}>
          {product.availability}
        </span>
      </div>
      <div className="mt-4 flex items-center justify-between gap-3">
        <Link to={`/approvisionnement/produits/${product.id}`} className="inline-flex items-center gap-2 text-sm font-black" style={{ color: 'var(--primary)' }}>
          Voir la fiche
          <ArrowRight size={15} />
        </Link>
        {isDiscontinued ? (
          <span className="text-xs font-black uppercase tracking-[0.24em] text-text-muted">Indisponible</span>
        ) : (
          <div className="flex items-center gap-2">
            <button type="button" onClick={() => onAdd(product.id, -1)} className="w-9 h-9 rounded-elite border border-border-main text-text-main flex items-center justify-center hover:bg-input-field transition-colors">
              <Minus size={14} />
            </button>
            <div className="w-10 text-center font-black text-text-main">{quantity}</div>
            <button type="button" onClick={() => onAdd(product.id, 1)} className="w-9 h-9 rounded-elite text-white flex items-center justify-center hover:brightness-110 transition-all" style={{ backgroundColor: 'var(--primary)' }}>
              <Plus size={14} />
            </button>
          </div>
        )}
      </div>
    </article>
  );
};

const SpecChip: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="rounded-elite border border-border-main bg-input-field px-4 py-3">
    <p className="text-[10px] uppercase tracking-[0.24em] font-black text-text-muted">{label}</p>
    <p className="mt-1 text-sm font-semibold text-text-main leading-relaxed">{value}</p>
  </div>
);

const StateCard: React.FC<{
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
}> = ({ title, description, actionLabel, actionHref, onAction }) => (
  <div className="rounded-elite-lg border border-dashed border-border-main bg-card-bg px-6 py-12 text-center shadow-elite space-y-4">
    <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-elite text-white" style={{ backgroundColor: 'var(--primary)' }}>
      <PackageOpen size={22} />
    </div>
    <div>
      <p className="font-outfit text-2xl font-black text-text-main">{title}</p>
      <p className="mt-2 max-w-xl mx-auto text-sm leading-relaxed text-text-muted">{description}</p>
    </div>
    {actionLabel && actionHref ? (
      <Link to={actionHref} className="inline-flex items-center gap-2 rounded-elite px-4 py-3 text-sm font-black text-white transition-all hover:brightness-110" style={{ backgroundColor: 'var(--primary)' }}>
        {actionLabel}
      </Link>
    ) : actionLabel && onAction ? (
      <button type="button" onClick={onAction} className="inline-flex items-center gap-2 rounded-elite px-4 py-3 text-sm font-black text-white transition-all hover:brightness-110" style={{ backgroundColor: 'var(--primary)' }}>
        {actionLabel}
      </button>
    ) : null}
  </div>
);

const SummaryRow: React.FC<{ label: string; value: string; strong?: boolean }> = ({ label, value, strong = false }) => (
  <div className="flex items-center justify-between text-sm">
    <span className="text-text-muted">{label}</span>
    <span className={cn('text-text-main', strong ? 'font-black text-base' : 'font-semibold')}>{value}</span>
  </div>
);

const OrderField: React.FC<{
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  type?: string;
}> = ({ label, value, onChange, required = false, type = 'text' }) => (
  <div>
    <label className="text-[10px] uppercase tracking-[0.28em] font-black text-text-muted">{label}</label>
    <input
      type={type}
      required={required}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="mt-2 w-full rounded-elite border border-border-main bg-input-field px-4 py-3 text-sm font-medium text-text-main outline-none focus:ring-2 focus:ring-primary/10"
    />
  </div>
);

const OrderTextArea: React.FC<{ label: string; value: string; onChange: (value: string) => void }> = ({ label, value, onChange }) => (
  <div>
    <label className="text-[10px] uppercase tracking-[0.28em] font-black text-text-muted">{label}</label>
    <textarea
      rows={4}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="mt-2 w-full rounded-elite border border-border-main bg-input-field px-4 py-3 text-sm font-medium text-text-main outline-none focus:ring-2 focus:ring-primary/10"
    />
  </div>
);

export default PartnerMarketplacePage;
