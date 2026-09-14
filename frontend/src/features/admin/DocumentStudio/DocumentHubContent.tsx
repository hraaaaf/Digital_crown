import React from 'react';
import { cn } from '../../../utils/cn';
import { AccountingStudio } from '../AccountingStudio';
import { CertificateForm } from './Forms/CertificateForm';
import { InstallmentStudio } from './Forms/InstallmentStudio';
import { LibreForm } from './Forms/LibreForm';
import { PrescriptionAgenticStudio, type DrugItem } from './Forms/PrescriptionAgenticStudio';
import { useDocumentGenerator } from './useDocumentGenerator';
import type { SelectedSurfaceData } from '../../../components/odontogram/types';
import type { CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';

type Generator = ReturnType<typeof useDocumentGenerator>;

type DocumentHubContentProps = {
  activeTab: CertifiableDocumentStudioTab;
  patientId: string | undefined;
  showLegalAnnotations: boolean;
  setShowLegalAnnotations: React.Dispatch<React.SetStateAction<boolean>>;
  drugs: DrugItem[];
  setDrugs: React.Dispatch<React.SetStateAction<DrugItem[]>>;
  prescriptionIndication: string;
  setPrescriptionIndication: React.Dispatch<React.SetStateAction<string>>;
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
  generator: Generator;
};

export const DocumentHubContent: React.FC<DocumentHubContentProps> = ({
  activeTab,
  patientId,
  showLegalAnnotations,
  setShowLegalAnnotations,
  drugs,
  setDrugs,
  prescriptionIndication,
  setPrescriptionIndication,
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
  generator,
}) => (
  <div data-tour="document-hub-content" className="flex-1 flex flex-col p-2 min-h-min shrink-0">
    {activeTab === 'ordonnance' && (
      <div data-ordonnance-coherence="u6">
        <style>{`
          [data-ordonnance-coherence="u6"] .prescription-r3-legacy div:has(> div[title^="État partiel des contrôles locaux"]) {
            display: none !important;
          }
        `}</style>

        <PrescriptionAgenticStudio
          patientId={patientId || '0'}
          drugs={drugs}
          setDrugs={setDrugs}
          prescriptionIndication={prescriptionIndication}
          onPrescriptionIndicationChange={(value) => {
            setPrescriptionIndication(value);
            generator.setHasChanges(true);
          }}
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
            { id: Date.now(), name: '', dosage: '', forme: '', posologie: '', type: 'MEDICAMENT' },
          ])}
          validationErrors={generator.validationErrors}
          hasChanges={generator.hasChanges}
          coherenceWarnings={generator.coherenceWarnings}
        />

        <div data-ordonnance-secondary-meta className="mt-3 flex min-h-11 items-center gap-2 rounded-xl border border-border-main bg-glass-bg px-2 text-text-muted backdrop-blur-xl">
          <button
            type="button"
            onClick={() => setShowLegalAnnotations(value => !value)}
            className="inline-flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center rounded-xl transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
            role="switch"
            aria-checked={showLegalAnnotations}
            aria-labelledby="document-studio-legal-annotations-label"
          >
            <span className={cn(
              'relative inline-flex h-5 w-9 rounded-full transition-colors duration-200',
              showLegalAnnotations ? 'bg-primary' : 'bg-input-field'
            )}>
              <span className={cn(
                'pointer-events-none absolute top-0.5 inline-block h-4 w-4 rounded-full bg-card shadow-sm ring-0 transition duration-200',
                showLegalAnnotations ? 'translate-x-[18px]' : 'translate-x-0.5'
              )} />
            </span>
          </button>
          <span id="document-studio-legal-annotations-label" className="text-[10px] font-bold uppercase tracking-widest">
            Mentions légales (Radioprotection)
          </span>
        </div>
      </div>
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
