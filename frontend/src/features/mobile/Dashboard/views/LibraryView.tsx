import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Clock3, Search, Star } from 'lucide-react';
import { CLINICAL_PROTOCOLS } from '../../../../data/clinical-protocols';
import { ClinicalRefContent } from '../../../clinical-ref/ClinicalRefContent';
import type { ClinicalProtocol } from '../../../clinical-ref/types';
import { cn } from '../../../../utils/cn';

const FAVORITES_KEY = 'dc_favs';
const RECENTS_KEY = 'dc_recents';

const DIFFICULTY_LABELS: Record<ClinicalProtocol['difficulty'], string> = {
  routine: 'Courant',
  complex: 'Complexe',
  specialist: 'Spécialiste',
};

const DIFFICULTY_CLASSES: Record<ClinicalProtocol['difficulty'], string> = {
  routine: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-700',
  complex: 'border-amber-500/20 bg-amber-500/10 text-amber-700',
  specialist: 'border-rose-500/20 bg-rose-500/10 text-rose-700',
};

function readStoredCodes(key: string): string[] {
  try {
    const raw = window.localStorage.getItem(key);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((value): value is string => typeof value === 'string') : [];
  } catch {
    return [];
  }
}

function writeStoredCodes(key: string, values: string[]) {
  try {
    window.localStorage.setItem(key, JSON.stringify(values));
  } catch {
    // Library remains usable even when browser storage is unavailable.
  }
}

