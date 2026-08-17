import React from 'react';
import { cn } from '../../../utils/cn';
import { AccountingStudio } from '../AccountingStudio';
import { TreatmentPlanStudio } from './TreatmentPlanStudio';
import { CertificateForm } from './Forms/CertificateForm';
import { InstallmentStudio } from './Forms/InstallmentStudio';
import { LibreForm } from './Forms/LibreForm';
import { PrescriptionAgenticStudio, type DrugItem } from './Forms/PrescriptionAgenticStudio';
import { useDocumentGenerator } from './useDocumentGenerator';
import type { SelectedSurfaceData } from '../../../components/odontogram/types';
import type { CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';

type Generator = ReturnType<typeof useDocumentGenerator>;
type PlanConversionHandler = React.ComponentProps<typeof TreatmentPlanStudio>['onConvertToQuote'];

type DocumentHubContentProps = {
  activeTab: CertifiableDocumentStudioTab;
  patientId: string | undefined;
  showLegalAnnotations: boolean;
  setShowLegalAnnotations: React.Dispatch<React.SetStateAction<boolean>>;
  drugs: DrugItem[];
  setDrugs: React.Dispatch<React.SetStateAction<DrugItem[]>>;
  certifType: string;
  setCertifType: React.Dispatch<React.SetStateAction<string>>;
  certifDays: number;
  setCertifDays: React.Dispatch<React.SetStateAction<number>>;
  docDate: string;
  certifStartDate: string;
  setCertifStartDate: React.Dispatch<React.SetStateAction<string>>;
  certifCustomMotif: string;
  setCertifCustomMotif: React.Dispatch<React.SetStateAction<string>>;
  libreTitle: string;
  setLibreTitle: React.Dispatch<React.SetStateAction<string>>;
  libreContent: string;
  setLibreContent: React.Dispatch<React.SetStateAction<string>>;
  libreCustomPatient: string;
  setLibreCustomPatient: React.Dispatch<React.SetStateAction<string>>;
  libreCustomDate: string;
  setLibreCustomDate: React.Dispatch<React.SetStateAction<string>>;
  libreHideHeader: boolean;
  setLibreHideHeader: React.Dispatch<React.SetStateAction<boolean>>;
  librePageSize: 'A5' | 'A4';
  setLibrePageSize: React.Dispatch<React.SetStateAction<'A5' | 'A4'>>;
  libreAlignment: 'left' | 'center' | 'right' | 'justify';
  setLibreAlignment: React.Dispatch<React.SetStateAction<'left' | 'center' | 'right' | 'justify'>>;
  setEcheancierPayload: React.Dispatch<React.SetStateAction<any>>;
  setSelectedTeethFromOdontogram: React.Dispatch<React.SetStateAction<SelectedSurfaceData[]>>;
  onConvertPlanToQuote: PlanConversionHandler;
  generator: Generator;
};

export const DocumentHubContent: React.FC<DocumentHubContentProps> = ({
  activeTab,
  patientId,
  showLegalAnnotations,
  setShowLegalAnnotations,
  drugs,
  setDrugs,
  certifType,
  setCertifType,
  certifDays,
  setCertifDays,
  docDate,
  certifStartDate,
  setCertifStartDate,
  certifCustomMotif,
  setCertifCustomMotif,
  libreTitle,
  setLibreTitle,
  libreContent,
  setLibreContent,
  libreCustomPatient,
  setLibreCustomPatient,
  libreCustomDate,
  setLibreCustomDate,
  libreHideHeader,
  setLibreHideHeader,
  librePageSize,
  setLibrePageSize,
  libreAlignment,
  setLibreAlignment,
  setEcheancierPayload,
  setSelectedTeethFromOdontogram,
  onConvertPlanToQuote,
  generator,
}) => (
  <div data-tour="document-hub-content" className="flex-1 flex flex-col p-2 min-h-min shrink-0">
    {activeTab === 'plan' && (
      <TreatmentPlanStudio
        patientId={Number(patientId)}
        onConvertToQuote={onConvertPlanToQuote}
      />
    )}

    {activeTab === 'ordonnance' && (
      <>
        <div className="flex items-center gap-2 mb-3 px-1">
          <button
            type="button"
            onClick={() => setShowLegalAnnotations(value => !value)}
            className={cn(
              'relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none',
              showLegalAnnotations ? 'bg-primary' : 'bg-slate-200'
            )}
            role="switch"
            aria-checked={showLegalAnnotations}
            aria-labelledby="document-studio-legal-annotations-label"
          >
            <span className={cn(
              'pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200',
              showLegalAnnotations ? 'translate-x-4' : 'translate-x-0'
            )} />
          </button>
          <span id="document-studio-legal-annotations-label" className="text-[10px] font-bold text-text-muted uppercase tracking-widest">
            Mentions légales (Radioprotection)
          </span>
        </div>
        <PrescriptionAgenticStudio
          patientId={patientId || '0'}
          drugs={drugs}
          setDrugs={setDrugs}
          onUpdateDrug={(id, field, value) => {
            setDrugs(previous => previous.map(drug => drug.id === id ? { ...drug, [field]: value } : drug));
            generator.setHasChanges(true);
          }}
          onRemoveDrug={(id) => {
            setDrugs(previous => previous.filter(drug => drug.id !== id));
            generator.setHasChanges(true);
          }}
          onAddDrug={() => setDrugs(previous => [
            ...previous,
            { id: Date.now(), name: '', dosage: '', forme: 'Comprimés', posologie: '', type: 'MEDICAMENT' },
          ])}
          validationErrors={generator.validationErrors}
          onSaveHabit={(context, nextDrugs) => generator.handleSavePreference({ protocol_name: context }, nextDrugs)}
          hasChanges={generator.hasChanges}
          coherenceWarnings={generator.coherenceWarnings}
        />
      </>
    )}

    {activeTab === 'certificat' && (
      <CertificateForm
        patientId={patientId || ''}
        certifType={certifType}
        setCertifType={setCertifType}
        certifDays={certifDays}
        setCertifDays={setCertifDays}
        docDate={docDate}
        certifStartDate={certifStartDate}
        setCertifStartDate={setCertifStartDate}
        certifCustomMotif={certifCustomMotif}
        setCertifCustomMotif={setCertifCustomMotif}
      />
    )}

    {activeTab === 'libre' && (
      <LibreForm
        title={libreTitle}
        setTitle={setLibreTitle}
        content={libreContent}
        setContent={setLibreContent}
        customPatient={libreCustomPatient}
        setCustomPatient={setLibreCustomPatient}
        customDate={libreCustomDate}
        setCustomDate={setLibreCustomDate}
        hideHeader={libreHideHeader}
        setHideHeader={setLibreHideHeader}
        pageSize={librePageSize}
        setPageSize={setLibrePageSize}
        alignment={libreAlignment}
        setAlignment={setLibreAlignment}
        validationErrors={generator.validationErrors}
      />
    )}

    {activeTab === 'echeancier' && (
      <InstallmentStudio
        patientId={patientId || '0'}
        onPayloadChange={setEcheancierPayload}
      />
    )}

    {(activeTab === 'devis' || activeTab === 'honoraires') && (
      <AccountingStudio
        isDevis={activeTab === 'devis'}
        patientId={patientId || '0'}
        coherenceWarnings={generator.coherenceWarnings}
        validationErrors={generator.validationErrors}
        setSelectedTeethFromOdontogram={setSelectedTeethFromOdontogram}
      />
    )}
  </div>
);
