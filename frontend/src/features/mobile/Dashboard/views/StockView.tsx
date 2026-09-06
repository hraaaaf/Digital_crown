import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Minus, Package, Plus, RefreshCw, Search, X } from 'lucide-react';
import { api } from '../../../../services/api';

export type MobileStockItem = {
  id: number;
  nom: string;
  categorie: string;
  quantite: number;
  seuil_alerte: number;
  unite: string;
  prix_unitaire?: number | null;
  fournisseur?: string | null;
  notes?: string | null;
  alerte: boolean;
};

type Filter = 'all' | 'attention';

const CATEGORIES = [
  ['CONSOMMABLE', 'Consommable'],
  ['MATERIAU', 'Matériau'],
  ['MEDICAMENT', 'Médicament'],
  ['EQUIPEMENT', 'Équipement'],
] as const;

const CATEGORY_LABELS = Object.fromEntries(CATEGORIES) as Record<string, string>;

function stockState(item: MobileStockItem) {
  if (item.quantite <= 0) {
    return { label: 'Rupture', className: 'border-rose-500/25 bg-rose-500/5 text-rose-600' };
  }
  if (item.alerte) {
    return { label: 'Alerte', className: 'border-amber-500/25 bg-amber-500/5 text-amber-700' };
  }
  return { label: 'OK', className: 'border-emerald-500/25 bg-emerald-500/5 text-emerald-700' };
}

