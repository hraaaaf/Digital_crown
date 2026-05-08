import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Brain } from 'lucide-react';
import { api } from '../../services/api';

// Composants Modulaires
import { StudioHeader } from './DocumentStudio/StudioHeader';
import { StudioTabs } from './DocumentStudio/StudioTabs';
import { StudioFooter } from './DocumentStudio/StudioFooter';
import { LivePreview } from './DocumentStudio/LivePreview';
import { useDocumentGenerator } from './DocumentStudio/useDocumentGenerator';

// Formulaires
import { PrescriptionAgenticStudio, type DrugItem } from './DocumentStudio/Forms/PrescriptionAgenticStudio';
import { CertificateForm } from './DocumentStudio/Forms/CertificateForm';
import { LibreForm } from './DocumentStudio/Forms/LibreForm';
import { AccountingStudio } from './AccountingStudio';

// Types
import { type SelectedSurfaceData, TREATMENT_TEMPLATES } from '../../components/odontogram/types';

type DocumentType = 'ordonnance' | 'certificat' | 'devis' | 'honoraires' | 'libre' | 'ai';
type PaymentMode = 'Espèces' | 'Chèque' | 'TPE' | 'Virement';

interface PriceItem {
  id: number;
  description: string;
  dent: string;
  price: number;
  toothNumbers?: number[];
  _odontogramKey?: string;
}

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

