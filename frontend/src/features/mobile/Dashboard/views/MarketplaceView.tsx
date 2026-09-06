import { useState } from 'react';
import { AlertCircle, CheckCircle2, Minus, Package, Plus, Search, ShoppingCart, X } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import { availabilityBadgeClass, formatMoney, type PartnerProduct } from '../../../partnerMarketplace/data';
import {
  type MarketplaceCustomer,
  type MarketplacePreviewData,
  usePartnerMarketplace,
} from '../../../partnerMarketplace/usePartnerMarketplace';

export function MarketplaceView({ previewData }: { previewData?: MarketplacePreviewData }) {
  const marketplace = usePartnerMarketplace({ previewData });
  const [checkoutOpen, setCheckoutOpen] = useState(false);

  const submitCheckout = async (event: React.FormEvent) => {
    event.preventDefault();
    await marketplace.submitDraft();
  };

  return (
    <section className="relative pb-28" data-mobile-marketplace>
      <div className="flex items-start justify-between gap-3 pt-1">
        <div className="min-w-0">
          <p className="text-[9px] font-black uppercase tracking-[0.18em] text-text-muted">Approvisionnement</p>
          <h1 className="mt-1 font-outfit text-[25px] font-black leading-none text-text-main">Marketplace</h1>
          <p className="mt-1.5 text-[11px] font-bold leading-relaxed text-text-muted">Référence connue → quantité → panier.</p>
        </div>
        <button
          type="button"
          disabled={marketplace.totalUnits === 0}
          onClick={() => setCheckoutOpen(true)}
          className="inline-flex min-h-11 shrink-0 items-center gap-2 rounded-[16px] bg-primary px-3 text-[11px] font-black text-white disabled:opacity-35"
          aria-label={`Ouvrir le panier, ${marketplace.totalUnits} unité${marketplace.totalUnits > 1 ? 's' : ''}`}
        >
          <ShoppingCart size={16} /> {marketplace.totalUnits}
        </button>
      </div>

      <label className="relative mt-4 block" htmlFor="mobile-marketplace-search">
        <span className="sr-only">Rechercher par nom ou SKU</span>
        <Search size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          id="mobile-marketplace-search"
          type="search"
          value={marketplace.search}
          onChange={(event) => marketplace.setSearch(event.target.value)}
          placeholder="Nom, référence ou SKU…"
          className="min-h-12 w-full rounded-[18px] border border-glass-border bg-card pl-10 pr-3 text-[12px] font-bold text-text-main outline-none focus:ring-2 focus:ring-primary/15"
        />
      </label>

      <div className="mt-3 flex gap-2 overflow-x-auto pb-1" aria-label="Filtres Marketplace mobile">
        <button
          type="button"
          onClick={() => marketplace.setAvailableOnly(!marketplace.availableOnly)}
          className={cn(
            'min-h-10 shrink-0 rounded-full border px-3 text-[10px] font-black',
            marketplace.availableOnly ? 'border-primary bg-primary text-white' : 'border-glass-border bg-card text-text-muted',
          )}
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
              'min-h-10 shrink-0 rounded-full border px-3 text-[10px] font-black',
              marketplace.category === item ? 'border-primary bg-primary text-white' : 'border-glass-border bg-card text-text-muted',
            )}
            aria-pressed={marketplace.category === item}
          >
            {item}
          </button>
        ))}
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <p className="text-[9px] font-black uppercase tracking-[0.16em] text-text-muted">{marketplace.filteredProducts.length} référence(s)</p>
        {marketplace.catalogError && (
          <button type="button" onClick={() => void marketplace.loadCatalog()} className="text-[10px] font-black text-primary">Réessayer</button>
        )}
      </div>

      <div className="mt-2.5 space-y-2.5">
        {marketplace.catalogLoading ? (
          <MobileState title="Chargement du catalogue…" />
        ) : marketplace.catalogError && marketplace.products.length === 0 ? (
          <MobileState title="Catalogue indisponible" />
        ) : marketplace.filteredProducts.length === 0 ? (
          <MobileState title="Aucune référence trouvée" />
        ) : marketplace.filteredProducts.map((product) => (
          <MobileProductRow
            key={product.id}
            product={product}
            quantity={marketplace.cart[product.id] ?? 0}
            onAdjust={marketplace.adjustQty}
          />
        ))}
      </div>

      {marketplace.totalUnits > 0 && !checkoutOpen && (
        <button
          type="button"
          onClick={() => setCheckoutOpen(true)}
          className="fixed left-5 right-5 z-[62] mx-auto flex min-h-14 max-w-[690px] items-center justify-between rounded-[20px] bg-primary px-4 text-[12px] font-black text-white shadow-2xl"
          style={{ bottom: 'max(100px, calc(env(safe-area-inset-bottom) + 92px))' }}
          data-mobile-marketplace-cart-cta
        >
          <span className="inline-flex items-center gap-2"><ShoppingCart size={18} /> Panier · {marketplace.totalUnits}</span>
          <span>{formatMoney(marketplace.estimatedTotal)} →</span>
        </button>
      )}

      {checkoutOpen && (
        <MobileCheckout
          customer={marketplace.customer}
          cartLines={marketplace.cartLines}
          total={marketplace.estimatedTotal}
          submitting={marketplace.submitting}
          successMessage={marketplace.successMessage}
          errorMessage={marketplace.errorMessage}
          onCustomerChange={marketplace.updateCustomer}
          onSubmit={submitCheckout}
          onClose={() => setCheckoutOpen(false)}
        />
      )}
    </section>
  );
}

