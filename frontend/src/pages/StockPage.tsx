import React, { useState, useCallback, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Package, AlertTriangle, Plus, Minus, Edit2, Trash2, X, Search, CheckCircle2
} from 'lucide-react';
import { cn } from '../utils/cn';
import { api } from '../services/api';
import { EliteGhostLoader } from '../components/EliteGhostLoader';
import { CrownDialog } from '../components/CrownDialog';

// ─── Types ────────────────────────────────────────────────────────────────────

interface StockItem {
  id: number;
  nom: string;
  categorie: string;
  quantite: number;
  seuil_alerte: number;
  unite: string;
  prix_unitaire: number | null;
  fournisseur: string | null;
  notes: string | null;
  alerte: boolean;
}

const CATEGORIES = [
  { value: 'ALL',         label: 'Tous' },
  { value: 'CONSOMMABLE', label: 'Consommables' },
  { value: 'MATERIAU',    label: 'Matériaux' },
  { value: 'MEDICAMENT',  label: 'Médicaments' },
  { value: 'EQUIPEMENT',  label: 'Équipements' },
];

const CATEGORIE_LABELS: Record<string, string> = {
  CONSOMMABLE: 'Consommable',
  MATERIAU:    'Matériau',
  MEDICAMENT:  'Médicament',
  EQUIPEMENT:  'Équipement',
};

const mutationErrorMessage = (error: any, fallback: string) => {
  const detail = error?.response?.data?.detail;
  return typeof detail === 'string' && detail.trim() ? detail : fallback;
};

const CATEGORIE_COLORS: Record<string, string> = {
  CONSOMMABLE: 'bg-blue-50 text-blue-700 border-blue-200',
  MATERIAU:    'bg-purple-50 text-purple-700 border-purple-200',
  MEDICAMENT:  'bg-emerald-50 text-emerald-700 border-emerald-200',
  EQUIPEMENT:  'bg-amber-50 text-amber-700 border-amber-200',
};

// ─── Modal Ajout / Édition ────────────────────────────────────────────────────

interface ModalProps {
  item: Partial<StockItem> | null;
  onClose: () => void;
  onSaved: () => void;
}

