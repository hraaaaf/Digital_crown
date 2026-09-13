import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AlertCircle, Loader2, RefreshCcw, ShieldCheck } from 'lucide-react';
import { api } from '../../../../services/api';
import { cn } from '../../../../utils/cn';
import {
  isPrescriptionDirty,
  setPrescriptionDirty,
} from '../PrescriptionDirtyState';
import {
  hasMissingMedicationForm,
  preserveExplicitMedicationForms,
} from '../PrescriptionFormPolicy';
import {
  derivePrescriptionSafetyViewState,
  prescriptionSafetyFingerprint,
  type PrescriptionSafetyStatus,
  type PrescriptionSafetyWarning,
} from '../PrescriptionSafetyState';
import { PrescriptionAgenticStudio as LegacyPrescriptionAgenticStudio } from './PrescriptionAgenticStudioLegacy';
import { DEFAULT_MOROCCO_PRESETS } from './prescriptionTypes';

export type { DrugItem } from './PrescriptionAgenticStudioLegacy';

type PrescriptionAgenticStudioProps = React.ComponentProps<typeof LegacyPrescriptionAgenticStudio>;

const safetyToneClass = {
  neutral: 'bg-white/45 dark:bg-slate-900/55 border-slate-200/70 dark:border-white/10 text-slate-600 dark:text-slate-300',
  progress: 'bg-blue-50/60 dark:bg-blue-950/25 border-blue-100/80 dark:border-blue-900/40 text-blue-700 dark:text-blue-300',
  success: 'bg-emerald-50/60 dark:bg-emerald-950/25 border-emerald-100/80 dark:border-emerald-900/40 text-emerald-700 dark:text-emerald-300',
  warning: 'bg-amber-50/60 dark:bg-amber-950/25 border-amber-100/80 dark:border-amber-900/40 text-amber-700 dark:text-amber-300',
  error: 'bg-red-50/60 dark:bg-red-950/25 border-red-100/80 dark:border-red-900/40 text-red-700 dark:text-red-300',
} as const;

const prescriptionMutationFingerprint = (drugs: PrescriptionAgenticStudioProps['drugs']): string => JSON.stringify(
  drugs.map(drug => ({
    id: drug.id,
    name: drug.name,
    dosage: drug.dosage,
    forme: drug.forme,
    posologie: drug.posologie,
    type: drug.type,
    quantite: drug.quantite,
    non_substituable: drug.non_substituable,
  })),
);