function MobileProductRow({ product, quantity, onAdjust }: { product: PartnerProduct; quantity: number; onAdjust: (product: PartnerProduct, delta: number) => void }) {
  const disabled = product.availability === 'Discontinué';
  return (
    <article className="rounded-[20px] border border-glass-border bg-card p-3.5 shadow-sm" data-mobile-marketplace-product={product.id}>
      <div className="flex items-start gap-3">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-[14px] bg-primary/8 text-primary"><Package size={18} /></div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h2 className="truncate text-[12px] font-black text-text-main">{product.name}</h2>
              <p className="mt-0.5 truncate text-[9px] font-bold text-text-muted">{product.sku} · {product.category}</p>
            </div>
            <span className={cn('shrink-0 rounded-full border px-2 py-1 text-[8px] font-black', availabilityBadgeClass(product.availability))}>{product.availability}</span>
          </div>

          <div className="mt-3 flex items-end justify-between gap-3">
            <div>
              <p className="text-[14px] font-black text-text-main">{formatMoney(product.price)}</p>
              <p className="text-[9px] font-bold text-text-muted">/{product.unit}</p>
            </div>
            {disabled ? (
              <span className="pb-2 text-[9px] font-black text-text-muted">Indisponible</span>
            ) : (
              <div className="flex items-center gap-1.5" aria-label={`Quantité de ${product.name}`}>
                <button type="button" onClick={() => onAdjust(product, -1)} disabled={quantity === 0} className="grid h-11 w-11 place-items-center rounded-[14px] border border-glass-border bg-background text-text-main disabled:opacity-30" aria-label={`Retirer une unité de ${product.name}`}><Minus size={15} /></button>
                <span className="w-6 text-center text-[11px] font-black text-text-main" aria-live="polite">{quantity}</span>
                <button type="button" onClick={() => onAdjust(product, 1)} className="grid h-11 w-11 place-items-center rounded-[14px] bg-primary text-white" aria-label={`Ajouter une unité de ${product.name}`}><Plus size={15} /></button>
              </div>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

function MobileCheckout({ customer, cartLines, total, submitting, successMessage, errorMessage, onCustomerChange, onSubmit, onClose }: {
  customer: MarketplaceCustomer;
  cartLines: Array<PartnerProduct & { quantity: number; lineTotal: number }>;
  total: number;
  submitting: boolean;
  successMessage: string;
  errorMessage: string;
  onCustomerChange: (field: keyof MarketplaceCustomer, value: string) => void;
  onSubmit: (event: React.FormEvent) => void;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-[90] bg-slate-950/30 backdrop-blur-[2px]" data-mobile-marketplace-checkout>
      <button type="button" className="absolute inset-0" aria-label="Fermer le checkout" onClick={onClose} />
      <section role="dialog" aria-modal="true" aria-labelledby="mobile-marketplace-checkout-title" className="absolute bottom-0 left-0 right-0 max-h-[88dvh] overflow-y-auto rounded-t-[28px] border-t border-glass-border bg-card p-5 shadow-2xl">
        <div className="mx-auto max-w-[720px]">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[9px] font-black uppercase tracking-[0.16em] text-text-muted">Panier · {cartLines.reduce((sum, line) => sum + line.quantity, 0)} unité(s)</p>
              <h2 id="mobile-marketplace-checkout-title" className="mt-1 font-outfit text-[22px] font-black text-text-main">Préparer le DRAFT</h2>
            </div>
            <button type="button" onClick={onClose} className="grid h-11 w-11 place-items-center rounded-full border border-glass-border bg-background text-text-muted" aria-label="Fermer"><X size={18} /></button>
          </div>

          <div className="mt-4 rounded-[18px] bg-background p-3.5">
            <div className="space-y-2">
              {cartLines.map((line) => (
                <div key={line.id} className="flex items-center justify-between gap-3 text-[10px]">
                  <span className="min-w-0 truncate font-black text-text-main">{line.name} · {line.quantity}</span>
                  <span className="shrink-0 font-black text-text-main">{formatMoney(line.lineTotal)}</span>
                </div>
              ))}
            </div>
            <div className="mt-3 flex items-center justify-between border-t border-glass-border pt-3">
              <span className="text-[10px] font-bold text-text-muted">Total estimé</span>
              <span className="text-[16px] font-black text-text-main">{formatMoney(total)}</span>
            </div>
          </div>

          <form onSubmit={onSubmit} className="mt-4 space-y-3">
            <div className="rounded-[18px] border border-primary/10 bg-primary/5 p-3.5">
              <p className="text-[9px] font-black uppercase tracking-[0.15em] text-primary">Commander pour</p>
              <p className="mt-1 text-[11px] font-black text-text-main">{customer.fullName || 'Nom à compléter'} · {customer.clinic || 'Cabinet à compléter'}</p>
              <p className="mt-0.5 text-[9px] font-bold text-text-muted">{customer.email || 'Email à compléter'}</p>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <MobileField label="Nom complet" value={customer.fullName} onChange={(value) => onCustomerChange('fullName', value)} required />
              <MobileField label="Cabinet" value={customer.clinic} onChange={(value) => onCustomerChange('clinic', value)} required />
              <MobileField label="Email" value={customer.email} onChange={(value) => onCustomerChange('email', value)} required type="email" />
              <MobileField label="Téléphone" value={customer.phone} onChange={(value) => onCustomerChange('phone', value)} required inputMode="tel" />
              <MobileField label="Ville" value={customer.city} onChange={(value) => onCustomerChange('city', value)} required />
            </div>
            <label className="block">
              <span className="text-[9px] font-black text-text-muted">Note</span>
              <textarea value={customer.note} onChange={(event) => onCustomerChange('note', event.target.value)} rows={2} className="mt-1 w-full rounded-[16px] border border-glass-border bg-background px-3 py-2.5 text-[11px] font-bold text-text-main outline-none focus:ring-2 focus:ring-primary/15" placeholder="Facultatif" />
            </label>

            {successMessage && <div className="flex gap-2 rounded-[16px] border border-emerald-200 bg-emerald-50 p-3 text-[10px] font-bold text-emerald-800" role="status"><CheckCircle2 size={15} className="shrink-0" />{successMessage}</div>}
            {errorMessage && <div className="flex gap-2 rounded-[16px] border border-red-200 bg-red-50 p-3 text-[10px] font-bold text-red-800" role="alert"><AlertCircle size={15} className="shrink-0" />{errorMessage}</div>}

            <button type="submit" disabled={submitting || cartLines.length === 0} className="min-h-12 w-full rounded-[18px] bg-primary px-4 text-[11px] font-black text-white disabled:opacity-40">
              {submitting ? 'Enregistrement…' : 'Enregistrer le brouillon'}
            </button>
            <p className="pb-[max(4px,env(safe-area-inset-bottom))] text-center text-[9px] font-bold leading-relaxed text-text-muted">
              Crée un DRAFT Digital Crown. Rien n’est transmis au fournisseur.
            </p>
          </form>
        </div>
      </section>
    </div>
  );
}

function MobileField({ label, value, onChange, required = false, type = 'text', inputMode }: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  type?: React.HTMLInputTypeAttribute;
  inputMode?: React.HTMLAttributes<HTMLInputElement>['inputMode'];
}) {
  return (
    <label className="block">
      <span className="text-[9px] font-black text-text-muted">{label}</span>
      <input type={type} inputMode={inputMode} value={value} onChange={(event) => onChange(event.target.value)} required={required} className="mt-1 min-h-11 w-full rounded-[16px] border border-glass-border bg-background px-3 text-[11px] font-bold text-text-main outline-none focus:ring-2 focus:ring-primary/15" />
    </label>
  );
}

function MobileState({ title }: { title: string }) {
  return <div className="rounded-[20px] border border-glass-border bg-card p-6 text-center text-[11px] font-black text-text-muted">{title}</div>;
}
