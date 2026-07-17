import React, { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Box, CheckCircle2, PackageOpen, RefreshCw, Store, Tags, Truck, Sparkles, ArrowRight } from 'lucide-react';
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

const heroSurfaceStyle: React.CSSProperties = {
  background: 'radial-gradient(circle at top right, rgba(255,255,255,0.16), transparent 28%), linear-gradient(135deg, var(--primary) 0%, var(--secondary) 55%, var(--accent) 100%)',
};

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
  const featuredProduct = products[0] || null;
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
    <div className="p-6 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <Link to="/approvisionnement" className="inline-flex items-center gap-2 rounded-elite border border-border-main px-4 py-3 text-sm font-black text-text-main hover:bg-input-field w-fit">
          <ArrowLeft size={16} />
          Retour marketplace
        </Link>
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" onClick={loadSupplierView} className="inline-flex items-center gap-2 rounded-elite border border-border-main px-4 py-3 text-sm font-black text-text-main hover:bg-input-field">
            <RefreshCw size={16} />
            Recharger
          </button>
          <div className="inline-flex items-center gap-2 rounded-elite px-4 py-3 text-sm font-black text-white" style={{ backgroundColor: 'var(--primary)' }}>
            <Box size={16} />
            {cartUnits} unité(s) dans le panier
          </div>
        </div>
      </div>

      <section className="rounded-elite-lg border border-border-main overflow-hidden shadow-elite" style={heroSurfaceStyle}>
        <div className="grid grid-cols-1 xl:grid-cols-[1.08fr_0.92fr] gap-6 p-8 lg:p-10 text-white">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-4 py-2 text-[11px] font-black uppercase tracking-[0.25em]">
              <Sparkles size={14} />
              {partnerProfile.badge}
            </div>
            <div className="space-y-4 max-w-3xl">
              <h1 className="font-outfit text-4xl md:text-5xl font-black leading-[0.95]">{partnerProfile.name}</h1>
              <p className="text-base md:text-lg text-white/82 leading-relaxed">{partnerProfile.description}</p>
            </div>
            <div className="rounded-elite border border-white/15 bg-white/10 p-5 backdrop-blur-md">
              <p className="text-[10px] font-black uppercase tracking-[0.28em] text-white/60 mb-2">Promesse fournisseur</p>
              <p className="text-sm leading-relaxed text-white/84 font-semibold">{partnerProfile.promise}</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {partnerProfile.metrics.map((metric) => (
                <div key={metric.label} className="rounded-elite border border-white/15 bg-white/10 px-4 py-4 backdrop-blur-md">
                  <p className="text-[10px] font-black uppercase tracking-[0.24em] text-white/60">{metric.label}</p>
                  <p className="mt-2 font-outfit text-2xl font-black text-white">{metric.value}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <SupplierStage
              name={partnerProfile.name}
              subtitle={featuredProduct?.name || 'Catalogue dentaire piloté'}
              caption={featuredProduct?.description || 'Une vitrine fournisseur prête à accueillir demain des photos réelles et des données synchronisées.'}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SupplierInfoCard title="Couverture" items={partnerProfile.coverage} />
              <SupplierInfoCard title="Logistique" items={partnerProfile.logistics} icon={<Truck size={15} />} />
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {partnerProfile.sections.map((section) => (
          <article key={section.title} className="rounded-elite-lg border border-border-main bg-card-bg p-6 shadow-elite">
            <p className="text-[10px] font-black uppercase tracking-[0.28em] text-text-muted">{section.eyebrow}</p>
            <h2 className="mt-3 font-outfit text-2xl font-black text-text-main">{section.title}</h2>
            <p className="mt-3 text-sm leading-relaxed text-text-muted">{section.description}</p>
            <div className="mt-4 space-y-3">
              {section.bullets.map((item) => (
                <div key={item} className="flex items-start gap-3 text-sm text-text-main">
                  <CheckCircle2 size={16} className="mt-0.5 shrink-0" style={{ color: 'var(--primary)' }} />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className="rounded-elite-lg border border-border-main bg-card-bg p-6 shadow-elite space-y-5">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-4 items-start">
          <div className="flex flex-wrap gap-2">
            {categoryOptions.map((category) => (
              <button
                key={category}
                type="button"
                onClick={() => setActiveCategory(category)}
                className={cn(
                  'rounded-full border px-4 py-3 text-[11px] font-black uppercase tracking-[0.22em] transition-all',
                  activeCategory === category
                    ? 'text-white shadow-lg'
                    : 'bg-card-bg text-text-muted border-border-main hover:border-border-hover'
                )}
                style={activeCategory === category ? { backgroundColor: 'var(--primary)', borderColor: 'var(--primary)' } : undefined}
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
                  'rounded-full border px-4 py-3 text-[11px] font-black uppercase tracking-[0.22em] transition-all',
                  activeSpecialty === specialty
                    ? 'text-white shadow-lg'
                    : 'bg-card-bg text-text-muted border-border-main hover:border-border-hover'
                )}
                style={activeSpecialty === specialty ? { backgroundColor: 'var(--secondary)', borderColor: 'var(--secondary)' } : undefined}
              >
                <span className="inline-flex items-center gap-2">
                  <Tags size={12} />
                  {specialty}
                </span>
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <StatePanel title="Chargement du catalogue fournisseur..." description="Nous synchronisons les produits et les données du partenaire." />
        ) : loadError ? (
          <StatePanel title="Impossible de charger le catalogue de ce fournisseur" description="Le service catalogue n'est pas joignable pour le moment." actionLabel="Réessayer" onAction={loadSupplierView} />
        ) : showNoCatalogState ? (
          <StatePanel title="Ce fournisseur n'a pas encore de produits publiés" description="Revenez bientôt ou contactez votre administrateur pour compléter ce catalogue." />
        ) : showNoResultsState ? (
          <StatePanel
            title="Aucun produit ne correspond à cette combinaison catégorie / spécialité"
            description="Réinitialisez les filtres ou explorez une autre spécialité."
            actionLabel="Réinitialiser les filtres"
            onAction={() => {
              setActiveCategory('Toutes');
              setActiveSpecialty('Toutes');
            }}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredProducts.map((product) => (
              <Link
                key={product.id}
                to={`/approvisionnement/produits/${product.id}`}
                className="block rounded-elite-lg border border-border-main bg-card-bg p-5 shadow-elite transition-all hover:-translate-y-1 hover:shadow-elite-hover"
              >
                <SupplierStage name={product.name} subtitle={product.category} caption={product.description} compact />
                <div className="mt-4 flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.24em] text-text-muted mb-2">{product.category} | {product.specialty || 'Omnipratique'}</p>
                    <h3 className="font-outfit text-xl font-black text-text-main leading-tight">{product.name}</h3>
                  </div>
                  <span className={cn('px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.24em] border whitespace-nowrap', availabilityBadgeClass(product.availability))}>
                    {product.availability}
                  </span>
                </div>
                <p className="mt-3 min-h-[42px] text-sm leading-relaxed text-text-muted">{product.description}</p>
                <div className="mt-4 rounded-elite border border-border-main bg-input-field p-3">
                  <p className="text-[10px] font-black uppercase tracking-[0.24em] text-text-muted mb-1">Cible clinique</p>
                  <p className="text-sm font-semibold text-text-main">{product.audience || product.specialty || 'Cabinet dentaire'}</p>
                </div>
                <div className="mt-4 flex items-center justify-between">
                  <span className="text-xl font-black text-text-main">{formatMoney(product.price)}</span>
                  <span className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.24em]" style={{ color: 'var(--primary)' }}>
                    Voir le détail
                    <ArrowRight size={14} />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

const SupplierStage: React.FC<{ name: string; subtitle: string; caption: string; compact?: boolean }> = ({ name, subtitle, caption, compact = false }) => (
  <div className={cn('relative overflow-hidden rounded-elite-lg border border-white/15 text-white', compact ? 'min-h-[210px] p-5' : 'min-h-[290px] p-6')} style={heroSurfaceStyle}>
    <div className="absolute inset-0 opacity-35" style={{ background: 'radial-gradient(circle at bottom left, rgba(255,255,255,0.18), transparent 30%)' }} />
    <div className="relative flex h-full flex-col justify-between gap-4">
      <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.24em]">
        <Store size={12} />
        {subtitle}
      </div>
      <div className="space-y-3">
        <h3 className={cn('font-outfit font-black leading-[0.95] text-white', compact ? 'text-3xl' : 'text-4xl')}>{name}</h3>
        <p className={cn('max-w-xl leading-relaxed text-white/80', compact ? 'text-sm' : 'text-base')}>{caption}</p>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <StageChip label="Expérience" value="Catalogue" />
        <StageChip label="Commande" value="Partenaire" />
        <StageChip label="Design" value="Token-driven" />
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

const SupplierInfoCard: React.FC<{ title: string; items: string[]; icon?: React.ReactNode }> = ({ title, items, icon }) => (
  <div className="rounded-elite-lg border border-white/15 bg-white/10 p-5 backdrop-blur-md">
    <p className="text-[10px] uppercase tracking-[0.28em] font-black text-white/60 mb-3">{title}</p>
    <div className="space-y-3">
      {(items.length ? items : ['Aucune information disponible pour le moment.']).map((item) => (
        <div key={item} className="flex items-start gap-3 text-sm text-white/84">
          <div className="mt-0.5 shrink-0">{icon || <CheckCircle2 size={15} />}</div>
          <span>{item}</span>
        </div>
      ))}
    </div>
  </div>
);

const StatePanel: React.FC<{ title: string; description: string; actionLabel?: string; onAction?: () => void }> = ({ title, description, actionLabel, onAction }) => (
  <div className="rounded-elite-lg border border-dashed border-border-main bg-input-field px-6 py-12 text-center space-y-4">
    <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-elite text-white" style={{ backgroundColor: 'var(--primary)' }}>
      <PackageOpen size={22} />
    </div>
    <div>
      <p className="font-outfit text-2xl font-black text-text-main">{title}</p>
      <p className="mt-2 max-w-xl mx-auto text-sm leading-relaxed text-text-muted">{description}</p>
    </div>
    {actionLabel && onAction && (
      <button type="button" onClick={onAction} className="inline-flex items-center gap-2 rounded-elite px-4 py-3 text-sm font-black text-white hover:brightness-110" style={{ backgroundColor: 'var(--primary)' }}>
        {actionLabel}
      </button>
    )}
  </div>
);

export default PartnerSupplierPage;
