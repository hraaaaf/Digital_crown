import React from 'react';
import { BookmarkPlus, Clock3, FileText, MoreHorizontal, Search, Sparkles, Star, X } from 'lucide-react';

import { api } from '../../../../services/api';
import type { DrugItem } from './prescriptionTypes';

type ReusableKind = 'PROTOCOL' | 'SAVED_PRESCRIPTION';

type ReusablePrescription = {
  id: number;
  act_context: string;
  label: string;
  kind: ReusableKind;
  drugs: Array<Partial<DrugItem>>;
  indication?: string | null;
  is_favorite: boolean;
  usage_count: number;
  last_used?: string | null;
};

type CatalogPresentation = {
  presentation_id: string;
  nom: string;
  dci: string;
  dosage: string;
  unite: string;
  forme: string;
  source?: {
    id?: string;
    label?: string;
    snapshot_date?: string;
    current_marketing_status_verified?: boolean;
  };
};

type QuickPicks = {
  recent_medications?: string[];
  frequent_medications?: string[];
};

type QuickSection = 'FAVORITES' | 'PROTOCOLS' | 'SAVED' | 'RECENT' | 'FREQUENT';

const sectionLabels: Record<QuickSection, string> = {
  FAVORITES: 'Favoris',
  PROTOCOLS: 'Protocoles',
  SAVED: 'Ordonnances',
  RECENT: 'Récentes',
  FREQUENT: 'Fréquentes',
};

const presentationStrength = (row: CatalogPresentation) =>
  [row.dosage, row.unite].filter(Boolean).join(' ').trim();

const hydrateReusable = (incoming: Array<Partial<DrugItem>>, current: DrugItem[]): DrugItem[] => {
  const occupied = current.filter(drug => drug.name.trim());
  const maxId = current.reduce((max, drug) => Math.max(max, Number(drug.id) || 0), 0);
  const added = incoming.map((drug, index) => ({
    id: maxId + index + 1,
    name: String(drug.name || ''),
    dosage: String(drug.dosage || ''),
    forme: String(drug.forme || ''),
    posologie: String(drug.posologie || ''),
    type: drug.type === 'EXAMEN' ? 'EXAMEN' as const : 'MEDICAMENT' as const,
    quantite: drug.quantite ?? undefined,
    non_substituable: Boolean(drug.non_substituable),
  }));
  return [...occupied, ...added];
};

function medicationOnly(name: string, current: DrugItem[]): DrugItem[] {
  const empty = current.findIndex(drug => !drug.name.trim());
  if (empty >= 0) {
    return current.map((drug, index) => index === empty ? { ...drug, name: name.toUpperCase() } : drug);
  }
  const maxId = current.reduce((max, drug) => Math.max(max, Number(drug.id) || 0), 0);
  return [...current, {
    id: maxId + 1,
    name: name.toUpperCase(),
    dosage: '',
    forme: '',
    posologie: '',
    type: 'MEDICAMENT',
  }];
}

function selectedPresentation(row: CatalogPresentation, current: DrugItem[]): DrugItem[] {
  const source = row.source || {};
  const next: Partial<DrugItem> = {
    name: row.nom,
    dosage: presentationStrength(row),
    forme: row.forme || '',
    posologie: '',
    type: 'MEDICAMENT',
    catalogPresentationId: row.presentation_id,
    catalogDci: row.dci || '',
    catalogSourceId: source.id,
    catalogSourceLabel: source.label,
    catalogSnapshotDate: source.snapshot_date,
    catalogMarketingStatusVerified: Boolean(source.current_marketing_status_verified),
  };
  const empty = current.findIndex(drug => !drug.name.trim());
  if (empty >= 0) {
    return current.map((drug, index) => index === empty ? { ...drug, ...next } as DrugItem : drug);
  }
  const maxId = current.reduce((max, drug) => Math.max(max, Number(drug.id) || 0), 0);
  return [...current, { id: maxId + 1, ...next } as DrugItem];
}