export function LibraryView({ role }: { role?: string }) {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<ClinicalProtocol | null>(null);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [favoritesOnly, setFavoritesOnly] = useState(false);

  const accessAllowed = !role || role === 'DENTISTE' || role === 'ADMIN';

  useEffect(() => {
    setFavorites(readStoredCodes(FAVORITES_KEY));
  }, []);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    return CLINICAL_PROTOCOLS
      .filter(protocol => !favoritesOnly || favorites.includes(protocol.act_code))
      .filter(protocol => {
        if (!query) return true;
        return protocol.act_names.some(name => name.toLowerCase().includes(query))
          || protocol.act_code.toLowerCase().includes(query)
          || protocol.category.toLowerCase().includes(query);
      })
      .sort((a, b) => a.act_names[0].localeCompare(b.act_names[0], 'fr'));
  }, [favorites, favoritesOnly, search]);

  const toggleFavorite = (protocol: ClinicalProtocol) => {
    const next = favorites.includes(protocol.act_code)
      ? favorites.filter(code => code !== protocol.act_code)
      : [...favorites, protocol.act_code];
    setFavorites(next);
    writeStoredCodes(FAVORITES_KEY, next);
  };

  const openProtocol = (protocol: ClinicalProtocol) => {
    const recents = readStoredCodes(RECENTS_KEY);
    writeStoredCodes(RECENTS_KEY, [protocol.act_code, ...recents.filter(code => code !== protocol.act_code)].slice(0, 8));
    setSelected(protocol);
  };

  if (!accessAllowed) {
    return (
      <section data-mobile-library className="pb-8 pt-2">
        <div className="rounded-[24px] border border-glass-border bg-card p-5 shadow-sm">
          <p className="text-[10px] font-black uppercase tracking-[0.16em] text-text-muted">Bibliothèque clinique</p>
          <h1 className="mt-2 text-[24px] font-black tracking-tight text-text-main">Accès réservé</h1>
          <p className="mt-2 text-[12px] font-semibold leading-relaxed text-text-muted">Cette référence clinique est disponible pour les praticiens et administrateurs.</p>
        </div>
      </section>
    );
  }

  if (selected) {
    return (
      <section data-mobile-library data-mobile-library-detail className="pb-6 pt-1">
        <button
          type="button"
          onClick={() => setSelected(null)}
          className="mb-3 inline-flex min-h-11 items-center gap-2 rounded-full border border-glass-border bg-card px-4 text-[11px] font-black text-text-main shadow-sm"
        >
          <ArrowLeft size={16} /> Bibliothèque
        </button>

        <div className="mb-4 rounded-[26px] border border-glass-border bg-card p-5 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">{selected.category}</p>
              <h1 className="mt-1 text-[25px] font-black leading-tight tracking-tight text-text-main">{selected.act_names[0]}</h1>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-full border border-glass-border bg-background px-2.5 py-1 text-[10px] font-black text-text-muted">
                  <Clock3 size={12} /> {selected.duration_min} min
                </span>
                <span className={cn('rounded-full border px-2.5 py-1 text-[10px] font-black', DIFFICULTY_CLASSES[selected.difficulty])}>
                  {DIFFICULTY_LABELS[selected.difficulty]}
                </span>
              </div>
            </div>
            <button
              type="button"
              aria-label={favorites.includes(selected.act_code) ? `Retirer ${selected.act_names[0]} des favoris` : `Ajouter ${selected.act_names[0]} aux favoris`}
              onClick={() => toggleFavorite(selected)}
              className={cn(
                'grid h-11 w-11 shrink-0 place-items-center rounded-full border transition-colors',
                favorites.includes(selected.act_code)
                  ? 'border-amber-400/30 bg-amber-400/10 text-amber-600'
                  : 'border-glass-border bg-background text-text-muted',
              )}
            >
              <Star size={18} fill={favorites.includes(selected.act_code) ? 'currentColor' : 'none'} />
            </button>
          </div>
        </div>

        <div className="min-h-[520px] rounded-[26px] border border-glass-border bg-card p-4 shadow-sm">
          <ClinicalRefContent protocol={selected} />
        </div>
      </section>
    );
  }

  return (
    <section data-mobile-library className="pb-8 pt-1">
      <div className="mb-5 flex items-end justify-between gap-4">
        <div>
          <p className="text-[9px] font-black uppercase tracking-[0.16em] text-text-muted">CABINET</p>
          <h1 className="mt-1 text-[28px] font-black tracking-tight text-text-main">Bibliothèque</h1>
        </div>
        <span className="rounded-full border border-primary/15 bg-primary/5 px-3 py-1.5 text-[10px] font-black text-primary">{CLINICAL_PROTOCOLS.length} protocoles</span>
      </div>

      <label className="relative block">
        <Search size={17} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          value={search}
          onChange={event => setSearch(event.target.value)}
          placeholder="Rechercher un acte, code, discipline…"
          className="h-12 w-full rounded-[18px] border border-glass-border bg-card pl-11 pr-4 text-[12px] font-bold text-text-main shadow-sm outline-none transition focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
        />
      </label>

      <div className="mt-3 flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => setFavoritesOnly(value => !value)}
          className={cn(
            'inline-flex min-h-11 items-center gap-2 rounded-full border px-4 text-[10px] font-black transition-colors',
            favoritesOnly ? 'border-amber-400/30 bg-amber-400/10 text-amber-700' : 'border-glass-border bg-card text-text-muted',
          )}
        >
          <Star size={14} fill={favoritesOnly ? 'currentColor' : 'none'} /> Favoris {favorites.length > 0 ? `(${favorites.length})` : ''}
        </button>
        <span className="text-[10px] font-black text-text-muted">{filtered.length} résultat{filtered.length === 1 ? '' : 's'}</span>
      </div>

      <div className="mt-4 grid gap-3">
        {filtered.map(protocol => {
          const isFavorite = favorites.includes(protocol.act_code);
          return (
            <article key={protocol.act_code} className="relative rounded-[22px] border border-glass-border bg-card shadow-sm">
              <button
                type="button"
                onClick={() => openProtocol(protocol)}
                className="min-h-[96px] w-full rounded-[22px] px-4 py-4 pr-14 text-left active:scale-[0.995]"
              >
                <h2 className="text-[14px] font-black leading-snug text-text-main">{protocol.act_names[0]}</h2>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] font-bold text-text-muted">
                  <span>{protocol.category}</span>
                  <span aria-hidden="true">•</span>
                  <span>{protocol.duration_min} min</span>
                  <span className={cn('rounded-full border px-2 py-0.5 font-black', DIFFICULTY_CLASSES[protocol.difficulty])}>
                    {DIFFICULTY_LABELS[protocol.difficulty]}
                  </span>
                </div>
              </button>
              <button
                type="button"
                aria-label={isFavorite ? `Retirer ${protocol.act_names[0]} des favoris` : `Ajouter ${protocol.act_names[0]} aux favoris`}
                onClick={() => toggleFavorite(protocol)}
                className={cn(
                  'absolute right-3 top-3 grid h-11 w-11 place-items-center rounded-full border',
                  isFavorite ? 'border-amber-400/30 bg-amber-400/10 text-amber-600' : 'border-glass-border bg-background text-text-muted',
                )}
              >
                <Star size={17} fill={isFavorite ? 'currentColor' : 'none'} />
              </button>
            </article>
          );
        })}

        {filtered.length === 0 && (
          <div className="rounded-[22px] border border-dashed border-glass-border bg-card px-5 py-8 text-center">
            <p className="text-[13px] font-black text-text-main">Aucun protocole</p>
            <p className="mt-1 text-[10px] font-bold text-text-muted">Modifie la recherche ou désactive le filtre Favoris.</p>
          </div>
        )}
      </div>
    </section>
  );
}
