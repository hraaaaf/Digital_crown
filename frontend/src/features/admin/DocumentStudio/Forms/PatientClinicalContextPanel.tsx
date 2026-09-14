import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, Loader2, Save, ShieldAlert, Weight } from 'lucide-react';

import { api } from '../../../../services/api';


type AllergyStatus = 'UNKNOWN' | 'NONE_KNOWN' | 'PRESENT';
type OrganStatus = 'UNKNOWN' | 'NO_KNOWN_IMPAIRMENT' | 'IMPAIRMENT_REPORTED';

type PatientClinicalContext = {
  patient_id?: number;
  employer_id?: number;
  weight_kg: number | null;
  medication_allergy_status: AllergyStatus;
  medication_allergies: string[] | null;
  renal_context_status: OrganStatus;
  renal_context_note: string | null;
  hepatic_context_status: OrganStatus;
  hepatic_context_note: string | null;
  prescription_indication: string | null;
  updated_at?: string | null;
  updated_by_user_id?: number | null;
};

const EMPTY_CONTEXT: PatientClinicalContext = {
  weight_kg: null,
  medication_allergy_status: 'UNKNOWN',
  medication_allergies: null,
  renal_context_status: 'UNKNOWN',
  renal_context_note: null,
  hepatic_context_status: 'UNKNOWN',
  hepatic_context_note: null,
  prescription_indication: null,
};

const fieldClass = 'min-h-[44px] w-full rounded-xl border border-border-main bg-background px-3 py-2 text-sm font-semibold text-text-main outline-none transition focus:border-accent/60 focus:ring-2 focus:ring-accent/10';
const labelClass = 'mb-1.5 block text-[10px] font-black uppercase tracking-[0.13em] text-text-muted';

