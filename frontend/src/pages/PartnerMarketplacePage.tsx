import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Minus,
  Package,
  Plus,
  RefreshCw,
  Search,
  ShoppingCart,
  Store,
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
  formatMoney,
  getPartnerProductFromList,
  normalizePartnerProduct,
  partnerCategories,
  readMarketplaceCache,
  readStoredCart,
  writeMarketplaceCache,
  writeStoredCart,
} from '../features/partnerMarketplace/data';

type MetaPayload = {
  strategyPresets: PartnerMarketplaceStrategyPreset[];
};

type CustomerForm = {
  fullName: string;
  clinic: string;
  phone: string;
  email: string;
  city: string;
  note: string;
};

const EMPTY_CUSTOMER: CustomerForm = {
  fullName: '',
  clinic: '',
  phone: '',
  email: '',
  city: '',
  note: '',
};

const fallbackCategories = [...partnerCategories];

export const PartnerMarketplacePage: React.FC = () => {
  const user = useAuthStore((state) => state.user);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('Toutes');
  const [cart, setCart] = useState<CartState>({});
  const [meta, setMeta] = useState<MetaPayload | null>(null);
  const [catalogMeta, setCatalogMeta] = useState<PartnerMarketplaceCatalogMeta | null>(null);
  const [suppliers, setSuppliers] = useState<PartnerCatalogSupplier[]>([]);
  const [catalogProducts, setCatalogProducts] = useState<PartnerProduct[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [customer, setCustomer] = useState<CustomerForm>(EMPTY_CUSTOMER);

  useEffect(() => {
    setCart(readStoredCart(user));
  }, [user?.employer_id, user?.id]);

  useEffect(() => {
    writeStoredCart(cart, user);
  }, [cart, user?.employer_id, user?.id]);

  const hydrateFromCache = () => {
    const cached = readMarketplaceCache(user);
    if (!cached) return false;
    setMeta({ strategyPresets: cached.strategyPresets });
    setCatalogMeta(cached.catalogMeta);
    setSuppliers(cached.suppliers);
    setCatalogProducts(cached.products);
    return true;
  };

  const loadCatalog = async () => {
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

      const strategyPresets = (ordersMetaRes.data?.strategyPresets || []) as PartnerMarketplaceStrategyPreset[];
      const nextCatalogMeta = (catalogMetaRes.data || null) as PartnerMarketplaceCatalogMeta | null;
      const nextSuppliers = (suppliersRes.data || []) as PartnerCatalogSupplier[];
      const nextProducts = ((productsRes.data || []) as PartnerCatalogProduct[]).map(normalizePartnerProduct);

      setMeta({ strategyPresets });
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
        setMeta({ strategyPresets: [] });
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
      if (active) await loadCatalog();
    };
    void bootstrap();
    return () => {
      active = false;
    };
  }, [user?.employer_id, user?.id]);

  const activeSuppliers = useMemo(() => suppliers.filter((supplier) => supplier.isActive), [suppliers]);
  const categoryOptions = useMemo(() => {
    const live = catalogMeta?.categories?.length ? catalogMeta.categories : fallbackCategories.slice(1);
    return ['Toutes', ...live];
  }, [catalogMeta]);

  const orderedProducts = useMemo(() => {
    return [...catalogProducts].sort((a, b) => {
      if (Boolean(a.isFeatured) !== Boolean(b.isFeatured)) return a.isFeatured ? -1 : 1;
      const sortDelta = (a.sortOrder ?? 0) - (b.sortOrder ?? 0);
      if (sortDelta !== 0) return sortDelta;
      return a.name.localeCompare(b.name, 'fr');
    });
  }, [catalogProducts]);

  const filteredProducts = useMemo(() => {
    const query = search.trim().toLowerCase();
    return orderedProducts.filter((product) => {
      const matchCategory = category === 'Toutes' || product.category === category;
      const haystack = `${product.name} ${product.sku} ${product.category} ${product.specialty || ''} ${product.description} ${product.longDescription}`.toLowerCase();
      return matchCategory && (!query || haystack.includes(query));
    });
  }, [orderedProducts, search, category]);

  const cartLines = useMemo(() => {
    return Object.entries(cart)
      .filter(([, quantity]) => quantity > 0)
      .map(([productId, quantity]) => {
        const product = getPartnerProductFromList(catalogProducts, productId);
        return product ? { ...product, quantity, lineTotal: product.price * quantity } : null;
      })
      .filter(Boolean) as Array<PartnerProduct & { quantity: number; lineTotal: number }>;
  }, [cart, catalogProducts]);

  const totalUnits = cartLines.reduce((sum, line) => sum + line.quantity, 0);
  const estimatedTotal = cartLines.reduce((sum, line) => sum + line.lineTotal, 0);
  const checkoutStrategy = meta?.strategyPresets?.[0] ?? null;
  const showNoResults = !catalogLoading && !catalogError && catalogProducts.length > 0 && filteredProducts.length === 0;
  const showNoCatalog = !catalogLoading && !catalogError && catalogProducts.length === 0;

  const adjustQty = (product: PartnerProduct, delta: number) => {
    if (product.availability === 'Discontinué') return;
    setSuccessMessage('');
    setCart((current) => {
      const next = { ...current };
      const target = Math.max(0, (next[product.id] ?? 0) + delta);
      if (target === 0) delete next[product.id];
      else next[product.id] = target;
      return next;
    });
  };

  const updateCustomer = (field: keyof CustomerForm, value: string) => {
    setCustomer((current) => ({ ...current, [field]: value }));
  };

  const submitOrder = async (event: React.FormEvent) => {
    event.preventDefault();
    setSuccessMessage('');
    setErrorMessage('');

    if (!cartLines.length) {
      setErrorMessage('Ajoutez au moins un produit au panier.');
      return;
    }
    if (!checkoutStrategy) {
      setErrorMessage('La configuration commerciale du Marketplace est indisponible.');
      return;
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
      setCustomer(EMPTY_CUSTOMER);
      setSuccessMessage(
        result.orderCount && result.orderCount > 1
          ? `${result.orderCount} commandes DRAFT ont été enregistrées pour les fournisseurs concernés.`
          : `Commande ${result.orderNumber} enregistrée en DRAFT.`
      );
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || error?.message || 'Impossible d’enregistrer la commande.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-5 p-4 pb-24 sm:p-6 sm:pb-24 xl:pb-6">
      <header className="rounded-elite-lg border border-border-main bg-card-bg p-4 shadow-elite sm:p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-[10px] font-black uppercase tracking-[0.24em] text-text-muted">Approvisionnement</p>
            <h1 className="mt-1 font-outfit text-3xl font-black leading-tight text-text-main sm:text-4xl">
              Acheter pour le cabinet
            </h1>
            <p className="mt-2 max-w-2xl text-sm font-medium leading-relaxed text-text-muted">
              Recherchez une référence, ajoutez les quantités utiles et enregistrez la commande dans DigitalCrown.
            </p>
          </div>
          <a
            href="#marketplace-cart"
            className="shrink-0 rounded-elite px-3 py-2 text-xs font-black text-white focus:outline-none focus:ring-2 focus:ring-offset-2 sm:px-4 sm:py-3 sm:text-sm"
            style={{ backgroundColor: 'var(--primary)' }}
            aria-label={`Ouvrir le panier, ${totalUnits} unité${totalUnits > 1 ? 's' : ''}`}
          >
            <span className="inline-flex items-center gap-2"><ShoppingCart size={16} /> {totalUnits}</span>
          </a>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-border-main pt-3 text-xs font-semibold text-text-muted">
          <span>{catalogProducts.length} référence(s)</span>
          <span>{activeSuppliers.length} fournisseur(s) actif(s)</span>
          {activeSuppliers[0] && (
            <Link to={`/approvisionnement/partenaire/${activeSuppliers[0].id}`} className="inline-flex items-center gap-1 font-black" style={{ color: 'var(--primary)' }}>
              <Store size={13} /> {activeSuppliers[0].name}
            </Link>
          )}
          <button
            type="button"
            onClick={loadCatalog}
            className="ml-auto inline-flex items-center gap-1 rounded-elite px-2 py-1 font-black focus:outline-none focus:ring-2 focus:ring-primary/20"
            aria-label="Actualiser le catalogue"
          >
            <RefreshCw size={13} /> Actualiser
          </button>
        </div>
      </header>

      <section aria-label="Recherche et filtres" className="rounded-elite-lg border border-border-main bg-card-bg p-4 shadow-elite">
        <label htmlFor="marketplace-search" className="sr-only">Rechercher dans le catalogue</label>
        <div className="relative">
          <Search size={17} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            id="marketplace-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Rechercher produit, SKU, catégorie ou spécialité…"
            className="w-full rounded-elite border border-border-main bg-input-field py-3 pl-11 pr-4 text-sm font-semibold text-text-main outline-none transition focus:border-border-hover focus:ring-2 focus:ring-primary/10"
          />
        </div>
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1" aria-label="Filtrer par catégorie">
          {categoryOptions.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setCategory(item)}
              className={cn(
                'shrink-0 rounded-full border px-3 py-2 text-xs font-black transition focus:outline-none focus:ring-2 focus:ring-primary/20',
                category === item
                  ? 'border-transparent text-white'
                  : 'border-border-main bg-card-bg text-text-muted hover:border-border-hover hover:text-text-main'
              )}
              style={category === item ? { backgroundColor: 'var(--primary)' } : undefined}
              aria-pressed={category === item}
            >
              {item}
            </button>
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <main className="min-w-0 space-y-4">
          <div className="flex items-end justify-between gap-3">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.24em] text-text-muted">Catalogue</p>
              <h2 className="mt-1 font-outfit text-2xl font-black text-text-main">Produits disponibles</h2>
            </div>
            <p className="shrink-0 text-sm font-semibold text-text-muted">{filteredProducts.length} affiché(s)</p>
          </div>

          {catalogLoading ? (
            <StateCard title="Chargement du catalogue…" description="Synchronisation des références disponibles." />
          ) : catalogError ? (
            <StateCard
              title="Catalogue indisponible"
              description="Les données en cache ont été conservées lorsqu'elles étaient encore valides."
              actionLabel="Réessayer"
              onAction={loadCatalog}
            />
          ) : showNoCatalog ? (
            <StateCard title="Aucun produit publié" description="Le catalogue partenaire ne contient encore aucune référence active." />
          ) : showNoResults ? (
            <StateCard
              title="Aucun résultat"
              description="Modifiez la recherche ou réinitialisez la catégorie."
              actionLabel="Réinitialiser"
              onAction={() => {
                setSearch('');
                setCategory('Toutes');
              }}
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {filteredProducts.map((product) => (
                <ProductCard key={product.id} product={product} quantity={cart[product.id] ?? 0} onAdjust={adjustQty} />
              ))}
            </div>
          )}
        </main>

        <aside id="marketplace-cart" className="scroll-mt-6 xl:sticky xl:top-6">
          <CartPanel
            cartLines={cartLines}
            totalUnits={totalUnits}
            estimatedTotal={estimatedTotal}
            customer={customer}
            submitting={submitting}
            successMessage={successMessage}
            errorMessage={errorMessage}
            onCustomerChange={updateCustomer}
            onSubmit={submitOrder}
          />
        </aside>
      </div>

      {totalUnits > 0 && (
        <a
          href="#marketplace-cart"
          className="fixed bottom-4 left-4 right-4 z-30 flex items-center justify-between rounded-elite-lg px-4 py-4 text-sm font-black text-white shadow-2xl xl:hidden"
          style={{ backgroundColor: 'var(--primary)' }}
          aria-label={`Voir le panier, ${totalUnits} unité${totalUnits > 1 ? 's' : ''}, total ${formatMoney(estimatedTotal)}`}
        >
          <span className="inline-flex items-center gap-2"><ShoppingCart size={18} /> Panier · {totalUnits}</span>
          <span>{formatMoney(estimatedTotal)} →</span>
        </a>
      )}
    </div>
  );
};

