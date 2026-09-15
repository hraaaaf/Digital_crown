import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronUp, Loader2, Save, ShieldAlert, Weight } from 'lucide-react';

import { api } from '../../../../services/api';


type AllergyStatus = 'UNKNOWN' | 'NONE_KNOWN' | 'PRESENT';
type OrganStatus = 'UNKNOWN' | 'NO_KNOWN_IMPAIRMENT' | 'IMPAIRMENT_REPORTED';
type IECardiacRiskCategory =
  | 'UNKNOWN'
  | 'NONE_REPORTED'
  | 'OTHER_CARDIAC_CONDITION'
  | 'PROSTHETIC_CARDIAC_VALVE'
  | 'PROSTHETIC_MATERIAL_FOR_CARDIAC_VALVE_REPAIR'
  | 'PREVIOUS_INFECTIVE_ENDOCARDITIS'
  | 'UNREPAIRED_CYANOTIC_CONGENITAL_HEART_DISEASE'
  | 'REPAIRED_CHD_WITH_RESIDUAL_SHUNT_OR_VALVULAR_REGURGITATION_AT_PROSTHETIC_PATCH_OR_DEVICE'
  | 'CARDIAC_TRANSPLANT_WITH_VALVE_REGURGITATION_DUE_STRUCTURALLY_ABNORMAL_VALVE';

type PatientClinicalContext = {
  patient_id?: number;
  employer_id?: number;
  weight_kg: number | null;
  medication_allergy_status: AllergyStatus;
  medication_allergies: string[] | null;
  penicillin_allergy_status: AllergyStatus;
  ie_cardiac_risk_category: IECardiacRiskCategory;
  renal_context_status: OrganStatus;
  renal_context_note: string | null;
  hepatic_context_status: OrganStatus;
  hepatic_context_note: string | null;
  updated_at?: string | null;
  updated_by_user_id?: number | null;
};

const EMPTY_CONTEXT: PatientClinicalContext = {
  weight_kg: null,
  medication_allergy_status: 'UNKNOWN',
  medication_allergies: null,
  penicillin_allergy_status: 'UNKNOWN',
  ie_cardiac_risk_category: 'UNKNOWN',
  renal_context_status: 'UNKNOWN',
  renal_context_note: null,
  hepatic_context_status: 'UNKNOWN',
  hepatic_context_note: null,
};

const fieldClass = 'min-h-[44px] w-full rounded-xl border border-border-main bg-background px-3 py-2 text-sm font-semibold text-text-main outline-none transition focus:border-accent/60 focus:ring-2 focus:ring-accent/10';
const labelClass = 'mb-1.5 block text-[10px] font-black uppercase tracking-[0.13em] text-text-muted';

function allergySummary(context: PatientClinicalContext): string {
  if (context.medication_allergy_status === 'NONE_KNOWN') return 'aucune connue déclarée';
  if (context.medication_allergy_status === 'PRESENT') {
    const count = context.medication_allergies?.length || 0;
    return `${count} rapportée${count > 1 ? 's' : ''}`;
  }
  return 'inconnues';
}

function penicillinSummary(status: AllergyStatus): string {
  if (status === 'NONE_KNOWN') return 'aucune connue';
  if (status === 'PRESENT') return 'rapportée';
  return 'non vérifiée';
}

function cardiacSummary(category: IECardiacRiskCategory): string {
  if (category === 'UNKNOWN') return 'non vérifié';
  if (category === 'NONE_REPORTED') return 'aucun haut risque déclaré';
  if (category === 'OTHER_CARDIAC_CONDITION') return 'autre cardiopathie';
  return 'haut risque déclaré';
}

function organSummary(status: OrganStatus): string {
  if (status === 'NO_KNOWN_IMPAIRMENT') return 'aucune atteinte connue';
  if (status === 'IMPAIRMENT_REPORTED') return 'atteinte rapportée';
  return 'inconnu';
}