export const PrescriptionAgenticStudio: React.FC<PrescriptionAgenticStudioProps> = props => {
  const [safetyStatus, setSafetyStatus] = useState<PrescriptionSafetyStatus>('unchecked');
  const [safetyWarnings, setSafetyWarnings] = useState<PrescriptionSafetyWarning[]>([]);
  const [legacyEpoch, setLegacyEpoch] = useState(0);
  const baselineFingerprintRef = useRef<string | null>(null);
  const currentFingerprintRef = useRef('');
  const currentDrugsRef = useRef(props.drugs);
  currentDrugsRef.current = props.drugs;

  const prescriptionFingerprint = useMemo(
    () => prescriptionMutationFingerprint(props.drugs),
    [props.drugs],
  );
  currentFingerprintRef.current = prescriptionFingerprint;

  const missingMedicationForm = useMemo(
    () => hasMissingMedicationForm(props.drugs),
    [props.drugs],
  );

  const activeLineCount = useMemo(
    () => props.drugs.filter(drug => drug.name.trim()).length,
    [props.drugs],
  );

  useEffect(() => {
    if (baselineFingerprintRef.current === null) {
      baselineFingerprintRef.current = prescriptionFingerprint;
      setPrescriptionDirty(false);
      return;
    }
    setPrescriptionDirty(prescriptionFingerprint !== baselineFingerprintRef.current);
  }, [prescriptionFingerprint]);

  useEffect(() => {
    const requestInterceptor = api.interceptors.request.use(config => {
      const url = config.url || '';
      if (!url.includes('/documents/generate')) return config;

      if (typeof config.data === 'string') {
        try {
          const parsed = JSON.parse(config.data);
          config.data = JSON.stringify(preserveExplicitMedicationForms(parsed, currentDrugsRef.current));
        } catch {
          return config;
        }
      } else if (config.data && typeof config.data === 'object') {
        config.data = preserveExplicitMedicationForms(config.data, currentDrugsRef.current);
      }
      return config;
    });

    const responseInterceptor = api.interceptors.response.use(response => {
      const url = response.config?.url || '';
      const archivedDocument = url.includes('/documents/generate')
        && url.includes('archive=true')
        && !url.includes('preview=true');
      if (archivedDocument) {
        baselineFingerprintRef.current = currentFingerprintRef.current;
        setPrescriptionDirty(false);
      }
      return response;
    });

    return () => {
      api.interceptors.request.eject(requestInterceptor);
      api.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (!isPrescriptionDirty()) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', beforeUnload);
    return () => window.removeEventListener('beforeunload', beforeUnload);
  }, []);

  const refreshClinicalContext = useCallback(() => {
    if (isPrescriptionDirty()) {
      const confirmed = window.confirm(
        'Actualiser le contexte patient ? L’ordonnance en cours sera conservée, mais les états temporaires du Studio seront réinitialisés.',
      );
      if (!confirmed) return;
    }
    setLegacyEpoch(epoch => epoch + 1);
  }, []);

  const restoreProtocols = useCallback(() => {
    setLegacyEpoch(epoch => epoch + 1);
  }, []);

  const applySystemProtocol = useCallback((label: string) => {
    const legacyRoot = document.querySelector('.prescription-r3-legacy');
    if (!legacyRoot) return;
    const systemSelect = Array.from(legacyRoot.querySelectorAll('select')).find(select =>
      Array.from(select.options).some(option => option.value === label),
    );
    if (!systemSelect) return;
    systemSelect.value = label;
    systemSelect.dispatchEvent(new Event('change', { bubbles: true }));
  }, []);

  const safetyDrugNames = useMemo(
    () => props.drugs
      .filter(drug => drug.type !== 'EXAMEN')
      .map(drug => drug.name.trim())
      .filter(Boolean),
    [props.drugs],
  );
  const safetyFingerprint = prescriptionSafetyFingerprint(props.patientId, safetyDrugNames);
  const safetyView = derivePrescriptionSafetyViewState(safetyStatus, safetyWarnings);

  useEffect(() => {
    if (!props.patientId.trim() || safetyDrugNames.length === 0) {
      setSafetyStatus('unchecked');
      setSafetyWarnings([]);
      return;
    }

    let cancelled = false;
    setSafetyStatus('checking');
    setSafetyWarnings([]);

    const timer = window.setTimeout(async () => {
      try {
        const response = await api.post('/prescriptions/safety/check', {
          patient_id: props.patientId,
          drug_names: safetyDrugNames,
        });
        if (cancelled) return;
        const warnings = Array.isArray(response.data) ? response.data : [];
        setSafetyWarnings(warnings);
        setSafetyStatus('verified');
      } catch (error) {
        if (cancelled) return;
        console.error('Prescription safety check failed:', error);
        setSafetyWarnings([]);
        setSafetyStatus('error');
      }
    }, 300);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [safetyFingerprint]);

  return (
    <div className="prescription-r3-safety-orchestrated space-y-3">
      <style>{`
        .prescription-r3-safety-orchestrated .prescription-r3-legacy > div > div:first-child > div:first-child,
        .prescription-r3-safety-orchestrated .prescription-r3-legacy > div > div:first-child > div:nth-child(2):not(:has([data-ordonnance-quick-entry])) {
          display: none !important;
        }
        .prescription-r3-safety-orchestrated .prescription-r3-legacy > div > div:first-child > div:last-child > button:last-child {
          display: none !important;
        }
        .prescription-r3-safety-orchestrated .prescription-r3-legacy div[class~="space-y-1.5"]:has(select option[value="Avulsion Simple"]) {
          display: none !important;
        }
        .prescription-r3-safety-orchestrated .prescription-r3-legacy div[class~="grid"]:has(> div select option[value="Avulsion Simple"]) {
          grid-template-columns: minmax(0, 1fr) !important;
        }
      `}</style>

      <section className="mx-1 overflow-hidden rounded-2xl border border-slate-200/70 bg-white/45 p-2.5 shadow-sm backdrop-blur-2xl dark:border-white/10 dark:bg-slate-900/45 sm:p-3">
        <div className="flex flex-wrap items-center justify-between gap-2 px-1 pb-2">
          <div className="min-w-0">
            <div className="text-[9px] font-black uppercase tracking-widest text-slate-700 dark:text-slate-200">Contexte patient</div>
            <div className="mt-0.5 hidden text-[9px] font-semibold text-slate-500 dark:text-slate-400 sm:block">
              Données du dossier et vérifications déterministes utilisées pour l’ordonnance en cours.
            </div>
          </div>
          <div className="rounded-lg border border-slate-200/70 bg-white/65 px-2.5 py-1 text-[9px] font-black uppercase tracking-wider text-slate-600 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-300">
            {activeLineCount} ligne{activeLineCount > 1 ? 's' : ''} renseignée{activeLineCount > 1 ? 's' : ''}
          </div>
        </div>

        <div className="grid gap-2 lg:grid-cols-[minmax(0,1fr)_auto]">
          <div
            className={cn(
              'flex min-w-0 items-start gap-2.5 rounded-xl border px-3 py-2.5 shadow-sm backdrop-blur-xl',
              safetyToneClass[safetyView.tone],
            )}
            role="status"
            aria-live="polite"
            data-safety-status={safetyStatus}
          >
            {safetyStatus === 'checking' ? (
              <Loader2 size={15} className="mt-0.5 shrink-0 animate-spin" />
            ) : safetyStatus === 'verified' && safetyWarnings.length === 0 ? (
              <ShieldCheck size={15} className="mt-0.5 shrink-0" />
            ) : (
              <AlertCircle size={15} className="mt-0.5 shrink-0" />
            )}
            <div className="min-w-0 flex-1">
              <div className="text-[9px] font-black uppercase tracking-widest">{safetyView.label}</div>
              <div className="mt-0.5 text-[9px] font-semibold opacity-80 sm:text-[10px]">
                {safetyStatus === 'unchecked' && 'Contrôle prêt dès qu’un médicament est renseigné.'}
                {safetyStatus === 'checking' && 'Contrôle déterministe local en cours.'}
                {safetyStatus === 'verified' && safetyWarnings.length === 0 && 'Contrôle backend exécuté : aucune alerte retournée.'}
                {safetyStatus === 'verified' && safetyWarnings.length > 0 && 'Revue praticien requise avant validation.'}
                {safetyStatus === 'error' && 'Contrôle indisponible : l’ordonnance ne doit pas être présentée comme vérifiée.'}
              </div>
              {safetyStatus === 'verified' && safetyWarnings.length > 0 && (
                <ul className="mt-2 space-y-1 text-[10px] font-bold">
                  {safetyWarnings.slice(0, 4).map((warning, index) => (
                    <li key={`${warning.type || 'warning'}-${index}`}>• {warning.message}</li>
                  ))}
                  {safetyWarnings.length > 4 && <li>• +{safetyWarnings.length - 4} autre(s) alerte(s)</li>}
                </ul>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 lg:flex lg:items-stretch">
            <button
              type="button"
              onClick={restoreProtocols}
              className="min-h-11 rounded-xl border border-slate-200/70 bg-white/65 px-3 py-2 text-[9px] font-black uppercase tracking-wider text-slate-600 shadow-sm backdrop-blur-xl transition-all hover:border-primary/20 hover:bg-white hover:text-primary dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-300 dark:hover:bg-slate-900 sm:px-3.5"
              title="Réafficher la zone Mes protocoles"
            >
              Mes protocoles
            </button>
            <button
              type="button"
              onClick={refreshClinicalContext}
              className="flex min-h-11 items-center justify-center gap-1.5 rounded-xl border border-slate-200/70 bg-white/65 px-3 py-2 text-[9px] font-black uppercase tracking-wider text-slate-600 shadow-sm backdrop-blur-xl transition-all hover:border-primary/20 hover:bg-white hover:text-primary dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-300 dark:hover:bg-slate-900 sm:px-3.5"
              title="Relancer le chargement du contexte patient"
            >
              <RefreshCcw size={13} className="shrink-0" />
              <span>Actualiser le contexte</span>
            </button>
          </div>
        </div>

        {missingMedicationForm && (
          <div className="mt-2 flex items-start gap-2.5 rounded-xl border border-amber-100/80 bg-amber-50/60 px-3 py-2.5 text-amber-800 shadow-sm backdrop-blur-xl dark:border-amber-900/40 dark:bg-amber-950/25 dark:text-amber-300" role="alert">
            <AlertCircle size={15} className="mt-0.5 shrink-0" />
            <div>
              <div className="text-[9px] font-black uppercase tracking-widest">Forme pharmaceutique non renseignée</div>
              <div className="mt-0.5 text-[9px] font-semibold opacity-80 sm:text-[10px]">
                Aucune forme ne sera déduite automatiquement. Renseignez-la avant validation si nécessaire.
              </div>
            </div>
          </div>
        )}
      </section>

      <section
        data-ordonnance-protocol-chips
        aria-label="Protocoles système rapides"
        className="mx-1 rounded-2xl border border-slate-200/70 bg-white/45 p-2.5 shadow-sm backdrop-blur-2xl dark:border-white/10 dark:bg-slate-900/45 sm:p-3"
      >
        <div className="mb-2 flex items-center justify-between gap-3 px-1">
          <div>
            <div className="text-[9px] font-black uppercase tracking-widest text-slate-700 dark:text-slate-200">Protocoles rapides</div>
            <div className="mt-0.5 hidden text-[9px] font-semibold text-slate-400 dark:text-slate-500 sm:block">
              Les protocoles existants passent toujours par l’arbitrage pharmacologique.
            </div>
          </div>
          <span className="shrink-0 rounded-lg border border-slate-200/70 bg-white/65 px-2 py-1 text-[8px] font-black uppercase tracking-wider text-slate-400 dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-500">
            1 clic
          </span>
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1 sm:flex-wrap sm:overflow-visible" role="group" aria-label="Choisir un protocole système">
          {DEFAULT_MOROCCO_PRESETS.map(preset => (
            <button
              key={preset.label}
              type="button"
              onClick={() => applySystemProtocol(preset.label)}
              className="inline-flex min-h-11 shrink-0 items-center rounded-xl border border-slate-200/80 bg-white/75 px-3 py-2 text-[9px] font-black uppercase tracking-wide text-slate-600 shadow-sm transition-all hover:border-primary/30 hover:bg-primary/5 hover:text-primary focus:outline-none focus:ring-4 focus:ring-primary/10 dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-300 dark:hover:bg-slate-900"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </section>

      <div className="prescription-r3-legacy">
        <LegacyPrescriptionAgenticStudio key={legacyEpoch} {...props} />
      </div>
    </div>
  );
};