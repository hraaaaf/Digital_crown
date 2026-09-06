import { useState } from 'react';
import { AlertCircle, CheckCircle2, Minus, Package, Plus, RefreshCw, Search, ShoppingCart, X, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '../utils/cn';
import { availabilityBadgeClass, formatMoney, type PartnerProduct } from '../features/partnerMarketplace/data';
import { type MarketplaceCustomer, usePartnerMarketplace } from '../features/partnerMarketplace/usePartnerMarketplace';

export const PartnerMarketplacePage = () => {
  const marketplace = usePartnerMarketplace();
  const [checkoutOpen, setCheckoutOpen] = useState(false);

  const showNoResults = !marketplace.catalogLoading && !marketplace.catalogError && marketplace.products.length > 0 && marketplace.filteredProducts.length === 0;
  const showNoCatalog = !marketplace.catalogLoading && !marketplace.catalogError && marketplace.products.length === 0;

  const openCheckout = () => {
    if (marketplace.totalUnits > 0) setCheckoutOpen(true);
  };

  const submitCheckout = async (event: React.FormEvent) => {
    event.preventDefault();
    const ok = await marketplace.submitDraft();
    if (ok && !marketplace.previewMode) setCheckoutOpen(false);
  };

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-3 pb-24 sm:p-6 xl:pb-8" data-marketplace-desktop>
      <header className="rounded-elite-lg border border-border-main bg-card-bg p-4 shadow-elite sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.22em] text-text-muted">
              <Zap size={14} className="text-primary" aria-hidden="true" />
              Approvisionnement rapide
            </div>
            <h1 className="mt-1 font-outfit text-2xl font-black leading-tight text-text-main sm:text-3xl">Marketplace</h1>
            <p className="mt-1 max-w-2xl text-sm font-medium text-text-muted">
              Trouvez une référence par nom ou SKU, ajustez la quantité et préparez un brouillon de commande.
            </p>
          </div>

          <button
            type="button"
            onClick={openCheckout}
            disabled={marketplace.totalUnits === 0}
            className="inline-flex min-h-12 shrink-0 items-center justify-between gap-4 rounded-elite px-4 py-3 text-sm font-black text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-45"
            style={{ backgroundColor: 'var(--primary)' }}
            aria-label={`Ouvrir le panier, ${marketplace.totalUnits} unité${marketplace.totalUnits > 1 ? 's' : ''}`}
          >
            <span className="inline-flex items-center gap-2"><ShoppingCart size={18} /> Panier · {marketplace.totalUnits}</span>
            <span>{formatMoney(marketplace.estimatedTotal)}</span>
          </button>
        </div>
      </header>

      <section className="rounded-elite-lg border border-border-main bg-card-bg p-3 shadow-elite sm:p-4" aria-label="Recherche Marketplace">
        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <label className="relative min-w-0 flex-1" htmlFor="marketplace-search">
            <span className="sr-only">Rechercher par nom ou SKU</span>
            <Search size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              id="marketplace-search"
              type="search"
              value={marketplace.search}
              onChange={(event) => marketplace.setSearch(event.target.value)}
              placeholder="Nom, référence ou SKU…"
              className="min-h-12 w-full rounded-elite border border-border-main bg-input-field py-3 pl-11 pr-4 text-sm font-bold text-text-main outline-none transition focus:border-border-hover focus:ring-2 focus:ring-primary/10"
              autoComplete="off"
            />
          </label>
          <button
            type="button"
            onClick={() => void marketplace.loadCatalog()}
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-elite border border-border-main px-4 text-sm font-black text-text-main hover:bg-input-field"
          >
            <RefreshCw size={16} /> Actualiser
          </button>
        </div>

        <div className="mt-3 flex gap-2 overflow-x-auto pb-1" aria-label="Filtres Marketplace">
          <button
            type="button"
            onClick={() => marketplace.setAvailableOnly(!marketplace.availableOnly)}
            className={cn(
              'shrink-0 rounded-full border px-3 py-2 text-xs font-black transition',
              marketplace.availableOnly ? 'border-transparent text-white' : 'border-border-main bg-card-bg text-text-muted',
            )}
            style={marketplace.availableOnly ? { backgroundColor: 'var(--primary)' } : undefined}
            aria-pressed={marketplace.availableOnly}
          >
            Disponibles
          </button>
          {marketplace.categoryOptions.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => marketplace.setCategory(item)}
              className={cn(
                'shrink-0 rounded-full border px-3 py-2 text-xs font-black transition',
                marketplace.category === item ? 'border-transparent text-white' : 'border-border-main bg-card-bg text-text-muted',
              )}
              style={marketplace.category === item ? { backgroundColor: 'var(--primary)' } : undefined}
              aria-pressed={marketplace.category === item}
            >
              {item}
            </button>
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 items-start gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <main className="min-w-0 space-y-3">
          <div className="flex items-end justify-between gap-3 px-1">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-text-muted">Références</p>
              <h2 className="mt-1 font-outfit text-xl font-black text-text-main">Acheter vite</h2>
            </div>
            <p className="text-xs font-bold text-text-muted">{marketplace.filteredProducts.length} affichée(s)</p>
          </div>

          {marketplace.catalogLoading ? (
            <StateCard title="Chargement du catalogue…" description="Synchronisation des références disponibles." />
          ) : marketplace.catalogError ? (
            <StateCard title="Catalogue indisponible" description="Les données en cache restent utilisées lorsqu'elles sont encore valides." actionLabel="Réessayer" onAction={() => void marketplace.loadCatalog()} />
          ) : showNoCatalog ? (
            <StateCard title="Aucun produit publié" description="Aucune référence active n'est disponible pour ce cabinet." />
          ) : showNoResults ? (
            <StateCard title="Aucun résultat" description="Modifiez la recherche ou les filtres." actionLabel="Réinitialiser" onAction={() => { marketplace.setSearch(''); marketplace.setCategory('Toutes'); marketplace.setAvailableOnly(false); }} />
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {marketplace.filteredProducts.map((product) => (
                <ProductCard key={product.id} product={product} quantity={marketplace.cart[product.id] ?? 0} onAdjust={marketplace.adjustQty} />
              ))}
            </div>
          )}
        </main>

        <aside className="rounded-elite-lg border border-border-main bg-card-bg p-4 shadow-elite xl:sticky xl:top-6" data-marketplace-cart>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-text-muted">Panier</p>
              <h2 className="mt-1 font-outfit text-xl font-black text-text-main">{marketplace.totalUnits} unité(s)</h2>
            </div>
            <ShoppingCart size={20} className="text-primary" />
          </div>

          <div className="mt-4 space-y-2">
            {marketplace.cartLines.length === 0 ? (
              <p className="rounded-elite bg-input-field p-4 text-sm font-semibold text-text-muted">Ajoutez une référence pour préparer la commande.</p>
            ) : marketplace.cartLines.map((line) => (
              <div key={line.id} className="flex items-start justify-between gap-3 rounded-elite border border-border-main p-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-black text-text-main">{line.name}</p>
                  <p className="mt-1 text-xs font-semibold text-text-muted">{line.quantity} × {formatMoney(line.price)}</p>
                </div>
                <p className="shrink-0 text-sm font-black text-text-main">{formatMoney(line.lineTotal)}</p>
              </div>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between border-y border-border-main py-4">
            <span className="text-sm font-semibold text-text-muted">Total estimé</span>
            <span className="text-xl font-black text-text-main">{formatMoney(marketplace.estimatedTotal)}</span>
          </div>

          <button
            type="button"
            onClick={openCheckout}
            disabled={marketplace.totalUnits === 0}
            className="mt-4 w-full rounded-elite px-4 py-3 text-sm font-black text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-45"
            style={{ backgroundColor: 'var(--primary)' }}
          >
            Préparer le DRAFT
          </button>
          <p className="mt-2 text-center text-[11px] font-semibold leading-relaxed text-text-muted">
            Le fournisseur ne reçoit rien à cette étape.
          </p>
        </aside>
      </div>

      {marketplace.totalUnits > 0 && (
        <button
          type="button"
          onClick={openCheckout}
          className="fixed bottom-4 left-4 right-4 z-30 flex items-center justify-between rounded-elite-lg px-4 py-3 text-sm font-black text-white shadow-2xl xl:hidden"
          style={{ backgroundColor: 'var(--primary)' }}
        >
          <span className="inline-flex items-center gap-2"><ShoppingCart size={18} /> Panier · {marketplace.totalUnits}</span>
          <span>{formatMoney(marketplace.estimatedTotal)} →</span>
        </button>
      )}

      {checkoutOpen && (
        <CheckoutDialog
          customer={marketplace.customer}
          cartLines={marketplace.cartLines}
          total={marketplace.estimatedTotal}
          submitting={marketplace.submitting}
          successMessage={marketplace.successMessage}
          errorMessage={marketplace.errorMessage}
          onCustomerChange={marketplace.updateCustomer}
          onClose={() => setCheckoutOpen(false)}
          onSubmit={submitCheckout}
        />
      )}
    </div>
  );
};

const ProductCard = ({ product, quantity, onAdjust }: { product: PartnerProduct; quantity: number; onAdjust: (product: PartnerProduct, delta: number) => void }) => {
  const disabled = product.availability === 'Discontinué';
  return (
    <article className="rounded-elite-lg border border-border-main bg-card-bg p-4 shadow-elite" data-marketplace-product={product.id}>
      <div className="flex gap-3">
        <div className="grid h-12 w-12 shrink-0 place-items-center rounded-elite bg-input-field text-text-muted"><Package size={22} /></div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="text-[9px] font-black uppercase tracking-[0.16em] text-text-muted">{product.category}</p>
            <span className={cn('shrink-0 rounded-full border px-2 py-1 text-[9px] font-black', availabilityBadgeClass(product.availability))}>{product.availability}</span>
          </div>
          <Link to={`/approvisionnement/produits/${product.id}`} className="mt-1 block font-outfit text-base font-black leading-tight text-text-main hover:opacity-80">{product.name}</Link>
          <p className="mt-1 text-[11px] font-bold text-text-muted">{product.sku}{product.specialty ? ` · ${product.specialty}` : ''}</p>
        </div>
      </div>

      <div className="mt-4 flex items-end justify-between gap-3 border-t border-border-main pt-3">
        <div>
          <p className="text-lg font-black text-text-main">{formatMoney(product.price)}</p>
          <p className="text-[11px] font-semibold text-text-muted">par {product.unit}</p>
        </div>
        {disabled ? (
          <span className="text-xs font-black text-text-muted">Indisponible</span>
        ) : (
          <div className="flex items-center gap-2" aria-label={`Quantité de ${product.name}`}>
            <button type="button" onClick={() => onAdjust(product, -1)} disabled={quantity === 0} className="grid h-11 w-11 place-items-center rounded-elite border border-border-main text-text-main disabled:opacity-35" aria-label={`Retirer une unité de ${product.name}`}><Minus size={16} /></button>
            <span className="w-7 text-center text-sm font-black text-text-main" aria-live="polite">{quantity}</span>
            <button type="button" onClick={() => onAdjust(product, 1)} className="grid h-11 w-11 place-items-center rounded-elite text-white" style={{ backgroundColor: 'var(--primary)' }} aria-label={`Ajouter une unité de ${product.name}`}><Plus size={16} /></button>
          </div>
        )}
      </div>
    </article>
  );
};

const CheckoutDialog = ({ customer, cartLines, total, submitting, successMessage, errorMessage, onCustomerChange, onClose, onSubmit }: {
  customer: MarketplaceCustomer;
  cartLines: Array<PartnerProduct & { quantity: number; lineTotal: number }>;
  total: number;
  submitting: boolean;
  successMessage: string;
  errorMessage: string;
  onCustomerChange: (field: keyof MarketplaceCustomer, value: string) => void;
  onClose: () => void;
  onSubmit: (event: React.FormEvent) => void;
}) => (
  <div className="fixed inset-0 z-[90] flex items-end justify-center bg-slate-950/35 p-0 backdrop-blur-sm sm:items-center sm:p-6" data-marketplace-checkout>
    <button type="button" className="absolute inset-0" aria-label="Fermer le checkout" onClick={onClose} />
    <section role="dialog" aria-modal="true" aria-labelledby="marketplace-checkout-title" className="relative z-10 max-h-[92dvh] w-full max-w-2xl overflow-y-auto rounded-t-[28px] border border-border-main bg-card-bg p-5 shadow-2xl sm:rounded-elite-lg sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-text-muted">Brouillon de commande</p>
          <h2 id="marketplace-checkout-title" className="mt-1 font-outfit text-2xl font-black text-text-main">Préparer le DRAFT</h2>
        </div>
        <button type="button" onClick={onClose} className="grid h-11 w-11 place-items-center rounded-full border border-border-main text-text-muted" aria-label="Fermer"><X size={18} /></button>
      </div>

      <div className="mt-4 rounded-elite bg-input-field p-4">
        <div className="space-y-2">
          {cartLines.map((line) => (
            <div key={line.id} className="flex items-center justify-between gap-3 text-sm">
              <span className="min-w-0 truncate font-bold text-text-main">{line.name} · {line.quantity}</span>
              <span className="shrink-0 font-black text-text-main">{formatMoney(line.lineTotal)}</span>
            </div>
          ))}
        </div>
        <div className="mt-3 flex items-center justify-between border-t border-border-main pt-3">
          <span className="text-sm font-bold text-text-muted">Total estimé</span>
          <span className="text-xl font-black text-text-main">{formatMoney(total)}</span>
        </div>
      </div>

      <form onSubmit={onSubmit} className="mt-5 space-y-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Nom complet" value={customer.fullName} onChange={(value) => onCustomerChange('fullName', value)} required />
          <Field label="Cabinet" value={customer.clinic} onChange={(value) => onCustomerChange('clinic', value)} required />
          <Field label="Email" value={customer.email} onChange={(value) => onCustomerChange('email', value)} required type="email" />
          <Field label="Téléphone" value={customer.phone} onChange={(value) => onCustomerChange('phone', value)} required inputMode="tel" />
          <Field label="Ville" value={customer.city} onChange={(value) => onCustomerChange('city', value)} required />
        </div>
        <label className="block">
          <span className="text-xs font-black text-text-muted">Note</span>
          <textarea value={customer.note} onChange={(event) => onCustomerChange('note', event.target.value)} rows={2} className="mt-1 w-full rounded-elite border border-border-main bg-input-field px-3 py-2 text-sm font-semibold text-text-main outline-none focus:ring-2 focus:ring-primary/10" placeholder="Précision facultative" />
        </label>

        {successMessage && <div className="flex gap-2 rounded-elite border border-emerald-200 bg-emerald-50 p-3 text-sm font-semibold text-emerald-800" role="status"><CheckCircle2 size={17} className="mt-0.5 shrink-0" />{successMessage}</div>}
        {errorMessage && <div className="flex gap-2 rounded-elite border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-800" role="alert"><AlertCircle size={17} className="mt-0.5 shrink-0" />{errorMessage}</div>}

        <button type="submit" disabled={submitting || cartLines.length === 0} className="w-full rounded-elite px-4 py-3 text-sm font-black text-white transition hover:brightness-110 disabled:opacity-45" style={{ backgroundColor: 'var(--primary)' }}>
          {submitting ? 'Enregistrement…' : 'Enregistrer le brouillon'}
        </button>
        <p className="text-center text-[11px] font-semibold leading-relaxed text-text-muted">
          Cette action crée une commande DRAFT dans Digital Crown. Rien n’est encore transmis au fournisseur.
        </p>
      </form>
    </section>
  </div>
);

const Field = ({ label, value, onChange, required = false, type = 'text', inputMode }: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  type?: React.HTMLInputTypeAttribute;
  inputMode?: React.HTMLAttributes<HTMLInputElement>['inputMode'];
}) => (
  <label className="block">
    <span className="text-xs font-black text-text-muted">{label}</span>
    <input type={type} inputMode={inputMode} value={value} onChange={(event) => onChange(event.target.value)} required={required} className="mt-1 min-h-11 w-full rounded-elite border border-border-main bg-input-field px-3 py-2 text-sm font-semibold text-text-main outline-none focus:ring-2 focus:ring-primary/10" />
  </label>
);

const StateCard = ({ title, description, actionLabel, onAction }: { title: string; description: string; actionLabel?: string; onAction?: () => void }) => (
  <div className="rounded-elite-lg border border-border-main bg-card-bg p-8 text-center shadow-elite">
    <Package size={28} className="mx-auto text-text-muted" />
    <h3 className="mt-3 font-outfit text-xl font-black text-text-main">{title}</h3>
    <p className="mx-auto mt-2 max-w-lg text-sm font-medium leading-relaxed text-text-muted">{description}</p>
    {actionLabel && onAction && <button type="button" onClick={onAction} className="mt-4 rounded-elite px-4 py-2 text-sm font-black text-white" style={{ backgroundColor: 'var(--primary)' }}>{actionLabel}</button>}
  </div>
);
