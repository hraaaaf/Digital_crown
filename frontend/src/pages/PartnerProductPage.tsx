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
  buildPartnerProductTemplate,
  buildPartnerProfile,
  formatMoney,
  normalizePartnerProduct,
  readMarketplaceCache,
  readStoredCart,
  writeStoredCart,
} from '../features/partnerMarketplace/data';

const heroSurfaceStyle: React.CSSProperties = {
  background: 'radial-gradient(circle at top right, rgba(255,255,255,0.16), transparent 30%), linear-gradient(135deg, var(--primary) 0%, var(--secondary) 55%, var(--accent) 100%)',
};

export const PartnerProductPage: React.FC = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const [product, setProduct] = useState<PartnerProduct | null>(null);
  const [supplier, setSupplier] = useState<PartnerCatalogSupplier | null>(null);
  const [cart, setCart] = useState<CartState>({});
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

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
        if (active && !hadCache) {
          setProduct(null);
          setSupplier(null);
          setNotFound(true);
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

  if (loading && !product) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <div className="rounded-elite-lg border border-border-main bg-card-bg p-8 shadow-elite">
          <p className="text-lg font-black text-text-main">Chargement de la fiche produit...</p>
        </div>
      </div>
    );
  }

  if (!product || notFound) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <div className="rounded-elite-lg border border-border-main bg-card-bg p-8 shadow-elite space-y-3">
          <p className="text-lg font-black text-text-main">Produit introuvable.</p>
          <p className="text-sm text-text-muted">Ce produit n'existe plus dans le catalogue partenaire ou le service catalogue est indisponible.</p>
          <button onClick={() => navigate('/approvisionnement')} className="mt-2 rounded-elite px-4 py-3 font-black text-white" style={{ backgroundColor: 'var(--primary)' }}>
            Revenir au catalogue
          </button>
        </div>
      </div>
    );
  }

  const template = buildPartnerProductTemplate(product);
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
    <div className="p-6 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap items-center gap-3">
          <Link to="/approvisionnement" className="inline-flex items-center gap-2 rounded-elite border border-border-main px-4 py-3 text-sm font-black text-text-main hover:bg-input-field">
            <ArrowLeft size={16} />
            Retour catalogue
          </Link>
          <Link to={`/approvisionnement/partenaire/${supplier ? supplier.id : partnerProfile.id}`} className="inline-flex items-center gap-2 rounded-elite border border-border-main px-4 py-3 text-sm font-black text-text-main hover:bg-input-field">
            <Store size={16} />
            Voir fournisseur
          </Link>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" onClick={() => window.location.reload()} className="inline-flex items-center gap-2 rounded-elite border border-border-main px-4 py-3 text-sm font-black text-text-main hover:bg-input-field">
            <RefreshCw size={16} />
            Recharger
          </button>
          <Link to="/approvisionnement" className="inline-flex items-center gap-2 rounded-elite px-4 py-3 text-sm font-black text-white" style={{ backgroundColor: 'var(--primary)' }}>
            <ShoppingCart size={16} />
            {quantity} dans le panier
          </Link>
        </div>
      </div>

      <section className="grid grid-cols-1 xl:grid-cols-[1.12fr_0.88fr] gap-6">
        <div className="space-y-6">
          <div className="rounded-elite-lg border border-border-main p-6 shadow-elite text-white" style={heroSurfaceStyle}>
            <ThemedProductStage product={product} />
          </div>

          <div className="rounded-elite-lg border border-border-main bg-card-bg p-6 shadow-elite space-y-5">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.28em] text-text-muted mb-2">
                {product.category} | {product.specialty || 'Omnipratique'} | {product.sku}
              </p>
              <h1 className="font-outfit text-4xl font-black tracking-tight text-text-main">{product.name}</h1>
              <p className="mt-4 text-base leading-relaxed text-text-muted">{product.longDescription}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {product.benefits.map((benefit) => (
                <div key={benefit} className="rounded-elite border border-border-main bg-input-field px-4 py-4 text-sm font-semibold text-text-main">
                  {benefit}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ContentPanel eyebrow="Lecture produit" title="Pourquoi cette fiche est premium" description={template.summary} />
              <ContentPanel eyebrow="Cible clinique" title={product.audience || product.specialty || 'Cabinet dentaire'} description="Le produit est présenté avec un angle métier clair pour aider le praticien à décider vite et commander sans friction." />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ListPanel title="Applications cliniques" items={template.clinicalApplications} />
            <ListPanel title="Ce que la fiche prépare" items={template.whatsIncluded} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[0.95fr_1.05fr] gap-4">
            <SpecsPanel specs={template.technicalSpecs} />
            <ListPanel title="Garanties du parcours" items={template.assurances} iconTone="primary" />
          </div>
        </div>

        <aside className="space-y-5 xl:sticky xl:top-6">
          <div className="rounded-elite-lg border border-border-main bg-card-bg p-6 shadow-elite space-y-5">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.28em] text-text-muted mb-2">Prix indicatif</p>
              <div className="flex items-end gap-3">
                <h2 className="text-4xl font-black text-text-main">{formatMoney(product.price)}</h2>
              </div>
              <p className="mt-2 text-sm text-text-muted">Conditionnement : {product.unit}</p>
            </div>

            <div className={cn('w-fit rounded-full px-4 py-2 text-[10px] font-black uppercase tracking-[0.24em] border', availabilityBadgeClass(product.availability))}>
              {product.availability}
            </div>

            <div className="rounded-elite border border-border-main p-5" style={{ background: 'linear-gradient(180deg, var(--glass-bg), var(--card-bg))' }}>
              <p className="text-[10px] font-black uppercase tracking-[0.28em] text-text-muted">Ajout au panier</p>
              {isDiscontinued ? (
                <p className="mt-3 text-sm text-text-muted">Ce produit est retiré du catalogue et ne peut plus être commandé.</p>
              ) : (
                <>
                  <div className="mt-4 flex items-center gap-3">
                    <button type="button" onClick={() => adjustQty(-1)} className="w-11 h-11 rounded-elite border border-border-main text-text-main flex items-center justify-center hover:bg-input-field">
                      <Minus size={16} />
                    </button>
                    <div className="w-14 text-center text-2xl font-black text-text-main">{quantity}</div>
                    <button type="button" onClick={() => adjustQty(1)} className="w-11 h-11 rounded-elite text-white flex items-center justify-center hover:brightness-110" style={{ backgroundColor: 'var(--primary)' }}>
                      <Plus size={16} />
                    </button>
                  </div>
                  <Link to="/approvisionnement" className="mt-4 block w-full rounded-elite px-4 py-3 text-center text-xs font-black uppercase tracking-[0.28em] text-white hover:brightness-110" style={{ backgroundColor: 'var(--primary)' }}>
                    Retourner à la commande partenaire
                  </Link>
                </>
              )}
            </div>

            <div className="rounded-elite border border-border-main bg-input-field p-5 space-y-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.28em] text-text-muted mb-2">Fournisseur associé</p>
                <p className="font-black text-text-main">{supplier?.name || partnerProfile.name}</p>
                <p className="mt-2 text-sm text-text-muted leading-relaxed">{partnerProfile.promise}</p>
              </div>
              <div className="space-y-3">
                <StatusLine icon={<ShieldCheck size={15} />} text="Commande tracée et transmise depuis DigitalCrown." />
                <StatusLine icon={<Truck size={15} />} text="Recalcul possible si le fournisseur modifie ou annule la commande." />
                <StatusLine icon={<CheckCircle2 size={15} />} text="Fiche prête pour accueillir de vraies photos et des données API enrichies." />
              </div>
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
};

const ThemedProductStage: React.FC<{ product: PartnerProduct }> = ({ product }) => (
  <div className="relative overflow-hidden rounded-elite-lg border border-white/15 p-6 min-h-[360px]">
    <div className="absolute inset-0 opacity-35" style={{ background: 'radial-gradient(circle at bottom left, rgba(255,255,255,0.18), transparent 30%)' }} />
    <div className="relative flex h-full flex-col justify-between gap-6">
      <div className="flex items-center justify-between gap-3">
        <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.24em]">
          {product.category}
        </span>
        <span className="rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.24em]">
          {product.sku}
        </span>
      </div>
      <div className="space-y-4">
        <p className="text-sm font-black uppercase tracking-[0.28em] text-white/70">{product.specialty || 'Omnipratique'}</p>
        <h2 className="font-outfit text-5xl font-black leading-[0.95] text-white">{product.name}</h2>
        <p className="max-w-xl text-sm leading-relaxed text-white/80">{product.description}</p>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <StageChip label="Lecture" value="Premium" />
        <StageChip label="Commande" value="Directe" />
        <StageChip label="Base" value="API-ready" />
      </div>
    </div>
  </div>
);