const ProductCard = ({
  product,
  quantity,
  onAdjust,
}: {
  product: PartnerProduct;
  quantity: number;
  onAdjust: (product: PartnerProduct, delta: number) => void;
}) => {
  const disabled = product.availability === 'Discontinué';
  return (
    <article className="rounded-elite-lg border border-border-main bg-card-bg p-4 shadow-elite transition hover:shadow-elite-hover sm:p-5">
      <div className="flex gap-4">
        <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-elite bg-input-field text-text-muted sm:h-24 sm:w-24">
          <Package size={30} aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-text-muted">{product.category}</p>
            <span className={cn('rounded-full border px-2 py-1 text-[10px] font-black', availabilityBadgeClass(product.availability))}>
              {product.availability}
            </span>
          </div>
          <Link to={`/approvisionnement/produits/${product.id}`} className="mt-2 block font-outfit text-lg font-black leading-tight text-text-main hover:opacity-80">
            {product.name}
          </Link>
          <p className="mt-1 text-xs font-semibold text-text-muted">{product.sku}{product.specialty ? ` · ${product.specialty}` : ''}</p>
        </div>
      </div>

      <p className="mt-4 line-clamp-2 text-sm font-medium leading-relaxed text-text-muted">{product.description}</p>

      <div className="mt-4 flex items-end justify-between gap-4 border-t border-border-main pt-4">
        <div>
          <p className="text-xl font-black text-text-main">{formatMoney(product.price)}</p>
          <p className="mt-1 text-xs font-semibold text-text-muted">par {product.unit}</p>
        </div>
        {disabled ? (
          <span className="text-xs font-black text-text-muted">Indisponible</span>
        ) : (
          <div className="flex items-center gap-2" aria-label={`Quantité de ${product.name}`}>
            <button
              type="button"
              onClick={() => onAdjust(product, -1)}
              disabled={quantity === 0}
              className="flex h-10 w-10 items-center justify-center rounded-elite border border-border-main text-text-main transition hover:bg-input-field disabled:cursor-not-allowed disabled:opacity-40 focus:outline-none focus:ring-2 focus:ring-primary/20"
              aria-label={`Retirer une unité de ${product.name}`}
            >
              <Minus size={15} />
            </button>
            <span className="w-7 text-center font-black text-text-main" aria-live="polite">{quantity}</span>
            <button
              type="button"
              onClick={() => onAdjust(product, 1)}
              className="flex h-10 w-10 items-center justify-center rounded-elite text-white transition hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-offset-2"
              style={{ backgroundColor: 'var(--primary)' }}
              aria-label={`Ajouter une unité de ${product.name}`}
            >
              <Plus size={15} />
            </button>
          </div>
        )}
      </div>
    </article>
  );
};

