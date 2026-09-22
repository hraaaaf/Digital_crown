import React from 'react';
import { BookmarkPlus, FileText, Trash2, X } from 'lucide-react';

import { api } from '../../../../services/api';
import type { DrugItem } from './prescriptionTypes';

type PresetSummary = {
  id: number;
  act_context: string;
  drugs: Array<Partial<DrugItem>>;
};

interface PrescriptionPresetBarProps {
  drugs: DrugItem[];
  setDrugs: (drugs: DrugItem[]) => void;
}

const comparableDrug = (drug: Partial<DrugItem>) => ({
  name: String(drug.name || '').trim(),
  dosage: String(drug.dosage || '').trim(),
  forme: String(drug.forme || '').trim(),
  posologie: String(drug.posologie || '').trim(),
  type: drug.type || 'MEDICAMENT',
  quantite: drug.quantite ?? null,
  non_substituable: Boolean(drug.non_substituable),
});

const sameDraft = (current: DrugItem[], incoming: Array<Partial<DrugItem>>): boolean =>
  JSON.stringify(current.map(comparableDrug)) === JSON.stringify(incoming.map(comparableDrug));

const hydratePresetDrugs = (
  incoming: Array<Partial<DrugItem>>,
  current: DrugItem[],
): DrugItem[] => {
  const maxId = current.reduce((max, drug) => Math.max(max, Number(drug.id) || 0), 0);
  return incoming.map((drug, index) => ({
    id: maxId + index + 1,
    name: String(drug.name || ''),
    dosage: String(drug.dosage || ''),
    forme: String(drug.forme || ''),
    posologie: String(drug.posologie || ''),
    type: drug.type === 'EXAMEN' ? 'EXAMEN' : 'MEDICAMENT',
    quantite: drug.quantite ?? undefined,
    non_substituable: Boolean(drug.non_substituable),
  })) as DrugItem[];
};

