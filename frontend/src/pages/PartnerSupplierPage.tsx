import React, { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Box, CheckCircle2, RefreshCw, Store, Tags, Truck, Sparkles } from 'lucide-react';
import { cn } from '../utils/cn';
import { api } from '../services/api';
import {
  type PartnerCatalogProduct,
  type PartnerCatalogSupplier,
  type PartnerProduct,
  buildPartnerProfile,
  formatMoney,
  normalizePartnerProduct,
  partnerCategories,
  partnerProducts,
  readStoredCart,
} from '../features/partnerMarketplace/data';

type CatalogMeta = {
  categories: string[];
  specialties: string[];
};

export const PartnerSupplierPage: React.FC = () => {
  const { partnerId } = useParams();
  const [activeCategory, setActiveCategory] = useState('Toutes');
  const [activeSpecialty, setActiveSpecialty] = useState('Toutes');
  const [supplier, setSupplier] = useState<PartnerCatalogSupplier | null>(null);
  const [products, setProducts] = useState<PartnerProduct[]>(partnerProducts);
  const [meta, setMeta] = useState<CatalogMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const cartUnits = Object.values(readStoredCart()).reduce((sum, qty) => sum + qty, 0);

  const loadSupplierView = async () => {
    setLoading(true);
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
      setProducts(supplierProducts.length ? supplierProducts : partnerProducts);
    } catch {
      setProducts(partnerProducts);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSupplierView();
  }, [partnerId]);

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

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between gap-4">
        <Link to="/approvisionnement" className="inline-flex items-center gap-2 px-4 py-3 rounded-xl border border-slate-200 text-sm font-black text-slate-700 hover:bg-slate-50">
          <ArrowLeft size={16} />
          Retour marketplace
        </Link>
        <div className="flex items-center gap-3">
          <button type="button" onClick={loadSupplierView} className="inline-flex items-center gap-2 px-4 py-3 rounded-xl border border-slate-200 text-sm font-black text-slate-700 hover:bg-slate-50">
            <RefreshCw size={16} />
            Recharger
          </button>
          <div className="inline-flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-900 text-white text-sm font-black">
            <Box size={16} />
            {cartUnits} unite(s) dans le panier
          </div>
        </div>
      </div>

      <section className="relative overflow-hidden bg-card-bg rounded-[2rem] border border-border-main shadow-elite p-8">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.10),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(245,158,11,0.10),transparent_28%)] pointer-events-none" />
        <div className="relative grid grid-cols-1 xl:grid-cols-[1.3fr_0.7fr] gap-6">
          <div className="space-y-5">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary border border-primary/10 text-[10px] font-black uppercase tracking-widest">
              <Sparkles size={13} />
              {partnerProfile.badge}
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight text-slate-900">{partnerProfile.name}</h1>
              <p className="text-slate-600 font-medium mt-2 max-w-3xl leading-relaxed">{partnerProfile.description}</p>
            </div>
            <div className="rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-5">
              <p className="text-[10px] font-black uppercase tracking-widest text-emerald-700 mb-2">Promesse V1</p>
              <p className="text-sm font-semibold text-emerald-900 leading-relaxed">{partnerProfile.promise}</p>
            </div>
          </div>

          <div className="bg-slate-950 text-white rounded-[1.75rem] p-6 space-y-5">
            <div>
              <p className="text-[10px] uppercase tracking-widest font-black text-slate-400 mb-2">Couverture</p>
              <div className="space-y-2">
                {partnerProfile.coverage.map((item) => (
                  <div key={item} className="flex items-start gap-2 text-sm text-slate-200">
                    <CheckCircle2 size={15} className="shrink-0 mt-0.5 text-emerald-400" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest font-black text-slate-400 mb-2">Logistique</p>
              <div className="space-y-2">
                {partnerProfile.logistics.map((item) => (
                  <div key={item} className="flex items-start gap-2 text-sm text-slate-200">
                    <Truck size={15} className="shrink-0 mt-0.5 text-amber-400" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white rounded-[2rem] border border-slate-200 shadow-sm p-6 space-y-5">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-4 items-start">
          <div className="flex flex-wrap gap-2">
            {categoryOptions.map((category) => (
              <button
                key={category}
                type="button"
                onClick={() => setActiveCategory(category)}
                className={cn(
                  'px-4 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest border transition-all',
                  activeCategory === category
                    ? 'bg-slate-900 text-white border-slate-900 shadow-lg'
                    : 'bg-slate-50 text-slate-500 border-slate-200 hover:border-slate-300'
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
                  'px-4 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest border transition-all',
                  activeSpecialty === specialty
                    ? 'bg-primary text-white border-primary shadow-lg'
                    : 'bg-slate-50 text-slate-500 border-slate-200 hover:border-slate-300'
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
            <p className="text-sm text-slate-500">Chargement du catalogue fournisseur...</p>
          ) : filteredProducts.length === 0 ? (
            <p className="text-sm text-slate-500">Aucun produit ne correspond a cette combinaison categorie / specialite.</p>
          ) : (
            filteredProducts.map((product) => (
              <Link
                key={product.id}
                to={`/approvisionnement/produits/${product.id}`}
                className="block border border-slate-200 rounded-[1.5rem] p-5 bg-slate-50 hover:bg-white hover:shadow-lg hover:-translate-y-1 transition-all"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">{product.category} | {product.specialty || 'General Dentistry'}</p>
                    <h3 className="text-lg font-black text-slate-900 leading-tight">{product.name}</h3>
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
                <p className="text-sm text-slate-500 mt-3 min-h-[42px] leading-relaxed">{product.description}</p>
                <div className="rounded-xl bg-white p-3 border border-slate-200 mt-4">
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Cible clinique</p>
                  <p className="text-sm font-semibold text-slate-700">{product.audience || product.specialty || 'Cabinet dentaire'}</p>
                </div>
                <div className="flex items-center justify-between mt-4">
                  <div>
                    <span className="font-black text-slate-900 text-xl">{formatMoney(product.price)}</span>
                    {product.originalPrice && (
                      <p className="text-xs text-slate-400 line-through font-bold mt-1">{formatMoney(product.originalPrice)}</p>
                    )}
                  </div>
                  <span className="text-xs font-black uppercase tracking-widest text-primary">Voir le detail</span>
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
