import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';

// Composants Modulaires
import { StudioHeader } from './DocumentStudio/StudioHeader';
import { StudioTabs } from './DocumentStudio/StudioTabs';
import { StudioFooter } from './DocumentStudio/StudioFooter';
import { LivePreview } from './DocumentStudio/LivePreview';

// Formulaires
import { PrescriptionAgenticStudio, type DrugItem } from './DocumentStudio/Forms/PrescriptionAgenticStudio';
import { CertificateForm } from './DocumentStudio/Forms/CertificateForm';
import { InstallmentStudio } from './DocumentStudio/Forms/InstallmentStudio';
import { LibreForm } from './DocumentStudio/Forms/LibreForm';
import { AccountingStudio } from './AccountingStudio';
import { TreatmentPlanStudio } from './DocumentStudio/TreatmentPlanStudio';
import { useDocumentGenerator } from './DocumentStudio/useDocumentGenerator';
import { type SelectedSurfaceData } from '../../components/odontogram/types';
import { useAccountingStore } from './store/useAccountingStore';
import { accountingDocumentTotal } from './DocumentStudio/AccountingTotalPolicy';
import { convertPlanActsToQuoteItems } from './DocumentStudio/AccountingPlanConversionPolicy';
import { isPrescriptionDirty, setPrescriptionDirty } from './DocumentStudio/PrescriptionDirtyState';
import { isCertificateDirty, setCertificateDirty } from './DocumentStudio/CertificateDirtyState';
import { isInstallmentDirty, setInstallmentDirty } from './DocumentStudio/InstallmentDirtyState';
import { isLibreDirty, setLibreDirty } from './DocumentStudio/LibreDirtyState';
import { isP7Dirty, setP7Dirty } from './DocumentStudio/P7DirtyState';
import { shouldGuardDocumentTabTransition } from './DocumentStudio/DocumentTabNavigationPolicy';

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

interface PatientDetails {
  id: number;
  nom: string;
  prenom: string;
  date_naissance?: string;
  genre?: string;
}

export type HubDocumentType = 'plan' | 'ordonnance' | 'certificat' | 'devis' | 'honoraires' | 'echeancier' | 'libre';

type TabChangeSource = 'ui' | 'url';

const isHubDocumentType = (value: string | null): value is HubDocumentType =>
  ['plan', 'ordonnance', 'certificat', 'devis', 'honoraires', 'echeancier', 'libre'].includes(value || '');

