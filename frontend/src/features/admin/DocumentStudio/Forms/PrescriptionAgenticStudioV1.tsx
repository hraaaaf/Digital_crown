import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AlertCircle, Plus, ShieldAlert, ShieldCheck } from 'lucide-react';

import { api } from '../../../../services/api';
import {
  isPrescriptionDirty,
  setPrescriptionDirty,
} from '../PrescriptionDirtyState';
import {
  preserveExplicitMedicationForms,
} from '../PrescriptionFormPolicy';
import type { ValidationError } from '../useDocumentGenerator';
import { DrugRow } from './DrugRow';
import type { DrugItem } from './prescriptionTypes';

export interface PrescriptionAgenticStudioProps {
  patientId: string;
  drugs: DrugItem[];
  setDrugs: (drugs: DrugItem[]) => void;
  onUpdateDrug: (id: number, field: keyof DrugItem, val: any) => void;
  onRemoveDrug: (id: number) => void;
  onAddDrug: () => void;
  validationErrors: ValidationError[];
  onSaveHabit?: (context: string, drugs: DrugItem[]) => void;
  hasChanges?: boolean;
  coherenceWarnings?: { level: string; message: string }[];
}

type SafetyWarning = { type?: string; message: string };
type SafetyStatus = 'unchecked' | 'checking' | 'verified' | 'error';

const fingerprint = (drugs: DrugItem[]): string => JSON.stringify(
  drugs.map(drug => ({
    id: drug.id,
    name: drug.name,
    dosage: drug.dosage,
    forme: drug.forme,
    posologie: drug.posologie,
    type: drug.type,
    quantite: drug.quantite,
    non_substituable: drug.non_substituable,
    catalogPresentationId: drug.catalogPresentationId,
  })),
);

const clearCatalogMetadata = (drug: DrugItem): DrugItem => ({
  ...drug,
  catalogPresentationId: undefined,
  catalogDci: undefined,
  catalogSourceId: undefined,
  catalogSourceLabel: undefined,
  catalogSnapshotDate: undefined,
  catalogMarketingStatusVerified: undefined,
});

