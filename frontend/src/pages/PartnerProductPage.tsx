import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, Minus, Plus, RefreshCw, ShoppingCart, ShieldCheck, Store, Truck } from 'lucide-react';
import { cn } from '../utils/cn';
import { api } from '../services/api';
import { useAuthStore } from '../stores/useAuthStore';
import {
  type CartState,
  type PartnerCatalogProduct,
  type PartnerCatalogSupplier,
  type PartnerProduct,
  availabilityBadgeClass,
  buildPartnerProfile,
  formatMoney,
  normalizePartnerProduct,
  readMarketplaceCache,
  readStoredCart,
  writeStoredCart,
} from '../features/partnerMarketplace/data';

export const PartnerProductPage: React.FC = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const [product, setProduct] = useState<PartnerProduct | null>(null);
  const [supplier, setSupplier] = useState<PartnerCatalogSupplier | null>(null);
  const [cart, setCart] = useState<CartState>({});
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [selectedImage, setSelectedImage] = useState('');

  useEffect(() => {
    setCart(readStoredCart());
  }, []);

  useEffect(() => {
    writeStoredCart(cart);
  }, [cart]);

  useEffect(() => {
    let active = true;
    const hydrateFromCache = () => {
      const cached = readMarketplaceCache(user);
      if (!cached || !productId) return false;
      const cachedProduct = cached.products.find((item) => item.id === productId) || null;
      if (!cachedProduct) return false;
      setProduct(cachedProduct);
      if (cachedProduct.supplierId) {
        setSupplier(cached.suppliers.find((item) => String(item.id) === cachedProduct.supplierId) || null);
      }
      setNotFound(false);
      return true;
    };

    const loadProduct = async () => {
      if (!productId) {
        setLoading(false);
        setNotFound(true);
        return;
      }
      const hadCache = hydrateFromCache();
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
          if (!hadCache) {
            setProduct(null);
            setSupplier(null);
            setNotFound(true);
          }
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    hydrateFromCache();
    loadProduct();
    return () => {
      active = false;
    };
  }, [productId, user?.employer_id, user?.id]);

  const partnerProfile = useMemo(() => buildPartnerProfile(supplier), [supplier]);

  useEffect(() => {
    if (!product) return;
    setSelectedImage(product.gallery?.[0] || product.imageUrl || '');
  }, [product]);

  if (loading && !product) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-card-bg rounded-elite-lg border border-border-main p-8 shadow-elite">
          <p className="text-lg font-black text-slate-900">Chargement de la fiche produit...</p>
        </div>
      </div>
    );
  }

  if (!product || notFound) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-card-bg rounded-elite-lg border border-border-main p-8 shadow-elite space-y-2">
          <p className="text-lg font-black text-slate-900">Produit introuvable.</p>
          <p className="text-sm text-text-muted">Ce produit n'existe plus dans le catalogue partenaire ou le service catalogue est indisponible.</p>
          <button onClick={() => navigate('/approvisionnement')} className="mt-2 px-4 py-3 rounded-elite bg-slate-900 text-white font-black">
            Revenir au catalogue
          </button>
        </div>
      </div>
    );
  }

  const isDiscontinued = product.availability === 'Discontinué';
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
          <Link to="/approvisionnement" className="inline-flex items-center gap-2 px-4 py-3 rounded-elite border border-border-main text-sm font-black text-slate-700 hover:bg-slate-50">
            <ArrowLeft size={16} />
            Retour catalogue
          </Link>
          <Link to={`/approvisionnement/partenaire/${supplier ? supplier.id : partnerProfile.id}`} className="inline-flex items-center gap-2 px-4 py-3 rounded-elite border border-border-main text-sm font-black text-slate-700 hover:bg-slate-50">
            <Store size={16} />
            Voir fournisseur
          </Link>
        </div>
        <div className="flex items-center gap-3">
          <button type="button" onClick={() => window.location.reload()} className="inline-flex items-center gap-2 px-4 py-3 rounded-elite border border-border-main text-sm font-black text-slate-700 hover:bg-slate-50">
            <RefreshCw size={16} />
            Recharger
          </button>
          <Link to="/approvisionnement" className="inline-flex items-center gap-2 px-4 py-3 rounded-elite bg-slate-900 text-white text-sm font-black">
            <ShoppingCart size={16} />
            {quantity} dans le panier
          </Link>
        </div>
      </div>

      <section className="grid grid-cols-1 xl:grid-cols-[1.08fr_0.92fr] gap-6">
        <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-8 space-y-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.08),transparent_28%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.96))] pointer-events-none" />
          <div className="relative space-y-6">
            {(selectedImage || product.imageUrl) && (
              <div className="space-y-3">
                <div className="overflow-hidden rounded-elite-lg border border-border-main bg-slate-100 shadow-elite">
                  <img
                    src={selectedImage || product.imageUrl}
                    alt={product.name}
                    className="h-[320px] md:h-[420px] w-full object-cover"
                  />
                </div>
                {product.gallery && product.gallery.length > 1 && (
                  <div className="grid grid-cols-3 gap-3">
                    {product.gallery.map((image, index) => (
                      <button
                        key={`${product.id}-gallery-${index}`}
                        type="button"
                        onClick={() => setSelectedImage(image)}
                        className={cn(
                          'overflow-hidden rounded-elite border bg-white transition-all',
                          (selectedImage || product.imageUrl) === image
                            ? 'border-primary ring-2 ring-primary/20'
                            : 'border-border-main hover:border-slate-300'
                        )}
                      >
                        <img src={image} alt={`${product.name} visuel ${index + 1}`} className="h-24 w-full object-cover" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-2">{product.category} | {product.specialty || 'Omnipratique'} | {product.sku}</p>
              <h1 className="font-outfit text-3xl font-black tracking-tight text-slate-900">{product.name}</h1>
              <p className="text-slate-600 font-medium mt-3 leading-relaxed">{product.longDescription}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {product.benefits.map((benefit) => (
                <div key={benefit} className="rounded-elite-sm border border-border-main bg-slate-50 px-4 py-4 text-sm font-semibold text-slate-700">
                  {benefit}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-elite border border-emerald-200 bg-emerald-50 p-5">
                <p className="text-[10px] font-black uppercase tracking-widest text-emerald-700 mb-2">Pourquoi ce produit est pertinent</p>
                <p className="text-sm font-semibold text-emerald-900 leading-relaxed">
                  Cette fiche produit valide un parcours fournisseur - catalogue - fiche produit - commande sans sortir de DigitalCrown.
                </p>
              </div>
              <div className="rounded-elite border border-blue-200 bg-blue-50 p-5">
                <p className="text-[10px] font-black uppercase tracking-widest text-blue-700 mb-2">Cible clinique</p>
                <p className="text-sm font-semibold text-blue-900 leading-relaxed">{product.audience || product.specialty || 'Cabinet dentaire'}</p>
              </div>
            </div>
          </div>
        </div>

        <aside className="space-y-5">
          <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-8 space-y-5">
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-2">Prix indicatif</p>
              <div className="flex items-end gap-3">
                <h2 className="text-3xl font-black text-slate-900">{formatMoney(product.price)}</h2>
              </div>
              <p className="text-sm text-text-muted mt-2">Unité : {product.unit}</p>
            </div>

            <div className={cn(
              'px-4 py-3 rounded-elite border text-sm font-black uppercase tracking-widest w-fit',
              availabilityBadgeClass(product.availability)
            )}>
              {product.availability}
            </div>

            <div className="rounded-elite border border-border-main bg-card-bg p-5 space-y-4">
              <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Ajout au panier</p>
              {isDiscontinued ? (
                <p className="text-sm text-text-muted">Ce produit est retiré du catalogue et ne peut plus être commandé.</p>
              ) : (
                <>
                  <div className="flex items-center gap-3">
                    <button type="button" onClick={() => adjustQty(-1)} className="w-11 h-11 rounded-elite border border-border-main text-slate-600 flex items-center justify-center hover:bg-slate-50">
                      <Minus size={16} />
                    </button>
                    <div className="w-14 text-center font-black text-xl text-slate-900">{quantity}</div>
                    <button type="button" onClick={() => adjustQty(1)} className="w-11 h-11 rounded-elite bg-primary text-white flex items-center justify-center hover:brightness-110">
                      <Plus size={16} />
                    </button>
                  </div>
                  <Link to="/approvisionnement" className="block w-full py-3 rounded-elite bg-slate-900 text-white text-center font-black uppercase tracking-widest text-xs hover:bg-black">
                    Retourner à la commande partenaire
                  </Link>
                </>
              )}
            </div>

            <div className="rounded-elite border border-border-main bg-slate-50 p-5 space-y-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-text-muted mb-2">Fournisseur associé</p>
                <p className="font-black text-slate-900">{supplier?.name || partnerProfile.name}</p>
                <p className="text-sm text-text-muted mt-2">{partnerProfile.promise}</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-start gap-2 text-sm text-slate-700">
                  <ShieldCheck size={15} className="shrink-0 mt-0.5 text-emerald-500" />
                  <span>Commande tracée et transmise depuis DigitalCrown.</span>
                </div>
                <div className="flex items-start gap-2 text-sm text-slate-700">
                  <Truck size={15} className="shrink-0 mt-0.5 text-amber-500" />
                  <span>Possibilité de recalcul si le fournisseur modifie ou annule.</span>
                </div>
                <div className="flex items-start gap-2 text-sm text-slate-700">
                  <CheckCircle2 size={15} className="shrink-0 mt-0.5 text-primary" />
                  <span>Fiche prête pour un futur enrichissement via API fournisseur.</span>
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
