import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';

// Composants Modulaires
import { StudioHeader } from './DocumentStudio/StudioHeader';
import { StudioTabs } from './DocumentStudio/StudioTabs';
import { StudioFooter } from './DocumentStudio/StudioFooter';
import { DocumentHubPreview } from './DocumentStudio/DocumentHubPreview';
import { DocumentHubDialogs } from './DocumentStudio/DocumentHubDialogs';
import { DocumentHubContent } from './DocumentStudio/DocumentHubContent';
import {
  DOCUMENT_STUDIO_PREVIEW_TITLES,
  type CertifiableDocumentStudioTab,
} from './DocumentStudio/DocumentStudioVocabulary';
import { useDocumentHubNavigation } from './DocumentStudio/useDocumentHubNavigation';
import { useDocumentHubPatient } from './DocumentStudio/useDocumentHubPatient';
import { type DrugItem } from './DocumentStudio/Forms/PrescriptionAgenticStudio';
import { useDocumentGenerator } from './DocumentStudio/useDocumentGenerator';
import { type SelectedSurfaceData } from '../../components/odontogram/types';
import { useAccountingStore } from './store/useAccountingStore';
import { accountingDocumentTotal } from './DocumentStudio/AccountingTotalPolicy';
import { convertPlanActsToQuoteItems } from './DocumentStudio/AccountingPlanConversionPolicy';
import { documentPreviewFingerprint } from './DocumentStudio/DocumentPreviewFingerprint';

interface DocumentHubProps {
  patientId: string | undefined;
  patientName: string;
  editData?: {
    type: string;
    clinical_data: Record<string, unknown>;
    id?: number;
  };
}

interface GenericClinicalData {
  medications?: { nom?: string; dosage?: string; forme?: string; posologie?: string; type?: 'MEDICAMENT' | 'EXAMEN' }[];
  reason?: string;
  days?: number;
  start_date?: string;
  title?: string;
  content?: string;
  custom_patient?: string;
  custom_date?: string;
  hide_patient_header?: boolean;
  page_size?: 'A5' | 'A4';
  alignment?: 'left' | 'center' | 'right' | 'justify';
  items?: { acte: string; dent: string; montant?: number; prix_unitaire?: number; dents?: number[] }[];
  payments?: { acte: string; dent: string; montant?: number; prix_unitaire?: number; dents?: number[] }[];
  doc_date?: string;
}

export type HubDocumentType = CertifiableDocumentStudioTab;