export function PatientClinicalContextPanel({ patientId }: { patientId?: number }) {
  const [context, setContext] = useState<PatientClinicalContext>(EMPTY_CONTEXT);
  const [allergyText, setAllergyText] = useState('');
  const [loading, setLoading] = useState(Boolean(patientId));
  const [loadError, setLoadError] = useState(false);
  const [saving, setSaving] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [saveState, setSaveState] = useState<'idle' | 'saved' | 'error'>('idle');

  useEffect(() => {
    let cancelled = false;
    setExpanded(false);
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
    if (!patientId || loading || loadError || saving) return;
    setSaving(true);
    setSaveState('idle');
    const allergies = context.medication_allergy_status === 'PRESENT'
      ? allergyText.split(',').map(item => item.trim()).filter(Boolean)
      : context.medication_allergy_status === 'NONE_KNOWN' ? [] : null;

    const payload = {
      weight_kg: context.weight_kg,
      medication_allergy_status: context.medication_allergy_status,
      medication_allergies: allergies,
      penicillin_allergy_status: context.penicillin_allergy_status,
      ie_cardiac_risk_category: context.ie_cardiac_risk_category,
      renal_context_status: context.renal_context_status,
      renal_context_note: context.renal_context_status === 'IMPAIRMENT_REPORTED' ? context.renal_context_note : null,
      hepatic_context_status: context.hepatic_context_status,
      hepatic_context_note: context.hepatic_context_status === 'IMPAIRMENT_REPORTED' ? context.hepatic_context_note : null,
    };

    try {
      const response = await api.put(`/patients/${patientId}/clinical-context`, payload);
      const saved = { ...EMPTY_CONTEXT, ...response.data } as PatientClinicalContext;
      setContext(saved);
      setAllergyText((saved.medication_allergies || []).join(', '));
      setSaveState('saved');
      setLoadError(false);
      setExpanded(false);
    } catch (error) {
      console.error('Clinical context save failed:', error);
      setSaveState('error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section
      data-patient-clinical-context="c2"
      data-context-expanded={expanded ? 'true' : 'false'}
      className="rounded-2xl border border-border-main bg-glass-bg/70 px-3.5 py-3 shadow-sm backdrop-blur-xl sm:px-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.14em] text-text-muted">
            <ShieldAlert size={13} /> Contexte patient
          </div>
          <p className="mt-1 text-[11px] font-semibold leading-relaxed text-text-muted">
            Poids, allergies et informations médicales utiles à la prescription.
          </p>
        </div>
        {!loading && patientId && !loadError && (
          <button
            type="button"
            aria-expanded={expanded}
            onClick={() => setExpanded(value => !value)}
            className="inline-flex min-h-[44px] shrink-0 items-center gap-1.5 rounded-xl border border-border-main bg-background px-3 text-[10px] font-black uppercase tracking-wide text-text-main transition hover:border-accent/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/20"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {expanded ? 'Réduire' : 'Renseigner'}
          </button>
        )}
        {loading && <Loader2 aria-label="Chargement du contexte clinique" size={17} className="shrink-0 animate-spin text-text-muted" />}
      </div>

      {!patientId ? (
        <div className="mt-3 rounded-xl border border-amber-500/25 bg-amber-500/5 px-3 py-2 text-xs font-bold text-amber-700 dark:text-amber-300">
          Contexte indisponible : aucun patient sélectionné.
        </div>
      ) : loading ? (
        <div className="mt-3 flex min-h-[64px] items-center justify-center rounded-xl border border-border-main bg-background/60 px-3 py-3 text-xs font-bold text-text-muted">
          <Loader2 size={15} className="mr-2 animate-spin" /> Chargement du contexte clinique…
        </div>
      ) : loadError ? (
        <div className="mt-3 flex items-center gap-2 rounded-xl border border-amber-500/25 bg-amber-500/5 px-3 py-2 text-xs font-bold text-amber-700 dark:text-amber-300">
          <AlertTriangle size={14} /> Contexte non chargé. Aucune valeur n’est supposée.
        </div>
      ) : !expanded ? (
        <div data-clinical-context-summary="compact" className="mt-2 rounded-xl border border-border-main/80 bg-background/55 px-3 py-2 text-[10px] font-bold leading-relaxed text-text-muted">
          <div>
            Poids : <span className="text-text-main">{context.weight_kg == null ? 'non renseigné' : `${context.weight_kg} kg`}</span>
            <span className="mx-1.5 opacity-50">•</span>
            Allergies : <span className="text-text-main">{allergySummary(context)}</span>
            <span className="mx-1.5 opacity-50">•</span>
            Rein : <span className="text-text-main">{organSummary(context.renal_context_status)}</span>
            <span className="mx-1.5 opacity-50">•</span>
            Foie : <span className="text-text-main">{organSummary(context.hepatic_context_status)}</span>
          </div>
          <div className="mt-0.5">
            Pénicilline : <span className="text-text-main">{penicillinSummary(context.penicillin_allergy_status)}</span>
            <span className="mx-1.5 opacity-50">•</span>
            Risque endocardite : <span className="text-text-main">{cardiacSummary(context.ie_cardiac_risk_category)}</span>
          </div>
        </div>
      ) : (
        <>
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
              <span className={labelClass}>Allergie pénicilline / amoxicilline</span>
              <select
                aria-label="Statut allergie pénicilline ou amoxicilline"
                className={fieldClass}
                value={context.penicillin_allergy_status}
                onChange={event => update('penicillin_allergy_status', event.target.value as AllergyStatus)}
              >
                <option value="UNKNOWN">Inconnu / non vérifié</option>
                <option value="NONE_KNOWN">Aucune connue déclarée</option>
                <option value="PRESENT">Allergie rapportée</option>
              </select>
            </label>

            <label>
              <span className={labelClass}>Risque cardiaque d’endocardite</span>
              <select
                aria-label="Catégorie cardiaque endocardite infectieuse"
                className={fieldClass}
                value={context.ie_cardiac_risk_category}
                onChange={event => update('ie_cardiac_risk_category', event.target.value as IECardiacRiskCategory)}
              >
                <option value="UNKNOWN">Non renseigné / à vérifier</option>
                <option value="NONE_REPORTED">Aucune situation à haut risque connue</option>
                <option value="PROSTHETIC_CARDIAC_VALVE">Valve cardiaque prothétique</option>
                <option value="PROSTHETIC_MATERIAL_FOR_CARDIAC_VALVE_REPAIR">Matériel prothétique utilisé pour réparation valvulaire</option>
                <option value="PREVIOUS_INFECTIVE_ENDOCARDITIS">Antécédent d’endocardite infectieuse</option>
                <option value="UNREPAIRED_CYANOTIC_CONGENITAL_HEART_DISEASE">Cardiopathie congénitale cyanogène non réparée</option>
                <option value="REPAIRED_CHD_WITH_RESIDUAL_SHUNT_OR_VALVULAR_REGURGITATION_AT_PROSTHETIC_PATCH_OR_DEVICE">Cardiopathie congénitale réparée avec shunt résiduel ou régurgitation au niveau d’un patch/dispositif prothétique</option>
                <option value="CARDIAC_TRANSPLANT_WITH_VALVE_REGURGITATION_DUE_STRUCTURALLY_ABNORMAL_VALVE">Greffe cardiaque avec régurgitation liée à une valve structurellement anormale</option>
                <option value="OTHER_CARDIAC_CONDITION">Autre cardiopathie</option>
              </select>
            </label>

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
          </div>

          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <div className="min-h-5 text-[11px] font-bold">
              {saveState === 'error' && <span className="flex items-center gap-1 text-rose-600"><AlertTriangle size={13} /> Enregistrement impossible</span>}
            </div>
            <button
              type="button"
              onClick={save}
              disabled={saving}
              className="inline-flex min-h-[44px] items-center gap-2 rounded-xl border border-border-main bg-background px-3.5 text-xs font-black text-text-main transition hover:border-accent/40 disabled:cursor-not-allowed disabled:opacity-45"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              Enregistrer le contexte
            </button>
          </div>
        </>
      )}

      {!expanded && saveState === 'saved' && (
        <div className="mt-2 flex items-center gap-1 text-[11px] font-bold text-emerald-600">
          <CheckCircle2 size={13} /> Contexte enregistré
        </div>
      )}
    </section>
  );
}