const CartPanel = ({
  cartLines,
  totalUnits,
  estimatedTotal,
  customer,
  submitting,
  successMessage,
  errorMessage,
  onCustomerChange,
  onSubmit,
}: {
  cartLines: Array<PartnerProduct & { quantity: number; lineTotal: number }>;
  totalUnits: number;
  estimatedTotal: number;
  customer: CustomerForm;
  submitting: boolean;
  successMessage: string;
  errorMessage: string;
  onCustomerChange: (field: keyof CustomerForm, value: string) => void;
  onSubmit: (event: React.FormEvent) => void;
}) => (
  <div className="rounded-elite-lg border border-border-main bg-card-bg p-5 shadow-elite">
    <div className="flex items-center gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-elite text-white" style={{ backgroundColor: 'var(--primary)' }}>
        <ShoppingCart size={18} />
      </div>
      <div>
        <h2 className="font-outfit text-xl font-black text-text-main">Panier</h2>
        <p className="text-xs font-semibold text-text-muted">{totalUnits} unité(s)</p>
      </div>
    </div>

    <div className="mt-4 space-y-2">
      {cartLines.length === 0 ? (
        <p className="rounded-elite bg-input-field p-4 text-sm font-medium text-text-muted">Ajoutez des produits pour préparer la commande.</p>
      ) : (
        cartLines.map((line) => (
          <div key={line.id} className="flex items-start justify-between gap-3 rounded-elite border border-border-main p-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-black text-text-main">{line.name}</p>
              <p className="mt-1 text-xs font-semibold text-text-muted">{line.quantity} × {formatMoney(line.price)}</p>
            </div>
            <p className="shrink-0 text-sm font-black text-text-main">{formatMoney(line.lineTotal)}</p>
          </div>
        ))
      )}
    </div>

    <div className="mt-4 flex items-center justify-between border-y border-border-main py-4">
      <span className="text-sm font-semibold text-text-muted">Total estimé</span>
      <span className="text-xl font-black text-text-main">{formatMoney(estimatedTotal)}</span>
    </div>

    <form onSubmit={onSubmit} className="mt-4 space-y-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-1">
        <Field label="Nom complet" value={customer.fullName} onChange={(value) => onCustomerChange('fullName', value)} required />
        <Field label="Cabinet" value={customer.clinic} onChange={(value) => onCustomerChange('clinic', value)} required />
        <Field label="Téléphone" value={customer.phone} onChange={(value) => onCustomerChange('phone', value)} required inputMode="tel" />
        <Field label="Email" value={customer.email} onChange={(value) => onCustomerChange('email', value)} required type="email" />
        <Field label="Ville" value={customer.city} onChange={(value) => onCustomerChange('city', value)} required />
      </div>
      <label className="block">
        <span className="text-xs font-black text-text-muted">Note</span>
        <textarea
          value={customer.note}
          onChange={(event) => onCustomerChange('note', event.target.value)}
          rows={2}
          className="mt-1 w-full rounded-elite border border-border-main bg-input-field px-3 py-2 text-sm font-semibold text-text-main outline-none focus:ring-2 focus:ring-primary/10"
          placeholder="Précision facultative"
        />
      </label>

      {successMessage && (
        <div className="flex gap-2 rounded-elite border border-emerald-200 bg-emerald-50 p-3 text-sm font-semibold text-emerald-800" role="status">
          <CheckCircle2 size={17} className="mt-0.5 shrink-0" /> {successMessage}
        </div>
      )}
      {errorMessage && (
        <div className="flex gap-2 rounded-elite border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-800" role="alert">
          <AlertCircle size={17} className="mt-0.5 shrink-0" /> {errorMessage}
        </div>
      )}

      <button
        type="submit"
        disabled={submitting || cartLines.length === 0}
        className="w-full rounded-elite px-4 py-3 text-sm font-black text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-offset-2"
        style={{ backgroundColor: 'var(--primary)' }}
      >
        {submitting ? 'Enregistrement…' : 'Enregistrer la commande'}
      </button>
      <p className="text-center text-[11px] font-semibold leading-relaxed text-text-muted">
        Cette action crée une commande DRAFT dans DigitalCrown. Elle n'est pas encore transmise au fournisseur.
      </p>
    </form>
  </div>
);

