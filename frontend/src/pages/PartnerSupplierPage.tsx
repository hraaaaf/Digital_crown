import React, { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Box, CheckCircle2, PackageOpen, RefreshCw, Store, Tags, Truck, Sparkles } from 'lucide-react';
import { cn } from '../utils/cn';
import { api } from '../services/api';
import { useAuthStore } from '../stores/useAuthStore';
import {
  type PartnerCatalogProduct,
  type PartnerMarketplaceCatalogMeta,
  type PartnerCatalogSupplier,
  type PartnerProduct,
  availabilityBadgeClass,
  buildPartnerProfile,
  formatMoney,
  normalizePartnerProduct,
  partnerCategories,
  readMarketplaceCache,
  readStoredCart,
  writeMarketplaceCache,
} from '../features/partnerMarketplace/data';

export const PartnerSupplierPage: React.FC = () => {
  const { partnerId } = useParams();
  const user = useAuthStore((state) => state.user);
  const [activeCategory, setActiveCategory] = useState('Toutes');
  const [activeSpecialty, setActiveSpecialty] = useState('Toutes');
  const [supplier, setSupplier] = useState<PartnerCatalogSupplier | null>(null);
  const [products, setProducts] = useState<PartnerProduct[]>([]);
  const [meta, setMeta] = useState<PartnerMarketplaceCatalogMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const cartUnits = Object.values(readStoredCart()).reduce((sum, qty) => sum + qty, 0);

  const hydrateFromCache = () => {
    const cached = readMarketplaceCache(user);
    if (!cached) return false;
    const cachedSuppliers = cached.suppliers;
    const matchedSupplier = cachedSuppliers.find((item) => String(item.id) === partnerId) || cachedSuppliers[0] || null;
    const supplierProducts = matchedSupplier
      ? cached.products.filter((product) => product.supplierId === String(matchedSupplier.id))
      : cached.products;
    setMeta(cached.catalogMeta);
    setSupplier(matchedSupplier);
    setProducts(supplierProducts);
    return true;
  };

  const loadSupplierView = async () => {
    setLoading(true);
    setLoadError(false);
    const hadCache = hydrateFromCache();
    try {
      const [metaRes, suppliersRes, productsRes] = await Promise.all([
        api.get('/partner-catalog/meta'),
        api.get('/partner-catalog/suppliers'),
        api.get('/partner-catalog/products'),
      ]);
      const nextSuppliers = (suppliersRes.data || []) as PartnerCatalogSupplier[];
      const matchedSupplier = nextSuppliers.find((item) => String(item.id) === partnerId) || nextSuppliers[0] || null;
      const normalizedProducts = ((productsRes.data || []) as PartnerCatalogProduct[]).map(normalizePartnerProduct);
      const supplierProducts = matchedSupplier
        ? normalizedProducts.filter((product) => product.supplierId === String(matchedSupplier.id))
        : normalizedProducts;

      setMeta(metaRes.data || null);
      setSupplier(matchedSupplier);
      setProducts(supplierProducts);
      writeMarketplaceCache(user, {
        strategyPresets: readMarketplaceCache(user)?.strategyPresets || [],
        catalogMeta: (metaRes.data || null) as PartnerMarketplaceCatalogMeta | null,
        suppliers: nextSuppliers,
        products: normalizedProducts,
      });
    } catch {
      if (!hadCache) {
        setSupplier(null);
        setProducts([]);
      }
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    hydrateFromCache();
    loadSupplierView();
  }, [partnerId, user?.employer_id, user?.id]);

  const partnerProfile = useMemo(() => buildPartnerProfile(supplier), [supplier]);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      const matchCategory = activeCategory === 'Toutes' || product.category === activeCategory;
      const matchSpecialty = activeSpecialty === 'Toutes' || product.specialty === activeSpecialty;
      return matchCategory && matchSpecialty;
    });
  }, [activeCategory, activeSpecialty, products]);

  const categoryOptions = ['Toutes', ...(meta?.categories?.length ? meta.categories : partnerCategories.slice(1))];
  const specialtyOptions = ['Toutes', ...(meta?.specialties || [])];

  const showNoCatalogState = !loading && !loadError && products.length === 0;
  const showNoResultsState = !loading && !loadError && products.length > 0 && filteredProducts.length === 0;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between gap-4">
        <Link to="/approvisionnement" className="inline-flex items-center gap-2 px-4 py-3 rounded-elite border border-border-main text-sm font-black text-slate-700 hover:bg-slate-50">
          <ArrowLeft size={16} />
          Retour marketplace
        </Link>
        <div className="flex items-center gap-3">
          <button type="button" onClick={loadSupplierView} className="inline-flex items-center gap-2 px-4 py-3 rounded-elite border border-border-main text-sm font-black text-slate-700 hover:bg-slate-50">
            <RefreshCw size={16} />
            Recharger
          </button>
          <div className="inline-flex items-center gap-2 px-4 py-3 rounded-elite bg-slate-900 text-white text-sm font-black">
            <Box size={16} />
            {cartUnits} unité(s) dans le panier
          </div>
        </div>
      </div>

      <section className="relative overflow-hidden bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-8">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.10),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(245,158,11,0.10),transparent_28%)] pointer-events-none" />
        <div className="relative grid grid-cols-1 xl:grid-cols-[1.3fr_0.7fr] gap-6">
          <div className="space-y-5">
            {partnerProfile.heroImageUrl && (
              <div className="overflow-hidden rounded-elite-lg border border-border-main bg-slate-950 shadow-elite">
                <img src={partnerProfile.heroImageUrl} alt={partnerProfile.name} className="h-64 w-full object-cover" />
              </div>
            )}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary border border-primary/10 text-[10px] font-black uppercase tracking-widest">
              <Sparkles size={13} />
              {partnerProfile.badge}
            </div>
            <div>
              <h1 className="font-outfit text-3xl font-black tracking-tight text-slate-900">{partnerProfile.name}</h1>
              <p className="text-slate-600 font-medium mt-2 max-w-3xl leading-relaxed">{partnerProfile.description}</p>
            </div>
            {partnerProfile.promise && (
              <div className="rounded-elite border border-emerald-200 bg-emerald-50 p-5">
                <p className="text-[10px] font-black uppercase tracking-widest text-emerald-700 mb-2">Promesse fournisseur</p>
                <p className="text-sm font-semibold text-emerald-900 leading-relaxed">{partnerProfile.promise}</p>
              </div>
            )}
          </div>

          <div className="bg-slate-950 text-white rounded-elite-lg p-6 space-y-5">
            <div>
              <p className="text-[10px] uppercase tracking-widest font-black text-slate-400 mb-2">Couverture</p>
              <div className="space-y-2">
                {partnerProfile.coverage.length > 0 ? (
                  partnerProfile.coverage.map((item) => (
                    <div key={item} className="flex items-start gap-2 text-sm text-slate-200">
                      <CheckCircle2 size={15} className="shrink-0 mt-0.5 text-emerald-400" />
                      <span>{item}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-400">Aucune information de couverture disponible.</p>
                )}
              </div>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest font-black text-slate-400 mb-2">Logistique</p>
              <div className="space-y-2">
                {partnerProfile.logistics.length > 0 ? (
                  partnerProfile.logistics.map((item) => (
                    <div key={item} className="flex items-start gap-2 text-sm text-slate-200">
                      <Truck size={15} className="shrink-0 mt-0.5 text-amber-400" />
                      <span>{item}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-400">Aucune information logistique disponible.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6 space-y-5">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-4 items-start">
          <div className="flex flex-wrap gap-2">
            {categoryOptions.map((category) => (
              <button
                key={category}
                type="button"
                onClick={() => setActiveCategory(category)}
                className={cn(
                  'px-4 py-3 rounded-elite text-[11px] font-black uppercase tracking-widest border transition-all',
                  activeCategory === category
                    ? 'bg-slate-900 text-white border-slate-900 shadow-lg'
                    : 'bg-slate-50 text-text-muted border-border-main hover:border-slate-300'
                )}
              >
                {category}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap gap-2 lg:justify-end">
            {specialtyOptions.map((specialty) => (
              <button
                key={specialty}
                type="button"
                onClick={() => setActiveSpecialty(specialty)}
                className={cn(
                  'px-4 py-3 rounded-elite text-[11px] font-black uppercase tracking-widest border transition-all',
                  activeSpecialty === specialty
                    ? 'bg-primary text-white border-primary shadow-lg'
                    : 'bg-slate-50 text-text-muted border-border-main hover:border-slate-300'
                )}
              >
                <span className="inline-flex items-center gap-2">
                  <Tags size={12} />
                  {specialty}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {loading ? (
            <p className="col-span-full text-sm text-text-muted">Chargement du catalogue fournisseur...</p>
          ) : loadError ? (
            <div className="col-span-full flex flex-col items-center text-center gap-3 rounded-elite-lg border border-dashed border-border-main bg-slate-50 px-6 py-12">
              <p className="font-black text-slate-900">Impossible de charger le catalogue de ce fournisseur</p>
              <p className="text-sm text-text-muted max-w-sm mx-auto">Le service catalogue n'est pas joignable pour le moment.</p>
              <button type="button" onClick={loadSupplierView} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-elite bg-slate-900 text-white text-xs font-black uppercase tracking-widest hover:bg-black transition-colors">
                <RefreshCw size={13} />
                Réessayer
              </button>
            </div>
          ) : showNoCatalogState ? (
            <div className="col-span-full flex flex-col items-center text-center gap-3 rounded-elite-lg border border-dashed border-border-main bg-slate-50 px-6 py-12">
              <div className="w-12 h-12 rounded-elite-sm bg-primary/10 text-primary flex items-center justify-center">
                <PackageOpen size={20} />
              </div>
              <p className="font-black text-slate-900">Ce fournisseur n'a pas encore de produits publiés</p>
              <p className="text-sm text-text-muted max-w-sm mx-auto">Revenez bientôt ou contactez votre administrateur pour compléter ce catalogue.</p>
            </div>
          ) : showNoResultsState ? (
            <div className="col-span-full flex flex-col items-center text-center gap-2 rounded-elite-lg border border-dashed border-border-main bg-slate-50 px-6 py-12">
              <p className="font-black text-slate-900">Aucun produit ne correspond à cette combinaison catégorie / spécialité</p>
              <button
                type="button"
                onClick={() => { setActiveCategory('Toutes'); setActiveSpecialty('Toutes'); }}
                className="mt-1 inline-flex items-center gap-2 px-4 py-2.5 rounded-elite border border-border-main text-slate-700 text-xs font-black uppercase tracking-widest hover:bg-white transition-colors"
              >
                Réinitialiser les filtres
              </button>
            </div>
          ) : (
            filteredProducts.map((product) => (
              <Link
                key={product.id}
                to={`/approvisionnement/produits/${product.id}`}
                className="block border border-border-main rounded-elite p-5 bg-slate-50 hover:bg-card-bg hover:shadow-elite-hover hover:-translate-y-1 transition-all"
              >
                {product.imageUrl && (
                  <div className="mb-4 overflow-hidden rounded-elite border border-border-main bg-white">
                    <img src={product.imageUrl} alt={product.name} className="h-44 w-full object-cover transition-transform duration-300 hover:scale-[1.02]" />
                  </div>
                )}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-2">{product.category} | {product.specialty || 'Omnipratique'}</p>
                    <h3 className="font-outfit text-lg font-black text-slate-900 leading-tight">{product.name}</h3>
                  </div>
                  <span className={cn('px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border whitespace-nowrap', availabilityBadgeClass(product.availability))}>
                    {product.availability}
                  </span>
                </div>
                <p className="text-sm text-text-muted mt-3 min-h-[42px] leading-relaxed">{product.description}</p>
                <div className="rounded-elite bg-card-bg p-3 border border-border-main mt-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-1">Cible clinique</p>
                  <p className="text-sm font-semibold text-slate-700">{product.audience || product.specialty || 'Cabinet dentaire'}</p>
                </div>
                <div className="flex items-center justify-between mt-4">
                  <span className="font-black text-slate-900 text-xl">{formatMoney(product.price)}</span>
                  <span className="text-xs font-black uppercase tracking-widest text-primary">Voir le détail</span>
                </div>
              </Link>
            ))
          )}
        </div>
      </section>
    </div>
  );
};

export default PartnerSupplierPage;
