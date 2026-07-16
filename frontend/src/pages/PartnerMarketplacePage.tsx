import React, { useEffect, useMemo, useState } from 'react';
import {
  ShoppingCart,
  Search,
  Package,
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
  type PartnerProduct,
  buildPartnerProfile,
  formatMoney,
  normalizePartnerProduct,
  partnerCategories,
  partnerProducts,
  readStoredCart,
  writeStoredCart,
} from '../features/partnerMarketplace/data';

type StrategyPreset = {
  key: string;
  label: string;
  settlementBasis: string;
  revenueModel: string;
  commissionRate: number;
  discountRate: number;
  fixedFeeAmount: number;
  description: string;
};

type StoredPartnerOrder = {
  id: number;
  orderNumber: string;
  createdAt: string;
  partnerId: string;
  partnerName?: string;
  strategyLabel: string;
  settlementBasis: string;
  revenueModel: string;
  commissionRate: number;
  discountRate: number;
  fixedFeeAmount: number;
  customer: {
    fullName: string;
    clinic: string;
    phone: string;
    email: string;
    city: string;
    note: string;
  };
  lines: Array<{
    productId: string;
    name: string;
    sku: string;
    quantity: number;
    unitPrice: number;
    lineTotal: number;
  }>;
  estimatedTotal: number;
  sentTotal: number;
  currentTotal: number;
  recognizedBaseAmount: number;
  recognizedRevenueAmount: number;
  revenueDeltaAmount: number;
  status: string;
  partnerReference?: string | null;
  statusNote?: string | null;
};

type MetaPayload = {
  supportedStatuses: string[];
  strategyPresets: StrategyPreset[];
};

type CatalogMeta = {
  categories: string[];
  specialties: string[];
  availability: string[];
};

type ReconcileState = Record<number, { status: string; currentTotal: string; note: string; partnerReference: string; saving: boolean }>;

