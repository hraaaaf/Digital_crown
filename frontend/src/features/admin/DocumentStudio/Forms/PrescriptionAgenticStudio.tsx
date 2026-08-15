import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Loader2, ShieldCheck } from 'lucide-react';
import { api } from '../../../../services/api';
import { cn } from '../../../../utils/cn';
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

export const PrescriptionAgenticStudio: React.FC<PrescriptionAgenticStudioProps> = props => {
  const [safetyStatus, setSafetyStatus] = useState<PrescriptionSafetyStatus>('unchecked');
  const [safetyWarnings, setSafetyWarnings] = useState<PrescriptionSafetyWarning[]>([]);

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
        .prescription-r3-safety-orchestrated .prescription-r3-legacy > div > div:first-child > div:nth-child(2) {
          display: none !important;
        }
      `}</style>

      <div
        className={cn(
          'mx-1 flex items-start gap-3 rounded-2xl border px-4 py-3 shadow-sm',
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

      <div className="prescription-r3-legacy">
        <LegacyPrescriptionAgenticStudio {...props} />
      </div>
    </div>
  );
};
