import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  CheckCircle2,
  CircleOff,
  FolderPlus,
  Pencil,
  Plus,
  Stethoscope,
  X,
} from 'lucide-react';
import { useCatalogStore } from '../hooks/useCatalogStore';
import type { CatalogAct, Pathology, Specialty } from '../hooks/useCatalogStore';
import { cn } from '../../../../utils/cn';
import { SettingsReadError } from '../components/SharedUI';

type CatalogModal =
  | { kind: 'specialty'; mode: 'create'; specialty?: never }
  | { kind: 'specialty'; mode: 'edit'; specialty: Specialty }
  | { kind: 'act'; mode: 'create'; specialtyId: number; act?: never }
  | { kind: 'act'; mode: 'edit'; specialtyId: number; act: CatalogAct }
  | { kind: 'pathology'; mode: 'create'; specialtyId: number; pathology?: never }
  | { kind: 'pathology'; mode: 'edit'; specialtyId: number; pathology: Pathology };

const DEFAULT_SPECIALTY_COLOR = '#3B82F6';
const DEFAULT_ACT_COLOR = '#60A5FA';

const normalizeName = (value: string) => value.trim().replace(/\s+/g, ' ');

const StatusBadge: React.FC<{ active: boolean }> = ({ active }) => (
  <span
    className={cn(
      'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-wide',
      active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500',
    )}
  >
    {active ? <CheckCircle2 size={12} /> : <CircleOff size={12} />}
    {active ? 'Actif' : 'Inactif'}
  </span>
);

const FieldLabel: React.FC<React.PropsWithChildren> = ({ children }) => (
  <span className="text-xs font-black uppercase tracking-wider text-slate-500">{children}</span>
);