const buildStrategyPreview = (preset: StrategyPreset, amount: number) => {
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
  const [orders, setOrders] = useState<StoredPartnerOrder[]>([]);
  const [meta, setMeta] = useState<MetaPayload | null>(null);
  const [selectedStrategyKey, setSelectedStrategyKey] = useState('');
  const [reconcileState, setReconcileState] = useState<ReconcileState>({});
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [loadingOrders, setLoadingOrders] = useState(true);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogMeta, setCatalogMeta] = useState<CatalogMeta | null>(null);
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

  const loadCatalog = async () => {
    setCatalogLoading(true);
    try {
      const [metaRes, suppliersRes, productsRes] = await Promise.all([
        api.get('/partner-catalog/meta'),
        api.get('/partner-catalog/suppliers'),
        api.get('/partner-catalog/products'),
      ]);
      setCatalogMeta(metaRes.data || null);
      const nextSuppliers = (suppliersRes.data || []) as PartnerCatalogSupplier[];
      const nextProducts = ((productsRes.data || []) as PartnerCatalogProduct[]).map(normalizePartnerProduct);
      setSuppliers(nextSuppliers);
      setCatalogProducts(nextProducts.length ? nextProducts : partnerProducts);
    } catch {
      setCatalogProducts(partnerProducts);
    } finally {
      setCatalogLoading(false);
    }
  };

  const loadOrders = async () => {
    setLoadingOrders(true);
    try {
      const response = await api.get('/partner-orders');
      const nextOrders = response.data || [];
      setOrders(nextOrders);
      setReconcileState((current) => {
        const next = { ...current };
        nextOrders.forEach((order: StoredPartnerOrder) => {
          next[order.id] = next[order.id] || {
            status: order.status,
            currentTotal: String(order.currentTotal || order.estimatedTotal),
            note: order.statusNote || '',
            partnerReference: order.partnerReference || '',
            saving: false
          };
        });
        return next;
      });
    } catch {
      setErrorMessage('Impossible de charger les commandes partenaire pour le moment.');
    } finally {
      setLoadingOrders(false);
    }
  };

  useEffect(() => {
    let active = true;
    const bootstrap = async () => {
      try {
        const response = await api.get('/partner-orders/meta');
        if (!active) return;
        setMeta(response.data);
        const presets = response.data?.strategyPresets || [];
        if (presets.length > 0) {
          setSelectedStrategyKey((current) => current || presets[0].key);
        }
      } catch {
        if (active) {
          setErrorMessage('Impossible de charger les strategies partenaire.');
        }
      }
      if (active) {
        await Promise.all([loadOrders(), loadCatalog()]);
      }
    };

    bootstrap();
    return () => {
      active = false;
    };
  }, []);

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
        const product = catalogProducts.find((item) => item.id === productId) || partnerProducts.find((item) => item.id === productId);
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
      setSuccessMessage('Ajoutez au moins un produit avant de preparer la commande.');
      return;
    }
    if (!selectedStrategy) {
      setErrorMessage('Choisissez une strategie de remuneration avant d enregistrer la commande.');
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
      const order: StoredPartnerOrder = response.data;
      if (!order?.orderNumber) {
        throw new Error('La commande n a pas pu etre enregistree correctement.');
      }

      setOrders((current) => [order, ...current]);
      setReconcileState((current) => ({
        ...current,
        [order.id]: {
          status: order.status,
          currentTotal: String(order.currentTotal || order.estimatedTotal),
          note: '',
          partnerReference: '',
          saving: false
        }
      }));
      setCart({});
      setCustomer({ fullName: '', clinic: '', phone: '', email: '', city: '', note: '' });
      setSuccessMessage(`Commande ${order.orderNumber} enregistree avec la strategie "${order.strategyLabel}".`);
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || error?.message || 'Impossible d enregistrer la commande partenaire.');
    } finally {
      setSubmitting(false);
    }
  };

  const updateReconcileField = (orderId: number, patch: Partial<ReconcileState[number]>) => {
    setReconcileState((current) => ({
      ...current,
      [orderId]: {
        status: current[orderId]?.status || 'DRAFT',
        currentTotal: current[orderId]?.currentTotal || '0',
        note: current[orderId]?.note || '',
        partnerReference: current[orderId]?.partnerReference || '',
        saving: false,
        ...patch
      }
    }));
  };

  const handleReconcile = async (order: StoredPartnerOrder) => {
    const state = reconcileState[order.id];
    if (!state) return;
    updateReconcileField(order.id, { saving: true });
    setErrorMessage('');
    setSuccessMessage('');
    try {
      await api.patch(`/partner-orders/${order.id}`, {
        status: state.status,
        currentTotal: Number(state.currentTotal || order.currentTotal),
        note: state.note,
        partnerReference: state.partnerReference
      });
      await loadOrders();
      setSuccessMessage(`Commande ${order.orderNumber} reconciliee avec le statut ${state.status}.`);
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || error?.message || 'Impossible de mettre a jour la commande partenaire.');
    } finally {
      updateReconcileField(order.id, { saving: false });
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <section className="relative overflow-hidden rounded-[2rem] border border-border-main bg-card-bg shadow-elite">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.12),transparent_36%),radial-gradient(circle_at_top_right,rgba(16,185,129,0.10),transparent_28%),linear-gradient(135deg,rgba(255,255,255,0.96),rgba(248,250,252,0.94))]" />
        <div className="relative p-8 lg:p-10 grid grid-cols-1 xl:grid-cols-[1.25fr_0.75fr] gap-6">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary border border-primary/10 text-[10px] font-black uppercase tracking-widest">
              <Sparkles size={13} />
              Marketplace fournisseur integree
            </div>
            <div className="space-y-3 max-w-3xl">
              <h1 className="text-3xl md:text-4xl font-black tracking-tight text-slate-900">Un espace catalogue premium, sans sortir de DigitalCrown.</h1>
              <p className="text-slate-600 font-medium leading-relaxed">
                Cette vitrine garde les repares de l application, mais adopte une lecture plus catalogue: categories, specialites dentaires, fiches produit, panier et commande partenaire.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <InfoTile icon={<ShieldCheck size={14} />} tone="emerald" title="Integration sure" text="Le module reste isole du coeur patient, agenda et comptabilite." />
              <InfoTile icon={<Package size={14} />} tone="blue" title="Catalogue extensible" text="Ajout manuel aujourd hui, import API fournisseur demain." />
              <InfoTile icon={<Truck size={14} />} tone="amber" title="Suivi commercial" text="Les commandes envoyees restent reconciliees pour le calcul de revenu." />
            </div>
            <div className="flex flex-wrap gap-2">
              {specialtyOptions.map((item) => (
                <span key={item} className="inline-flex items-center gap-2 px-3 py-2 rounded-full border border-slate-200 bg-white/85 text-xs font-black text-slate-600 uppercase tracking-widest shadow-sm">
                  <Tags size={12} className="text-primary" />
                  {item}
                </span>
              ))}
            </div>
          </div>

          <aside className="rounded-[1.75rem] border border-slate-200 bg-slate-950 text-white p-6 lg:p-7 shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center">
                <ClipboardList size={22} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-widest font-black text-slate-400">{partnerProfile.badge}</p>
                <h2 className="text-xl font-black">{partnerProfile.name}</h2>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <MetricCard label="References" value={String(catalogProducts.length)} />
              <MetricCard label="Categories" value={String(Math.max(0, categoryOptions.length - 1))} />
              <MetricCard label="Panier" value={String(totalUnits)} />
              <MetricCard label="Commandes" value={String(orders.length)} />
            </div>
            {selectedStrategy && (
              <div className="rounded-[1.25rem] bg-white/5 border border-white/10 p-4">
                <p className="text-[10px] uppercase tracking-widest font-black text-slate-400 mb-2">Strategie active</p>
                <p className="font-black">{selectedStrategy.label}</p>
                <p className="text-sm text-slate-300 mt-2 leading-relaxed">{selectedStrategy.description}</p>
              </div>
            )}
            <div className={cn('grid gap-3', user?.is_superadmin ? 'grid-cols-1 md:grid-cols-3' : 'grid-cols-1 md:grid-cols-2')}>
              <Link to={`/approvisionnement/partenaire/${partnerProfile.id}`} className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-white/10 bg-white/5 text-sm font-black hover:bg-white/10 transition-colors">
                <Store size={15} />
                Fournisseur
              </Link>
              {user?.is_superadmin && (
                <Link to="/approvisionnement/admin" className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-white/10 bg-white/5 text-sm font-black hover:bg-white/10 transition-colors">
                  <Settings2 size={15} />
                  Dashboard
                </Link>
              )}
              <button type="button" onClick={loadCatalog} className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-white/10 bg-white/5 text-sm font-black hover:bg-white/10 transition-colors">
                <RefreshCw size={15} />
                Sync vue
              </button>
            </div>
          </aside>
        </div>
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-[0.95fr_1.45fr_0.7fr] gap-6">
        <aside className="space-y-5">
          <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm p-5 space-y-4 sticky top-6">
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">Recherche produit</p>
              <div className="relative">
                <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Reference, categorie, specialite"
                  className="w-full pl-11 pr-4 py-3 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-white"
                />
              </div>
            </div>
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">Categories</p>
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
                        : 'bg-slate-50 text-slate-500 border-slate-200 hover:border-slate-300'
                    )}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
            <div className="rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-4 space-y-3">
              <p className="text-[10px] font-black uppercase tracking-widest text-emerald-700">Promesse fournisseur</p>
              <p className="text-sm font-semibold text-emerald-900 leading-relaxed">{partnerProfile.promise}</p>
              <div className="space-y-2">
                {partnerProfile.coverage.slice(0, 3).map((item) => (
                  <div key={item} className="text-sm text-emerald-900/85 font-medium flex items-start gap-2">
                    <CheckCircle2 size={14} className="shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </aside>

        <section className="space-y-5">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {featuredProducts.map((product, index) => (
              <Link key={product.id} to={`/approvisionnement/produits/${product.id}`} className={cn(
                'relative overflow-hidden rounded-[1.75rem] border shadow-sm p-5 transition-all hover:-translate-y-1 hover:shadow-xl',
                index === 0 ? 'bg-slate-950 text-white border-slate-900' : 'bg-white border-slate-200'
              )}>
                <div className={cn('absolute inset-0 opacity-70 pointer-events-none', index === 0 ? 'bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.28),transparent_30%)]' : 'bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.08),transparent_28%)]')} />
                <div className="relative space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className={cn('px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border', index === 0 ? 'border-white/10 bg-white/10 text-white' : 'border-slate-200 bg-slate-50 text-slate-500')}>
                      {index === 0 ? 'Selection premium' : 'Top rotation'}
                    </span>
                    <ArrowRight size={16} className={index === 0 ? 'text-white/70' : 'text-slate-400'} />
                  </div>
                  <div>
                    <p className={cn('text-[10px] font-black uppercase tracking-widest mb-2', index === 0 ? 'text-slate-300' : 'text-slate-400')}>
                      {product.category} | {product.specialty || 'General Dentistry'}
                    </p>
                    <h3 className={cn('text-lg font-black leading-tight', index === 0 ? 'text-white' : 'text-slate-900')}>{product.name}</h3>
                    <p className={cn('text-sm mt-2 leading-relaxed min-h-[42px]', index === 0 ? 'text-slate-300' : 'text-slate-500')}>{product.description}</p>
                  </div>
                  <div className="flex items-end justify-between gap-3">
                    <div>
                      <p className={cn('text-2xl font-black', index === 0 ? 'text-white' : 'text-slate-900')}>{formatMoney(product.price)}</p>
                      {product.originalPrice && (
                        <p className={cn('text-xs font-bold mt-1 line-through', index === 0 ? 'text-slate-400' : 'text-slate-400')}>
                          {formatMoney(product.originalPrice)}
                        </p>
                      )}
                    </div>
                    <span className={cn(
                      'px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border whitespace-nowrap',
                      product.availability === 'Disponible'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'
                    )}>
                      {product.availability}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {catalogLoading ? (
              <p className="text-sm text-slate-500">Chargement du catalogue partenaire...</p>
            ) : filteredProducts.length === 0 ? (
              <p className="text-sm text-slate-500">Aucun produit ne correspond aux filtres actuels.</p>
            ) : (
              filteredProducts.map((product) => (
                <article key={product.id} className="bg-white rounded-[1.75rem] border border-slate-200 shadow-sm p-6 space-y-4 transition-all hover:-translate-y-1 hover:shadow-xl">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">
                        {product.category} | {product.specialty || 'General Dentistry'}
                      </p>
                      <Link to={`/approvisionnement/produits/${product.id}`} className="text-lg font-black text-slate-900 leading-tight hover:text-primary transition-colors">
                        {product.name}
                      </Link>
                      <p className="text-xs text-slate-400 font-bold uppercase tracking-widest mt-2">{product.sku}</p>
                    </div>
                    <span className={cn(
                      'px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border whitespace-nowrap',
                      product.availability === 'Disponible'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'
                    )}>
                      {product.availability}
                    </span>
                  </div>
                  <p className="text-sm text-slate-500 leading-relaxed min-h-[42px]">{product.description}</p>
                  <div className="rounded-[1.25rem] bg-slate-50 border border-slate-200 p-4">
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Pour qui</p>
                    <p className="text-sm font-semibold text-slate-700">{product.audience || product.specialty || 'Cabinet dentaire'}</p>
                  </div>
                  <div className="flex items-end justify-between gap-4">
                    <div>
                      <p className="text-2xl font-black text-slate-900">{formatMoney(product.price)}</p>
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Prix indicatif | unite {product.unit}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button type="button" onClick={() => adjustQty(product.id, -1)} className="w-9 h-9 rounded-xl border border-slate-200 text-slate-600 flex items-center justify-center hover:bg-slate-50 transition-colors">
                        <Minus size={14} />
                      </button>
                      <div className="w-10 text-center font-black text-slate-900">{cart[product.id] ?? 0}</div>
                      <button type="button" onClick={() => adjustQty(product.id, 1)} className="w-9 h-9 rounded-xl bg-primary text-white flex items-center justify-center hover:brightness-110 transition-all">
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>
                  <Link to={`/approvisionnement/produits/${product.id}`} className="inline-flex items-center text-sm font-black text-primary hover:underline">
                    Voir la fiche produit
                  </Link>
                </article>
              ))
            )}
          </div>
        </section>

        <aside className="space-y-5">
          <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-11 h-11 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
                <ShoppingCart size={20} />
              </div>
              <div>
                <h2 className="text-lg font-black text-slate-900">Commande partenaire</h2>
                <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Panier, contact et strategie</p>
              </div>
            </div>

            <div className="p-4 rounded-[1.25rem] border border-amber-200 bg-amber-50 text-amber-800 text-sm font-medium leading-relaxed mb-4">
              La commande est d abord creee en brouillon. Ensuite tu peux la marquer envoyee, modifiee, confirmee, livree ou annulee pour recalculer ton revenu.
            </div>

            <div className="space-y-3 mb-5">
              {cartLines.length === 0 ? (
                <div className="text-sm text-slate-500 bg-slate-50 border border-slate-200 rounded-[1.25rem] p-4">
                  Aucun produit selectionne pour le moment.
                </div>
              ) : (
                cartLines.map((line) => (
                  <div key={line.id} className="border border-slate-200 rounded-[1.25rem] p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-black text-slate-900">{line.name}</p>
                        <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mt-1">{line.sku}</p>
                      </div>
                      <p className="font-black text-slate-900">{formatMoney(line.lineTotal)}</p>
                    </div>
                    <div className="flex items-center justify-between mt-3 text-sm text-slate-500">
                      <span>{line.quantity} x {formatMoney(line.price)}</span>
                      <span>{line.unit}</span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="space-y-2 pb-5 border-b border-slate-100">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Lignes</span>
                <span className="font-black text-slate-900">{cartLines.length}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Unites</span>
                <span className="font-black text-slate-900">{totalUnits}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Total estime</span>
                <span className="text-xl font-black text-slate-900">{formatMoney(estimatedTotal)}</span>
              </div>
            </div>

            <form onSubmit={submitOrder} className="space-y-3 pt-5">
              <div>
                <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Strategie partenaire</label>
                <select
                  value={selectedStrategyKey}
                  onChange={(event) => setSelectedStrategyKey(event.target.value)}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-white"
                >
                  {(meta?.strategyPresets || []).map((preset) => (
                    <option key={preset.key} value={preset.key}>{preset.label}</option>
                  ))}
                </select>
              </div>

              {selectedStrategy && (
                <div className="rounded-[1.25rem] border border-slate-200 bg-slate-50 p-4 space-y-2">
                  <div className="flex items-center gap-2 text-slate-700 text-xs font-black uppercase tracking-widest">
                    <Calculator size={14} />
                    Simulation de revenu
                  </div>
                  <p className="text-sm text-slate-600">{selectedStrategy.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-500">Base choisie</span>
                    <span className="font-black text-slate-900">{selectedStrategy.settlementBasis}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-500">Revenu theorique</span>
                    <span className="font-black text-slate-900">{formatMoney(previewRevenue)}</span>
                  </div>
                </div>
              )}

              <InputField label="Nom complet" value={customer.fullName} onChange={(value) => setCustomer((prev) => ({ ...prev, fullName: value }))} required />
              <InputField label="Cabinet" value={customer.clinic} onChange={(value) => setCustomer((prev) => ({ ...prev, clinic: value }))} required />
              <div className="grid grid-cols-2 gap-3">
                <InputField label="Telephone" value={customer.phone} onChange={(value) => setCustomer((prev) => ({ ...prev, phone: value }))} required />
                <InputField label="Ville" value={customer.city} onChange={(value) => setCustomer((prev) => ({ ...prev, city: value }))} required />
              </div>
              <InputField label="Email" type="email" value={customer.email} onChange={(value) => setCustomer((prev) => ({ ...prev, email: value }))} required />
              <div>
                <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Note</label>
                <textarea
                  value={customer.note}
                  onChange={(event) => setCustomer((prev) => ({ ...prev, note: event.target.value }))}
                  rows={3}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-white resize-none"
                  placeholder="Instruction de commande ou precision utile"
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3 rounded-xl bg-slate-900 text-white font-black uppercase tracking-widest text-xs hover:bg-black transition-colors disabled:opacity-60"
              >
                {submitting ? 'Enregistrement...' : 'Enregistrer la commande partenaire'}
              </button>
              {successMessage && (
                <div className="rounded-[1.25rem] border border-emerald-200 bg-emerald-50 text-emerald-800 p-4 text-sm font-medium leading-relaxed flex gap-3">
                  <CheckCircle2 size={18} className="shrink-0 mt-0.5" />
                  <span>{successMessage}</span>
                </div>
              )}
              {errorMessage && (
                <div className="rounded-[1.25rem] border border-rose-200 bg-rose-50 text-rose-800 p-4 text-sm font-medium leading-relaxed">
                  {errorMessage}
                </div>
              )}
            </form>
          </div>

          <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm p-6">
            <div className="flex items-center justify-between gap-3 mb-4">
              <h3 className="text-sm font-black uppercase tracking-widest text-slate-400">Reconciliation des commandes</h3>
              <button
                type="button"
                onClick={loadOrders}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200 text-xs font-black uppercase tracking-widest text-slate-600 hover:bg-slate-50"
              >
                <RefreshCw size={12} />
                Recharger
              </button>
            </div>
            <div className="space-y-4">
              {loadingOrders ? (
                <p className="text-sm text-slate-500">Chargement des commandes partenaire...</p>
              ) : orders.length === 0 ? (
                <p className="text-sm text-slate-500">Aucune commande partenaire enregistree pour le moment.</p>
              ) : (
                orders.slice(0, 4).map((order) => {
                  const state = reconcileState[order.id] || {
                    status: order.status,
                    currentTotal: String(order.currentTotal || order.estimatedTotal),
                    note: order.statusNote || '',
                    partnerReference: order.partnerReference || '',
                    saving: false
                  };
                  return (
                    <div key={order.orderNumber} className="border border-slate-200 rounded-[1.25rem] p-4 space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-black text-slate-900">{order.orderNumber}</p>
                          <p className="text-sm text-slate-500 mt-1">{order.strategyLabel}</p>
                        </div>
                        <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-[10px] font-black uppercase tracking-widest">
                          {order.status}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="rounded-xl bg-slate-50 p-3">
                          <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest">Total courant</p>
                          <p className="font-black text-slate-900 mt-1">{formatMoney(order.currentTotal)}</p>
                        </div>
                        <div className="rounded-xl bg-slate-50 p-3">
                          <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest">Revenu reconnu</p>
                          <p className="font-black text-slate-900 mt-1">{formatMoney(order.recognizedRevenueAmount)}</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Nouveau statut</label>
                          <select
                            value={state.status}
                            onChange={(event) => updateReconcileField(order.id, { status: event.target.value })}
                            className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-white"
                          >
                            {(meta?.supportedStatuses || []).map((statusValue) => (
                              <option key={statusValue} value={statusValue}>{statusValue}</option>
                            ))}
                          </select>
                        </div>
                        <InputField
                          label="Total courant"
                          type="number"
                          value={state.currentTotal}
                          onChange={(value) => updateReconcileField(order.id, { currentTotal: value })}
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <InputField
                          label="Reference partenaire"
                          value={state.partnerReference}
                          onChange={(value) => updateReconcileField(order.id, { partnerReference: value })}
                        />
                        <InputField
                          label="Note"
                          value={state.note}
                          onChange={(value) => updateReconcileField(order.id, { note: value })}
                        />
                      </div>

                      <button
                        type="button"
                        disabled={state.saving}
                        onClick={() => handleReconcile(order)}
                        className="w-full py-3 rounded-xl border border-slate-200 text-slate-800 font-black uppercase tracking-widest text-xs hover:bg-slate-50 disabled:opacity-60"
                      >
                        {state.saving ? 'Mise a jour...' : 'Appliquer le recalcul'}
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};

const MetricCard = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-[1.25rem] bg-white/5 border border-white/10 px-4 py-4">
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
    <div className={cn('rounded-[1.25rem] px-4 py-4 border', tones[tone])}>
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
    <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">{label}</label>
    <input
      type={type}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      required={required}
      className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-white"
    />
  </div>
);

export default PartnerMarketplacePage;