export const DocumentHub: React.FC<DocumentHubProps> = ({ patientId, patientName, editData }) => {
  const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);
  const [sideStudioType, setSideStudioType] = useState<'NONE' | 'PREVIEW'>('NONE');
  const [smartSuggestion, setSmartSuggestion] = useState<{ rationale: string; drugs: DrugItem[] } | null>(null);

  const [drugs, setDrugs] = useState<DrugItem[]>([{ id: 1, name: '', dosage: '', forme: '', posologie: '', type: 'MEDICAMENT' }]);
  const [showLegalAnnotations, setShowLegalAnnotations] = useState(true);
  const [certifType, setCertifType] = useState('');
  const [certifDays, setCertifDays] = useState(0);
  const [certifStartDate, setCertifStartDate] = useState('');
  const [certifCustomMotif, setCertifCustomMotif] = useState('');
  const {
    items, setItems,
    paymentMode, setPaymentMode,
    installments, setInstallments,
    isAccounted,
    paymentStatus, setPaymentStatus,
    isGlobalNote, setIsGlobalNote,
  } = useAccountingStore();

  const [libreTitle, setLibreTitle] = useState('Note Médicale');
  const [libreContent, setLibreContent] = useState('');
  const [libreCustomPatient, setLibreCustomPatient] = useState('');
  const [libreCustomDate, setLibreCustomDate] = useState('');
  const [libreHideHeader, setLibreHideHeader] = useState(false);
  const [librePageSize, setLibrePageSize] = useState<'A5' | 'A4'>('A5');
  const [libreAlignment, setLibreAlignment] = useState<'left' | 'center' | 'right' | 'justify'>('justify');

  const resetHonorairesFinancialDraft = useCallback(() => {
    setPaymentMode('');
    setPaymentStatus('EN_ATTENTE');
    setIsGlobalNote(false);
    setInstallments([]);
  }, [setPaymentMode, setPaymentStatus, setIsGlobalNote, setInstallments]);

  const {
    activeTab,
    setActiveTab,
    pendingTab,
    handleTabChange,
    cancelPendingTab,
    confirmPendingTab,
    syncDocumentTab,
  } = useDocumentHubNavigation({
    hasAccountingDraft: items.some(item => item.description.trim()),
    resetHonorairesFinancialDraft,
  });

  const patientDetails = useDocumentHubPatient(patientId);
  const [selectedTeethFromOdontogram, setSelectedTeethFromOdontogram] = useState<SelectedSurfaceData[]>([]);
  const [echeancierPayload, setEcheancierPayload] = useState<any>(null);

  const generatorParams = useMemo(() => ({
    patientId, patientDetails, activeTab, drugs, certifType, certifDays, certifStartDate, certifCustomMotif,
    items,
    paymentMode,
    libreTitle, libreContent, libreCustomPatient, libreCustomDate,
    libreHideHeader, librePageSize, libreAlignment, docDate, selectedTeethFromOdontogram, smartSuggestion,
    installments, isAccounted, paymentStatus, isGlobalNote,
    showLegalAnnotations, echeancierPayload,
  }), [
    patientId, patientDetails, activeTab, drugs, certifType, certifDays, certifStartDate, certifCustomMotif,
    items, paymentMode, libreTitle, libreContent, libreCustomPatient, libreCustomDate,
    libreHideHeader, librePageSize, libreAlignment, docDate, selectedTeethFromOdontogram, smartSuggestion,
    installments, isAccounted, paymentStatus, isGlobalNote, showLegalAnnotations, echeancierPayload,
  ]);

  const generator = useDocumentGenerator(generatorParams);

  const previewFingerprint = useMemo(() => documentPreviewFingerprint({
    activeTab,
    patientId,
    docDate,
    drugs: drugs as unknown as Array<Record<string, unknown>>,
    certificate: {
      type: certifType,
      days: certifDays,
      startDate: certifStartDate,
      customReason: certifCustomMotif,
    },
    accounting: {
      items: items as unknown as Array<Record<string, unknown>>,
      paymentMode,
      paymentStatus,
      installments: installments as Array<Record<string, unknown>>,
      isGlobalNote,
      selectedTeeth: selectedTeethFromOdontogram as unknown as Array<Record<string, unknown>>,
    },
    libre: {
      title: libreTitle,
      content: libreContent,
      customPatient: libreCustomPatient,
      customDate: libreCustomDate,
      hideHeader: libreHideHeader,
      pageSize: librePageSize,
      alignment: libreAlignment,
    },
    isAccounted,
    showLegalAnnotations,
    installmentPayload: echeancierPayload,
  }), [
    activeTab, patientId, docDate, drugs,
    certifType, certifDays, certifStartDate, certifCustomMotif,
    items, paymentMode, paymentStatus, installments, isGlobalNote, selectedTeethFromOdontogram,
    libreTitle, libreContent, libreCustomPatient, libreCustomDate, libreHideHeader, librePageSize, libreAlignment,
    isAccounted, showLegalAnnotations, echeancierPayload,
  ]);

  const generatePreview = useCallback(() => {
    return generator.handleGenerate(false, false, true);
  }, [generator.handleGenerate]);

  useEffect(() => {
    if (editData?.clinical_data) {
      const type = editData.type.toLowerCase();
      const d = editData.clinical_data as GenericClinicalData;
      if (type === 'ordonnance') {
        setActiveTab('ordonnance');
        if (d.medications) setDrugs(d.medications.map((m: { nom?: string; dosage?: string; forme?: string; posologie?: string; type?: 'MEDICAMENT' | 'EXAMEN' }, idx: number) => ({
          id: Date.now() + idx, name: m.nom || '', dosage: m.dosage || '',
          forme: m.forme || 'Sachets', posologie: m.posologie || '',
          type: m.type || 'MEDICAMENT'
        })));
      } else if (type === 'certificat') {
        setActiveTab('certificat');
        setCertifType(d.reason || 'Arrêt de travail');
        setCertifDays(d.days ?? 0);
        setCertifStartDate(d.start_date || '');
        setCertifCustomMotif(d.content || '');
        if (!d.doc_date && d.start_date) setDocDate(d.start_date);
      } else if (type === 'libre' || type === 'lettre') {
        setActiveTab('libre');
        setLibreTitle(d.title || 'Note Médicale');
        setLibreContent(d.content || '');
        setLibreCustomPatient(d.custom_patient || '');
        setLibreCustomDate(d.custom_date || '');
        setLibreHideHeader(d.hide_patient_header || false);
        setLibrePageSize(d.page_size || 'A5');
        setLibreAlignment(d.alignment || 'justify');
      } else {
        setActiveTab(type === 'devis' ? 'devis' : 'honoraires');
        const srcItems = d.items || d.payments || [];
        setItems(srcItems.map((i: { acte: string; dent: string; montant?: number; prix_unitaire?: number; dents?: number[] }, idx: number) => ({
          id: Date.now() + idx,
          description: i.acte || '',
          dent: i.dent || '0',
          price: i.montant ?? i.prix_unitaire ?? 0,
          toothNumbers: i.dents || [],
        })));
      }
      if (d.doc_date) setDocDate(d.doc_date);
    }
  }, [editData, setActiveTab, setItems]);

  useEffect(() => {
    if (!patientId || activeTab !== 'ordonnance') {
      setSmartSuggestion(null);
      return;
    }

    let cancelled = false;
    api.get(`/prescriptions/smart-suggest/${patientId}`)
      .then(res => {
        if (!cancelled) setSmartSuggestion(res.data);
      })
      .catch(err => {
        if (!cancelled) console.error(err);
      });

    return () => {
      cancelled = true;
    };
  }, [patientId, activeTab]);

  useEffect(() => {
    if (activeTab === 'certificat' || activeTab === 'libre') {
      setSideStudioType('PREVIEW');
    }
  }, [activeTab]);

  const handleConvertPlanToQuote = useCallback((allActs: any[]) => {
    const newItems = convertPlanActsToQuoteItems(allActs);
    setItems(previous => [...previous, ...newItems]);
    setActiveTab('devis');
    syncDocumentTab('devis');
  }, [setItems, setActiveTab, syncDocumentTab]);

  return (
    <div className="relative w-full h-full overflow-hidden flex animate-in fade-in duration-700">
      <div className={cn(
        "flex-1 h-full flex flex-col px-4 sm:px-8 pt-6 pb-32 gap-3 overflow-y-auto bg-transparent dark:bg-slate-900/50 transition-all duration-500 custom-scrollbar",
        sideStudioType === 'PREVIEW' ? "xl:pr-[570px]" : ""
      )}>
        <StudioHeader
          patientName={patientName}
          docDate={docDate}
          onDateChange={setDocDate}
          activeTab={activeTab}
          showOdontoPanoramique={useAccountingStore(s => s.showOdontoPanoramique)}
          onToggleOdonto={() => useAccountingStore.getState().setShowOdontoPanoramique(v => !v)}
          onGenerate={generator.handleGenerate}
          loading={generator.loading}
          sideStudioType={sideStudioType}
          onTogglePreview={() => setSideStudioType(prev => prev === 'PREVIEW' ? 'NONE' : 'PREVIEW')}
        />

        <StudioTabs data-tour="document-tabs" activeTab={activeTab} onTabChange={handleTabChange} />

        <DocumentHubContent
          activeTab={activeTab}
          patientId={patientId}
          showLegalAnnotations={showLegalAnnotations}
          setShowLegalAnnotations={setShowLegalAnnotations}
          drugs={drugs}
          setDrugs={setDrugs}
          certifType={certifType}
          setCertifType={setCertifType}
          certifDays={certifDays}
          setCertifDays={setCertifDays}
          docDate={docDate}
          certifStartDate={certifStartDate}
          setCertifStartDate={setCertifStartDate}
          certifCustomMotif={certifCustomMotif}
          setCertifCustomMotif={setCertifCustomMotif}
          libreTitle={libreTitle}
          setLibreTitle={setLibreTitle}
          libreContent={libreContent}
          setLibreContent={setLibreContent}
          libreCustomPatient={libreCustomPatient}
          setLibreCustomPatient={setLibreCustomPatient}
          libreCustomDate={libreCustomDate}
          setLibreCustomDate={setLibreCustomDate}
          libreHideHeader={libreHideHeader}
          setLibreHideHeader={setLibreHideHeader}
          librePageSize={librePageSize}
          setLibrePageSize={setLibrePageSize}
          libreAlignment={libreAlignment}
          setLibreAlignment={setLibreAlignment}
          setEcheancierPayload={setEcheancierPayload}
          setSelectedTeethFromOdontogram={setSelectedTeethFromOdontogram}
          onConvertPlanToQuote={handleConvertPlanToQuote}
          generator={generator}
        />

        <StudioFooter
          loading={generator.loading}
          activeTab={activeTab}
          onGenerate={generator.handleGenerate}
          showPrintWarning={generator.showPrintWarning}
          onCloseWarning={generator.closeWarning}
          hasChanges={generator.hasChanges}
          onSavePreference={() => generator.handleSavePreference(smartSuggestion, drugs)}
          total={accountingDocumentTotal(items)}
          sideStudioType={sideStudioType}
          onTogglePreview={() => setSideStudioType(prev => prev === 'PREVIEW' ? 'NONE' : 'PREVIEW')}
        />
      </div>

      <DocumentHubDialogs
        showDiscardDraft={pendingTab !== null}
        onCancelDiscard={cancelPendingTab}
        onConfirmDiscard={confirmPendingTab}
        showDuplicate={generator.showDuplicateModal}
        onCancelDuplicate={generator.cancelDuplicate}
        onConfirmDuplicate={generator.confirmDuplicate}
      />

      <DocumentHubPreview
        open={sideStudioType === 'PREVIEW'}
        fingerprint={previewFingerprint}
        pdfUrl={generator.pdfUrl}
        loading={generator.loading}
        onClose={() => setSideStudioType('NONE')}
        onGeneratePreview={generatePreview}
        title={DOCUMENT_STUDIO_PREVIEW_TITLES[activeTab]}
      />
    </div>
  );
};