export const PrescriptionPresetBar: React.FC<PrescriptionPresetBarProps> = ({
  drugs,
  setDrugs,
}) => {
  const [presets, setPresets] = React.useState<PresetSummary[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [showSave, setShowSave] = React.useState(false);
  const [presetName, setPresetName] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const [pendingApply, setPendingApply] = React.useState<PresetSummary | null>(null);
  const [deletingId, setDeletingId] = React.useState<number | null>(null);

  const loadPresets = React.useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/prescriptions/habits/presets');
      setPresets(Array.isArray(response?.data) ? response.data : []);
    } catch {
      setPresets([]);
      setError('Impossible de charger les presets du praticien.');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    let active = true;
    void (async () => {
      setLoading(true);
      try {
        const response = await api.get('/prescriptions/habits/presets');
        if (active) setPresets(Array.isArray(response?.data) ? response.data : []);
      } catch {
        if (active) {
          setPresets([]);
          setError('Impossible de charger les presets du praticien.');
        }
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const applyPreset = (preset: PresetSummary) => {
    const incoming = Array.isArray(preset.drugs) ? preset.drugs : [];
    if (!incoming.length) {
      setError('Ce preset ne contient aucune ligne réutilisable.');
      return;
    }
    if (drugs.some(drug => drug.name.trim()) && !sameDraft(drugs, incoming)) {
      setPendingApply(preset);
      return;
    }
    setDrugs(hydratePresetDrugs(incoming, drugs));
  };

  const savePreset = async () => {
    const name = presetName.trim();
    const reusableDrugs = drugs.filter(drug => drug.name.trim());
    if (!name || !reusableDrugs.length || saving) return;

    setSaving(true);
    setError('');
    try {
      await api.post('/prescriptions/preferences', {
        act_code: name,
        drugs: reusableDrugs.map(comparableDrug),
      });
      setShowSave(false);
      setPresetName('');
      await loadPresets();
    } catch (requestError: any) {
      setError(
        requestError?.response?.data?.detail
        || 'Impossible d’enregistrer ce preset.',
      );
    } finally {
      setSaving(false);
    }
  };

  const deletePreset = async (preset: PresetSummary) => {
    if (deletingId !== null) return;
    setDeletingId(preset.id);
    setError('');
    try {
      await api.delete(`/prescriptions/preferences/${encodeURIComponent(preset.act_context)}`);
      setPresets(current => current.filter(item => item.id !== preset.id));
    } catch (requestError: any) {
      setError(
        requestError?.response?.data?.detail
        || 'Impossible de supprimer ce preset.',
      );
    } finally {
      setDeletingId(null);
    }
  };

  const hasReusableDraft = drugs.some(drug => drug.name.trim());

  return (
    <section
      data-cust04-presets
      className="rounded-2xl border border-border-main bg-glass-bg/70 p-3 shadow-sm backdrop-blur-xl sm:p-4"
      aria-label="Presets personnels d’ordonnance"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[9px] font-black uppercase tracking-[0.18em] text-text-muted">
            Mes presets
          </div>
          <p className="mt-1 max-w-2xl text-[10px] font-semibold leading-relaxed text-text-muted">
            Un preset remplit uniquement les lignes de prescription après votre clic. Il reste entièrement éditable.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setPresetName('');
            setError('');
            setShowSave(true);
          }}
          disabled={!hasReusableDraft}
          className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-primary/20 bg-card px-3 py-2 text-[10px] font-black uppercase tracking-wider text-primary transition hover:bg-primary/5 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <BookmarkPlus size={14} /> Enregistrer ce brouillon
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {loading ? (
          <span className="text-[10px] font-bold text-text-muted">Chargement des presets…</span>
        ) : presets.length ? (
          presets.map(preset => (
            <div
              key={preset.id}
              className="inline-flex min-h-10 max-w-full items-stretch overflow-hidden rounded-xl border border-border-main bg-card"
            >
              <button
                type="button"
                onClick={() => applyPreset(preset)}
                className="inline-flex min-w-0 items-center gap-2 px-3 py-2 text-left text-[11px] font-bold text-text-main transition hover:bg-primary/5 hover:text-primary"
              >
                <FileText size={14} className="shrink-0" />
                <span className="truncate">{preset.act_context}</span>
              </button>
              <button
                type="button"
                aria-label={`Supprimer le preset ${preset.act_context}`}
                disabled={deletingId !== null}
                onClick={() => void deletePreset(preset)}
                className="inline-flex w-10 shrink-0 items-center justify-center border-l border-border-main text-text-muted transition hover:bg-red-50 hover:text-red-600 disabled:opacity-40"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))
        ) : (
          <span className="text-[10px] font-bold text-text-muted">Aucun preset personnel enregistré.</span>
        )}
      </div>

      {error && (
        <p role="alert" className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-[10px] font-bold text-rose-700">
          {error}
        </p>
      )}

      {pendingApply && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="cust04-replace-title"
          className="fixed inset-0 z-[140] flex items-center justify-center bg-slate-950/40 p-4"
        >
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Ordonnance</p>
            <h3 id="cust04-replace-title" className="mt-1 text-lg font-black text-slate-900">
              Remplacer les lignes actuelles ?
            </h3>
            <p className="mt-3 text-sm font-medium leading-relaxed text-slate-600">
              Le preset « {pendingApply.act_context} » remplacera uniquement les lignes de prescription. Le patient, la date et l’indication restent inchangés.
            </p>
            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <button
                type="button"
                onClick={() => setPendingApply(null)}
                className="min-h-10 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600"
              >
                Conserver mon brouillon
              </button>
              <button
                type="button"
                onClick={() => {
                  setDrugs(hydratePresetDrugs(pendingApply.drugs || [], drugs));
                  setPendingApply(null);
                }}
                className="min-h-10 rounded-xl bg-primary px-4 py-2 text-sm font-black text-white"
              >
                Remplacer par le preset
              </button>
            </div>
          </div>
        </div>
      )}

      {showSave && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="cust04-save-title"
          className="fixed inset-0 z-[140] flex items-center justify-center bg-slate-950/40 p-4"
        >
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Ordonnance</p>
                <h3 id="cust04-save-title" className="mt-1 text-lg font-black text-slate-900">
                  Enregistrer un preset
                </h3>
              </div>
              <button
                type="button"
                aria-label="Fermer"
                onClick={() => setShowSave(false)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-50"
              >
                <X size={16} />
              </button>
            </div>

            <label className="mt-5 block space-y-1.5">
              <span className="text-xs font-bold text-slate-600">Nom du preset *</span>
              <input
                value={presetName}
                onChange={event => setPresetName(event.target.value)}
                maxLength={100}
                placeholder="Ex. Post-op personnel"
                className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold outline-none focus:border-primary focus:ring-2 focus:ring-primary/10"
              />
            </label>

            <p className="mt-3 text-[10px] font-semibold leading-relaxed text-slate-500">
              {drugs.filter(drug => drug.name.trim()).length} ligne(s) seront enregistrées. Aucune donnée patient, date ou indication n’est incluse.
            </p>

            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowSave(false)}
                className="min-h-10 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600"
              >
                Annuler
              </button>
              <button
                type="button"
                onClick={() => void savePreset()}
                disabled={!presetName.trim() || !hasReusableDraft || saving}
                className="min-h-10 rounded-xl bg-primary px-4 py-2 text-sm font-black text-white disabled:opacity-40"
              >
                {saving ? 'Enregistrement…' : 'Enregistrer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
