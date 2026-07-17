import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, ClipboardList, Layers3, Plus, RefreshCw, Store } from 'lucide-react';
import { api } from '../services/api';
import { cn } from '../utils/cn';
import { formatMoney } from '../features/partnerMarketplace/data';

type Supplier = {
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

type Product = {
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

type Meta = {
  categories: string[];
  specialties: string[];
  availability: string[];
};

type PartnerOrder = {
  id: number;
  orderNumber: string;
  partnerName?: string;
  strategyLabel: string;
  status: string;
  estimatedTotal: number;
  currentTotal: number;
  recognizedRevenueAmount: number;
  partnerReference?: string | null;
  statusNote?: string | null;
};

type OrdersMeta = {
  supportedStatuses: string[];
};

type ReconcileState = Record<number, { status: string; currentTotal: string; note: string; partnerReference: string; saving: boolean }>;

const emptySupplier = {
  supplierKey: '',
  name: '',
  badge: '',
  description: '',
  promise: '',
  apiBaseUrl: '',
  syncMode: 'manual',
  isActive: true,
};

const emptyProduct = {
  supplierId: '',
  externalProductId: '',
  name: '',
  sku: '',
  dentalCategory: '',
  dentalSpecialty: '',
  unit: 'boite',
  price: '0',
  availability: 'AVAILABLE',
  shortDescription: '',
  longDescription: '',
  benefits: '',
  isFeatured: false,
  sortOrder: '0',
};

export const PartnerCatalogAdminPage: React.FC = () => {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [supplierForm, setSupplierForm] = useState(emptySupplier);
  const [productForm, setProductForm] = useState(emptyProduct);
  const [filters, setFilters] = useState({ supplierId: 'all', category: 'all', specialty: 'all', q: '' });
  const [loading, setLoading] = useState(true);
  const [savingSupplier, setSavingSupplier] = useState(false);
  const [savingProduct, setSavingProduct] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const [orders, setOrders] = useState<PartnerOrder[]>([]);
  const [ordersMeta, setOrdersMeta] = useState<OrdersMeta | null>(null);
  const [loadingOrders, setLoadingOrders] = useState(true);
  const [reconcileState, setReconcileState] = useState<ReconcileState>({});

  const loadAll = async () => {
    setLoading(true);
    try {
      const [metaRes, suppliersRes, productsRes] = await Promise.all([
        api.get('/partner-catalog/meta'),
        api.get('/partner-catalog/suppliers'),
        api.get('/partner-catalog/products'),
      ]);
      setMeta(metaRes.data);
      setSuppliers(suppliersRes.data || []);
      setProducts(productsRes.data || []);
      if (!productForm.dentalCategory && metaRes.data?.categories?.length) {
        setProductForm((current) => ({
          ...current,
          dentalCategory: current.dentalCategory || metaRes.data.categories[0],
          dentalSpecialty: current.dentalSpecialty || metaRes.data.specialties?.[0] || '',
          availability: current.availability || metaRes.data.availability?.[0] || 'AVAILABLE',
        }));
      }
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || 'Impossible de charger le dashboard catalogue partenaire.');
    } finally {
      setLoading(false);
    }
  };

  const loadOrders = async () => {
    setLoadingOrders(true);
    try {
      const [ordersRes, ordersMetaRes] = await Promise.all([
        api.get('/partner-orders'),
        api.get('/partner-orders/meta'),
      ]);
      const nextOrders = (ordersRes.data || []) as PartnerOrder[];
      setOrders(nextOrders);
      setOrdersMeta(ordersMetaRes.data || null);
      setReconcileState((current) => {
        const next = { ...current };
        nextOrders.forEach((order) => {
          next[order.id] = next[order.id] || {
            status: order.status,
            currentTotal: String(order.currentTotal || order.estimatedTotal),
            note: order.statusNote || '',
            partnerReference: order.partnerReference || '',
            saving: false,
          };
        });
        return next;
      });
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || 'Impossible de charger les commandes partenaire.');
    } finally {
      setLoadingOrders(false);
    }
  };

  useEffect(() => {
    loadAll();
    loadOrders();
  }, []);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      const matchSupplier = filters.supplierId === 'all' || String(product.supplierId) === filters.supplierId;
      const matchCategory = filters.category === 'all' || product.dentalCategory === filters.category;
      const matchSpecialty = filters.specialty === 'all' || product.dentalSpecialty === filters.specialty;
      const q = filters.q.trim().toLowerCase();
      const haystack = `${product.name} ${product.sku} ${product.shortDescription || ''}`.toLowerCase();
      const matchQuery = !q || haystack.includes(q);
      return matchSupplier && matchCategory && matchSpecialty && matchQuery;
    });
  }, [products, filters]);

  const handleCreateSupplier = async (event: React.FormEvent) => {
    event.preventDefault();
    setSavingSupplier(true);
    setSuccessMessage('');
    setErrorMessage('');
    try {
      await api.post('/partner-catalog/suppliers', {
        supplierKey: supplierForm.supplierKey,
        name: supplierForm.name,
        badge: supplierForm.badge || null,
        description: supplierForm.description || null,
        promise: supplierForm.promise || null,
        apiBaseUrl: supplierForm.apiBaseUrl || null,
        syncMode: supplierForm.syncMode || 'manual',
        isActive: supplierForm.isActive,
      });
      setSupplierForm(emptySupplier);
      setSuccessMessage('Fournisseur partenaire ajoute.');
      await loadAll();
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || "Impossible d'ajouter le fournisseur.");
    } finally {
      setSavingSupplier(false);
    }
  };

  const handleCreateProduct = async (event: React.FormEvent) => {
    event.preventDefault();
    setSavingProduct(true);
    setSuccessMessage('');
    setErrorMessage('');
    try {
      await api.post('/partner-catalog/products', {
        supplierId: Number(productForm.supplierId),
        externalProductId: productForm.externalProductId || null,
        name: productForm.name,
        sku: productForm.sku,
        dentalCategory: productForm.dentalCategory,
        dentalSpecialty: productForm.dentalSpecialty,
        unit: productForm.unit,
        price: Number(productForm.price),
        availability: productForm.availability,
        shortDescription: productForm.shortDescription || null,
        longDescription: productForm.longDescription || null,
        benefits: productForm.benefits.split('\n').map((item) => item.trim()).filter(Boolean),
        isFeatured: productForm.isFeatured,
        sortOrder: Number(productForm.sortOrder || 0),
      });
      setProductForm((current) => ({
        ...emptyProduct,
        dentalCategory: current.dentalCategory,
        dentalSpecialty: current.dentalSpecialty,
        availability: current.availability,
      }));
      setSuccessMessage('Produit partenaire ajoute.');
      await loadAll();
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || "Impossible d'ajouter le produit.");
    } finally {
      setSavingProduct(false);
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
        ...patch,
      },
    }));
  };

  const handleReconcile = async (order: PartnerOrder) => {
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
        partnerReference: state.partnerReference,
      });
      await loadOrders();
      setSuccessMessage(`Commande ${order.orderNumber} réconciliée avec le statut ${state.status}.`);
    } catch (error: any) {
      setErrorMessage(error?.response?.data?.detail || error?.message || 'Impossible de mettre à jour la commande partenaire.');
    } finally {
      updateReconcileField(order.id, { saving: false });
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between gap-4">
        <Link to="/approvisionnement" className="inline-flex items-center gap-2 px-4 py-3 rounded-elite border border-border-main text-sm font-black text-slate-700 hover:bg-slate-50">
          <ArrowLeft size={16} />
          Retour marketplace
        </Link>
        <button
          type="button"
          onClick={() => { loadAll(); loadOrders(); }}
          className="inline-flex items-center gap-2 px-4 py-3 rounded-elite bg-slate-900 text-white text-sm font-black hover:bg-black"
        >
          <RefreshCw size={16} />
          Recharger
        </button>
      </div>

      {successMessage && <div className="rounded-elite border border-emerald-200 bg-emerald-50 text-emerald-800 p-4 text-sm font-medium">{successMessage}</div>}
      {errorMessage && <div className="rounded-elite border border-rose-200 bg-rose-50 text-rose-800 p-4 text-sm font-medium">{errorMessage}</div>}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <section className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-elite bg-primary/10 text-primary flex items-center justify-center">
              <Store size={20} />
            </div>
            <div>
              <h2 className="font-outfit text-lg font-black text-slate-900">Ajouter un fournisseur</h2>
              <p className="text-xs font-bold uppercase tracking-widest text-text-muted">Base pour futur import API fournisseur</p>
            </div>
          </div>
          <form onSubmit={handleCreateSupplier} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Input label="Clé fournisseur" value={supplierForm.supplierKey} onChange={(value) => setSupplierForm((current) => ({ ...current, supplierKey: value }))} required />
            <Input label="Nom fournisseur" value={supplierForm.name} onChange={(value) => setSupplierForm((current) => ({ ...current, name: value }))} required />
            <Input label="Badge" value={supplierForm.badge} onChange={(value) => setSupplierForm((current) => ({ ...current, badge: value }))} />
            <Input label="API base URL" value={supplierForm.apiBaseUrl} onChange={(value) => setSupplierForm((current) => ({ ...current, apiBaseUrl: value }))} />
            <Input label="Sync mode" value={supplierForm.syncMode} onChange={(value) => setSupplierForm((current) => ({ ...current, syncMode: value }))} />
            <Toggle label="Actif" checked={supplierForm.isActive} onChange={(checked) => setSupplierForm((current) => ({ ...current, isActive: checked }))} />
            <TextArea label="Description" value={supplierForm.description} onChange={(value) => setSupplierForm((current) => ({ ...current, description: value }))} />
            <TextArea label="Promesse" value={supplierForm.promise} onChange={(value) => setSupplierForm((current) => ({ ...current, promise: value }))} />
            <div className="md:col-span-2">
              <button type="submit" disabled={savingSupplier} className="w-full py-3 rounded-elite bg-slate-900 text-white font-black uppercase tracking-widest text-xs disabled:opacity-60">
                {savingSupplier ? 'Enregistrement...' : 'Ajouter fournisseur'}
              </button>
            </div>
          </form>
        </section>

        <section className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-elite bg-primary/10 text-primary flex items-center justify-center">
              <Plus size={20} />
            </div>
            <div>
              <h2 className="font-outfit text-lg font-black text-slate-900">Ajouter un produit</h2>
              <p className="text-xs font-bold uppercase tracking-widest text-text-muted">Tri par catégorie et spécialité dentaire</p>
            </div>
          </div>
          <form onSubmit={handleCreateProduct} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Select label="Fournisseur" value={productForm.supplierId} onChange={(value) => setProductForm((current) => ({ ...current, supplierId: value }))} options={suppliers.map((supplier) => ({ value: String(supplier.id), label: supplier.name }))} required />
            <Input label="Référence externe" value={productForm.externalProductId} onChange={(value) => setProductForm((current) => ({ ...current, externalProductId: value }))} />
            <Input label="Nom produit" value={productForm.name} onChange={(value) => setProductForm((current) => ({ ...current, name: value }))} required />
            <Input label="SKU" value={productForm.sku} onChange={(value) => setProductForm((current) => ({ ...current, sku: value }))} required />
            <Select label="Catégorie" value={productForm.dentalCategory} onChange={(value) => setProductForm((current) => ({ ...current, dentalCategory: value }))} options={(meta?.categories || []).map((item) => ({ value: item, label: item }))} required />
            <Select label="Spécialité" value={productForm.dentalSpecialty} onChange={(value) => setProductForm((current) => ({ ...current, dentalSpecialty: value }))} options={(meta?.specialties || []).map((item) => ({ value: item, label: item }))} required />
            <Input label="Unité" value={productForm.unit} onChange={(value) => setProductForm((current) => ({ ...current, unit: value }))} required />
            <Input label="Prix" type="number" value={productForm.price} onChange={(value) => setProductForm((current) => ({ ...current, price: value }))} required />
            <Select label="Disponibilité" value={productForm.availability} onChange={(value) => setProductForm((current) => ({ ...current, availability: value }))} options={(meta?.availability || []).map((item) => ({ value: item, label: item }))} required />
            <Input label="Ordre tri" type="number" value={productForm.sortOrder} onChange={(value) => setProductForm((current) => ({ ...current, sortOrder: value }))} />
            <TextArea label="Description courte" value={productForm.shortDescription} onChange={(value) => setProductForm((current) => ({ ...current, shortDescription: value }))} />
            <TextArea label="Description longue" value={productForm.longDescription} onChange={(value) => setProductForm((current) => ({ ...current, longDescription: value }))} />
            <TextArea label="Bénéfices (une ligne par item)" value={productForm.benefits} onChange={(value) => setProductForm((current) => ({ ...current, benefits: value }))} />
            <Toggle label="Produit mis en avant" checked={productForm.isFeatured} onChange={(checked) => setProductForm((current) => ({ ...current, isFeatured: checked }))} />
            <div className="md:col-span-2">
              <button type="submit" disabled={savingProduct || !suppliers.length} className="w-full py-3 rounded-elite bg-slate-900 text-white font-black uppercase tracking-widest text-xs disabled:opacity-60">
                {savingProduct ? 'Enregistrement...' : 'Ajouter produit'}
              </button>
            </div>
          </form>
        </section>
      </div>

      <section className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6 space-y-5">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-elite bg-primary/10 text-primary flex items-center justify-center">
            <Layers3 size={20} />
          </div>
          <div>
            <h2 className="font-outfit text-lg font-black text-slate-900">Catalogue fournisseur</h2>
            <p className="text-xs font-bold uppercase tracking-widest text-text-muted">Vue triable par fournisseur, catégorie et spécialité</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <Select label="Fournisseur" value={filters.supplierId} onChange={(value) => setFilters((current) => ({ ...current, supplierId: value }))} options={[{ value: 'all', label: 'Tous les fournisseurs' }, ...suppliers.map((supplier) => ({ value: String(supplier.id), label: supplier.name }))]} />
          <Select label="Catégorie" value={filters.category} onChange={(value) => setFilters((current) => ({ ...current, category: value }))} options={[{ value: 'all', label: 'Toutes les catégories' }, ...(meta?.categories || []).map((item) => ({ value: item, label: item }))]} />
          <Select label="Spécialité" value={filters.specialty} onChange={(value) => setFilters((current) => ({ ...current, specialty: value }))} options={[{ value: 'all', label: 'Toutes les spécialités' }, ...(meta?.specialties || []).map((item) => ({ value: item, label: item }))]} />
          <Input label="Recherche" value={filters.q} onChange={(value) => setFilters((current) => ({ ...current, q: value }))} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {loading ? (
            <p className="text-sm text-text-muted">Chargement du catalogue...</p>
          ) : filteredProducts.length === 0 ? (
            <div className="col-span-full flex flex-col items-center text-center gap-2 rounded-elite border border-dashed border-border-main bg-slate-50 px-6 py-10">
              <p className="font-black text-slate-900">Aucun produit ne correspond aux filtres</p>
              <p className="text-sm text-text-muted">Ajoutez un produit ci-dessus ou ajustez les filtres.</p>
            </div>
          ) : (
            filteredProducts.map((product) => (
              <article key={product.id} className="border border-border-main rounded-elite p-5 bg-slate-50 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-2">{product.dentalCategory} · {product.dentalSpecialty}</p>
                    <h3 className="font-outfit text-lg font-black text-slate-900">{product.name}</h3>
                    <p className="text-sm text-text-muted mt-1">{product.supplierName} · {product.sku}</p>
                  </div>
                  <span className={cn(
                    'px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border whitespace-nowrap',
                    product.availability === 'AVAILABLE' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                    product.availability === 'ON_REQUEST' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                    'bg-slate-100 text-slate-500 border-slate-200'
                  )}>
                    {product.availability}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <Stat label="Prix" value={`${product.price} MAD`} />
                  <Stat label="Unité" value={product.unit} />
                  <Stat label="Ordre" value={String(product.sortOrder)} />
                </div>
                <div className="rounded-elite bg-card-bg p-3 border border-border-main">
                  <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">Description courte</p>
                  <p className="text-sm text-slate-600">{product.shortDescription || 'Non renseignée'}</p>
                </div>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6 space-y-5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-elite bg-primary/10 text-primary flex items-center justify-center">
              <ClipboardList size={20} />
            </div>
            <div>
              <h2 className="font-outfit text-lg font-black text-slate-900">Commandes partenaire</h2>
              <p className="text-xs font-bold uppercase tracking-widest text-text-muted">Suivi et réconciliation des commandes envoyées</p>
            </div>
          </div>
          <button
            type="button"
            onClick={loadOrders}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-elite border border-border-main text-xs font-black uppercase tracking-widest text-slate-600 hover:bg-slate-50"
          >
            <RefreshCw size={12} />
            Recharger
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {loadingOrders ? (
            <p className="text-sm text-text-muted">Chargement des commandes partenaire...</p>
          ) : orders.length === 0 ? (
            <div className="col-span-full flex flex-col items-center text-center gap-2 rounded-elite border border-dashed border-border-main bg-slate-50 px-6 py-10">
              <p className="font-black text-slate-900">Aucune commande partenaire enregistrée</p>
              <p className="text-sm text-text-muted">Les commandes passées depuis la marketplace apparaîtront ici pour réconciliation.</p>
            </div>
          ) : (
            orders.map((order) => {
              const state = reconcileState[order.id] || {
                status: order.status,
                currentTotal: String(order.currentTotal || order.estimatedTotal),
                note: order.statusNote || '',
                partnerReference: order.partnerReference || '',
                saving: false,
              };
              return (
                <div key={order.orderNumber} className="border border-border-main rounded-elite p-4 space-y-3 bg-slate-50">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-black text-slate-900">{order.orderNumber}</p>
                      <p className="text-sm text-text-muted mt-1">{order.strategyLabel}</p>
                    </div>
                    <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-[10px] font-black uppercase tracking-widest">
                      {order.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded-elite bg-card-bg p-3 border border-border-main">
                      <p className="text-text-muted text-[10px] font-black uppercase tracking-widest">Total courant</p>
                      <p className="font-black text-slate-900 mt-1">{formatMoney(order.currentTotal)}</p>
                    </div>
                    <div className="rounded-elite bg-card-bg p-3 border border-border-main">
                      <p className="text-text-muted text-[10px] font-black uppercase tracking-widest">Revenu reconnu</p>
                      <p className="font-black text-slate-900 mt-1">{formatMoney(order.recognizedRevenueAmount)}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <Select
                      label="Nouveau statut"
                      value={state.status}
                      onChange={(value) => updateReconcileField(order.id, { status: value })}
                      options={(ordersMeta?.supportedStatuses || []).map((statusValue) => ({ value: statusValue, label: statusValue }))}
                    />
                    <Input
                      label="Total courant"
                      type="number"
                      value={state.currentTotal}
                      onChange={(value) => updateReconcileField(order.id, { currentTotal: value })}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <Input
                      label="Référence partenaire"
                      value={state.partnerReference}
                      onChange={(value) => updateReconcileField(order.id, { partnerReference: value })}
                    />
                    <Input
                      label="Note"
                      value={state.note}
                      onChange={(value) => updateReconcileField(order.id, { note: value })}
                    />
                  </div>

                  <button
                    type="button"
                    disabled={state.saving}
                    onClick={() => handleReconcile(order)}
                    className="w-full py-3 rounded-elite border border-border-main bg-card-bg text-slate-800 font-black uppercase tracking-widest text-xs hover:bg-slate-50 disabled:opacity-60"
                  >
                    {state.saving ? 'Mise à jour...' : 'Appliquer le recalcul'}
                  </button>
                </div>
              );
            })
          )}
        </div>
      </section>
    </div>
  );
};

const Input = ({
  label,
  value,
  onChange,
  type = 'text',
  required = false,
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

const TextArea = ({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) => (
  <div>
    <label className="block text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">{label}</label>
    <textarea
      value={value}
      onChange={(event) => onChange(event.target.value)}
      rows={3}
      className="w-full px-4 py-3 border border-border-main rounded-elite text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-card-bg resize-none"
    />
  </div>
);

const Select = ({
  label,
  value,
  onChange,
  options,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  required?: boolean;
}) => (
  <div>
    <label className="block text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">{label}</label>
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      required={required}
      className="w-full px-4 py-3 border border-border-main rounded-elite text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-card-bg"
    >
      <option value="">Selectionner</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>{option.label}</option>
      ))}
    </select>
  </div>
);

const Toggle = ({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) => (
  <div className="rounded-elite border border-border-main px-4 py-3 flex items-center justify-between">
    <span className="text-sm font-black text-slate-700">{label}</span>
    <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="w-4 h-4" />
  </div>
);

const Stat = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-elite bg-card-bg p-3 border border-border-main">
    <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">{label}</p>
    <p className="text-sm font-black text-slate-900 mt-1">{value}</p>
  </div>
);

export default PartnerCatalogAdminPage;