export function PrescriptionQuickAccessBar({
  drugs,
  setDrugs,
  prescriptionIndication,
  onPrescriptionIndicationChange,
}: {
  drugs: DrugItem[];
  setDrugs: (drugs: DrugItem[]) => void;
  prescriptionIndication: string;
  onPrescriptionIndicationChange?: (value: string) => void;
}) {
  const [section, setSection] = React.useState<QuickSection>('FAVORITES');
  const [query, setQuery] = React.useState('');
  const [reusables, setReusables] = React.useState<ReusablePrescription[]>([]);
  const [quickPicks, setQuickPicks] = React.useState<QuickPicks>({});
  const [catalog, setCatalog] = React.useState<CatalogPresentation[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [highlighted, setHighlighted] = React.useState(0);
  const [showActions, setShowActions] = React.useState(false);
  const [saveKind, setSaveKind] = React.useState<ReusableKind | null>(null);
  const [saveName, setSaveName] = React.useState('');
  const [saveActCode, setSaveActCode] = React.useState<string | null>(null);
  const [appliedReusable, setAppliedReusable] = React.useState<ReusablePrescription | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [saveError, setSaveError] = React.useState('');
  const inputRef = React.useRef<HTMLInputElement>(null);

  const reload = React.useCallback(async () => {
    const [reusableResponse, habitsResponse] = await Promise.all([
      api.get('/prescriptions/habits/presets'),
      api.get('/prescriptions/habits/suggest', { params: { q: '' } }),
    ]);
    setReusables(Array.isArray(reusableResponse.data) ? reusableResponse.data : []);
    setQuickPicks(habitsResponse.data || {});
  }, []);

  React.useEffect(() => {
    void reload().catch(() => {
      setReusables([]);
      setQuickPicks({});
    });
  }, [reload]);

  React.useEffect(() => {
    const value = query.trim();
    if (value.length < 2) {
      setCatalog([]);
      setHighlighted(0);
      return;
    }
    let cancelled = false;
    setLoading(true);
    const timer = window.setTimeout(async () => {
      try {
        const response = await api.get('/medications/neo/search', { params: { q: value } });
        if (!cancelled) setCatalog(Array.isArray(response.data) ? response.data.slice(0, 6) : []);
      } catch {
        if (!cancelled) setCatalog([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 180);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query]);

  const normalizedQuery = query.trim().toLocaleLowerCase();
  const matchingReusables = reusables.filter(item => (
    !normalizedQuery
    || item.label.toLocaleLowerCase().includes(normalizedQuery)
    || item.act_context.toLocaleLowerCase().includes(normalizedQuery)
  )).slice(0, 6);

  const searchItems: Array<
    | { type: 'presentation'; row: CatalogPresentation }
    | { type: 'reusable'; row: ReusablePrescription }
  > = [
    ...catalog.map(row => ({ type: 'presentation' as const, row })),
    ...matchingReusables.map(row => ({ type: 'reusable' as const, row })),
  ];

  const applyReusable = async (row: ReusablePrescription) => {
    setDrugs(hydrateReusable(row.drugs || [], drugs));
    if (row.kind === 'SAVED_PRESCRIPTION' && row.indication) {
      onPrescriptionIndicationChange?.(row.indication);
    }
    setAppliedReusable(row);
    setQuery('');
    setCatalog([]);
    inputRef.current?.focus();
    try {
      await api.post(`/prescriptions/preferences/${row.id}/use`);
      await reload();
    } catch {
      // Usage analytics must never block prescription editing.
    }
  };

  const applyMedicationName = (name: string) => {
    setDrugs(medicationOnly(name, drugs));
    setQuery('');
    setCatalog([]);
    inputRef.current?.focus();
  };
  const toggleFavorite = async (row: ReusablePrescription) => {
    const next = !row.is_favorite;
    setReusables(current => current.map(item => item.id === row.id ? { ...item, is_favorite: next } : item));
    try {
      await api.put(`/prescriptions/preferences/${row.id}/favorite`, { is_favorite: next });
    } catch {
      setReusables(current => current.map(item => item.id === row.id ? { ...item, is_favorite: row.is_favorite } : item));
    }
  };


  const applyPresentation = (row: CatalogPresentation) => {
    setDrugs(selectedPresentation(row, drugs));
    setQuery('');
    setCatalog([]);
    inputRef.current?.focus();
  };

  const idleRows = React.useMemo(() => {
    if (section === 'FAVORITES') return reusables.filter(item => item.is_favorite).slice(0, 6);
    if (section === 'PROTOCOLS') return reusables.filter(item => item.kind !== 'SAVED_PRESCRIPTION').slice(0, 6);
    if (section === 'SAVED') return reusables.filter(item => item.kind === 'SAVED_PRESCRIPTION').slice(0, 6);
    if (section === 'RECENT') return [...reusables]
      .filter(item => item.last_used)
      .sort((a, b) => String(b.last_used).localeCompare(String(a.last_used)))
      .slice(0, 4);
    if (section === 'FREQUENT') return [...reusables]
      .filter(item => item.usage_count > 0)
      .sort((a, b) => b.usage_count - a.usage_count)
      .slice(0, 4);
    return [];
  }, [reusables, section]);

  const idleMedicationNames = section === 'RECENT'
    ? (quickPicks.recent_medications || [])
    : section === 'FREQUENT'
      ? (quickPicks.frequent_medications || [])
      : [];

  const saveReusable = async () => {
    const name = saveName.trim();
    const reusableDrugs = drugs.filter(drug => drug.name.trim());
    if (!saveKind || !name || !reusableDrugs.length || saving) return;
    setSaving(true);
    setSaveError('');
    try {
      await api.post('/prescriptions/preferences', {
        act_code: saveActCode || name,
        label: name,
        kind: saveKind,
        indication: saveKind === 'SAVED_PRESCRIPTION' ? (prescriptionIndication.trim() || null) : null,
        drugs: reusableDrugs.map(drug => ({
          name: drug.name,
          dosage: drug.dosage,
          forme: drug.forme,
          posologie: drug.posologie,
          type: drug.type || 'MEDICAMENT',
          quantite: drug.quantite ?? null,
          non_substituable: Boolean(drug.non_substituable),
        })),
      });
      setSaveKind(null);
      setSaveName('');
      setSaveActCode(null);
      setShowActions(false);
      await reload();
    } catch (error: any) {
      setSaveError(error?.response?.data?.detail || 'Enregistrement impossible.');
    } finally {
      setSaving(false);
    }
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!query.trim() || !searchItems.length) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setHighlighted(value => Math.min(value + 1, searchItems.length - 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setHighlighted(value => Math.max(value - 1, 0));
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const item = searchItems[highlighted] || searchItems[0];
      if (!item) return;
      if (item.type === 'reusable') void applyReusable(item.row);
      else applyPresentation(item.row);
    } else if (event.key === 'Escape') {
      setQuery('');
      setCatalog([]);
    }
  };

  return (
    <section data-neo-quick-access className="rounded-2xl border border-border-main bg-card/95 p-3 shadow-sm sm:p-4">
      <div className="flex items-stretch gap-2">
        <div className="relative min-w-0 flex-1">
          <Search size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            ref={inputRef}
            value={query}
            onChange={event => { setQuery(event.target.value); setHighlighted(0); }}
            onKeyDown={onKeyDown}
            autoComplete="off"
            aria-label="Ajouter un médicament ou un protocole"
            placeholder="Ajouter un médicament ou un protocole…"
            className="min-h-12 w-full rounded-xl border border-border-main bg-background pl-10 pr-4 text-sm font-bold text-text-main outline-none transition focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
          />
        </div>
        <div className="relative">
          <button
            type="button"
            aria-label="Actions ordonnance"
            aria-expanded={showActions}
            onClick={() => setShowActions(value => !value)}
            className="flex h-12 w-12 items-center justify-center rounded-xl border border-border-main bg-background text-text-muted transition hover:border-primary/30 hover:text-primary"
          >
            <MoreHorizontal size={18} />
          </button>
          {showActions && (
            <div className="absolute right-0 top-full z-[120] mt-2 w-64 overflow-hidden rounded-xl border border-border-main bg-card py-1.5 shadow-2xl">
              <button
                type="button"
                disabled={!drugs.some(drug => drug.name.trim())}
                onClick={() => { setSaveKind('PROTOCOL'); setSaveName(''); setSaveActCode(null); setSaveError(''); }}
                className="flex min-h-11 w-full items-center gap-2 px-3 text-left text-xs font-bold text-text-main hover:bg-primary/5 disabled:opacity-40"
              >
                <BookmarkPlus size={14} /> Enregistrer comme protocole
              </button>
              <button
                type="button"
                disabled={!drugs.some(drug => drug.name.trim())}
                onClick={() => { setSaveKind('SAVED_PRESCRIPTION'); setSaveName(''); setSaveActCode(null); setSaveError(''); }}
                className="flex min-h-11 w-full items-center gap-2 px-3 text-left text-xs font-bold text-text-main hover:bg-primary/5 disabled:opacity-40"
              >
                <FileText size={14} /> Enregistrer cette ordonnance
              </button>
              {appliedReusable?.kind === 'PROTOCOL' && (
                <button
                  type="button"
                  disabled={!drugs.some(drug => drug.name.trim())}
                  onClick={() => {
                    setSaveKind('PROTOCOL');
                    setSaveName(appliedReusable.label);
                    setSaveActCode(appliedReusable.act_context);
                    setSaveError('');
                  }}
                  className="flex min-h-11 w-full items-center gap-2 border-t border-border-main px-3 text-left text-xs font-bold text-text-main hover:bg-primary/5 disabled:opacity-40"
                >
                  <Sparkles size={14} /> Mettre à jour « {appliedReusable.label} »
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {!query.trim() && (
        <div className="mt-2 flex flex-wrap gap-1.5" role="tablist" aria-label="Accès rapides ordonnance">
          {(Object.keys(sectionLabels) as QuickSection[]).map(key => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={section === key}
              onClick={() => setSection(key)}
              className={`min-h-9 rounded-lg px-3 text-[10px] font-black transition ${
                section === key ? 'bg-primary/10 text-primary' : 'text-text-muted hover:bg-background hover:text-text-main'
              }`}
            >
              {sectionLabels[key]}
            </button>
          ))}
        </div>
      )}

      {query.trim() ? (
        <div className="mt-2 overflow-hidden rounded-xl border border-border-main bg-background">
          {loading && !searchItems.length ? (
            <div className="px-3 py-3 text-xs font-semibold text-text-muted">Recherche…</div>
          ) : searchItems.length ? searchItems.map((item, index) => {
            if (item.type === 'reusable') {
              const row = item.row;
              return (
                <button
                  key={`r-${row.id}`}
                  type="button"
                  onClick={() => void applyReusable(row)}
                  className={`flex min-h-12 w-full items-center justify-between gap-3 px-3 py-2 text-left ${
                    highlighted === index ? 'bg-primary/10' : 'hover:bg-primary/5'
                  }`}
                >
                  <span className="min-w-0">
                    <span className="block truncate text-xs font-black text-text-main">{row.label}</span>
                    <span className="block text-[9px] font-bold text-text-muted">
                      {row.kind === 'SAVED_PRESCRIPTION' ? 'Ordonnance enregistrée' : 'Protocole'} · {row.drugs?.length || 0} ligne(s)
                    </span>
                  </span>
                  <FileText size={14} className="shrink-0 text-text-muted" />
                </button>
              );
            }
            const row = item.row;
            return (
              <button
                key={`m-${row.presentation_id}`}
                type="button"
                onClick={() => applyPresentation(row)}
                className={`flex min-h-12 w-full items-center justify-between gap-3 px-3 py-2 text-left ${
                  highlighted === index ? 'bg-primary/10' : 'hover:bg-primary/5'
                }`}
              >
                <span className="min-w-0">
                  <span className="block truncate text-xs font-black text-text-main">{row.nom}</span>
                  <span className="block truncate text-[9px] font-bold text-text-muted">{row.dci || 'DCI non renseignée'} · {presentationStrength(row) || 'dosage à préciser'}</span>
                </span>
                <Sparkles size={14} className="shrink-0 text-text-muted" />
              </button>
            );
          }) : (
            <div className="px-3 py-3 text-xs font-semibold text-text-muted">Aucun résultat.</div>
          )}
        </div>
      ) : (
        <div className="mt-2 flex flex-wrap gap-2">
          {idleRows.map(row => (
            <div key={row.id} className="inline-flex min-h-10 overflow-hidden rounded-xl border border-border-main bg-background">
              <button
                type="button"
                onClick={() => void applyReusable(row)}
                className="inline-flex items-center gap-2 px-3 text-[10px] font-black text-text-main transition hover:bg-primary/5 hover:text-primary"
              >
                <FileText size={12} /> {row.label}
              </button>
              <button
                type="button"
                aria-label={row.is_favorite ? `Retirer ${row.label} des favoris` : `Ajouter ${row.label} aux favoris`}
                onClick={() => void toggleFavorite(row)}
                className="flex w-9 items-center justify-center border-l border-border-main text-text-muted transition hover:bg-primary/5 hover:text-primary"
              >
                <Star size={12} fill={row.is_favorite ? 'currentColor' : 'none'} />
              </button>
            </div>
          ))}
          {idleMedicationNames.map(name => (
            <button
              key={name}
              type="button"
              onClick={() => applyMedicationName(name)}
              className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-border-main bg-background px-3 text-[10px] font-black text-text-main transition hover:border-primary/30 hover:text-primary"
            >
              <Clock3 size={12} /> {name}
            </button>
          ))}
          {!idleRows.length && !idleMedicationNames.length && (
            <span className="px-1 py-2 text-[10px] font-bold text-text-muted">
              {section === 'FAVORITES' ? 'Aucun favori.' : section === 'PROTOCOLS' ? 'Aucun protocole enregistré.' : section === 'SAVED' ? 'Aucune ordonnance enregistrée.' : 'Aucun usage enregistré.'}
            </span>
          )}
        </div>
      )}
      {saveKind && (
        <div role="dialog" aria-modal="true" aria-label={saveKind === 'PROTOCOL' ? 'Enregistrer comme protocole' : 'Enregistrer cette ordonnance'} className="fixed inset-0 z-[160] flex items-center justify-center bg-slate-950/40 p-4">
          <div className="w-full max-w-md rounded-2xl border border-border-main bg-card p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-[9px] font-black uppercase tracking-widest text-text-muted">
                  {saveKind === 'PROTOCOL' ? 'Protocole' : 'Ordonnance enregistrée'}
                </div>
                <h3 className="mt-1 text-lg font-black text-text-main">
                  {saveKind === 'PROTOCOL' ? 'Enregistrer comme protocole' : 'Enregistrer cette ordonnance'}
                </h3>
              </div>
              <button type="button" aria-label="Fermer" onClick={() => { setSaveKind(null); setSaveActCode(null); }} className="rounded-lg p-2 text-text-muted hover:bg-background">
                <X size={16} />
              </button>
            </div>
            <label className="mt-4 block">
              <span className="mb-1.5 block text-xs font-bold text-text-muted">Nom</span>
              <input
                autoFocus
                value={saveName}
                onChange={event => setSaveName(event.target.value)}
                onKeyDown={event => { if (event.key === 'Enter') void saveReusable(); }}
                placeholder={saveKind === 'PROTOCOL' ? 'Ex. Post-op extraction' : 'Ex. Ordonnance post-op habituelle'}
                className="min-h-11 w-full rounded-xl border border-border-main bg-background px-3 text-sm font-semibold text-text-main outline-none focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
              />
            </label>
            <p className="mt-2 text-[10px] font-semibold text-text-muted">
              {drugs.filter(drug => drug.name.trim()).length} ligne(s). {saveKind === 'PROTOCOL' ? 'Le protocole restera éditable après insertion.' : 'L’indication actuelle est conservée avec ce modèle.'}
            </p>
            {saveError && <p role="alert" className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700">{saveError}</p>}
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={() => { setSaveKind(null); setSaveActCode(null); }} className="min-h-11 rounded-xl border border-border-main px-4 text-sm font-bold text-text-muted">Annuler</button>
              <button type="button" onClick={() => void saveReusable()} disabled={!saveName.trim() || saving} className="min-h-11 rounded-xl bg-primary px-4 text-sm font-black text-white disabled:opacity-40">
                {saving ? 'Enregistrement…' : 'Enregistrer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