export function PatientClinicalContextPanel({ patientId }: { patientId?: number }) {
  const [context, setContext] = useState<PatientClinicalContext>(EMPTY_CONTEXT);
  const [allergyText, setAllergyText] = useState('');
  const [loading, setLoading] = useState(Boolean(patientId));
  const [loadError, setLoadError] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveState, setSaveState] = useState<'idle' | 'saved' | 'error'>('idle');

  useEffect(() => {
    let cancelled = false;
    if (!patientId) {
      setContext(EMPTY_CONTEXT);
      setAllergyText('');
      setLoading(false);
      setLoadError(false);
      return;
    }

    setLoading(true);
    setLoadError(false);
    setSaveState('idle');
    api.get(`/patients/${patientId}/clinical-context`)
      .then(response => {
        if (cancelled) return;
        const next = { ...EMPTY_CONTEXT, ...response.data } as PatientClinicalContext;
        setContext(next);
        setAllergyText((next.medication_allergies || []).join(', '));
      })
      .catch(error => {
        if (cancelled) return;
        console.error('Clinical context load failed:', error);
        setContext(EMPTY_CONTEXT);
        setAllergyText('');
        setLoadError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [patientId]);

  const update = <K extends keyof PatientClinicalContext>(field: K, value: PatientClinicalContext[K]) => {
    setContext(previous => ({ ...previous, [field]: value }));
    setSaveState('idle');
  };

  const handleAllergyStatus = (value: AllergyStatus) => {
    update('medication_allergy_status', value);
    if (value !== 'PRESENT') setAllergyText('');
  };

  const handleOrganStatus = (
    field: 'renal_context_status' | 'hepatic_context_status',
    noteField: 'renal_context_note' | 'hepatic_context_note',
    value: OrganStatus,
  ) => {
    setContext(previous => ({
      ...previous,
      [field]: value,
      [noteField]: value === 'IMPAIRMENT_REPORTED' ? previous[noteField] : null,
    }));
    setSaveState('idle');
  };

  const save = async () => {
    if (!patientId || saving) return;
    setSaving(true);
    setSaveState('idle');
    const allergies = context.medication_allergy_status === 'PRESENT'
      ? allergyText.split(',').map(item => item.trim()).filter(Boolean)
      : context.medication_allergy_status === 'NONE_KNOWN' ? [] : null;

    const payload = {
      weight_kg: context.weight_kg,
      medication_allergy_status: context.medication_allergy_status,
      medication_allergies: allergies,
      renal_context_status: context.renal_context_status,
      renal_context_note: context.renal_context_status === 'IMPAIRMENT_REPORTED' ? context.renal_context_note : null,
      hepatic_context_status: context.hepatic_context_status,
      hepatic_context_note: context.hepatic_context_status === 'IMPAIRMENT_REPORTED' ? context.hepatic_context_note : null,
      prescription_indication: context.prescription_indication,
    };

    try {
      const response = await api.put(`/patients/${patientId}/clinical-context`, payload);
      const saved = { ...EMPTY_CONTEXT, ...response.data } as PatientClinicalContext;
      setContext(saved);
      setAllergyText((saved.medication_allergies || []).join(', '));
      setSaveState('saved');
      setLoadError(false);
    } catch (error) {
      console.error('Clinical context save failed:', error);
      setSaveState('error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section
      data-patient-clinical-context="c1"
      className="rounded-2xl border border-border-main bg-glass-bg/70 px-3.5 py-3 shadow-sm backdrop-blur-xl sm:px-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.14em] text-text-muted">
            <ShieldAlert size={13} /> Contexte clinique structuré
          </div>
          <p className="mt-1 text-[11px] font-semibold leading-relaxed text-text-muted">
            Données factuelles saisies par le praticien. Aucun calcul de dose n’est activé par ces champs.
          </p>
        </div>
        {loading && <Loader2 aria-label="Chargement du contexte clinique" size={17} className="shrink-0 animate-spin text-text-muted" />}
      </div>

      {!patientId ? (
        <div className="mt-3 rounded-xl border border-amber-500/25 bg-amber-500/5 px-3 py-2 text-xs font-bold text-amber-700 dark:text-amber-300">
          Contexte indisponible : aucun patient sélectionné.
        </div>
      ) : loadError ? (
        <div className="mt-3 flex items-center gap-2 rounded-xl border border-amber-500/25 bg-amber-500/5 px-3 py-2 text-xs font-bold text-amber-700 dark:text-amber-300">
          <AlertTriangle size={14} /> Contexte non chargé. Aucune valeur n’est supposée.
        </div>
      ) : (
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <label>
            <span className={labelClass}>Poids explicite (kg)</span>
            <div className="relative">
              <Weight size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
              <input
                aria-label="Poids explicite en kilogrammes"
                type="number"
                step="any"
                inputMode="decimal"
                className={`${fieldClass} pl-9`}
                value={context.weight_kg ?? ''}
                onChange={event => update('weight_kg', event.target.value === '' ? null : Number(event.target.value))}
                placeholder="Non renseigné"
              />
            </div>
          </label>

          <label>
            <span className={labelClass}>Allergies médicamenteuses</span>
            <select
              aria-label="Statut des allergies médicamenteuses"
              className={fieldClass}
              value={context.medication_allergy_status}
              onChange={event => handleAllergyStatus(event.target.value as AllergyStatus)}
            >
              <option value="UNKNOWN">Inconnu / non vérifié</option>
              <option value="NONE_KNOWN">Aucune connue déclarée</option>
              <option value="PRESENT">Allergie(s) rapportée(s)</option>
            </select>
          </label>

          {context.medication_allergy_status === 'PRESENT' && (
            <label className="md:col-span-2">
              <span className={labelClass}>Allergies rapportées, séparées par des virgules</span>
              <input
                aria-label="Allergies médicamenteuses rapportées"
                className={fieldClass}
                value={allergyText}
                onChange={event => { setAllergyText(event.target.value); setSaveState('idle'); }}
                placeholder="Ex. substance ou médicament rapporté par le patient"
              />
            </label>
          )}

          <label>
            <span className={labelClass}>Contexte rénal</span>
            <select
              aria-label="Statut du contexte rénal"
              className={fieldClass}
              value={context.renal_context_status}
              onChange={event => handleOrganStatus('renal_context_status', 'renal_context_note', event.target.value as OrganStatus)}
            >
              <option value="UNKNOWN">Inconnu / non vérifié</option>
              <option value="NO_KNOWN_IMPAIRMENT">Aucune atteinte connue déclarée</option>
              <option value="IMPAIRMENT_REPORTED">Atteinte rapportée</option>
            </select>
          </label>

          <label>
            <span className={labelClass}>Contexte hépatique</span>
            <select
              aria-label="Statut du contexte hépatique"
              className={fieldClass}
              value={context.hepatic_context_status}
              onChange={event => handleOrganStatus('hepatic_context_status', 'hepatic_context_note', event.target.value as OrganStatus)}
            >
              <option value="UNKNOWN">Inconnu / non vérifié</option>
              <option value="NO_KNOWN_IMPAIRMENT">Aucune atteinte connue déclarée</option>
              <option value="IMPAIRMENT_REPORTED">Atteinte rapportée</option>
            </select>
          </label>

          {context.renal_context_status === 'IMPAIRMENT_REPORTED' && (
            <label>
              <span className={labelClass}>Note rénale factuelle</span>
              <input
                aria-label="Note rénale factuelle"
                className={fieldClass}
                value={context.renal_context_note ?? ''}
                onChange={event => update('renal_context_note', event.target.value || null)}
                placeholder="Information rapportée / documentée"
              />
            </label>
          )}

          {context.hepatic_context_status === 'IMPAIRMENT_REPORTED' && (
            <label>
              <span className={labelClass}>Note hépatique factuelle</span>
              <input
                aria-label="Note hépatique factuelle"
                className={fieldClass}
                value={context.hepatic_context_note ?? ''}
                onChange={event => update('hepatic_context_note', event.target.value || null)}
                placeholder="Information rapportée / documentée"
              />
            </label>
          )}

          <label className="md:col-span-2">
            <span className={labelClass}>Indication de cette prescription</span>
            <textarea
              aria-label="Indication de la prescription"
              className={`${fieldClass} min-h-[64px] resize-y`}
              value={context.prescription_indication ?? ''}
              onChange={event => update('prescription_indication', event.target.value || null)}
              placeholder="À saisir explicitement pour cette décision de prescription"
            />
          </label>
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <div className="min-h-5 text-[11px] font-bold">
          {saveState === 'saved' && <span className="flex items-center gap-1 text-emerald-600"><CheckCircle2 size={13} /> Contexte enregistré</span>}
          {saveState === 'error' && <span className="flex items-center gap-1 text-rose-600"><AlertTriangle size={13} /> Enregistrement impossible</span>}
        </div>
        <button
          type="button"
          onClick={save}
          disabled={!patientId || loading || loadError || saving}
          className="inline-flex min-h-[44px] items-center gap-2 rounded-xl border border-border-main bg-background px-3.5 text-xs font-black text-text-main transition hover:border-accent/40 disabled:cursor-not-allowed disabled:opacity-45"
        >
          {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
          Enregistrer le contexte
        </button>
      </div>
    </section>
  );
}