const Field = ({
  label,
  value,
  onChange,
  required = false,
  type = 'text',
  inputMode,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  type?: React.HTMLInputTypeAttribute;
  inputMode?: React.HTMLAttributes<HTMLInputElement>['inputMode'];
}) => (
  <label className="block">
    <span className="text-xs font-black text-text-muted">{label}</span>
    <input
      type={type}
      inputMode={inputMode}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      required={required}
      className="mt-1 w-full rounded-elite border border-border-main bg-input-field px-3 py-2 text-sm font-semibold text-text-main outline-none focus:ring-2 focus:ring-primary/10"
    />
  </label>
);

const StateCard = ({
  title,
  description,
  actionLabel,
  onAction,
}: {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}) => (
  <div className="rounded-elite-lg border border-border-main bg-card-bg p-8 text-center shadow-elite">
    <Package size={28} className="mx-auto text-text-muted" />
    <h3 className="mt-3 font-outfit text-xl font-black text-text-main">{title}</h3>
    <p className="mx-auto mt-2 max-w-lg text-sm font-medium leading-relaxed text-text-muted">{description}</p>
    {actionLabel && onAction && (
      <button
        type="button"
        onClick={onAction}
        className="mt-4 rounded-elite px-4 py-2 text-sm font-black text-white focus:outline-none focus:ring-2 focus:ring-offset-2"
        style={{ backgroundColor: 'var(--primary)' }}
      >
        {actionLabel}
      </button>
    )}
  </div>
);