export const DocumentHub: React.FC<DocumentHubProps> = ({ patientId, patientName, editData }) => {
  // --- ÉTATS GÉNÉRAUX ---
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedDocumentTab = searchParams.get('documentTab');
  const [activeTab, setActiveTab] = useState<HubDocumentType>(() =>
    isHubDocumentType(requestedDocumentTab) ? requestedDocumentTab : 'ordonnance'
  );
  const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);
  const [patientDetails, setPatientDetails] = useState<PatientDetails | null>(null);
  const [sideStudioType, setSideStudioType] = useState<'NONE' | 'PREVIEW'>('NONE');

  // --- SUGGESTIONS PRESCRIPTION ---
  const [smartSuggestion, setSmartSuggestion] = useState<{ rationale: string; drugs: DrugItem[] } | null>(null);

  // --- ÉTATS FORMULAIRES ---
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

  // P5 charge désormais son plan via son endpoint /latest dans InstallmentStudio.
  // Aucun plan historique P5 n'est injecté dans le brouillon financier P3/P4.

  // --- ÉTATS DOCUMENT LIBRE ---
  const [libreTitle, setLibreTitle] = useState('Note Médicale');
  const [libreContent, setLibreContent] = useState('');
  const [libreCustomPatient, setLibreCustomPatient] = useState('');
  const [libreCustomDate, setLibreCustomDate] = useState('');
  const [libreHideHeader, setLibreHideHeader] = useState(false);
  const [librePageSize, setLibrePageSize] = useState<'A5' | 'A4'>('A5');
  const [libreAlignment, setLibreAlignment] = useState<'left' | 'center' | 'right' | 'justify'>('justify');

  // --- GARDES NAVIGATION ---
  const [pendingTab, setPendingTab] = useState<HubDocumentType | null>(null);
  const [pendingTabSource, setPendingTabSource] = useState<TabChangeSource>('ui');

  const resetHonorairesFinancialDraft = () => {
    setPaymentMode('');
    setPaymentStatus('EN_ATTENTE');
    setIsGlobalNote(false);
    setInstallments([]);
  };

  const dirtySnapshot = () => ({
    prescription: isPrescriptionDirty(),
    certificate: isCertificateDirty(),
    accounting: items.some(item => item.description.trim()),
    installment: isInstallmentDirty(),
    libre: isLibreDirty(),
    plan: isP7Dirty(),
  });

  const clearDirtyForTab = (tab: HubDocumentType) => {
    switch (tab) {
      case 'ordonnance':
        setPrescriptionDirty(false);
        break;
      case 'certificat':
        setCertificateDirty(false);
        break;
      case 'devis':
      case 'honoraires':
        useAccountingStore.getState().reset();
        break;
      case 'echeancier':
        setInstallmentDirty(false);
        break;
      case 'libre':
        setLibreDirty(false);
        break;
      case 'plan':
        setP7Dirty(false);
        break;
      default:
        break;
    }
  };

  const syncDocumentTab = (tab: HubDocumentType) => {
    if (searchParams.get('documentTab') === tab) return;
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set('documentTab', tab);
    setSearchParams(nextParams, { replace: true });
  };

  const commitTabChange = (newTab: HubDocumentType, source: TabChangeSource) => {
    setActiveTab(newTab);
    if (source === 'ui') syncDocumentTab(newTab);
  };

  const handleTabChange = (newTab: HubDocumentType, source: TabChangeSource = 'ui') => {
    if (newTab === activeTab) return;

    // P3 → P4 conserve les actes mais repart d'un contexte financier neutre.
    if (activeTab === 'devis' && newTab === 'honoraires') {
      resetHonorairesFinancialDraft();
      commitTabChange(newTab, source);
      return;
    }

    if (shouldGuardDocumentTabTransition(activeTab, newTab, dirtySnapshot())) {
      setPendingTab(newTab);
      setPendingTabSource(source);
      return;
    }

    commitTabChange(newTab, source);
  };

  useEffect(() => {
    const nextTab = searchParams.get('documentTab');
    if (isHubDocumentType(nextTab) && nextTab !== activeTab) {
      handleTabChange(nextTab, 'url');
    }
  // Deliberately reacts only to URL/search changes; current dirty state is read at transition time.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const cancelPendingTab = () => {
    if (pendingTabSource === 'url') {
      const nextParams = new URLSearchParams(searchParams);
      nextParams.set('documentTab', activeTab);
      setSearchParams(nextParams, { replace: true });
    }
    setPendingTab(null);
    setPendingTabSource('ui');
  };

  const confirmPendingTab = () => {
    if (!pendingTab) return;
    const nextTab = pendingTab;
    const source = pendingTabSource;
    clearDirtyForTab(activeTab);
    setPendingTab(null);
    setPendingTabSource('ui');
    commitTabChange(nextTab, source);
  };

  // Garde fermeture navigateur pour P3/P4 ; les autres pages publient aussi leur dirty-state
  // au niveau de la frontière patient T1.
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if ((activeTab === 'devis' || activeTab === 'honoraires') && items.some(i => i.description.trim())) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [activeTab, items]);

  // --- ÉTATS UI ---
  const [selectedTeethFromOdontogram, setSelectedTeethFromOdontogram] = useState<SelectedSurfaceData[]>([]);
  const [echeancierPayload, setEcheancierPayload] = useState<any>(null);

  // --- HOOK GÉNÉRATEUR (Phases 1, 3, 4) ---
  const generatorParams = useMemo(() => ({
    patientId, patientDetails, activeTab, drugs, certifType, certifDays, certifStartDate, certifCustomMotif,
    items, paymentMode,
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

  // --- HYDRATATION ---
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
  }, [editData]);

  // --- DATA FETCHING ---
  useEffect(() => {
    if (!patientId) {
      setPatientDetails(null);
      return;
    }

    let cancelled = false;
    setPatientDetails(null);

    api.get(`/patients/${patientId}`)
      .then(res => {
        if (!cancelled) setPatientDetails(res.data);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error('DocumentHub: patient fetch failed', err);
        const status = err.response?.status;
        if (status === 403 || status === 404) {
          setPatientDetails(null);
          toast.error("Dossier patient introuvable ou accès non autorisé.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [patientId]);

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
    if (sideStudioType !== 'PREVIEW') return;
    const timer = setTimeout(() => generator.handleGenerate(false, false, true), 1200);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    sideStudioType, drugs, items, certifType, certifDays, certifStartDate, paymentMode,
    libreTitle, libreContent, docDate, activeTab,
    generator.handleGenerate
  ]);

  useEffect(() => {
    if (activeTab === 'certificat' || activeTab === 'libre') {
      setSideStudioType('PREVIEW');
    }
  }, [activeTab]);

  return (
    <div className="relative w-full h-full overflow-hidden flex animate-in fade-in duration-700">

      {/* ESPACE DE TRAVAIL */}
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

        <div data-tour="document-hub-content" className="flex-1 flex flex-col p-2 min-h-min shrink-0">
          {activeTab === 'plan' && (
            <TreatmentPlanStudio
              patientId={Number(patientId)}
              onConvertToQuote={(allActs) => {
                const newItems = convertPlanActsToQuoteItems(allActs);
                setItems(prev => [...prev, ...newItems]);
                setP7Dirty(false);
                commitTabChange('devis', 'ui');
              }}
            />
          )}

          {activeTab === 'ordonnance' && (
            <>
            <div className="flex items-center gap-2 mb-3 px-1">
              <button
                type="button"
                onClick={() => setShowLegalAnnotations(v => !v)}
                className={cn(
                  "relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none",
                  showLegalAnnotations ? "bg-primary" : "bg-slate-200"
                )}
                role="switch"
                aria-checked={showLegalAnnotations}
                aria-label="Afficher les mentions légales de radioprotection"
              >
                <span className={cn(
                  "pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200",
                  showLegalAnnotations ? "translate-x-4" : "translate-x-0"
                )} />
              </button>
              <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">
                Mentions légales (Radioprotection)
              </span>
            </div>
            <PrescriptionAgenticStudio
              patientId={patientId || '0'}
              drugs={drugs}
              setDrugs={setDrugs}
              onUpdateDrug={(id, field, val) => {
                setDrugs(prev => prev.map(d => d.id === id ? { ...d, [field]: val } : d));
                generator.setHasChanges(true);
              }}
              onRemoveDrug={(id) => {
                setDrugs(drugs.filter(d => d.id !== id));
                generator.setHasChanges(true);
              }}
              onAddDrug={() => setDrugs([...drugs, { id: Date.now(), name: '', dosage: '', forme: 'Comprimés', posologie: '', type: 'MEDICAMENT' }])}
              validationErrors={generator.validationErrors}
              onSaveHabit={(context, drugs) => generator.handleSavePreference({ protocol_name: context }, drugs)}
              hasChanges={generator.hasChanges}
              coherenceWarnings={generator.coherenceWarnings}
            />
            </>
          )}

          {activeTab === 'certificat' && (
            <CertificateForm
              patientId={patientId || ""}
              certifType={certifType} setCertifType={setCertifType}
              certifDays={certifDays} setCertifDays={setCertifDays}
              docDate={docDate}
              certifStartDate={certifStartDate} setCertifStartDate={setCertifStartDate}
              certifCustomMotif={certifCustomMotif} setCertifCustomMotif={setCertifCustomMotif}
            />
          )}

          {activeTab === 'libre' && (
            <LibreForm
              title={libreTitle}
              setTitle={setLibreTitle}
              content={libreContent} setContent={setLibreContent}
              customPatient={libreCustomPatient} setCustomPatient={setLibreCustomPatient}
              customDate={libreCustomDate} setCustomDate={setLibreCustomDate}
              hideHeader={libreHideHeader} setHideHeader={setLibreHideHeader}
              pageSize={librePageSize} setPageSize={setLibrePageSize}
              alignment={libreAlignment} setAlignment={setLibreAlignment}
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

      {/* MODALE — Garde changement d'onglet */}
      {pendingTab && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={cancelPendingTab} />
          <div
            className="relative bg-white dark:bg-slate-950 rounded-[2rem] p-8 w-80 shadow-2xl flex flex-col gap-5"
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-navigation-warning-title"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center text-amber-500 text-lg">⚠️</div>
              <div>
                <h3 id="document-navigation-warning-title" className="text-sm font-black text-slate-800 dark:text-white">Document en cours</h3>
                <p className="text-xs text-slate-400 font-bold mt-0.5">Le brouillon non enregistré sera abandonné.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={cancelPendingTab}
                className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900 transition-all"
              >Annuler</button>
              <button
                type="button"
                onClick={confirmPendingTab}
                className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest bg-slate-800 text-white hover:bg-primary transition-all"
                style={{ '--tw-bg-primary': 'var(--primary)' } as React.CSSProperties}
              >Continuer</button>
            </div>
          </div>
        </div>
      )}

      {/* MODALE — Doublon détecté (remplace window.confirm) */}
      {generator.showDuplicateModal && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={generator.cancelDuplicate} />
          <div
            className="relative bg-white dark:bg-slate-950 rounded-[2rem] p-8 w-80 shadow-2xl flex flex-col gap-5"
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-duplicate-warning-title"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-50 rounded-xl flex items-center justify-center text-orange-500 text-lg">⚠️</div>
              <div>
                <h3 id="document-duplicate-warning-title" className="text-sm font-black text-slate-800 dark:text-white">Doublon détecté</h3>
                <p className="text-xs text-slate-400 font-bold mt-0.5">Un document similaire existe déjà pour ce patient.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={generator.cancelDuplicate}
                className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900 transition-all"
              >Annuler</button>
              <button
                type="button"
                onClick={generator.confirmDuplicate}
                className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest bg-orange-500 text-white hover:bg-orange-600 transition-all"
              >Forcer</button>
            </div>
          </div>
        </div>
      )}

      {/* APERÇU RESPONSIVE */}
      <AnimatePresence>
        {sideStudioType === 'PREVIEW' && (
          <motion.div
            initial={{ x: 600, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 600, opacity: 0 }}
            className="fixed inset-2 z-[11000] drop-shadow-2xl xl:left-auto xl:w-[550px]"
          >
            <LivePreview
              pdfUrl={generator.pdfUrl}
              loading={generator.loading}
              onClose={() => setSideStudioType('NONE')}
              onRefresh={() => generator.handleGenerate(false, false, true)}
              title={{
                'plan': 'Stratégie Clinique',
                'ordonnance': 'Ordonnance',
                'certificat': 'Certificat',
                'devis': 'Devis Quantitatif',
                'honoraires': 'Note d\'Honoraires',
                'echeancier': 'Échéancier',
                'libre': 'Document Libre'
              }[activeTab] || activeTab.toUpperCase()}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};