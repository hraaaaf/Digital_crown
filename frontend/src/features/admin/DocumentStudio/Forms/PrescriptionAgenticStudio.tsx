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

export type { DrugItem } from './PrescriptionAgenticStudioLegacy';

type PrescriptionAgenticStudioProps = React.ComponentProps<typeof LegacyPrescriptionAgenticStudio>;

const safetyToneClass = {
  neutral: 'bg-slate-50 border-slate-200 text-slate-600',
  progress: 'bg-blue-50 border-blue-200 text-blue-600',
  success: 'bg-emerald-50 border-emerald-200 text-emerald-700',
  warning: 'bg-amber-50 border-amber-200 text-amber-700',
  error: 'bg-red-50 border-red-200 text-red-700',
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
        .prescription-r3-safety-orchestrated .prescription-r3-legacy > div > div:first-child > div:nth-child(2) {
          display: none !important;
        }
        .prescription-r3-safety-orchestrated .prescription-r3-legacy > div > div:first-child > div:last-child > button:last-child {
          display: none !important;
        }
      `}</style>

      <div className="mx-1 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 shadow-sm">
        <div className="min-w-0">
          <div className="text-[10px] font-black uppercase tracking-widest text-slate-700">Contexte patient</div>
          <div className="mt-0.5 text-[10px] font-semibold text-slate-500">
            Données du dossier et vérifications déterministes utilisées pour l’ordonnance en cours.
          </div>
        </div>
        <div className="rounded-xl bg-slate-100 px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-slate-600">
          {activeLineCount} ligne{activeLineCount > 1 ? 's' : ''} renseignée{activeLineCount > 1 ? 's' : ''}
        </div>
      </div>

      <div className="mx-1 flex flex-wrap items-start gap-3">
        <div
          className={cn(
            'flex min-w-0 flex-1 items-start gap-3 rounded-2xl border px-4 py-3 shadow-sm',
            safetyToneClass[safetyView.tone],
          )}
          role="status"
          aria-live="polite"
          data-safety-status={safetyStatus}
        >
          {safetyStatus === 'checking' ? (
            <Loader2 size={16} className="mt-0.5 shrink-0 animate-spin" />
          ) : safetyStatus === 'verified' && safetyWarnings.length === 0 ? (
            <ShieldCheck size={16} className="mt-0.5 shrink-0" />
          ) : (
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
          )}
          <div className="min-w-0 flex-1">
            <div className="text-[10px] font-black uppercase tracking-widest">{safetyView.label}</div>
            <div className="mt-0.5 text-[10px] font-semibold opacity-80">
              {safetyStatus === 'unchecked' && 'Le contrôle sécurité patient/médicaments n’a pas encore été exécuté.'}
              {safetyStatus === 'checking' && 'Contrôle déterministe local en cours sur l’ordonnance actuelle.'}
              {safetyStatus === 'verified' && safetyWarnings.length === 0 && 'Contrôle backend exécuté sur cette combinaison patient/médicaments : aucune alerte retournée.'}
              {safetyStatus === 'verified' && safetyWarnings.length > 0 && 'Contrôle backend exécuté : revue praticien requise avant validation.'}
              {safetyStatus === 'error' && 'Le contrôle backend n’a pas abouti. L’ordonnance ne doit pas être présentée comme vérifiée.'}
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

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={restoreProtocols}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-[10px] font-black uppercase tracking-widest text-slate-600 shadow-sm transition-colors hover:border-primary/30 hover:text-primary"
            title="Réafficher la zone Mes protocoles"
          >
            Mes protocoles
          </button>
          <button
            type="button"
            onClick={refreshClinicalContext}
            className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-[10px] font-black uppercase tracking-widest text-slate-600 shadow-sm transition-colors hover:border-primary/30 hover:text-primary"
            title="Relancer le chargement du contexte patient"
          >
            <RefreshCcw size={14} />
            Actualiser le contexte
          </button>
        </div>
      </div>

      {missingMedicationForm && (
        <div className="mx-1 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800" role="alert">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <div>
            <div className="text-[10px] font-black uppercase tracking-widest">Forme pharmaceutique non renseignée</div>
            <div className="mt-0.5 text-[10px] font-semibold opacity-80">
              Aucune forme ne sera déduite automatiquement. Renseignez la forme avant validation si elle est nécessaire au document.
            </div>
          </div>
        </div>
      )}

      <div className="prescription-r3-legacy">
        <LegacyPrescriptionAgenticStudio key={legacyEpoch} {...props} />
      </div>
    </div>
  );
};