const StockModal = ({ item, onClose, onSaved }: ModalProps) => {
  const isEdit = !!item?.id;
  const [form, setForm] = useState({
    nom:           item?.nom           ?? '',
    categorie:     item?.categorie     ?? 'CONSOMMABLE',
    quantite:      item?.quantite      ?? 0,
    seuil_alerte:  item?.seuil_alerte  ?? 5,
    unite:         item?.unite         ?? 'unité',
    prix_unitaire: item?.prix_unitaire ?? '',
    fournisseur:   item?.fournisseur   ?? '',
    notes:         item?.notes         ?? '',
  });
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (savingRef.current) return;
    savingRef.current = true;
    setSaving(true);
    setError(null);
    try {
      const payload = {
        ...form,
        quantite:      Number(form.quantite),
        seuil_alerte:  Number(form.seuil_alerte),
        prix_unitaire: form.prix_unitaire !== '' ? Number(form.prix_unitaire) : null,
        fournisseur:   form.fournisseur || null,
        notes:         form.notes || null,
      };
      if (isEdit) {
        await api.patch(`/stock/items/${item!.id}`, payload);
      } else {
        await api.post('/stock/items', payload);
      }
      onSaved();
    } catch (err: any) {
      setError(mutationErrorMessage(err, isEdit ? "La modification n'a pas été enregistrée." : "L'article n'a pas été ajouté."));
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  };

  const field = (label: string, key: keyof typeof form, type = 'text', props?: React.InputHTMLAttributes<HTMLInputElement>) => (
    <div>
      <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">{label}</label>
      <input
        type={type}
        value={String(form[key])}
        onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
        className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:ring-2 focus:ring-primary/20 bg-white"
        {...props}
      />
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-[2rem] shadow-2xl w-full max-w-lg overflow-hidden">
        <div className="flex items-center justify-between px-8 py-5 border-b border-slate-100">
          <h2 className="text-sm font-black uppercase tracking-widest" style={{ color: 'var(--primary)' }}>
            {isEdit ? 'Modifier l\'article' : 'Nouvel article'}
          </h2>
          <button onClick={onClose} className="p-2 rounded-xl hover:bg-slate-100 transition-colors">
            <X size={18} className="text-slate-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-8 py-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {field('Nom de l\'article', 'nom', 'text', { required: true, placeholder: 'Ex: Gants nitrile S' })}
            <div>
              <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Catégorie</label>
              <select
                value={form.categorie}
                onChange={e => setForm(f => ({ ...f, categorie: e.target.value }))}
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:ring-2 focus:ring-primary/20 bg-white"
              >
                {CATEGORIES.filter(c => c.value !== 'ALL').map(c => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {field('Quantité', 'quantite', 'number', { min: '0', step: '0.5' })}
            {field('Seuil alerte', 'seuil_alerte', 'number', { min: '0', step: '0.5' })}
            {field('Unité', 'unite', 'text', { placeholder: 'boîte, mL, pcs…' })}
          </div>

          <div className="grid grid-cols-2 gap-4">
            {field('Prix unitaire (MAD)', 'prix_unitaire', 'number', { min: '0', step: '0.01', placeholder: 'Optionnel' })}
            {field('Fournisseur', 'fournisseur', 'text', { placeholder: 'Optionnel' })}
          </div>

          <div>
            <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Notes</label>
            <textarea
              value={form.notes}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:ring-2 focus:ring-primary/20 bg-white resize-none"
              rows={2}
              placeholder="Optionnel"
            />
          </div>

          {error && (
            <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">
              {error}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 border border-slate-200 rounded-xl text-[11px] font-black uppercase tracking-widest text-slate-500 hover:bg-slate-50 transition-colors"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={saving || !form.nom}
              className="flex-1 py-2.5 rounded-xl text-[11px] font-black uppercase tracking-widest text-white transition-colors disabled:opacity-50"
              style={{ background: 'var(--primary)' }}
            >
              {saving ? 'Enregistrement…' : isEdit ? 'Mettre à jour' : 'Ajouter'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── Page principale ─────────────────────────────────────────────────────────

export const StockPage = () => {
  const qc = useQueryClient();
  const [activeCategorie, setActiveCategorie] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [modalItem, setModalItem] = useState<Partial<StockItem> | null | undefined>(undefined);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<StockItem | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);

  const { data: items = [], isLoading, isError, refetch } = useQuery<StockItem[]>({
    queryKey: ['stock-items'],
    queryFn: () => api.get('/stock/items').then(r => r.data),
  });

  const { data: alertsData } = useQuery<{ count: number; items: StockItem[] }>({
    queryKey: ['stock-alerts'],
    queryFn: () => api.get('/stock/alerts').then(r => r.data),
  });

  const invalidate = useCallback(() => {
    qc.invalidateQueries({ queryKey: ['stock-items'] });
    qc.invalidateQueries({ queryKey: ['stock-alerts'] });
  }, [qc]);

  const adjustQuantite = async (item: StockItem, delta: number) => {
    const next = Math.max(0, item.quantite + delta);
    setMutationError(null);
    try {
      await api.patch(`/stock/items/${item.id}`, { quantite: next });
      invalidate();
    } catch (err: any) {
      setMutationError(mutationErrorMessage(err, "La quantité n'a pas été enregistrée."));
    }
  };

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    setMutationError(null);
    try {
      await api.delete(`/stock/items/${id}`);
      invalidate();
      setDeleteTarget(null);
    } catch (err: any) {
      setMutationError(mutationErrorMessage(err, "L'article n'a pas été supprimé."));
    } finally {
      setDeletingId(null);
    }
  };

  const filtered = items.filter(item => {
    const matchCat = activeCategorie === 'ALL' || item.categorie === activeCategorie;
    const matchSearch = item.nom.toLowerCase().includes(searchTerm.toLowerCase())
      || (item.fournisseur ?? '').toLowerCase().includes(searchTerm.toLowerCase());
    return matchCat && matchSearch;
  });

  if (isLoading) {
    return <EliteGhostLoader text="Chargement du stock…" size="medium" />;
  }

  if (isError) {
    return (
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-xl font-black tracking-tight text-slate-800">Gestion du Stock</h1>
        </div>
        <div className="min-h-[320px] flex flex-col items-center justify-center gap-4 rounded-[2rem] border border-amber-200 bg-amber-50/70 px-6 text-center">
          <AlertTriangle size={40} className="text-amber-500" />
          <div>
            <h2 className="font-black text-slate-800">Stock indisponible</h2>
            <p className="mt-1 max-w-xl text-sm text-slate-600">Impossible de confirmer le contenu du stock. Aucun état vide n’est affiché tant que la lecture n’a pas réussi.</p>
          </div>
          <button type="button" onClick={() => void refetch()} className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-black uppercase tracking-wider text-white">Réessayer</button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

      <div className="space-y-3">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ background: 'var(--primary)/10', backgroundColor: 'color-mix(in srgb, var(--primary) 10%, transparent)' }}>
              <Package size={20} style={{ color: 'var(--primary)' }} />
            </div>
            <div>
              <h1 className="text-xl font-black tracking-tight text-slate-800">Gestion du Stock</h1>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                {items.length} article{items.length !== 1 ? 's' : ''} · {alertsData?.count ?? 0} alerte{(alertsData?.count ?? 0) !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <button
            onClick={() => setModalItem({})}
            className="flex w-full sm:w-auto items-center justify-center gap-2 px-5 py-2.5 rounded-2xl text-[11px] font-black uppercase tracking-widest text-white shadow-lg transition-all hover:opacity-90 active:scale-95"
            style={{ background: 'var(--primary)' }}
          >
            <Plus size={14} /> Ajouter un article
          </button>
        </div>
      </div>

      {/* Alert banner */}
      {(alertsData?.count ?? 0) > 0 && (
        <div className="flex items-center gap-3 px-6 py-4 bg-red-50 border border-red-200 rounded-[1.5rem]">
          <AlertTriangle size={18} className="text-red-500 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-black text-red-700">
              {alertsData!.count} article{alertsData!.count > 1 ? 's' : ''} en dessous du seuil d'alerte
            </p>
            <p className="text-[10px] font-medium text-red-500 mt-0.5">
              {alertsData!.items.map(i => `${i.nom} (${i.quantite} ${i.unite})`).join(' · ')}
            </p>
          </div>
        </div>
      )}

      {mutationError && (
        <div role="alert" className="flex items-start gap-3 rounded-[1.5rem] border border-red-200 bg-red-50 px-5 py-4 text-red-700">
          <AlertTriangle size={18} className="mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-black">Action stock non enregistrée</p>
            <p className="mt-0.5 text-xs font-semibold">{mutationError}</p>
          </div>
        </div>
      )}

      {/* Filtres */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex max-w-full gap-1.5 overflow-x-auto p-1 bg-slate-100 rounded-xl">
          {CATEGORIES.map(cat => (
            <button
              key={cat.value}
              onClick={() => setActiveCategorie(cat.value)}
              className={cn(
                "px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all",
                activeCategorie === cat.value ? "bg-white shadow-sm" : "text-slate-500 hover:text-slate-700"
              )}
              style={activeCategorie === cat.value ? { color: 'var(--primary)' } : {}}
            >
              {cat.label}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={15} />
          <input
            type="text"
            placeholder="Rechercher…"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="pl-9 pr-4 py-2 border border-slate-200 rounded-xl text-sm font-medium outline-none focus:ring-2 focus:ring-primary/10 bg-white w-56"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm overflow-x-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center py-20 text-slate-400">
            <CheckCircle2 size={40} className="text-emerald-300 mb-3" />
            <p className="font-bold text-sm">
              {items.length === 0 ? 'Aucun article. Commencez par en ajouter un.' : 'Aucun résultat pour cette recherche.'}
            </p>
          </div>
        ) : (
          <table className="w-full min-w-[760px]">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50">
                <th className="text-left px-6 py-3 text-[9px] font-black text-slate-400 uppercase tracking-widest">Article</th>
                <th className="text-left px-6 py-3 text-[9px] font-black text-slate-400 uppercase tracking-widest">Catégorie</th>
                <th className="text-center px-6 py-3 text-[9px] font-black text-slate-400 uppercase tracking-widest">Quantité</th>
                <th className="text-center px-6 py-3 text-[9px] font-black text-slate-400 uppercase tracking-widest">Seuil</th>
                <th className="text-left px-6 py-3 text-[9px] font-black text-slate-400 uppercase tracking-widest">Fournisseur</th>
                <th className="px-6 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {filtered.map(item => (
                <tr
                  key={item.id}
                  className={cn(
                    "transition-colors group",
                    item.alerte ? "bg-red-50/40 hover:bg-red-50" : "hover:bg-slate-50"
                  )}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {item.alerte && <AlertTriangle size={13} className="text-red-400 shrink-0" />}
                      <div>
                        <p className="font-black text-sm text-slate-800">{item.nom}</p>
                        {item.notes && (
                          <p className="text-[10px] text-slate-400 font-medium mt-0.5 truncate max-w-[200px]">{item.notes}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={cn(
                      "text-[9px] font-black uppercase tracking-widest px-2.5 py-1 rounded-lg border",
                      CATEGORIE_COLORS[item.categorie] ?? 'bg-slate-50 text-slate-600 border-slate-200'
                    )}>
                      {CATEGORIE_LABELS[item.categorie] ?? item.categorie}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={() => adjustQuantite(item, -1)}
                        disabled={item.quantite <= 0}
                        className="w-6 h-6 rounded-lg border border-slate-200 flex items-center justify-center hover:bg-slate-100 disabled:opacity-30 transition-colors"
                      >
                        <Minus size={10} />
                      </button>
                      <span className={cn(
                        "text-sm font-black w-16 text-center",
                        item.alerte ? "text-red-600" : "text-slate-800"
                      )}>
                        {item.quantite} <span className="text-[10px] font-medium text-slate-400">{item.unite}</span>
                      </span>
                      <button
                        onClick={() => adjustQuantite(item, 1)}
                        className="w-6 h-6 rounded-lg border border-slate-200 flex items-center justify-center hover:bg-slate-100 transition-colors"
                      >
                        <Plus size={10} />
                      </button>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-sm font-bold text-slate-500">
                      {item.seuil_alerte} <span className="text-[10px] text-slate-400">{item.unite}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500 font-medium">
                    {item.fournisseur ?? <span className="text-slate-300">—</span>}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => setModalItem(item)}
                        className="p-2 rounded-xl border border-slate-200 hover:bg-slate-100 transition-colors"
                        title="Modifier"
                      >
                        <Edit2 size={13} className="text-slate-500" />
                      </button>
                      <button
                        onClick={() => { setMutationError(null); setDeleteTarget(item); }}
                        disabled={deletingId === item.id}
                        className="p-2 rounded-xl border border-red-100 hover:bg-red-50 transition-colors disabled:opacity-50"
                        title="Supprimer"
                      >
                        <Trash2 size={13} className="text-red-400" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <CrownDialog
        open={deleteTarget !== null}
        ariaLabel="Supprimer cet article ?"
        onClose={() => {
          if (deletingId === null) {
            setDeleteTarget(null);
            setMutationError(null);
          }
        }}
        className="max-w-md"
      >
        {deleteTarget && (
          <section className="w-full rounded-[2rem] bg-white p-6 shadow-2xl">
            <h2 className="text-lg font-black text-slate-800">Supprimer cet article ?</h2>
            <p className="mt-2 text-sm font-semibold text-slate-600">{deleteTarget.nom} sera supprimé définitivement du stock.</p>
            {mutationError && <div role="alert" className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{mutationError}</div>}
            <div className="mt-6 grid grid-cols-2 gap-3">
              <button type="button" data-dialog-autofocus onClick={() => { if (deletingId === null) { setDeleteTarget(null); setMutationError(null); } }} disabled={deletingId !== null} className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-black text-slate-600 disabled:opacity-50">Annuler</button>
              <button type="button" onClick={() => void handleDelete(deleteTarget.id)} disabled={deletingId === deleteTarget.id} className="rounded-xl bg-red-600 px-4 py-3 text-sm font-black text-white disabled:opacity-50">{deletingId === deleteTarget.id ? 'Suppression…' : 'Supprimer définitivement'}</button>
            </div>
          </section>
        )}
      </CrownDialog>

      {/* Modal */}
      {modalItem !== undefined && (
        <StockModal
          item={modalItem}
          onClose={() => setModalItem(undefined)}
          onSaved={() => {
            setModalItem(undefined);
            invalidate();
          }}
        />
      )}
    </div>
  );
};