export function StockView({ previewData }: { previewData?: MobileStockItem[] }) {
  const [items, setItems] = useState<MobileStockItem[]>(previewData ?? []);
  const [filter, setFilter] = useState<Filter>('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(!previewData);
  const [error, setError] = useState<string | null>(null);
  const [mutatingId, setMutatingId] = useState<number | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    nom: '',
    categorie: 'CONSOMMABLE',
    quantite: '0',
    seuil_alerte: '5',
    unite: 'unité',
  });

  const load = async () => {
    if (previewData) {
      setItems(previewData);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<MobileStockItem[]>('/stock/items');
      setItems(Array.isArray(response.data) ? response.data : []);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Impossible de charger le stock.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, [previewData]);

  const counts = useMemo(() => ({
    rupture: items.filter(item => item.quantite <= 0).length,
    alert: items.filter(item => item.quantite > 0 && item.alerte).length,
    ok: items.filter(item => !item.alerte).length,
  }), [items]);

  const visible = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return items.filter(item => {
      if (filter === 'attention' && !item.alerte) return false;
      if (!needle) return true;
      return item.nom.toLowerCase().includes(needle)
        || String(item.fournisseur ?? '').toLowerCase().includes(needle);
    });
  }, [items, filter, search]);

  const adjust = async (item: MobileStockItem, delta: number) => {
    if (previewData) return;
    const next = Math.max(0, Number(item.quantite) + delta);
    if (next === item.quantite) return;
    setMutatingId(item.id);
    setError(null);
    try {
      const response = await api.patch<MobileStockItem>(`/stock/items/${item.id}`, { quantite: next });
      setItems(current => current.map(candidate => candidate.id === item.id ? response.data : candidate));
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Mouvement de stock impossible.');
    } finally {
      setMutatingId(null);
    }
  };

  const addItem = async (event: React.FormEvent) => {
    event.preventDefault();
    if (previewData || !form.nom.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const response = await api.post<MobileStockItem>('/stock/items', {
        nom: form.nom.trim(),
        categorie: form.categorie,
        quantite: Math.max(0, Number(form.quantite) || 0),
        seuil_alerte: Math.max(0, Number(form.seuil_alerte) || 0),
        unite: form.unite.trim() || 'unité',
      });
      setItems(current => [...current, response.data]);
      setForm({ nom: '', categorie: 'CONSOMMABLE', quantite: '0', seuil_alerte: '5', unite: 'unité' });
      setAddOpen(false);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Impossible d’ajouter cet article.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="pb-6" data-mobile-stock>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">Cabinet</p>
          <h1 className="mt-1 text-[24px] font-black text-text-main">Stock</h1>
          <p className="mt-1 text-[11px] font-bold text-text-muted">{items.length} article{items.length > 1 ? 's' : ''}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            aria-label="Actualiser le stock"
            onClick={() => void load()}
            disabled={loading || Boolean(previewData)}
            className="grid min-h-11 min-w-11 place-items-center rounded-full border border-glass-border bg-card text-text-muted disabled:opacity-50"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          </button>
          <button
            type="button"
            aria-label="Ajouter un article"
            onClick={() => setAddOpen(true)}
            disabled={Boolean(previewData)}
            className="grid min-h-11 min-w-11 place-items-center rounded-full bg-primary text-white disabled:opacity-50"
          >
            <Plus size={20} />
          </button>
        </div>
      </div>

      <div className="mb-4 grid grid-cols-3 gap-2" aria-label="Résumé du stock">
        {[
          ['Rupture', counts.rupture, 'text-rose-600'],
          ['Alerte', counts.alert, 'text-amber-700'],
          ['OK', counts.ok, 'text-emerald-700'],
        ].map(([label, count, color]) => (
          <div key={String(label)} className="rounded-[18px] border border-glass-border bg-card px-3 py-3 text-center shadow-sm">
            <p className={`text-[18px] font-black ${color}`}>{count}</p>
            <p className="mt-0.5 text-[9px] font-black uppercase tracking-wider text-text-muted">{label}</p>
          </div>
        ))}
      </div>

      <div className="mb-3 relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" size={16} />
        <input
          value={search}
          onChange={event => setSearch(event.target.value)}
          placeholder="Rechercher un article…"
          className="min-h-11 w-full rounded-[16px] border border-glass-border bg-card pl-10 pr-4 text-[12px] font-bold text-text-main outline-none focus:ring-2 focus:ring-primary/20"
        />
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2 rounded-[18px] border border-glass-border bg-card p-1.5">
        {([['all', 'Tous'], ['attention', 'À traiter']] as const).map(([id, label]) => (
          <button
            key={id}
            type="button"
            aria-pressed={filter === id}
            onClick={() => setFilter(id)}
            className={`min-h-11 rounded-[14px] px-3 text-[11px] font-black ${filter === id ? 'bg-primary text-white' : 'text-text-muted'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-3 rounded-[18px] border border-rose-500/20 bg-rose-500/5 px-4 py-3 text-[11px] font-bold text-rose-600">
          {error}
        </div>
      )}

      {!loading && visible.length === 0 && (
        <div className="rounded-[24px] border border-glass-border bg-card px-5 py-8 text-center shadow-sm">
          <Package size={28} className="mx-auto text-primary" />
          <h2 className="mt-3 text-[16px] font-black text-text-main">Aucun article</h2>
          <p className="mt-1 text-[11px] font-bold text-text-muted">Aucun résultat pour ce filtre.</p>
        </div>
      )}

      <div className="grid gap-3">
        {visible.map(item => {
          const meta = stockState(item);
          const busy = mutatingId === item.id;
          return (
            <article key={item.id} className="rounded-[24px] border border-glass-border bg-card p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <span className={`inline-flex rounded-full border px-2.5 py-1 text-[9px] font-black ${meta.className}`}>{meta.label}</span>
                  <h2 className="mt-2 truncate text-[15px] font-black text-text-main">{item.nom}</h2>
                  <p className="mt-1 text-[10px] font-bold text-text-muted">
                    {CATEGORY_LABELS[item.categorie] ?? item.categorie} · seuil {item.seuil_alerte} {item.unite}
                  </p>
                  {item.fournisseur && <p className="mt-1 truncate text-[10px] font-bold text-text-muted">{item.fournisseur}</p>}
                </div>
                {item.alerte && <AlertTriangle size={18} className={item.quantite <= 0 ? 'text-rose-500' : 'text-amber-500'} />}
              </div>

              <div className="mt-4 grid grid-cols-[44px_1fr_44px] items-center gap-2">
                <button
                  type="button"
                  aria-label={`Retirer une ${item.unite} de ${item.nom}`}
                  disabled={busy || Boolean(previewData) || item.quantite <= 0}
                  onClick={() => void adjust(item, -1)}
                  className="grid min-h-11 place-items-center rounded-[16px] border border-glass-border bg-background text-text-main disabled:opacity-35"
                >
                  <Minus size={17} />
                </button>
                <div className="text-center">
                  <p className="text-[22px] font-black text-text-main">{item.quantite}</p>
                  <p className="text-[9px] font-black uppercase tracking-wider text-text-muted">{item.unite}</p>
                </div>
                <button
                  type="button"
                  aria-label={`Ajouter une ${item.unite} à ${item.nom}`}
                  disabled={busy || Boolean(previewData)}
                  onClick={() => void adjust(item, 1)}
                  className="grid min-h-11 place-items-center rounded-[16px] bg-primary text-white disabled:opacity-35"
                >
                  <Plus size={17} />
                </button>
              </div>
            </article>
          );
        })}
      </div>

      {addOpen && (
        <div className="fixed inset-0 z-[80] flex items-end bg-slate-950/20 px-3 pb-[max(12px,env(safe-area-inset-bottom))] pt-12 backdrop-blur-[1px]">
          <section role="dialog" aria-modal="true" aria-labelledby="mobile-stock-add-title" className="mx-auto w-full max-w-[720px] rounded-[28px] border border-glass-border bg-card p-5 shadow-elite-hover">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Mouvement rapide</p>
                <h2 id="mobile-stock-add-title" className="mt-1 text-[18px] font-black text-text-main">Ajouter un article</h2>
              </div>
              <button type="button" aria-label="Fermer" onClick={() => setAddOpen(false)} className="grid min-h-11 min-w-11 place-items-center rounded-full border border-glass-border bg-background text-text-muted"><X size={18} /></button>
            </div>

            <form onSubmit={addItem} className="grid gap-3">
              <input required value={form.nom} onChange={event => setForm(current => ({ ...current, nom: event.target.value }))} placeholder="Nom de l’article" className="min-h-11 rounded-[16px] border border-glass-border bg-background px-4 text-[12px] font-bold text-text-main outline-none focus:ring-2 focus:ring-primary/20" />
              <select value={form.categorie} onChange={event => setForm(current => ({ ...current, categorie: event.target.value }))} className="min-h-11 rounded-[16px] border border-glass-border bg-background px-4 text-[12px] font-bold text-text-main outline-none">
                {CATEGORIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
              <div className="grid grid-cols-3 gap-2">
                <input aria-label="Quantité" type="number" min="0" step="0.5" value={form.quantite} onChange={event => setForm(current => ({ ...current, quantite: event.target.value }))} placeholder="Qté" className="min-h-11 min-w-0 rounded-[16px] border border-glass-border bg-background px-3 text-[12px] font-bold text-text-main outline-none" />
                <input aria-label="Seuil d'alerte" type="number" min="0" step="0.5" value={form.seuil_alerte} onChange={event => setForm(current => ({ ...current, seuil_alerte: event.target.value }))} placeholder="Seuil" className="min-h-11 min-w-0 rounded-[16px] border border-glass-border bg-background px-3 text-[12px] font-bold text-text-main outline-none" />
                <input aria-label="Unité" value={form.unite} onChange={event => setForm(current => ({ ...current, unite: event.target.value }))} placeholder="Unité" className="min-h-11 min-w-0 rounded-[16px] border border-glass-border bg-background px-3 text-[12px] font-bold text-text-main outline-none" />
              </div>
              <button type="submit" disabled={saving || !form.nom.trim()} className="min-h-11 rounded-[16px] bg-primary px-4 text-[11px] font-black text-white disabled:opacity-50">{saving ? 'Ajout…' : 'Ajouter'}</button>
            </form>
          </section>
        </div>
      )}
    </section>
  );
}