const CatalogFormModal: React.FC<{
  modal: CatalogModal;
  onClose: () => void;
}> = ({ modal, onClose }) => {
  const {
    createSpecialty,
    updateSpecialty,
    createAct,
    updateAct,
    createPathology,
    updatePathology,
  } = useCatalogStore();

  const editingSpecialty = modal.kind === 'specialty' && modal.mode === 'edit' ? modal.specialty : undefined;
  const editingAct = modal.kind === 'act' && modal.mode === 'edit' ? modal.act : undefined;
  const editingPathology = modal.kind === 'pathology' && modal.mode === 'edit' ? modal.pathology : undefined;

  const [name, setName] = useState(editingSpecialty?.name || editingAct?.name || editingPathology?.name || '');
  const [color, setColor] = useState(editingSpecialty?.color || editingAct?.color || (modal.kind === 'specialty' ? DEFAULT_SPECIALTY_COLOR : DEFAULT_ACT_COLOR));
  const [code, setCode] = useState(editingAct?.code || '');
  const [price, setPrice] = useState(editingAct ? String(editingAct.base_price) : '');
  const [description, setDescription] = useState(editingPathology?.description || '');
  const [isActive, setIsActive] = useState(editingAct?.is_active ?? editingPathology?.is_active ?? true);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !saving) onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose, saving]);

  const title = useMemo(() => {
    if (modal.kind === 'specialty') return modal.mode === 'create' ? 'Nouvelle spécialité' : 'Modifier la spécialité';
    if (modal.kind === 'act') return modal.mode === 'create' ? 'Nouvel acte' : "Modifier l'acte";
    return modal.mode === 'create' ? 'Nouvelle pathologie' : 'Modifier la pathologie';
  }, [modal]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setFormError(null);

    const cleanName = normalizeName(name);
    if (!cleanName) {
      setFormError('Le nom est obligatoire.');
      return;
    }

    setSaving(true);
    let ok = false;

    if (modal.kind === 'specialty') {
      const payload = { name: cleanName, color: color || DEFAULT_SPECIALTY_COLOR };
      ok = modal.mode === 'create'
        ? await createSpecialty(payload)
        : await updateSpecialty(modal.specialty.id, payload);
    }

    if (modal.kind === 'act') {
      const parsedPrice = Number(price.replace(',', '.'));
      if (!Number.isFinite(parsedPrice) || parsedPrice < 0) {
        setFormError('Le tarif doit être un nombre positif ou nul.');
        setSaving(false);
        return;
      }
      const payload = {
        name: cleanName,
        code: code.trim() || undefined,
        base_price: parsedPrice,
        color: color || DEFAULT_ACT_COLOR,
        is_active: isActive,
      };
      ok = modal.mode === 'create'
        ? await createAct(modal.specialtyId, payload)
        : await updateAct(modal.act.id, payload);
    }

    if (modal.kind === 'pathology') {
      const payload = {
        name: cleanName,
        description: description.trim() || undefined,
        is_active: isActive,
      };
      ok = modal.mode === 'create'
        ? await createPathology(modal.specialtyId, payload)
        : await updatePathology(modal.pathology.id, payload);
    }

    setSaving(false);
    if (ok) onClose();
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center bg-slate-950/40 p-0 backdrop-blur-sm sm:items-center sm:p-6"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !saving) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="catalog-modal-title"
        className="max-h-[92vh] w-full overflow-y-auto rounded-t-[2rem] bg-white p-6 shadow-2xl sm:max-w-xl sm:rounded-[2rem] sm:p-8"
      >
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">Catalogue du cabinet</p>
            <h3 id="catalog-modal-title" className="mt-1 text-2xl font-black tracking-tight text-slate-900">{title}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            aria-label="Fermer"
            className="rounded-xl border border-slate-200 p-2 text-slate-500 transition-colors hover:bg-slate-50 disabled:opacity-40"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={submit} className="space-y-5">
          <label className="block space-y-2">
            <FieldLabel>Nom *</FieldLabel>
            <input
              autoFocus
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={255}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-800 outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
              placeholder={modal.kind === 'act' ? 'Ex. Détartrage' : modal.kind === 'pathology' ? 'Ex. Gingivite' : 'Ex. Orthodontie'}
            />
          </label>

          {modal.kind === 'specialty' && (
            <label className="block space-y-2">
              <FieldLabel>Couleur</FieldLabel>
              <div className="flex items-center gap-3 rounded-2xl border border-slate-200 p-3">
                <input
                  type="color"
                  value={color}
                  onChange={(event) => setColor(event.target.value)}
                  className="h-10 w-14 cursor-pointer rounded-lg border-0 bg-transparent p-0"
                  aria-label="Couleur de la spécialité"
                />
                <span className="text-sm font-bold uppercase text-slate-500">{color}</span>
              </div>
            </label>
          )}

          {modal.kind === 'act' && (
            <>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <label className="block space-y-2">
                  <FieldLabel>Code</FieldLabel>
                  <input
                    value={code}
                    onChange={(event) => setCode(event.target.value)}
                    maxLength={50}
                    className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-800 outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
                    placeholder="Ex. DET"
                  />
                </label>
                <label className="block space-y-2">
                  <FieldLabel>Tarif de base (DHS) *</FieldLabel>
                  <input
                    inputMode="decimal"
                    value={price}
                    onChange={(event) => setPrice(event.target.value)}
                    className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-800 outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
                    placeholder="0"
                  />
                </label>
              </div>
              <label className="block space-y-2">
                <FieldLabel>Couleur</FieldLabel>
                <div className="flex items-center gap-3 rounded-2xl border border-slate-200 p-3">
                  <input
                    type="color"
                    value={color}
                    onChange={(event) => setColor(event.target.value)}
                    className="h-10 w-14 cursor-pointer rounded-lg border-0 bg-transparent p-0"
                    aria-label="Couleur de l'acte"
                  />
                  <span className="text-sm font-bold uppercase text-slate-500">{color}</span>
                </div>
              </label>
            </>
          )}

          {modal.kind === 'pathology' && (
            <label className="block space-y-2">
              <FieldLabel>Description</FieldLabel>
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={3}
                maxLength={1000}
                className="w-full resize-none rounded-2xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-800 outline-none transition focus:border-rose-400 focus:ring-4 focus:ring-rose-100"
                placeholder="Description facultative"
              />
            </label>
          )}

          {modal.kind !== 'specialty' && modal.mode === 'edit' && (
            <label className="flex cursor-pointer items-center justify-between gap-4 rounded-2xl border border-slate-200 p-4">
              <div>
                <p className="font-bold text-slate-800">Disponible dans le catalogue</p>
                <p className="mt-0.5 text-xs text-slate-500">Désactiver conserve l'historique sans supprimer la donnée.</p>
              </div>
              <input
                type="checkbox"
                checked={isActive}
                onChange={(event) => setIsActive(event.target.checked)}
                className="h-5 w-5 accent-slate-900"
                aria-label="Actif"
              />
            </label>
          )}

          {formError && (
            <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-bold text-rose-700">{formError}</p>
          )}

          <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-bold text-slate-600 transition hover:bg-slate-50 disabled:opacity-40"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={saving}
              className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-black text-white shadow-lg shadow-slate-900/15 transition hover:bg-black disabled:cursor-wait disabled:opacity-60"
            >
              {saving ? 'Enregistrement…' : modal.mode === 'create' ? 'Créer' : 'Enregistrer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export const CatalogTab: React.FC = () => {
  const { specialties, loading, readError, fetchCatalog } = useCatalogStore();
  const [activeSpecialtyId, setActiveSpecialtyId] = useState<number | null>(null);
  const [modal, setModal] = useState<CatalogModal | null>(null);

  useEffect(() => {
    void fetchCatalog();
  }, [fetchCatalog]);

  const activeSpecialty = specialties.find((specialty) => specialty.id === activeSpecialtyId) || specialties[0];

  useEffect(() => {
    if (activeSpecialty && activeSpecialtyId === null) setActiveSpecialtyId(activeSpecialty.id);
  }, [activeSpecialty, activeSpecialtyId]);

  if (loading && specialties.length === 0) {
    return <div className="p-8 text-center text-sm font-bold uppercase tracking-widest text-slate-500 animate-pulse">Chargement du catalogue...</div>;
  }

  if (readError) {
    return <SettingsReadError title="Catalogue indisponible" message={readError} onRetry={fetchCatalog} />;
  }

  return (
    <div className="space-y-7 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 className="text-3xl font-black tracking-tight text-slate-900">Catalogue des actes</h2>
          <p className="mt-1 max-w-2xl text-sm font-medium text-slate-500">Gérez les spécialités, tarifs et pathologies utilisés dans le cabinet.</p>
        </div>
        <button
          type="button"
          onClick={() => setModal({ kind: 'specialty', mode: 'create' })}
          className="inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-2xl bg-slate-900 px-5 py-3 font-bold text-white shadow-xl shadow-slate-900/15 transition hover:bg-black sm:w-auto"
        >
          <Plus size={18} /> Nouvelle spécialité
        </button>
      </div>

      <div className="flex flex-col gap-7 xl:flex-row">
        <aside className="flex w-full flex-col gap-3 xl:w-1/3" aria-label="Spécialités">
          {specialties.map((specialty) => {
            const selected = activeSpecialty?.id === specialty.id;
            const activeActs = specialty.acts.filter((act) => act.is_active).length;
            const inactiveActs = specialty.acts.length - activeActs;
            return (
              <div
                key={specialty.id}
                className={cn(
                  'flex items-stretch overflow-hidden rounded-[1.5rem] border transition-all duration-200',
                  selected
                    ? 'border-slate-900 bg-slate-900 text-white shadow-xl shadow-slate-900/15'
                    : 'border-slate-100 bg-white text-slate-700 hover:border-slate-300 hover:shadow-md',
                )}
              >
                <button
                  type="button"
                  onClick={() => setActiveSpecialtyId(specialty.id)}
                  className="flex min-w-0 flex-1 items-center gap-4 p-5 text-left"
                >
                  <span className={cn('shrink-0 rounded-2xl p-3', selected ? 'bg-white/10' : 'bg-slate-50')}>
                    <Stethoscope size={22} className={selected ? 'text-white' : 'text-slate-600'} />
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-[1.05rem] font-bold tracking-tight">{specialty.name}</span>
                    <span className={cn('mt-1 block text-xs font-semibold', selected ? 'text-slate-300' : 'text-slate-500')}>
                      {activeActs} actif{activeActs > 1 ? 's' : ''}
                      {inactiveActs > 0 ? ` · ${inactiveActs} inactif${inactiveActs > 1 ? 's' : ''}` : ''}
                      {' · '}{specialty.pathologies.length} pathol.
                    </span>
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setModal({ kind: 'specialty', mode: 'edit', specialty })}
                  aria-label={`Modifier ${specialty.name}`}
                  title="Modifier la spécialité"
                  className={cn(
                    'flex w-12 shrink-0 items-center justify-center border-l transition-colors',
                    selected ? 'border-white/10 text-slate-300 hover:bg-white/10 hover:text-white' : 'border-slate-100 text-slate-400 hover:bg-slate-50 hover:text-slate-700',
                  )}
                >
                  <Pencil size={16} />
                </button>
              </div>
            );
          })}

          {specialties.length === 0 && (
            <div className="rounded-[2rem] border-2 border-dashed border-slate-200 bg-slate-50/50 p-10 text-center text-slate-400">
              <p className="mb-2 text-lg font-bold text-slate-500">Aucune spécialité</p>
              <p className="text-sm">Ajoutez une spécialité pour construire le catalogue du cabinet.</p>
            </div>
          )}
        </aside>

        {activeSpecialty && (
          <div className="min-w-0 flex-1 space-y-6">
            <section className="relative overflow-hidden rounded-[2rem] border border-slate-100 bg-white p-5 shadow-xl shadow-slate-100/50 sm:p-8">
              <div className="pointer-events-none absolute right-0 top-0 h-64 w-64 -translate-y-1/2 translate-x-1/3 rounded-full bg-sky-500/5 blur-3xl" />
              <div className="relative mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-[0.16em] text-slate-400">{activeSpecialty.name}</p>
                  <h3 className="mt-1 flex items-center gap-3 text-xl font-black text-slate-900">
                    <span className="rounded-xl bg-sky-100 p-2 text-sky-600"><Activity size={20} /></span>
                    Actes cliniques
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setModal({ kind: 'act', mode: 'create', specialtyId: activeSpecialty.id })}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-sky-50 px-4 py-2.5 text-sm font-bold text-sky-700 transition-colors hover:bg-sky-100 sm:w-auto"
                >
                  <Plus size={16} /> Ajouter un acte
                </button>
              </div>

              <div className="relative grid grid-cols-1 gap-3 md:grid-cols-2">
                {activeSpecialty.acts.map((act) => (
                  <article
                    key={act.id}
                    className={cn(
                      'flex min-w-0 items-center justify-between gap-4 rounded-[1.25rem] border p-4 shadow-sm transition-colors sm:p-5',
                      act.is_active ? 'border-slate-100 bg-white hover:border-sky-200' : 'border-slate-200 bg-slate-50/80',
                    )}
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className={cn('font-bold', act.is_active ? 'text-slate-700' : 'text-slate-500')}>{act.name}</p>
                        <StatusBadge active={act.is_active} />
                      </div>
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        {act.code && <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] font-bold text-slate-400">{act.code}</span>}
                        <span className="text-sm font-black text-sky-700">{act.base_price} DHS</span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setModal({ kind: 'act', mode: 'edit', specialtyId: activeSpecialty.id, act })}
                      aria-label={`Modifier l'acte ${act.name}`}
                      title="Modifier l'acte"
                      className="shrink-0 rounded-xl border border-slate-200 p-2.5 text-slate-500 transition hover:border-sky-200 hover:bg-sky-50 hover:text-sky-700"
                    >
                      <Pencil size={15} />
                    </button>
                  </article>
                ))}
                {activeSpecialty.acts.length === 0 && (
                  <div className="col-span-full py-8 text-center text-sm font-medium text-slate-400">Aucun acte dans cette spécialité</div>
                )}
              </div>
            </section>

            <section className="relative overflow-hidden rounded-[2rem] border border-slate-100 bg-white p-5 shadow-xl shadow-slate-100/50 sm:p-8">
              <div className="pointer-events-none absolute right-0 top-0 h-64 w-64 -translate-y-1/2 translate-x-1/3 rounded-full bg-rose-500/5 blur-3xl" />
              <div className="relative mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <h3 className="flex items-center gap-3 text-xl font-black text-slate-900">
                  <span className="rounded-xl bg-rose-100 p-2 text-rose-600"><FolderPlus size={20} /></span>
                  Pathologies
                </h3>
                <button
                  type="button"
                  onClick={() => setModal({ kind: 'pathology', mode: 'create', specialtyId: activeSpecialty.id })}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-rose-50 px-4 py-2.5 text-sm font-bold text-rose-700 transition-colors hover:bg-rose-100 sm:w-auto"
                >
                  <Plus size={16} /> Ajouter une pathologie
                </button>
              </div>

              <div className="relative grid grid-cols-1 gap-3 sm:grid-cols-2">
                {activeSpecialty.pathologies.map((pathology) => (
                  <article
                    key={pathology.id}
                    className={cn(
                      'flex min-w-0 items-center justify-between gap-3 rounded-xl border px-4 py-3 shadow-sm',
                      pathology.is_active ? 'border-slate-200 bg-white' : 'border-slate-200 bg-slate-50/80',
                    )}
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className={cn('text-sm font-bold', pathology.is_active ? 'text-slate-700' : 'text-slate-500')}>{pathology.name}</p>
                        <StatusBadge active={pathology.is_active} />
                      </div>
                      {pathology.description && <p className="mt-1 line-clamp-2 text-xs text-slate-400">{pathology.description}</p>}
                    </div>
                    <button
                      type="button"
                      onClick={() => setModal({ kind: 'pathology', mode: 'edit', specialtyId: activeSpecialty.id, pathology })}
                      aria-label={`Modifier la pathologie ${pathology.name}`}
                      title="Modifier la pathologie"
                      className="shrink-0 rounded-lg p-2 text-slate-400 transition hover:bg-rose-50 hover:text-rose-700"
                    >
                      <Pencil size={14} />
                    </button>
                  </article>
                ))}
                {activeSpecialty.pathologies.length === 0 && (
                  <div className="col-span-full py-8 text-center text-sm font-medium text-slate-400">Aucune pathologie dans cette spécialité</div>
                )}
              </div>
            </section>
          </div>
        )}
      </div>

      {modal && <CatalogFormModal modal={modal} onClose={() => setModal(null)} />}
    </div>
  );
};