export const DocumentHub: React.FC<DocumentHubProps> = ({ patientId, patientName, editData }) => {
  // --- ÉTATS GÉNÉRAUX ---
  const [activeTab, setActiveTab] = useState<DocumentType>('ordonnance');
  const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);
  const [patientDetails, setPatientDetails] = useState<PatientDetails | null>(null);
  const [sideStudioType, setSideStudioType] = useState<'NONE' | 'PREVIEW'>('NONE');

  // --- ÉTATS IA ---
  const [smartSuggestion, setSmartSuggestion] = useState<{ rationale: string; drugs: DrugItem[] } | null>(null);

  // --- ÉTATS FORMULAIRES ---
  const [drugs, setDrugs] = useState<DrugItem[]>([{ id: 1, name: '', dosage: '', forme: '', posologie: '', type: 'MEDICAMENT' }]);
  const [certifType, setCertifType] = useState('Repos médical');
  const [certifDays, setCertifDays] = useState(5);
  const [certifCustomMotif, setCertifCustomMotif] = useState('');
  const [items, setItems] = useState<PriceItem[]>([]);
  const [paymentMode, setPaymentMode] = useState<PaymentMode>('Espèces');
  const [installments, setInstallments] = useState<{ id: number; date: string; amount: number; label: string }[]>([]);

  // --- ÉTATS DOCUMENT LIBRE ---
  const [libreTitle, setLibreTitle] = useState('Note Médicale');
  const [libreContent, setLibreContent] = useState('');
  const [libreCustomPatient, setLibreCustomPatient] = useState('');
  const [libreCustomDate, setLibreCustomDate] = useState('');
  const [libreHideHeader, setLibreHideHeader] = useState(false);
  const [librePageSize, setLibrePageSize] = useState<'A5' | 'A4'>('A5');
  const [libreAlignment, setLibreAlignment] = useState<'left' | 'center' | 'right' | 'justify'>('justify');

  // --- GARDES NAVIGATION ---
  const [pendingTab, setPendingTab] = useState<DocumentType | null>(null);

  // Garde sur changement d'onglet (1.3)
  const handleTabChange = (newTab: DocumentType) => {
    const hasUnsaved = (activeTab === 'devis' || activeTab === 'honoraires') &&
      items.some(i => i.description.trim()) && newTab !== activeTab;
    if (hasUnsaved) {
      setPendingTab(newTab);
    } else {
      setActiveTab(newTab);
    }
  };

  // Garde fermeture navigateur (1.6)
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
  const [showOdontoPanoramique, setShowOdontoPanoramique] = useState(true);
  const [selectedTeethFromOdontogram, setSelectedTeethFromOdontogram] = useState<SelectedSurfaceData[]>([]);
  const [odontogramMode, setOdontogramMode] = useState<'individual' | 'group' | 'ortho'>('individual');
  const [groupSelectedTeeth, setGroupSelectedTeeth] = useState<number[]>([]);
  const [groupTreatmentName, setGroupTreatmentName] = useState('');
  const [groupTreatmentPrice, setGroupTreatmentPrice] = useState<number | ''>('');
  const [actSuggestions, setActSuggestions] = useState<{ id: string | number; name: string; base_price: number; category: string; isLocal?: boolean }[]>([]);
  const [activeActSearchId, setActiveActSearchId] = useState<number | null>(null);

  // --- HOOK GÉNÉRATEUR (Phases 1, 3, 4) ---
  const generator = useDocumentGenerator({
    patientId, patientDetails, activeTab, drugs, certifType, certifDays, certifCustomMotif,
    items, paymentMode, libreTitle, libreContent, libreCustomPatient, libreCustomDate,
    libreHideHeader, librePageSize, libreAlignment, docDate, selectedTeethFromOdontogram, smartSuggestion,
    installments,
  });

  // --- HYDRATATION ---
  useEffect(() => {
    if (editData?.clinical_data) {
      const type = editData.type.toLowerCase();
      const d = editData.clinical_data as GenericClinicalData;
      if (type === 'ordonnance') {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setActiveTab('ordonnance');
        if (d.medications) setDrugs(d.medications.map((m: { nom?: string; dosage?: string; forme?: string; posologie?: string; type?: 'MEDICAMENT' | 'EXAMEN' }, idx: number) => ({
          id: Date.now() + idx, name: m.nom || '', dosage: m.dosage || '',
          forme: m.forme || 'Sachets', posologie: m.posologie || '',
          type: m.type || 'MEDICAMENT'
        })));
      } else if (type === 'certificat') {
        setActiveTab('certificat');
        setCertifType(d.reason || 'Certificat de Repos');
        setCertifDays(d.days || 0);
      } else if (type === 'libre') {
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

  const handleTeethFromOdontogram = useCallback((teeth: SelectedSurfaceData[]) => {
    setSelectedTeethFromOdontogram(teeth);
    setItems(prev => {
      const activeKeys = new Set(teeth.flatMap(t => t.treatments.map(tr => `${t.toothNumber}::${tr.id}`)));
      const surviving = prev.filter(i => !i._odontogramKey || activeKeys.has(i._odontogramKey));
      const existingKeys = new Set(surviving.map(i => i._odontogramKey).filter(Boolean));
      const newItems: PriceItem[] = [];
      teeth.forEach(t => {
        t.treatments.forEach(tr => {
          const k = `${t.toothNumber}::${tr.id}`;
          if (!existingKeys.has(k)) {
            newItems.push({
              id: Date.now() + Math.random(),
              description: tr.name, dent: t.toothNumber.toString(),
              price: tr.price, toothNumbers: [t.toothNumber], _odontogramKey: k,
            });
          }
        });
      });
      return [...surviving, ...newItems as PriceItem[]];
    });
  }, []);

  // --- DATA FETCHING ---
  useEffect(() => {
    if (!patientId) return;
    api.get(`/patients/${patientId}`).then(res => setPatientDetails(res.data)).catch(console.error);
    if (activeTab === 'ordonnance') {
      api.get(`/prescriptions/smart-suggest/${patientId}`)
        .then(res => setSmartSuggestion(res.data))
        .catch(console.error);
    }
  }, [patientId, activeTab]);

  // --- AUTO-PREVIEW ---
  useEffect(() => {
    if (sideStudioType !== 'PREVIEW' || activeTab === 'ai') return;
    const timer = setTimeout(() => generator.handleGenerate(false, false, true), 1200);
    return () => clearTimeout(timer);
  }, [sideStudioType, drugs, items, certifType, certifDays, paymentMode, libreTitle, libreContent, docDate, activeTab, generator]);

  return (
    <div className="relative w-full h-full overflow-hidden flex animate-in fade-in duration-700">

      {/* ESPACE DE TRAVAIL */}
      <div className="flex-1 h-full flex flex-col px-8 pt-6 pb-2 gap-3 overflow-y-auto">

        <StudioHeader
          patientName={patientName}
          docDate={docDate}
          onDateChange={setDocDate}
          activeTab={activeTab}
          sideStudioType={sideStudioType}
          onTogglePreview={() => setSideStudioType(prev => prev === 'PREVIEW' ? 'NONE' : 'PREVIEW')}
          showOdontoPanoramique={showOdontoPanoramique}
          onToggleOdonto={() => setShowOdontoPanoramique(v => !v)}
        />

        <StudioTabs activeTab={activeTab} onTabChange={handleTabChange} />

        <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
          {activeTab === 'ordonnance' && (
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
          )}

          {activeTab === 'certificat' && (
            <CertificateForm
              patientId={patientId || ""}
              certifType={certifType} setCertifType={setCertifType}
              certifDays={certifDays} setCertifDays={setCertifDays}
              certifCustomMotif={certifCustomMotif} setCertifCustomMotif={setCertifCustomMotif}
            />
          )}

          {activeTab === 'libre' && (
            <LibreForm
              title={libreTitle} setTitle={setLibreTitle}
              content={libreContent} setContent={setLibreContent}
              customPatient={libreCustomPatient} setCustomPatient={setLibreCustomPatient}
              customDate={libreCustomDate} setCustomDate={setLibreCustomDate}
              hideHeader={libreHideHeader} setHideHeader={setLibreHideHeader}
              pageSize={librePageSize} setPageSize={setLibrePageSize}
              alignment={libreAlignment} setAlignment={setLibreAlignment}
              validationErrors={generator.validationErrors}
            />
          )}

          {(activeTab === 'devis' || activeTab === 'honoraires') && (
            <AccountingStudio
              isDevis={activeTab === 'devis'}
              patientId={patientId || '0'} items={items} setItems={setItems}
              coherenceWarnings={generator.coherenceWarnings}
              paymentMode={paymentMode} setPaymentMode={(m) => setPaymentMode(m as PaymentMode)}
              installments={installments} setInstallments={setInstallments}
              showOdontoPanoramique={showOdontoPanoramique} odontogramMode={odontogramMode} setOdontogramMode={setOdontogramMode}
              groupSelectedTeeth={groupSelectedTeeth}
              handleToothDirectClick={(n) => setGroupSelectedTeeth(prev => prev.includes(n) ? prev.filter(x => x !== n) : [...prev, n])}
              selectTeethGroup={(g) => {
                const max = [11, 12, 13, 14, 15, 16, 17, 18, 21, 22, 23, 24, 25, 26, 27, 28];
                const mand = [31, 32, 33, 34, 35, 36, 37, 38, 41, 42, 43, 44, 45, 46, 47, 48];
                if (g === 'all') setGroupSelectedTeeth([...max, ...mand]);
                else if (g === 'maxillaire') setGroupSelectedTeeth(max);
                else if (g === 'mandibule') setGroupSelectedTeeth(mand);
                else setGroupSelectedTeeth([]);
              }}
              groupTreatmentName={groupTreatmentName} setGroupTreatmentName={setGroupTreatmentName}
              groupTreatmentPrice={groupTreatmentPrice} setGroupTreatmentPrice={setGroupTreatmentPrice}
              applyGroupTreatment={() => {
                if (!groupTreatmentName.trim() || groupSelectedTeeth.length === 0) return;
                const sorted = [...groupSelectedTeeth].sort((a, b) => a - b);
                setItems(prev => [...prev, { id: Date.now(), description: groupTreatmentName, dent: sorted.join('-'), price: Number(groupTreatmentPrice) || 0, toothNumbers: sorted }]);
                setGroupSelectedTeeth([]);
                setGroupTreatmentName('');
                setGroupTreatmentPrice('');
              }}
              handleTeethFromOdontogram={handleTeethFromOdontogram}
              addEmptyRow={() => setItems([...items, { id: Date.now(), description: '', dent: '0', price: 0 }])}
              removeItem={(id) => setItems(items.filter(i => i.id !== id))}
              updateItem={(id, f, v) => setItems(items.map(i => i.id === id ? { ...i, [f]: f === 'price' ? Number(v) : v } : i))}
              handleActSearch={async (q, id) => {
                setItems(items.map(i => i.id === id ? { ...i, description: q } : i));
                if (q.length < 2) { setActSuggestions([]); setActiveActSearchId(null); return; }
                setActiveActSearchId(id);
                
                // 1. Search in Treatment Templates (Odontogram acts)
                const localMatches = TREATMENT_TEMPLATES.filter((t: { name: string; category: string; id: string }) => 
                  t.name.toLowerCase().includes(q.toLowerCase()) || 
                  t.category.toLowerCase().includes(q.toLowerCase())
                ).map((t: { id: string; name: string; category: string }) => ({ id: t.id, name: t.name, base_price: 0, category: t.category, isLocal: true }));

                // 2. Search in API
                try {
                  const res = await api.get(`/actes/catalog/search?q=${q}`);
                  const apiMatches = res.data || [];
                  
                  // Merge and deduplicate by name
                  const merged: { id: string | number; name: string; base_price: number; category: string; isLocal?: boolean }[] = [...localMatches];
                  apiMatches.forEach((a: { name: string; base_price: number; category: string; id: string | number }) => {
                    if (!merged.find(m => m.name.toLowerCase() === a.name.toLowerCase())) {
                      merged.push({ ...a, isLocal: false });
                    }
                  });
                  
                  setActSuggestions(merged.slice(0, 10));
                } catch {
                  setActSuggestions(localMatches.slice(0, 10));
                }
              }}
              activeActSearchId={activeActSearchId}
              setActiveActSearchId={setActiveActSearchId}
              actSuggestions={actSuggestions}
              applyActSuggestion={(id, act) => {
                setItems(items.map(i => i.id === id ? { ...i, description: act.name, price: act.base_price || 0 } : i));
                setActSuggestions([]);
                setActiveActSearchId(null);
              }}
              validationErrors={generator.validationErrors}
            />
          )}

          {activeTab === 'ai' && (
            <div className="p-8 bg-slate-50/50 rounded-[2.5rem] border border-slate-200">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 bg-primary/10 text-primary rounded-2xl flex items-center justify-center">
                  <Brain size={24} />
                </div>
                <h3 className="text-2xl font-black text-slate-800">Diagnostic IA Expert</h3>
              </div>
              {generator.aiReport ? (
                <div className="prose prose-slate max-w-none prose-p:font-medium prose-headings:font-black">
                  <ReactMarkdown>{generator.aiReport}</ReactMarkdown>
                </div>
              ) : (
                <div className="text-center py-20">
                  <p className="text-slate-400 font-bold">L'analyse IA scannera le dossier complet du patient pour suggérer un plan de traitement.</p>
                </div>
              )}
            </div>
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
          aiReport={generator.aiReport}
          onGenerateAI={generator.handleGenerateAI}
          loadingAi={generator.loadingAi}
          total={items.reduce((acc, i) => acc + (Number(i.price) || 0), 0)}
        />
      </div>

      {/* MODALE — Garde changement d'onglet (1.3) */}
      {pendingTab && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={() => setPendingTab(null)} />
          <div className="relative bg-white rounded-[2rem] p-8 w-80 shadow-2xl flex flex-col gap-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center text-amber-500 text-lg">⚠️</div>
              <div>
                <h3 className="text-sm font-black text-slate-800">Document en cours</h3>
                <p className="text-xs text-slate-400 font-bold mt-0.5">Les actes saisis seront effacés.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setPendingTab(null)}
                className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest border border-slate-200 text-slate-500 hover:bg-slate-50 transition-all"
              >Annuler</button>
              <button
                onClick={() => { setActiveTab(pendingTab); setPendingTab(null); }}
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
          <div className="relative bg-white rounded-[2rem] p-8 w-80 shadow-2xl flex flex-col gap-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-50 rounded-xl flex items-center justify-center text-orange-500 text-lg">⚠️</div>
              <div>
                <h3 className="text-sm font-black text-slate-800">Doublon détecté</h3>
                <p className="text-xs text-slate-400 font-bold mt-0.5">Un document similaire existe déjà pour ce patient.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={generator.cancelDuplicate}
                className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest border border-slate-200 text-slate-500 hover:bg-slate-50 transition-all"
              >Annuler</button>
              <button
                onClick={generator.confirmDuplicate}
                className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest bg-orange-500 text-white hover:bg-orange-600 transition-all"
              >Forcer</button>
            </div>
          </div>
        </div>
      )}

      {/* APERÇU LATÉRAL */}
      <AnimatePresence>
        {sideStudioType === 'PREVIEW' && (
          <motion.div 
            initial={{ x: 600, opacity: 0 }} 
            animate={{ x: 0, opacity: 1 }} 
            exit={{ x: 600, opacity: 0 }} 
            className="fixed right-6 top-6 bottom-6 w-[550px] z-[200] drop-shadow-2xl"
          >
            <LivePreview
              pdfUrl={generator.pdfUrl}
              loading={generator.loading}
              onClose={() => setSideStudioType('NONE')}
              title={{
                'ordonnance': 'Ordonnance',
                'certificat': 'Certificat',
                'devis': 'Devis Quantitatif',
                'honoraires': 'Note d\'Honoraires',
                'libre': 'Document Libre',
                'ai': 'Rapport IA'
              }[activeTab] || activeTab.toUpperCase()}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
