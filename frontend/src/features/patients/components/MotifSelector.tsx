import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Search, X, ChevronDown, ChevronUp, Zap, Plus } from 'lucide-react';
import {
  MOTIFS_DICTIONARY,
  MOTIF_URGENCY_LABELS,
  type MotifCategory,
  type MotifItem,
} from '../../../data/motifsDictionary';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';

interface MotifSelectorProps {
  selected: string[];
  onChange: (ids: string[]) => void;
  maxSelect?: number;
}

type CabinetMotif = {
  id: string;
  label: string;
  category_id: string;
  urgency: MotifItem['urgency'];
  is_active: boolean;
  source: 'cabinet';
};

type DisplayMotif = MotifItem & {
  source?: 'system' | 'cabinet';
  is_active?: boolean;
};

type DisplayCategory = Omit<MotifCategory, 'motifs'> & { motifs: DisplayMotif[] };

const CABINET_CATEGORY: Omit<DisplayCategory, 'motifs'> = {
  id: 'CABINET',
  label: 'Cabinet',
  color: 'text-slate-700',
  bgColor: 'bg-slate-50',
  borderColor: 'border-slate-200',
};

export const MotifSelector: React.FC<MotifSelectorProps> = ({ selected, onChange, maxSelect = 6 }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['DOULEUR', 'URGENCE']));
  const [cabinetMotifs, setCabinetMotifs] = useState<CabinetMotif[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const createDialogRef = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = createDialogRef.current;
    if (!dialog) return;
    if (showCreate && !dialog.open) dialog.showModal();
    if (!showCreate && dialog.open) dialog.close();
  }, [showCreate]);
  const [newLabel, setNewLabel] = useState('');
  const [newCategory, setNewCategory] = useState('CABINET');
  const [newUrgency, setNewUrgency] = useState<MotifItem['urgency']>('normal');
  const [saving, setSaving] = useState(false);
  const [createError, setCreateError] = useState('');

  useEffect(() => {
    let cancelled = false;
    api.get('/motifs/', { params: { include_inactive: true } })
      .then(response => {
        if (!cancelled && Array.isArray(response.data)) setCabinetMotifs(response.data);
      })
      .catch(() => {
        if (!cancelled) setCabinetMotifs([]);
      });
    return () => { cancelled = true; };
  }, []);

  const categories = useMemo<DisplayCategory[]>(() => {
    const byId = new Map<string, DisplayCategory>(
      MOTIFS_DICTIONARY.map(cat => [
        cat.id,
        { ...cat, motifs: cat.motifs.map(motif => ({ ...motif, source: 'system' as const })) },
      ]),
    );
    byId.set('CABINET', { ...CABINET_CATEGORY, motifs: [] });

    for (const motif of cabinetMotifs.filter(item => item.is_active)) {
      const target = byId.get(motif.category_id) || byId.get('CABINET')!;
      target.motifs.push({
        id: motif.id,
        label: motif.label,
        urgency: motif.urgency,
        specialty_hints: [],
        act_hints: [],
        source: 'cabinet',
        is_active: motif.is_active,
      });
    }

    return Array.from(byId.values()).filter(cat => cat.motifs.length > 0);
  }, [cabinetMotifs]);

  const motifIndex = useMemo(() => {
    const map = new Map<string, { motif: DisplayMotif; category: DisplayCategory }>();
    for (const category of categories) {
      for (const motif of category.motifs) map.set(motif.id, { motif, category });
    }

    // Keep inactive cabinet motifs resolvable for historical patient records.
    for (const motif of cabinetMotifs.filter(item => !item.is_active)) {
      const systemCategory = MOTIFS_DICTIONARY.find(cat => cat.id === motif.category_id);
      const category: DisplayCategory = systemCategory
        ? { ...systemCategory, motifs: [] }
        : { ...CABINET_CATEGORY, motifs: [] };
      map.set(motif.id, {
        motif: {
          id: motif.id,
          label: motif.label,
          urgency: motif.urgency,
          specialty_hints: [],
          act_hints: [],
          source: 'cabinet',
          is_active: false,
        },
        category,
      });
    }
    return map;
  }, [categories, cabinetMotifs]);

  const toggleCategory = (id: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggle = (motifId: string) => {
    if (selected.includes(motifId)) onChange(selected.filter(id => id !== motifId));
    else if (selected.length < maxSelect) onChange([...selected, motifId]);
  };

  const filteredDict = useMemo(() => {
    const query = searchQuery.trim().toLocaleLowerCase('fr-FR');
    if (!query) return categories;
    return categories
      .map(cat => ({
        ...cat,
        motifs: cat.motifs.filter(m => m.label.toLocaleLowerCase('fr-FR').includes(query)),
      }))
      .filter(cat => cat.motifs.length > 0);
  }, [categories, searchQuery]);

  const hasUrgent = selected.some(id => motifIndex.get(id)?.motif.urgency === 'urgence');

  const createMotif = async () => {
    const label = newLabel.trim();
    if (!label || saving) return;
    setSaving(true);
    setCreateError('');
    try {
      const response = await api.post('/motifs/', {
        label,
        category_id: newCategory,
        urgency: newUrgency,
      });
      const created = response.data as CabinetMotif;
      setCabinetMotifs(prev => [...prev.filter(item => item.id !== created.id), created]);
      setExpandedCategories(prev => new Set(prev).add(created.category_id || 'CABINET'));
      if (selected.length < maxSelect && !selected.includes(created.id)) onChange([...selected, created.id]);
      setNewLabel('');
      setNewCategory('CABINET');
      setNewUrgency('normal');
      setShowCreate(false);
    } catch (error: any) {
      const status = error?.response?.status;
      // Never render raw FastAPI validation details: they may be structured arrays
      // (React would crash) or include submitted sensitive data.
      setCreateError(
        status === 403
          ? 'La création de motifs est réservée aux utilisateurs autorisés à modifier les réglages du cabinet.'
          : status === 422
            ? 'Motif invalide. Vérifiez les informations avant de réessayer.'
            : status === 409
              ? 'Ce motif existe déjà. Modifiez son nom avant de réessayer.'
              : 'Impossible de créer ce motif. Réessayez.',
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-3">
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 p-3 bg-slate-50 rounded-xl border border-slate-200">
          {hasUrgent && (
            <span className="flex items-center gap-1 text-xs font-black text-red-600 uppercase tracking-widest bg-red-50 border border-red-200 px-2 py-1 rounded-full">
              <Zap size={9} /> URGENCE DÉTECTÉE
            </span>
          )}
          {selected.map(id => {
            const resolved = motifIndex.get(id);
            if (!resolved) {
              return (
                <span key={id} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border border-slate-200 bg-slate-50 text-slate-600">
                  {id}
                  <span className="text-xs uppercase tracking-wider text-slate-400">Historique</span>
                  <button type="button" onClick={() => toggle(id)} className="hover:opacity-70 transition-opacity ml-0.5" aria-label={`Retirer ${id}`}>
                    <X size={12} />
                  </button>
                </span>
              );
            }
            const { motif, category } = resolved;
            const inactive = motif.source === 'cabinet' && motif.is_active === false;
            return (
              <span
                key={id}
                className={cn('flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border', category.bgColor, category.color, category.borderColor)}
              >
                {motif.label}
                {motif.source === 'cabinet' && (
                  <span className="text-xs uppercase tracking-wider opacity-60">{inactive ? 'Historique' : 'Cabinet'}</span>
                )}
                <button type="button" onClick={() => toggle(id)} className="hover:opacity-70 transition-opacity ml-0.5" aria-label={`Retirer ${motif.label}`}>
                  <X size={12} />
                </button>
              </span>
            );
          })}
          <button type="button" onClick={() => onChange([])} className="text-xs font-bold text-slate-400 hover:text-red-500 transition-colors px-2 py-1">
            Tout effacer
          </button>
        </div>
      )}

      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Rechercher un motif..."
          aria-label="Rechercher un motif de consultation"
          value={searchQuery}
          onChange={e => {
            setSearchQuery(e.target.value);
            if (e.target.value) setExpandedCategories(new Set(categories.map(c => c.id)));
          }}
          className="w-full pl-9 pr-9 py-2 text-sm bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
        />
        {searchQuery && (
          <button type="button" onClick={() => setSearchQuery('')} aria-label="Effacer la recherche de motifs" className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
            <X size={14} />
          </button>
        )}
      </div>

      <button
        type="button"
        onClick={() => { setShowCreate(true); setCreateError(''); }}
        className="inline-flex items-center gap-1.5 text-xs font-black text-primary hover:opacity-80"
      >
        <Plus size={14} /> Ajouter un motif
      </button>

      {selected.length >= maxSelect && (
        <p className="text-xs font-semibold text-amber-600 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-lg">
          Maximum {maxSelect} motifs sélectionnés.
        </p>
      )}

      <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1 custom-scrollbar">
        {filteredDict.map(cat => (
          <div key={cat.id} className="border border-slate-100 rounded-xl overflow-hidden">
            <button
              type="button"
              onClick={() => toggleCategory(cat.id)}
              aria-expanded={expandedCategories.has(cat.id)}
              aria-controls={"motif-category-" + cat.id}
              className={cn('w-full flex items-center justify-between px-4 py-2.5 font-bold text-sm transition-colors', cat.bgColor, cat.color)}
            >
              <span>{cat.label}</span>
              <div className="flex items-center gap-2">
                {selected.filter(id => cat.motifs.some(m => m.id === id)).length > 0 && (
                  <span className="text-xs font-black px-1.5 py-0.5 rounded-full bg-white/60">
                    {selected.filter(id => cat.motifs.some(m => m.id === id)).length}
                  </span>
                )}
                {expandedCategories.has(cat.id) ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </div>
            </button>
            {expandedCategories.has(cat.id) && (
              <div id={"motif-category-" + cat.id} className="bg-white divide-y divide-slate-50">
                {cat.motifs.map(motif => {
                  const isSelected = selected.includes(motif.id);
                  const urgency = MOTIF_URGENCY_LABELS[motif.urgency];
                  return (
                    <button
                      key={motif.id}
                      type="button"
                      onClick={() => toggle(motif.id)}
                      aria-pressed={isSelected}
                      disabled={!isSelected && selected.length >= maxSelect}
                      className={cn(
                        'w-full flex items-center justify-between px-4 py-2.5 text-left transition-all text-sm',
                        isSelected ? cn(cat.bgColor, 'font-bold') : 'hover:bg-slate-50 text-slate-700',
                        !isSelected && selected.length >= maxSelect && 'opacity-40 cursor-not-allowed',
                      )}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <div className={cn('w-4 h-4 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-all', isSelected ? cn('border-current', cat.color, cat.bgColor) : 'border-slate-300')}>
                          {isSelected && <div className={cn('w-2 h-2 rounded-sm', cat.color.replace('text-', 'bg-'))} />}
                        </div>
                        <span className={cn('truncate', isSelected ? cat.color : '')}>{motif.label}</span>
                        {motif.source === 'cabinet' && <span className="text-xs font-black uppercase tracking-wider text-slate-400">Cabinet</span>}
                      </div>
                      <span className={cn('text-xs font-black border px-1.5 py-0.5 rounded-full uppercase tracking-wider flex-shrink-0', urgency.color)}>
                        {urgency.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      <dialog
        ref={createDialogRef}
        onClose={() => setShowCreate(false)}
        aria-labelledby="custom-motif-title"
        className="fixed inset-0 m-auto w-[min(92vw,28rem)] max-h-[90dvh] overflow-y-auto rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl backdrop:bg-slate-900/50 backdrop:backdrop-blur-sm"
      >
        {showCreate && (
          <div className="w-full">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-black uppercase tracking-widest text-slate-400">Motif du cabinet</p>
                <h3 id="custom-motif-title" className="mt-1 text-lg font-black text-slate-900">Ajouter un motif</h3>
              </div>
              <button type="button" onClick={() => setShowCreate(false)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-50" aria-label="Fermer">
                <X size={16} />
              </button>
            </div>

            <div className="mt-5 space-y-4">
              <label className="block space-y-1.5">
                <span className="text-xs font-bold text-slate-600">Nom du motif *</span>
                <input value={newLabel} onChange={e => setNewLabel(e.target.value)} maxLength={255} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold outline-none focus:border-primary focus:ring-2 focus:ring-primary/10" placeholder="Ex. Contrôle gouttière ancienne" />
              </label>
              <label className="block space-y-1.5">
                <span className="text-xs font-bold text-slate-600">Catégorie</span>
                <select value={newCategory} onChange={e => setNewCategory(e.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold">
                  <option value="CABINET">Cabinet</option>
                  {MOTIFS_DICTIONARY.map(cat => <option key={cat.id} value={cat.id}>{cat.label}</option>)}
                </select>
              </label>
              <label className="block space-y-1.5">
                <span className="text-xs font-bold text-slate-600">Priorité d’accueil</span>
                <select value={newUrgency} onChange={e => setNewUrgency(e.target.value as MotifItem['urgency'])} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold">
                  <option value="urgence">Urgence</option>
                  <option value="normal">Normal</option>
                  <option value="planifié">Planifié</option>
                </select>
              </label>
              <p className="text-xs font-medium text-slate-500">Aucun acte ni spécialité ne sera suggéré automatiquement pour un motif du cabinet.</p>
              {createError && <p role="alert" className="rounded-xl bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700">{createError}</p>}
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={() => setShowCreate(false)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-bold text-slate-600">Annuler</button>
              <button type="button" onClick={() => void createMotif()} disabled={!newLabel.trim() || saving} className="rounded-xl bg-primary px-4 py-2.5 text-sm font-black text-white disabled:opacity-40">
                {saving ? 'Enregistrement…' : 'Enregistrer'}
              </button>
            </div>
          </div>
        )}
      </dialog>
    </div>
  );
};
