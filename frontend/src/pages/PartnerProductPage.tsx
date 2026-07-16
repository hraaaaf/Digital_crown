import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, Minus, Plus, RefreshCw, ShoppingCart, ShieldCheck, Store, Truck } from 'lucide-react';
import { cn } from '../utils/cn';
import { api } from '../services/api';
import {
  type CartState,
  type PartnerCatalogProduct,
  type PartnerCatalogSupplier,
  type PartnerProduct,
  buildPartnerProfile,
  formatMoney,
  getPartnerProduct,
  normalizePartnerProduct,
  readStoredCart,
  writeStoredCart,
} from '../features/partnerMarketplace/data';

export const PartnerProductPage: React.FC = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState<PartnerProduct | null>(productId ? getPartnerProduct(productId) : null);
  const [supplier, setSupplier] = useState<PartnerCatalogSupplier | null>(null);
  const [cart, setCart] = useState<CartState>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setCart(readStoredCart());
  }, []);

  useEffect(() => {
    writeStoredCart(cart);
  }, [cart]);

  useEffect(() => {
    let active = true;
    const loadProduct = async () => {
      if (!productId) {
        setLoading(false);
        return;
      }
      try {
        const productRes = await api.get(`/partner-catalog/products/${productId}`);
        if (!active) return;
        const normalizedProduct = normalizePartnerProduct(productRes.data as PartnerCatalogProduct);
        setProduct(normalizedProduct);
        if (normalizedProduct.supplierId) {
          const supplierRes = await api.get(`/partner-catalog/suppliers/${normalizedProduct.supplierId}`);
          if (!active) return;
          setSupplier(supplierRes.data as PartnerCatalogSupplier);
        }
      } catch {
        if (active) {
          setProduct(productId ? getPartnerProduct(productId) : null);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadProduct();
    return () => {
      active = false;
    };
  }, [productId]);

  const partnerProfile = useMemo(() => buildPartnerProfile(supplier), [supplier]);

  if (loading && !product) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-white rounded-[2rem] border border-slate-200 p-8 shadow-sm">
          <p className="text-lg font-black text-slate-900">Chargement de la fiche produit...</p>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-white rounded-[2rem] border border-slate-200 p-8 shadow-sm">
          <p className="text-lg font-black text-slate-900">Produit introuvable.</p>
          <button onClick={() => navigate('/approvisionnement')} className="mt-4 px-4 py-3 rounded-xl bg-slate-900 text-white font-black">
            Revenir au catalogue
          </button>
        </div>
      </div>
    );
  }

  const quantity = cart[product.id] ?? 0;

  const adjustQty = (delta: number) => {
    setCart((current) => {
      const next = { ...current };
      const target = Math.max(0, (next[product.id] ?? 0) + delta);
      if (target === 0) {
        delete next[product.id];
      } else {
        next[product.id] = target;
      }
      return next;
    });
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/approvisionnement" className="inline-flex items-center gap-2 px-4 py-3 rounded-xl border border-slate-200 text-sm font-black text-slate-700 hover:bg-slate-50">
            <ArrowLeft size={16} />
            Retour catalogue
          </Link>
          <Link to={`/approvisionnement/partenaire/${supplier ? supplier.id : partnerProfile.id}`} className="inline-flex items-center gap-2 px-4 py-3 rounded-xl border border-slate-200 text-sm font-black text-slate-700 hover:bg-slate-50">
            <Store size={16} />
            Voir fournisseur
          </Link>
        </div>
        <div className="flex items-center gap-3">
          <button type="button" onClick={() => window.location.reload()} className="inline-flex items-center gap-2 px-4 py-3 rounded-xl border border-slate-200 text-sm font-black text-slate-700 hover:bg-slate-50">
            <RefreshCw size={16} />
            Recharger
          </button>
          <Link to="/approvisionnement" className="inline-flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-900 text-white text-sm font-black">
            <ShoppingCart size={16} />
            {quantity} dans le panier
          </Link>
        </div>
      </div>

      <section className="grid grid-cols-1 xl:grid-cols-[1.08fr_0.92fr] gap-6">
        <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm p-8 space-y-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.08),transparent_28%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.96))] pointer-events-none" />
          <div className="relative space-y-6">
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">{product.category} | {product.specialty || 'General Dentistry'} | {product.sku}</p>
              <h1 className="text-3xl font-black tracking-tight text-slate-900">{product.name}</h1>
              <p className="text-slate-600 font-medium mt-3 leading-relaxed">{product.longDescription}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {product.benefits.map((benefit) => (
                <div key={benefit} className="rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-4 text-sm font-semibold text-slate-700">
                  {benefit}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-5">
                <p className="text-[10px] font-black uppercase tracking-widest text-emerald-700 mb-2">Pourquoi ce produit est pertinent</p>
                <p className="text-sm font-semibold text-emerald-900 leading-relaxed">
                  Cette fiche produit valide un parcours fournisseur - catalogue - fiche produit - commande sans sortir de DigitalCrown.
                </p>
              </div>
              <div className="rounded-[1.5rem] border border-blue-200 bg-blue-50 p-5">
                <p className="text-[10px] font-black uppercase tracking-widest text-blue-700 mb-2">Cible clinique</p>
                <p className="text-sm font-semibold text-blue-900 leading-relaxed">{product.audience || product.specialty || 'Cabinet dentaire'}</p>
              </div>
            </div>
          </div>
        </div>

        <aside className="space-y-5">
          <div className="bg-card-bg rounded-[2rem] border border-border-main shadow-elite p-8 space-y-5">
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">Prix indicatif</p>
              <div className="flex items-end gap-3">
                <h2 className="text-3xl font-black text-slate-900">{formatMoney(product.price)}</h2>
                {product.originalPrice && (
                  <span className="text-sm text-slate-400 line-through font-bold">{formatMoney(product.originalPrice)}</span>
                )}
              </div>
              <p className="text-sm text-slate-500 mt-2">Unite: {product.unit}</p>
            </div>

            <div className={cn(
              'px-4 py-3 rounded-xl border text-sm font-black uppercase tracking-widest w-fit',
              product.availability === 'Disponible'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            )}>
              {product.availability}
            </div>

            <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5 space-y-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Ajout au panier</p>
              <div className="flex items-center gap-3">
                <button type="button" onClick={() => adjustQty(-1)} className="w-11 h-11 rounded-xl border border-slate-200 text-slate-600 flex items-center justify-center hover:bg-slate-50">
                  <Minus size={16} />
                </button>
                <div className="w-14 text-center font-black text-xl text-slate-900">{quantity}</div>
                <button type="button" onClick={() => adjustQty(1)} className="w-11 h-11 rounded-xl bg-primary text-white flex items-center justify-center hover:brightness-110">
                  <Plus size={16} />
                </button>
              </div>
              <Link to="/approvisionnement" className="block w-full py-3 rounded-xl bg-slate-900 text-white text-center font-black uppercase tracking-widest text-xs hover:bg-black">
                Retourner a la commande partenaire
              </Link>
            </div>

            <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5 space-y-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2">Fournisseur associe</p>
                <p className="font-black text-slate-900">{supplier?.name || partnerProfile.name}</p>
                <p className="text-sm text-slate-500 mt-2">{partnerProfile.promise}</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-start gap-2 text-sm text-slate-700">
                  <ShieldCheck size={15} className="shrink-0 mt-0.5 text-emerald-500" />
                  <span>Commande tracee et transmise depuis DigitalCrown.</span>
                </div>
                <div className="flex items-start gap-2 text-sm text-slate-700">
                  <Truck size={15} className="shrink-0 mt-0.5 text-amber-500" />
                  <span>Possibilite de recalcul si le fournisseur modifie ou annule.</span>
                </div>
                <div className="flex items-start gap-2 text-sm text-slate-700">
                  <CheckCircle2 size={15} className="shrink-0 mt-0.5 text-primary" />
                  <span>Fiche prete pour un futur enrichissement via API fournisseur.</span>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
};

export default PartnerProductPage;