const StageChip: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="rounded-elite border border-white/15 bg-white/10 px-3 py-3">
    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-white/60">{label}</p>
    <p className="mt-1 text-sm font-black text-white">{value}</p>
  </div>
);

const ContentPanel: React.FC<{ eyebrow: string; title: string; description: string }> = ({ eyebrow, title, description }) => (
  <div className="rounded-elite border border-border-main bg-input-field p-5">
    <p className="text-[10px] font-black uppercase tracking-[0.28em] text-text-muted mb-2">{eyebrow}</p>
    <h3 className="font-outfit text-2xl font-black text-text-main">{title}</h3>
    <p className="mt-3 text-sm leading-relaxed text-text-muted">{description}</p>
  </div>
);

const ListPanel: React.FC<{ title: string; items: string[]; iconTone?: 'default' | 'primary' }> = ({ title, items, iconTone = 'default' }) => (
  <div className="rounded-elite-lg border border-border-main bg-card-bg p-6 shadow-elite">
    <h3 className="font-outfit text-2xl font-black text-text-main">{title}</h3>
    <div className="mt-4 space-y-3">
      {items.map((item) => (
        <div key={item} className="flex items-start gap-3 text-sm leading-relaxed text-text-main">
          <CheckCircle2 size={16} className="mt-0.5 shrink-0" style={iconTone === 'primary' ? { color: 'var(--primary)' } : undefined} />
          <span>{item}</span>
        </div>
      ))}
    </div>
  </div>
);

const SpecsPanel: React.FC<{ specs: Array<{ label: string; value: string }> }> = ({ specs }) => (
  <div className="rounded-elite-lg border border-border-main bg-card-bg p-6 shadow-elite">
    <h3 className="font-outfit text-2xl font-black text-text-main">Spécifications visibles</h3>
    <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
      {specs.map((spec) => (
        <div key={spec.label} className="rounded-elite border border-border-main bg-input-field px-4 py-4">
          <p className="text-[10px] font-black uppercase tracking-[0.24em] text-text-muted">{spec.label}</p>
          <p className="mt-2 text-sm font-semibold text-text-main">{spec.value}</p>
        </div>
      ))}
    </div>
  </div>
);

const StatusLine: React.FC<{ icon: React.ReactNode; text: string }> = ({ icon, text }) => (
  <div className="flex items-start gap-3 text-sm text-text-main">
    <div className="mt-0.5 shrink-0" style={{ color: 'var(--primary)' }}>{icon}</div>
    <span>{text}</span>
  </div>
);

export default PartnerProductPage;
