import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
import type { Insight } from './DocumentStudio/EliteAssistant';
import { useDocumentGenerator } from './DocumentStudio/useDocumentGenerator';
import { type SelectedSurfaceData } from '../../components/odontogram/types';
import { PriceBrain } from '../../components/odontogram/PriceBrain';
import { useCatalogStore } from './Settings/hooks/useCatalogStore';

type DocumentType = 'plan' | 'ordonnance' | 'certificat' | 'devis' | 'honoraires' | 'echeancier' | 'libre';
type PaymentMode = 'Espèces' | 'Chèque' | 'TPE' | 'Virement';

interface PriceItem {
  id: number;
  description: string;
  dent: string;
  price: number;
  toothNumbers?: number[];
  _odontogramKey?: string;
  category?: string;
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
  antecedents_medicaux?: string;
  assurance?: string;
}

export const DocumentHub: React.FC<DocumentHubProps> = ({ patientId, patientName, editData }) => {
  // --- ÉTATS GÉNÉRAUX ---
  const [activeTab, setActiveTab] = useState<DocumentType>('ordonnance');
  const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);
  const [patientDetails, setPatientDetails] = useState<PatientDetails | null>(null);
  const [sideStudioType, setSideStudioType] = useState<'NONE' | 'PREVIEW'>('NONE');

  // --- ÉTATS IA ---
  const [smartSuggestion, setSmartSuggestion] = useState<{ rationale: string; drugs: DrugItem[] } | null>(null);

  // --- CATALOGUE ---
  const { specialties, fetchCatalog } = useCatalogStore();
  const TREATMENT_TEMPLATES = useMemo(() => {
    return specialties.flatMap(s => s.acts.map(act => ({
      id: act.id.toString(),
      name: act.name,
      category: s.name,
      base_price: act.base_price,
    })));
  }, [specialties]);

  useEffect(() => {
    if (specialties.length === 0) {
      fetchCatalog();
    }
  }, [fetchCatalog, specialties.length]);

  // --- ÉTATS FORMULAIRES ---
  const [drugs, setDrugs] = useState<DrugItem[]>([{ id: 1, name: '', dosage: '', forme: '', posologie: '', type: 'MEDICAMENT' }]);
  const [certifType, setCertifType] = useState('Repos médical');
  const [certifDays, setCertifDays] = useState(5);
  const [certifCustomMotif, setCertifCustomMotif] = useState('');
  const [items, setItems] = useState<PriceItem[]>([]);
  const [paymentMode, setPaymentMode] = useState<PaymentMode>('Espèces');
  const [installments, setInstallments] = useState<{ id: number; date: string; amount: number; label: string }[]>([]);
  const [isAccounted, setIsAccounted] = useState(true);
  const [paymentStatus, setPaymentStatus] = useState('EN_ATTENTE');
  const [isGlobalNote, setIsGlobalNote] = useState(false);

  // --- PERSISTENCE ECHEANCES ---
  useEffect(() => {
    if (patientId && patientId !== '0') {
      api.get(`/installments/patient/${patientId}`)
        .then(res => {
          const plans = res.data;
          if (plans && plans.length > 0) {
            const latestPlan = plans[plans.length - 1];
            if (latestPlan && latestPlan.installments && latestPlan.installments.length > 0) {
              const loadedInstallments = latestPlan.installments.map((inst: any) => ({
                id: inst.id,
                date: inst.due_date ? inst.due_date.split('T')[0] : new Date().toISOString().split('T')[0],
                amount: inst.amount,
                label: inst.label || 'Versement'
              }));
              setInstallments(loadedInstallments);
            }
          }
        })
        .catch(console.error);
    }
  }, [patientId]);

  // --- ÉTATS DOCUMENT LIBRE ---
  const [libreTitle, setLibreTitle] = useState('Note Médicale');
  const [libreContent, setLibreContent] = useState('');
  const [libreCustomPatient, setLibreCustomPatient] = useState('');
  const [libreCustomDate, setLibreCustomDate] = useState('');
  const [libreHideHeader, setLibreHideHeader] = useState(false);
  const [librePageSize, setLibrePageSize] = useState<'A5' | 'A4'>('A5');
  const [libreAlignment, setLibreAlignment] = useState<'left' | 'center' | 'right' | 'justify'>('justify');
  const [insights, setInsights] = useState<Insight[]>([]);

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
  const generatorParams = useMemo(() => ({
    patientId, patientDetails, activeTab, drugs, certifType, certifDays, certifCustomMotif,
    items, paymentMode, libreTitle, libreContent, libreCustomPatient, libreCustomDate,
    libreHideHeader, librePageSize, libreAlignment, docDate, selectedTeethFromOdontogram, smartSuggestion,
    installments, isAccounted, paymentStatus, isGlobalNote,
  }), [
    patientId, patientDetails, activeTab, drugs, certifType, certifDays, certifCustomMotif,
    items, paymentMode, libreTitle, libreContent, libreCustomPatient, libreCustomDate,
    libreHideHeader, librePageSize, libreAlignment, docDate, selectedTeethFromOdontogram, smartSuggestion,
    installments, isAccounted, paymentStatus, isGlobalNote,
  ]);

  // --- INTELLIGENCE SCOPE ---
  const isSurgical = useMemo(() => items.some(i => 
    i.description.toLowerCase().includes('extraction') || 
    i.description.toLowerCase().includes('implant') || 
    i.description.toLowerCase().includes('chirurgie')
  ), [items]);

  const hasDrugs = useMemo(() => drugs.length > 0, [drugs]);

  // --- BRAIN ENGINE : INTELLIGENCE PROACTIVE ---
  useEffect(() => {
    // 1. Détection des actes pour suggestions croisées (Bundles)
    const currentActNames = items.map(i => i.description).filter(Boolean);
    if (currentActNames.length > 0) {
      const timer = setTimeout(() => {
        api.post('/actes/catalog/bundles', { act_names: currentActNames })
          .then(res => {
            const bundles = res.data as { name: string; price: number; category: string }[];
            bundles.forEach(b => {
              const id = `bundle-${b.name}`;
              if (!insights.find(ins => ins.id === id)) {
                setInsights(prev => [{
                  id: id,
                  type: 'suggestion',
                  title: 'Acte Complémentaire',
                  content: `Pour un traitement complet, l'assistant suggère d'ajouter : ${b.name}.`,
                  actionLabel: `Ajouter (+${b.price} MAD)`,
                  onAction: () => {
                    setItems(prev => [...prev, { id: Date.now(), description: b.name, price: b.price, dent: '0', category: b.category }]);
                    setInsights(prev => prev.filter(i => i.id !== id));
                  }
                }, ...prev]);
              }
            });
          })
          .catch(console.error);
      }, 500); // Debounce pour éviter trop d'appels
      return () => clearTimeout(timer);
    }

    // 2. Intelligence Elite : Détection des Protocoles Oubliés
    if (isSurgical && !hasDrugs && !insights.find(ins => ins.id === 'ins-missing-protocol')) {
       
      setInsights(prev => [{
        id: 'ins-missing-protocol',
        type: 'safety',
        title: 'Protocole Post-Op Manquant',
        content: "Détection d'un acte chirurgical sans ordonnance associée. Souhaitez-vous générer un protocole antalgique/antibiotique ?",
        actionLabel: 'Générer Protocole',
        onAction: () => { setActiveTab('ordonnance'); }
      }, ...prev]);
    }

    // 3. Profil Patient Premium (Analyse sans redondance)
    if (patientDetails && !insights.find(ins => ins.id === 'ins-platinum')) {
       setInsights(prev => [{
         id: 'ins-platinum',
         type: 'habit',
         title: 'Standard de Soins Elite',
         content: `${patientDetails.prenom} bénéficie du programme Platinum. Un compte-rendu détaillé est recommandé après cette séance.`,
         actionLabel: 'Préparer CR',
         onAction: () => { setActiveTab('libre'); }
       }, ...prev]);
    }

    // 4. GHOST COMPLICATIONS (Bouclier de Sécurité Médicolégal)
    if (patientDetails?.antecedents_medicaux) {
      const ant = patientDetails.antecedents_medicaux.toLowerCase();
      const currentActNames = items.map(i => i.description.toLowerCase());
      const hasSurgery = currentActNames.some(a => a.includes('extraction') || a.includes('implant') || a.includes('chirurgie') || a.includes('lambeau'));
      const hasRadio = currentActNames.some(a => a.includes('radio') || a.includes('panoramique') || a.includes('cbct') || a.includes('cone beam'));

      const complications: any[] = [];

      if (hasSurgery && (ant.includes('sintrom') || ant.includes('anticoagulant') || ant.includes('kardegic') || ant.includes('aspirine'))) {
        complications.push({
          id: 'ghost-comp-bleeding', type: 'safety', title: '⚠️ Risque Hémorragique',
          content: "Patient sous anticoagulants. Risque élevé d'hémorragie post-opératoire. Avez-vous le bilan d'hémostase (INR) ?"
        });
      }
      
      if (hasSurgery && (ant.includes('diabète') || ant.includes('diabete'))) {
        complications.push({
          id: 'ghost-comp-diabetes', type: 'safety', title: '⚠️ Patient Diabétique',
          content: "Risque accru d'infection et de retard de cicatrisation osseuse. Couverture antibiotique stricte recommandée."
        });
      }

      if (hasSurgery && (ant.includes('bisphosphonate') || ant.includes('prolia') || ant.includes('xgeva'))) {
        complications.push({
          id: 'ghost-comp-mronj', type: 'safety', title: '🚨 DANGER : Ostéochimionécrose',
          content: "Antécédent de bisphosphonates. Risque majeur d'ostéochimionécrose des mâchoires (MRONJ). Prudence extrême."
        });
      }

      if (hasRadio && (ant.includes('enceinte') || ant.includes('grossesse'))) {
        complications.push({
          id: 'ghost-comp-pregnancy', type: 'safety', title: '⚠️ Grossesse',
          content: "Radiographies contre-indiquées (surtout T1). Utiliser un tablier de plomb si urgence absolue."
        });
      }

      complications.forEach(comp => {
        if (!insights.find(ins => ins.id === comp.id)) {
          setInsights(prev => [comp, ...prev]);
        }
      });
    }

    // 5. GHOST MUTUELLE (Optimiseur de Plafond Fin d'Année)
    // Les mutuelles privées ont un plafond annuel. CNSS/CNOPS ont un plafond prothèse (3000 MAD/2 ans).
    if (patientDetails?.assurance && patientDetails.assurance !== 'AUCUNE') {
      const currentMonth = new Date().getMonth(); // 0 = Jan, 11 = Dec
      const isEndOfYear = currentMonth >= 9; // Octobre à Décembre
      const currentActNames = items.map(i => i.description.toLowerCase());
      const hasProsthesis = currentActNames.some(a => a.includes('couronne') || a.includes('bridge') || a.includes('inlay') || a.includes('prothèse') || a.includes('facette'));
      const totalAmount = items.reduce((sum, item: any) => sum + ((item.price || item.montant || 0) * (item.toothNumbers?.length || item.dents?.length || 1)), 0);

      // Si le montant global est lourd et contient de la prothèse
      if (isEndOfYear && hasProsthesis && totalAmount >= 3000) {
        if (!insights.find(ins => ins.id === 'ghost-mutuelle-plafond')) {
          setInsights(prev => [{
            id: 'ghost-mutuelle-plafond',
            type: 'habit',
            title: '💡 Ghost Mutuelle : Optimisation',
            content: `Le plafond prothétique de la ${patientDetails.assurance} se renouvelle bientôt. Séparer ce devis de ${totalAmount} MAD (Décembre / Janvier) maximisera le remboursement du patient !`,
            actionLabel: 'Scinder le Devis',
            onAction: () => {
              window.dispatchEvent(new CustomEvent('toast-alert', { detail: { type: 'success', message: "Ghost Mutuelle a scindé le devis en deux phases annuelles." }}));
            }
          }, ...prev]);
        }
      }
    }

    // 6. Sécurité Clinique Médicamenteuse : Double-contrôle CRE, DDI et Omissions
    const drugNames = drugs.map(d => d.name).filter(Boolean);
    if (drugNames.length > 0 && patientId) {
      const timer = setTimeout(() => {
        api.post('/prescriptions/safety/check', { patient_id: patientId, drug_names: drugNames })
          .then(res => {
            const warnings = res.data as { type: string; severity: string; message: string; drug: string }[];
            warnings.forEach(w => {
              const id = `safety-${w.drug}`;
              if (!insights.find(ins => ins.id === id)) {
                setInsights(prev => [{
                  id: id,
                  type: w.type === 'omission' ? 'suggestion' : 'safety',
                  title: w.type === 'coherence' ? 'Incohérence Clinique' :
                         w.type === 'omission' ? 'Prévention' :
                         w.type === 'ddi' ? 'Interaction Médicamenteuse' : 'Contre-indication',
                  content: w.message,
                  source_type: 'DETERMINISTIC'
                }, ...prev]);
              }
            });
          })
          .catch(console.error);
      }, 800);
      return () => clearTimeout(timer);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items, drugs, patientDetails, insights, patientId]);

  useEffect(() => {
    // Calcul du Score d'Intelligence "Réel"
    let score = 72;
    score += items.length * 2;
    if (isSurgical) score += 10;
    if (hasDrugs) score += 5;
    
    // Malus si oublis ou alertes (pour pousser la rigueur)
    if (isSurgical && !hasDrugs) score -= 15;
    
    const finalScore = Math.min(99, Math.max(40, score));

    window.dispatchEvent(new CustomEvent('elite-insights-update', { 
      detail: { insights, score: finalScore } 
    }));
  }, [insights, items.length, isSurgical, hasDrugs]);

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
        setCertifType(d.reason || 'Certificat de Repos');
        setCertifDays(d.days || 0);
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

  const handleTeethFromOdontogram = useCallback((teeth: SelectedSurfaceData[]) => {
    setSelectedTeethFromOdontogram(teeth);
    setItems(prev => {
      const activeKeys = new Set(teeth.flatMap(t => t.treatments.map(tr => `${t.toothNumber}::${tr.id}`)));
      // Filter out empty manual rows OR rows whose odontogram key is no longer active
      const surviving = prev.filter(i => {
        if (i._odontogramKey) return activeKeys.has(i._odontogramKey);
        return i.description.trim() !== ''; // Keep manual rows only if they have content
      });
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
    api.get(`/patients/${patientId}`)
      .then(res => setPatientDetails(res.data))
      .catch((err) => {
        console.error('DocumentHub: patient fetch failed', err);
        const status = err.response?.status;
        if (status === 403 || status === 404) {
          setPatientDetails(null);
          toast.error("Dossier patient introuvable ou accès non autorisé.");
        }
      });
    if (activeTab === 'ordonnance') {
      api.get(`/prescriptions/smart-suggest/${patientId}`)
        .then(res => setSmartSuggestion(res.data))
        .catch(console.error);
    }
  }, [patientId, activeTab]);

  useEffect(() => {
    if (sideStudioType !== 'PREVIEW') return;
    const timer = setTimeout(() => generator.handleGenerate(false, false, true), 1200);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    sideStudioType, drugs, items, certifType, certifDays, paymentMode, 
    libreTitle, libreContent, docDate, activeTab, 
    generator.handleGenerate // Seule la fonction stable est nécessaire
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
        "flex-1 h-full flex flex-col px-8 pt-6 pb-32 gap-3 overflow-y-auto bg-transparent dark:bg-slate-900/50 transition-all duration-500 custom-scrollbar",
        sideStudioType === 'PREVIEW' ? "pr-[570px]" : ""
      )}>

        <StudioHeader
          patientName={patientName}
          docDate={docDate}
          onDateChange={setDocDate}
          activeTab={activeTab}
          showOdontoPanoramique={showOdontoPanoramique}
          onToggleOdonto={() => setShowOdontoPanoramique(v => !v)}
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
                const newItems: PriceItem[] = allActs.map((act: any) => ({
                  id: Date.now() + Math.random(),
                  description: act.suggested_act,
                  dent: act.fdi,
                  price: 0, // À remplir par le praticien ou le catalogue
                  toothNumbers: act.fdi !== 'Global' ? [Number(act.fdi)] : []
                }));
                setItems(prev => [...prev, ...newItems]);
                setActiveTab('devis');
              }}
            />
          )}

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
            <InstallmentStudio patientId={patientId || '0'} />
          )}

          {(activeTab === 'devis' || activeTab === 'honoraires') && (
            <AccountingStudio
              isDevis={activeTab === 'devis'}
              patientId={patientId || '0'} items={items} setItems={(newItems) => {
                // Si on change les items, on peut aussi apprendre les prix ici si c'est pertinent
                setItems(newItems);
              }}
              coherenceWarnings={generator.coherenceWarnings}
              paymentMode={paymentMode} setPaymentMode={(m) => setPaymentMode(m as PaymentMode)}
              installments={installments} setInstallments={setInstallments}
              isAccounted={isAccounted} setIsAccounted={setIsAccounted}
              paymentStatus={paymentStatus} setPaymentStatus={setPaymentStatus}
              isGlobalNote={isGlobalNote} setIsGlobalNote={setIsGlobalNote}
              showOdontoPanoramique={showOdontoPanoramique} odontogramMode={odontogramMode} setOdontogramMode={setOdontogramMode}
              groupSelectedTeeth={groupSelectedTeeth}
              handleToothDirectClick={(n) => setGroupSelectedTeeth(prev => prev.includes(n) ? prev.filter(x => x !== n) : [...prev, n])}
              selectTeethGroup={(g) => {
                const max = [11, 12, 13, 14, 15, 16, 17, 18, 21, 22, 23, 24, 25, 26, 27, 28];
                const mand = [31, 32, 33, 34, 35, 36, 37, 38, 41, 42, 43, 44, 45, 46, 47, 48];
                const regions: Record<string, number[]> = {
                  'all': [...max, ...mand],
                  'maxillaire': max,
                  'mandibule': mand,
                  'Q1': [11, 12, 13, 14, 15, 16, 17, 18],
                  'Q2': [21, 22, 23, 24, 25, 26, 27, 28],
                  'Q3': [31, 32, 33, 34, 35, 36, 37, 38],
                  'Q4': [41, 42, 43, 44, 45, 46, 47, 48],
                  'S1': [14, 15, 16, 17, 18],
                  'S2': [13, 12, 11, 21, 22, 23],
                  'S3': [24, 25, 26, 27, 28],
                  'S4': [34, 35, 36, 37, 38],
                  'S5': [33, 32, 31, 41, 42, 43],
                  'S6': [44, 45, 46, 47, 48]
                };
                if (regions[g]) setGroupSelectedTeeth(regions[g]);
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
              addEmptyRow={() => setItems((prev: any) => [...prev, { id: Date.now(), description: '', dent: '0', price: 0 }])}
              removeItem={(id) => setItems((prev: any) => prev.filter((i: any) => i.id !== id))}
              updateItem={(id, f, v) => {
                const newItems = items.map(i => i.id === id ? { ...i, [f]: f === 'price' ? Number(v) : v } : i);
                setItems(newItems);
                // Apprentissage Brain Ghost (v4.9)
                const item = newItems.find(i => i.id === id);
                if (item && item.description && item.price > 0 && (f === 'price' || f === 'description')) {
                  PriceBrain.recordAct(item.description, item.price, item.category || 'CONSERVATRICE');
                }
              }}
              handleActSearch={async (q, id) => {
                setItems(items.map(i => i.id === id ? { ...i, description: q } : i));
                if (q.length < 2) { setActSuggestions([]); setActiveActSearchId(null); return; }
                setActiveActSearchId(id);
                
                // 1. Search in Treatment Templates (Odontogram acts)
                const localMatches = TREATMENT_TEMPLATES.filter((t: { name: string; category: string; id: string }) => 
                  t.name.toLowerCase().includes(q.toLowerCase()) || 
                  t.category.toLowerCase().includes(q.toLowerCase())
                ).map((t: { id: string; name: string; category: string }) => ({ 
                  id: `template_${t.id}`, 
                  name: t.name, 
                  base_price: 0, 
                  category: t.category, 
                  isLocal: true,
                  is_habit: false
                }));

                // 2. Search in API (Enhanced with Habits in backend)
                try {
                  const res = await api.get(`/actes/catalog/search?q=${q}`);
                  const apiMatches = res.data || [];
                  
                  // Priorité 0 : Local Brain (Ghost Conscience)
                  const brainHistory = PriceBrain.getHistory();
                  const localBrainMatches = Object.values(brainHistory)
                    .filter(a => a.name.toLowerCase().includes(q.toLowerCase()))
                    .map(a => ({
                      id: `brain_${a.name}`,
                      name: a.name,
                      base_price: a.price,
                      category: a.category,
                      isLocal: true,
                      is_habit: true
                    }));

                  // Merge and deduplicate by name
                  const merged: any[] = [...localBrainMatches];
                  
                  // Priorité 1 : Habits de l'API
                  apiMatches.filter((a: any) => a.is_habit).forEach((a: any) => {
                    if (!merged.find(x => x.name.toLowerCase() === a.name.toLowerCase())) {
                      merged.push({ ...a, isLocal: false });
                    }
                  });

                  // Priorité 2 : Local Templates
                  localMatches.forEach((m: any) => {
                    if (!merged.find(x => x.name.toLowerCase() === m.name.toLowerCase())) {
                      merged.push(m);
                    }
                  });

                  // Priorité 3 : Reste du catalogue API
                  apiMatches.filter((a: any) => !a.is_habit).forEach((a: any) => {
                    if (!merged.find(x => x.name.toLowerCase() === a.name.toLowerCase())) {
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
                setItems(items.map(i => i.id === id ? { ...i, description: act.name, price: act.base_price || 0, category: act.category } : i));
                // Apprentissage immédiat si prix dispo
                if (act.name && act.base_price > 0) {
                  PriceBrain.recordAct(act.name, act.base_price, act.category || 'CONSERVATRICE');
                }
                setActSuggestions([]);
                setActiveActSearchId(null);
              }}
              validationErrors={generator.validationErrors}
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
          aiReport={generator.aiReport}
          onGenerateAI={generator.handleGenerateAI}
          loadingAi={generator.loadingAi}
          total={items.reduce((acc, i) => acc + (Number(i.price) || 0), 0)}
          sideStudioType={sideStudioType}
          onTogglePreview={() => setSideStudioType(prev => prev === 'PREVIEW' ? 'NONE' : 'PREVIEW')}
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
            className="fixed right-2 top-2 bottom-2 w-[550px] z-[11000] drop-shadow-2xl"
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