export const PrescriptionAgenticStudio: React.FC<PrescriptionAgenticStudioProps> = ({
  patientId,
  drugs,
  setDrugs,
  onUpdateDrug,
  onRemoveDrug,
  onAddDrug,
  validationErrors,
}) => {
  const [safetyStatus, setSafetyStatus] = useState<SafetyStatus>('unchecked');
  const [safetyWarnings, setSafetyWarnings] = useState<SafetyWarning[]>([]);
  const baselineFingerprintRef = useRef<string | null>(null);
  const currentDrugsRef = useRef(drugs);
  currentDrugsRef.current = drugs;

  const currentFingerprint = useMemo(() => fingerprint(drugs), [drugs]);
  const medicationNames = useMemo(
    () => drugs
      .filter(drug => drug.type !== 'EXAMEN' && drug.name.trim())
      .map(drug => drug.name.trim()),
    [drugs],
  );
  const activeLineCount = drugs.filter(drug => drug.name.trim()).length;

  useEffect(() => {
    if (baselineFingerprintRef.current === null) {
      baselineFingerprintRef.current = currentFingerprint;
      setPrescriptionDirty(false);
      return;
    }
    setPrescriptionDirty(currentFingerprint !== baselineFingerprintRef.current);
  }, [currentFingerprint]);

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
        baselineFingerprintRef.current = fingerprint(currentDrugsRef.current);
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

  useEffect(() => {
    if (!patientId.trim() || medicationNames.length === 0) {
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
          patient_id: patientId,
          drug_names: medicationNames,
        });
        if (cancelled) return;
        setSafetyWarnings(Array.isArray(response.data) ? response.data : []);
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
  }, [patientId, JSON.stringify(medicationNames)]);

  const moveDrug = (id: number, direction: 'up' | 'down') => {
    const index = drugs.findIndex(drug => drug.id === id);
    if (index < 0) return;
    const target = direction === 'up' ? index - 1 : index + 1;
    if (target < 0 || target >= drugs.length) return;
    const next = [...drugs];
    [next[index], next[target]] = [next[target], next[index]];
    setDrugs(next);
  };

  const toggleType = (id: number, type: 'MEDICAMENT' | 'EXAMEN') => {
    setDrugs(drugs.map(drug => {
      if (drug.id !== id) return drug;
      const clean = clearCatalogMetadata(drug);
      if (type === 'EXAMEN') {
        return { ...clean, type, dosage: '', forme: '', posologie: '' };
      }
      return { ...clean, type, dosage: '', forme: '', posologie: '' };
    }));
  };

  return (
    <div data-prescription-intelligence-studio="v1" className="space-y-3">
      <section className="rounded-2xl border border-border-main bg-glass-bg/70 p-3 shadow-sm backdrop-blur-xl sm:p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="text-[9px] font-black uppercase tracking-[0.18em] text-text-muted">Prescription Intelligence V1</div>
            <div className="mt-1 text-xs font-black text-text-main">Recherche documentaire → présentation explicite → validation praticien</div>
            <p className="mt-1 max-w-3xl text-[10px] font-semibold leading-relaxed text-text-muted">
              Les protocoles automatiques, habitudes de posologie et suggestions cliniques legacy sont désactivés dans ce flux. Le snapshot CNOPS sert à identifier une présentation, jamais à décider une dose.
            </p>
          </div>
          <div className="rounded-xl border border-border-main bg-card/80 px-3 py-2 text-[9px] font-black uppercase tracking-wide text-text-muted">
            {activeLineCount} ligne{activeLineCount > 1 ? 's' : ''} renseignée{activeLineCount > 1 ? 's' : ''}
          </div>
        </div>

        <div className="mt-3 grid gap-2 lg:grid-cols-2">
          <div
            data-clinical-rule-status="blocked"
            className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/65 px-3 py-2 text-[10px] font-semibold text-amber-800"
          >
            <ShieldAlert size={14} className="mt-0.5 shrink-0" />
            <div><span className="font-black">Suggestion clinique bloquée.</span> Aucune règle V1 n’est certifiée et le dossier patient ne possède pas encore tous les champs structurés requis.</div>
          </div>

          <div
            data-safety-status={safetyStatus}
            className="flex items-start gap-2 rounded-xl border border-border-main bg-card/70 px-3 py-2 text-[10px] font-semibold text-text-muted"
          >
            {safetyStatus === 'verified' && safetyWarnings.length === 0
              ? <ShieldCheck size={14} className="mt-0.5 shrink-0 text-emerald-600" />
              : <AlertCircle size={14} className="mt-0.5 shrink-0" />}
            <div>
              {safetyStatus === 'unchecked' && 'Contrôle de sécurité backend prêt après identification d’un médicament.'}
              {safetyStatus === 'checking' && 'Contrôle de sécurité backend en cours…'}
              {safetyStatus === 'verified' && safetyWarnings.length === 0 && 'Contrôle de sécurité backend exécuté : aucune alerte retournée.'}
              {safetyStatus === 'verified' && safetyWarnings.length > 0 && `Revue praticien requise : ${safetyWarnings.length} alerte(s) retournée(s).`}
              {safetyStatus === 'error' && 'Contrôle de sécurité indisponible : aucune validation implicite.'}
            </div>
          </div>
        </div>

        {safetyWarnings.length > 0 && (
          <ul className="mt-2 space-y-1 rounded-xl border border-amber-200 bg-amber-50/65 px-3 py-2 text-[10px] font-semibold text-amber-800">
            {safetyWarnings.slice(0, 5).map((warning, index) => (
              <li key={`${warning.type || 'warning'}-${index}`}>• {warning.message}</li>
            ))}
          </ul>
        )}
      </section>

      <div className="space-y-3">
        {drugs.map((drug, idx) => (
          <DrugRow
            key={drug.id}
            drug={drug}
            idx={idx}
            drugsCount={drugs.length}
            assessment={null}
            validationErrors={validationErrors}
            forcedDrugs={[]}
            activeSearchId={null}
            suggestions={{ medications: [], dosages: [], posologies: [] }}
            highlightedIdx={-1}
            medChecks={{}}
            onUpdateDrug={onUpdateDrug}
            onRemoveDrug={onRemoveDrug}
            onMove={moveDrug}
            onSearch={(id, field, value) => onUpdateDrug(id, field as keyof DrugItem, value)}
            onKeyDown={() => undefined}
            onApplySuggestion={() => undefined}
            onFormeOpen={() => undefined}
            onForceAllergy={() => undefined}
            onToggleType={toggleType}
          />
        ))}
      </div>

      <button
        type="button"
        onClick={onAddDrug}
        className="flex min-h-11 w-full items-center justify-center gap-2 rounded-2xl border border-dashed border-primary/30 bg-primary/5 px-4 py-3 text-[10px] font-black uppercase tracking-widest text-primary transition-all hover:border-primary/50 hover:bg-primary/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
      >
        <Plus size={15} /> Ajouter une ligne
      </button>
    </div>
  );
};
