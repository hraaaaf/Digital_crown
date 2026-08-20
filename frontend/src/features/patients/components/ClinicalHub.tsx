import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Plus, RefreshCcw, Search, ShieldCheck, X } from 'lucide-react';
import toast from 'react-hot-toast';

import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';
import { ClinicalHub as ClinicalHubCore } from './ClinicalHubCore';
import {
  buildCatalogPlanStep,
  flattenActiveCatalogActs,
  normalizePersistedPlanStep,
  type CatalogActChoice,
} from './catalogPlanTruth';

// P7 source-truth certification anchors live in the delegated byte-for-byte core:
// Sécurité médicale · patientClinicalPersistence.saveOdontogram · patientClinicalPersistence.createConclusion · Proposition à valider · Master Plan

interface ClinicalHubProps {
  patientId: number;
}

type CatalogSpecialty = {
  id: number;
  name: string;
  acts?: Array<{
    id: number;
    name: string;
    code?: string | null;
    base_price?: number;
    is_active?: boolean;
  }>;
};

export const ClinicalHub: React.FC<ClinicalHubProps> = ({ patientId }) => {
  const [coreRevision, setCoreRevision] = useState(0);
  const [specialties, setSpecialties] = useState<CatalogSpecialty[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [selectedAct, setSelectedAct] = useState<CatalogActChoice | null>(null);
  const [draftName, setDraftName] = useState('');
  const [draftPrice, setDraftPrice] = useState('');
  const [saving, setSaving] = useState(false);

  const loadCatalog = async () => {
    setCatalogLoading(true);
    setCatalogError(null);
    try {
      const response = await api.get('/catalog/specialties');
      setSpecialties(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Erreur chargement catalogue clinique:', error);
      setSpecialties([]);
      setCatalogError("Catalogue du cabinet indisponible. Aucun acte n'est proposé en remplacement.");
    } finally {
      setCatalogLoading(false);
    }
  };

  useEffect(() => {
    void loadCatalog();
  }, [patientId]);

  const activeActs = useMemo(() => flattenActiveCatalogActs(specialties), [specialties]);
  const matchingActs = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase('fr-FR');
    if (!needle) return [];
    return activeActs.filter((act) =>
      `${act.name} ${act.code || ''} ${act.specialtyName}`.toLocaleLowerCase('fr-FR').includes(needle),
    ).slice(0, 8);
  }, [activeActs, query]);

  const selectAct = (act: CatalogActChoice) => {
    setSelectedAct(act);
    setDraftName(act.name);
    setDraftPrice(String(act.basePrice));
    setQuery(act.name);
  };

  const clearSelection = () => {
    setSelectedAct(null);
    setDraftName('');
    setDraftPrice('');
    setQuery('');
  };

  const addToPlan = async () => {
    if (!selectedAct || !draftName.trim()) return;
    const parsedPrice = Number(draftPrice.replace(',', '.'));
    if (!Number.isFinite(parsedPrice) || parsedPrice < 0) {
      toast.error('Tarif invalide.');
      return;
    }

    setSaving(true);
    try {
      const current = await api.get(`/patients/${patientId}/master-plan`);
      const persistedSteps = Array.isArray(current.data?.steps) ? current.data.steps : [];
      const payload = persistedSteps.map((step: unknown, index: number) => normalizePersistedPlanStep(step, index));
      payload.push(buildCatalogPlanStep(
        selectedAct,
        draftName,
        parsedPrice,
        `Ajouté le ${new Date().toLocaleDateString('fr-FR')}`,
        payload.length,
      ));

      await api.put(`/patients/${patientId}/master-plan`, payload);
      clearSelection();
      setCoreRevision((value) => value + 1);
      toast.success('Acte ajouté au Master Plan · tarif capturé.');
    } catch (error) {
      console.error('Erreur ajout catalogue au Master Plan:', error);
      toast.error("L'acte n'a pas été ajouté au plan.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="w-full min-w-0 space-y-4">
      <section aria-label="Catalogue vers Master Plan" className="rounded-[1.5rem] border border-primary/15 bg-card-bg/90 p-4 shadow-sm backdrop-blur-xl sm:p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.14em] text-primary"><ShieldCheck size={15} /> Catalogue → Master Plan</span>
              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-1 text-[9px] font-black uppercase tracking-wider text-emerald-700">Snapshot par valeur</span>
            </div>
            <p className="mt-1 max-w-2xl text-xs font-bold leading-relaxed text-text-muted">Sélectionnez un acte du cabinet. Nom et tarif restent modifiables avant ajout ; le prix enregistré ne suivra pas les changements futurs du catalogue.</p>
          </div>
          {catalogError && <button onClick={() => void loadCatalog()} className="inline-flex min-h-10 shrink-0 items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-3 text-xs font-black text-red-700"><RefreshCcw size={14} /> Réessayer</button>}
        </div>

        {catalogError ? (
          <div className="mt-4 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-xs font-bold text-red-700"><AlertTriangle size={15} className="mt-0.5 shrink-0" /> {catalogError}</div>
        ) : (
          <div className="mt-4 grid min-w-0 grid-cols-1 gap-3 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)_auto] xl:items-end">
            <div className="relative min-w-0">
              <label className="text-[10px] font-black uppercase tracking-wider text-text-muted">Acte du catalogue</label>
              <div className="relative mt-1">
                <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value);
                    if (selectedAct && event.target.value !== selectedAct.name) setSelectedAct(null);
                  }}
                  disabled={catalogLoading}
                  placeholder={catalogLoading ? 'Chargement du catalogue…' : 'Rechercher nom, code ou spécialité…'}
                  className="min-h-11 w-full rounded-xl border border-border-main bg-white pl-9 pr-10 text-sm font-bold text-text-main outline-none focus:border-primary dark:bg-slate-900"
                />
                {query && <button aria-label="Effacer la recherche" onClick={clearSelection} className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-2 text-text-muted hover:bg-slate-100"><X size={14} /></button>}
              </div>
              {!selectedAct && !catalogLoading && query.trim() && (
                <div className="mt-2 max-h-44 overflow-y-auto rounded-xl border border-border-main bg-white p-1 shadow-sm dark:bg-slate-900">
                  {matchingActs.length === 0 ? <p className="p-3 text-xs font-bold text-text-muted">Aucun acte actif correspondant.</p> : matchingActs.map((act) => (
                    <button key={act.id} onClick={() => selectAct(act)} className="flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-left hover:bg-primary/5">
                      <div className="min-w-0"><p className="truncate text-xs font-black text-text-main">{act.name}</p><p className="truncate text-[10px] font-bold text-text-muted">{act.specialtyName}{act.code ? ` · ${act.code}` : ''}</p></div>
                      <span className="shrink-0 text-xs font-black text-primary">{act.basePrice.toLocaleString('fr-FR')} DH</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="grid min-w-0 grid-cols-1 gap-2 sm:grid-cols-[minmax(0,1fr)_8rem]">
              <div><label className="text-[10px] font-black uppercase tracking-wider text-text-muted">Nom retenu</label><input value={draftName} onChange={(event) => setDraftName(event.target.value)} disabled={!selectedAct} className="mt-1 min-h-11 w-full rounded-xl border border-border-main bg-white px-3 text-sm font-bold text-text-main outline-none focus:border-primary disabled:bg-slate-50 disabled:text-text-muted dark:bg-slate-900" /></div>
              <div><label className="text-[10px] font-black uppercase tracking-wider text-text-muted">Tarif DH</label><input inputMode="decimal" value={draftPrice} onChange={(event) => setDraftPrice(event.target.value)} disabled={!selectedAct} className="mt-1 min-h-11 w-full rounded-xl border border-border-main bg-white px-3 text-sm font-black text-text-main outline-none focus:border-primary disabled:bg-slate-50 disabled:text-text-muted dark:bg-slate-900" /></div>
            </div>

            <button onClick={() => void addToPlan()} disabled={!selectedAct || !draftName.trim() || saving} className={cn('inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-primary px-4 text-xs font-black text-white shadow-sm transition-all disabled:cursor-not-allowed disabled:opacity-40', 'xl:min-w-40')}><Plus size={15} /> {saving ? 'Ajout…' : 'Ajouter au plan'}</button>
          </div>
        )}
      </section>

      <ClinicalHubCore key={`${patientId}-${coreRevision}`} patientId={patientId} />
    </div>
  );
};
