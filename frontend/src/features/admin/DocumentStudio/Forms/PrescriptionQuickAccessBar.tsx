import React from 'react';
import { Clock3, FileText, Search, Sparkles, Star } from 'lucide-react';

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

type QuickSection = 'FAVORITES' | 'PROTOCOLS' | 'RECENT' | 'FREQUENT';

const sectionLabels: Record<QuickSection, string> = {
  FAVORITES: 'Favoris',
  PROTOCOLS: 'Protocoles',
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
}: {
  drugs: DrugItem[];
  setDrugs: (drugs: DrugItem[]) => void;
}) {
  const [section, setSection] = React.useState<QuickSection>('FAVORITES');
  const [query, setQuery] = React.useState('');
  const [reusables, setReusables] = React.useState<ReusablePrescription[]>([]);
  const [quickPicks, setQuickPicks] = React.useState<QuickPicks>({});
  const [catalog, setCatalog] = React.useState<CatalogPresentation[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [highlighted, setHighlighted] = React.useState(0);
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
        const response = await api.get('/medications/search', { params: { q: value } });
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
    ...matchingReusables.map(row => ({ type: 'reusable' as const, row })),
    ...catalog.map(row => ({ type: 'presentation' as const, row })),
  ];

  const applyReusable = async (row: ReusablePrescription) => {
    setDrugs(hydrateReusable(row.drugs || [], drugs));
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

  const applyPresentation = (row: CatalogPresentation) => {
    setDrugs(selectedPresentation(row, drugs));
    setQuery('');
    setCatalog([]);
    inputRef.current?.focus();
  };

  const idleRows = React.useMemo(() => {
    if (section === 'FAVORITES') return reusables.filter(item => item.is_favorite).slice(0, 6);
    if (section === 'PROTOCOLS') return reusables.filter(item => item.kind !== 'SAVED_PRESCRIPTION').slice(0, 6);
    return [];
  }, [reusables, section]);

  const idleMedicationNames = section === 'RECENT'
    ? (quickPicks.recent_medications || [])
    : section === 'FREQUENT'
      ? (quickPicks.frequent_medications || [])
      : [];

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
      <div className="relative">
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
            <button
              key={row.id}
              type="button"
              onClick={() => void applyReusable(row)}
              className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-border-main bg-background px-3 text-[10px] font-black text-text-main transition hover:border-primary/30 hover:text-primary"
            >
              {row.is_favorite ? <Star size={12} fill="currentColor" /> : <FileText size={12} />}
              {row.label}
            </button>
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
              {section === 'FAVORITES' ? 'Aucun favori.' : section === 'PROTOCOLS' ? 'Aucun protocole enregistré.' : 'Aucun usage enregistré.'}
            </span>
          )}
        </div>
      )}
    </section>
  );
}
