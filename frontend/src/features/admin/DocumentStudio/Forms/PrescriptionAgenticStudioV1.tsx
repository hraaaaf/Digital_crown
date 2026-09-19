import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Plus } from 'lucide-react';

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
import { IEProphylaxisRulePanel } from './IEProphylaxisRulePanel';
import { PatientClinicalContextPanel } from './PatientClinicalContextPanel';
import { FORMES, type DrugItem } from './prescriptionTypes';

export interface PrescriptionAgenticStudioProps {
  patientId: string;
  drugs: DrugItem[];
  setDrugs: (drugs: DrugItem[]) => void;
  prescriptionIndication: string;
  onPrescriptionIndicationChange: (value: string) => void;
  onUpdateDrug: (id: number, field: keyof DrugItem, val: any) => void;
  onRemoveDrug: (id: number) => void;
  onAddDrug: () => void;
  validationErrors: ValidationError[];
  onSaveHabit?: (context: string, drugs: DrugItem[]) => void;
  hasChanges?: boolean;
  coherenceWarnings?: { level: string; message: string }[];
}

const fingerprint = (drugs: DrugItem[], prescriptionIndication: string): string => JSON.stringify({
  prescriptionIndication: prescriptionIndication.trim(),
  drugs: drugs.map(drug => ({
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
});

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
  prescriptionIndication,
  onPrescriptionIndicationChange,
  onUpdateDrug,
  onRemoveDrug,
  onAddDrug,
  validationErrors,
}) => {
  const baselineFingerprintRef = useRef<string | null>(null);
  const currentDrugsRef = useRef(drugs);
  const currentIndicationRef = useRef(prescriptionIndication);
  const [formePicker, setFormePicker] = useState<{ drugId: number; top: number; left: number; width: number } | null>(null);
  currentDrugsRef.current = drugs;
  currentIndicationRef.current = prescriptionIndication;

  const currentFingerprint = useMemo(
    () => fingerprint(drugs, prescriptionIndication),
    [drugs, prescriptionIndication],
  );
  const activeLineCount = drugs.filter(drug => drug.name.trim()).length;
  const numericPatientId = patientId.trim() ? Number(patientId) : Number.NaN;
  const contextPatientId = Number.isInteger(numericPatientId) && numericPatientId > 0
    ? numericPatientId
    : undefined;
  const ieAmoxicillinDrug = drugs.find(drug => (
    Boolean(drug.catalogPresentationId)
    && ['AMOXICILLINE', 'AMOXICILLIN'].includes((drug.catalogDci || '').trim().toUpperCase())
  ));

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
          const preserved = preserveExplicitMedicationForms(parsed, currentDrugsRef.current);
          config.data = JSON.stringify(
            preserved?.type === 'ordonnance' && preserved?.data && typeof preserved.data === 'object'
              ? { ...preserved, data: { ...preserved.data, indication: currentIndicationRef.current.trim() || null } }
              : preserved,
          );
        } catch {
          return config;
        }
      } else if (config.data && typeof config.data === 'object') {
        const preserved = preserveExplicitMedicationForms(config.data, currentDrugsRef.current);
        config.data = preserved?.type === 'ordonnance' && preserved?.data && typeof preserved.data === 'object'
          ? { ...preserved, data: { ...preserved.data, indication: currentIndicationRef.current.trim() || null } }
          : preserved;
      }
      return config;
    });

    const responseInterceptor = api.interceptors.response.use(response => {
      const url = response.config?.url || '';
      const archivedDocument = url.includes('/documents/generate')
        && url.includes('archive=true')
        && !url.includes('preview=true');
      if (archivedDocument) {
        baselineFingerprintRef.current = fingerprint(currentDrugsRef.current, currentIndicationRef.current);
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

  const moveDrug = (id: number, direction: 'up' | 'down') => {
    const index = drugs.findIndex(drug => drug.id === id);
    if (index < 0) return;
    const target = direction === 'up' ? index - 1 : index + 1;
    if (target < 0 || target >= drugs.length) return;
    const next = [...drugs];
    [next[index], next[target]] = [next[target], next[index]];
    setDrugs(next);
  };

  const handleFormeOpen = (event: React.MouseEvent<HTMLButtonElement>, drugId: number) => {
    event.stopPropagation();
    const rect = event.currentTarget.getBoundingClientRect();
    setFormePicker(current => current?.drugId === drugId
      ? null
      : { drugId, top: rect.bottom + 8, left: rect.left, width: rect.width });
  };

  useEffect(() => {
    if (!formePicker) return;
    const close = () => setFormePicker(null);
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') close();
    };
    window.addEventListener('scroll', close, true);
    window.addEventListener('resize', close);
    window.addEventListener('keydown', closeOnEscape);
    return () => {
      window.removeEventListener('scroll', close, true);
      window.removeEventListener('resize', close);
      window.removeEventListener('keydown', closeOnEscape);
    };
  }, [formePicker]);

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
    <div
      data-prescription-intelligence-studio="v1"
      data-clinical-rule-status="blocked"
      data-safety-status="blocked"
      className="space-y-3"
    >
      <style>{`
        [data-prescription-intelligence-studio="v1"] [data-clinical-suggestion-status="blocked"] {
          display: none !important;
        }
      `}</style>

      <section className="rounded-2xl border border-border-main bg-glass-bg/70 p-3 shadow-sm backdrop-blur-xl sm:p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="text-[9px] font-black uppercase tracking-[0.18em] text-text-muted">Prescription</div>
            <div className="mt-1 text-xs font-black text-text-main">Recherche médicament → présentation → validation</div>
            <p className="mt-1 max-w-3xl text-[10px] font-semibold leading-relaxed text-text-muted">
              Recherchez le médicament, choisissez sa présentation puis complétez les instructions de prescription avant validation.
            </p>
          </div>
          <div className="rounded-xl border border-border-main bg-card/80 px-3 py-2 text-[9px] font-black uppercase tracking-wide text-text-muted">
            {activeLineCount} ligne{activeLineCount > 1 ? 's' : ''} renseignée{activeLineCount > 1 ? 's' : ''}
          </div>
        </div>
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
            onFormeOpen={handleFormeOpen}
            onForceAllergy={() => undefined}
            onToggleType={toggleType}
          />
        ))}
      </div>

      {formePicker && (() => {
        const activeDrug = drugs.find(drug => drug.id === formePicker.drugId);
        return (
          <div
            data-g4-manual-form-picker
            role="menu"
            aria-label="Choisir la forme"
            style={{
              position: 'fixed',
              top: formePicker.top,
              left: formePicker.left,
              width: Math.max(formePicker.width, 208),
              zIndex: 200,
            }}
            className="overflow-hidden rounded-2xl border border-border-main bg-card py-2 shadow-2xl"
          >
            {FORMES.map(forme => {
              const Icon = forme.icon;
              const selected = Boolean(activeDrug?.forme.startsWith(forme.l));
              return (
                <button
                  key={forme.l}
                  type="button"
                  role="menuitemradio"
                  aria-checked={selected}
                  onClick={() => {
                    onUpdateDrug(formePicker.drugId, 'forme', forme.l === 'AUTRE' ? 'AUTRE: ' : forme.l);
                    setFormePicker(null);
                  }}
                  className={`flex min-h-11 w-full items-center gap-3 px-5 py-2.5 text-left text-[10px] font-black uppercase tracking-widest transition-colors ${selected ? 'bg-primary/10 text-primary' : 'text-text-muted hover:bg-primary/5 hover:text-primary'}`}
                >
                  <Icon size={14} /> {forme.l}
                </button>
              );
            })}
          </div>
        );
      })()}

      <button
        type="button"
        onClick={onAddDrug}
        className="flex min-h-11 w-full items-center justify-center gap-2 rounded-2xl border border-dashed border-primary/30 bg-primary/5 px-4 py-3 text-[10px] font-black uppercase tracking-widest text-primary transition-all hover:border-primary/50 hover:bg-primary/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
      >
        <Plus size={15} /> Ajouter une ligne
      </button>

      <PatientClinicalContextPanel patientId={contextPatientId} />

      <IEProphylaxisRulePanel patientId={contextPatientId} drug={ieAmoxicillinDrug} />

      <section
        data-prescription-indication="document"
        className="rounded-2xl border border-border-main bg-glass-bg/70 px-3.5 py-3 shadow-sm backdrop-blur-xl sm:px-4"
      >
        <label>
          <span className="mb-1.5 block text-[10px] font-black uppercase tracking-[0.13em] text-text-muted">Indication de cette ordonnance</span>
          <textarea
            aria-label="Indication de cette ordonnance"
            className="min-h-[64px] w-full resize-y rounded-xl border border-border-main bg-background px-3 py-2 text-sm font-semibold text-text-main outline-none transition focus:border-accent/60 focus:ring-2 focus:ring-accent/10"
            value={prescriptionIndication}
            onChange={event => onPrescriptionIndicationChange(event.target.value)}
            placeholder="Contexte explicite de cette décision de prescription"
          />
        </label>
        <p className="mt-1.5 text-[10px] font-semibold leading-relaxed text-text-muted">
          Cette indication reste liée à cette ordonnance.
        </p>
      </section>
    </div>
  );
};
