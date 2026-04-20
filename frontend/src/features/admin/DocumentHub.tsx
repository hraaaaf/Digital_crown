import React, { useState, useEffect } from 'react';
import { 
  Pill, 
  FileBadge, 
  Receipt, 
  Calculator, 
  Plus, 
  Trash2, 
  Printer, 
  Loader2, 
  Calendar as CalendarIcon,
  Type,
  Eye,
  EyeOff,
  Archive,
  AlertTriangle,
  X,
  Search,
  Zap,
  AlertCircle,
  Brain,
  Check,
  Save,
  ChevronRight,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { cn } from '../../utils/cn';
import { api } from '../../services/api';
import { Odontogram } from '../../components/odontogram';
import { OdontogramSVG } from '../../components/odontogram/OdontogramSVG';
import type { SelectedSurfaceData, ToothSurface } from '../../components/odontogram/types';

type DocumentType = 'ordonnance' | 'certificat' | 'devis' | 'honoraires' | 'libre' | 'ai';
type PaymentMode = 'Espèces' | 'Chèque' | 'TPE' | 'Virement';

interface DrugItem { id: number; name: string; dosage: string; forme: string; posologie: string; }
interface PriceItem { 
  id: number; 
  description: string; 
  dent: string; 
  price: number;
  toothNumbers?: number[];
  /** Clé stable pour les items issus de l'odontogramme: `${toothNumber}::${treatment.id}` */
  _odontogramKey?: string;
}
interface DocumentHubProps { patientId: string | undefined; patientName: string; editData?: any; }

interface PatientDetails {
  id: number;
  nom: string;
  prenom: string;
  date_naissance?: string;
  genre?: string;
}

interface ClinicalCategory { id: number; label: string; }
interface ClinicalProtocol { id: number; category_id: number; variant_name: string; medications_json: any; }
interface MedicationOut { id: number; nom: string; dosage: string; forme: string; usage_count: number; }
interface ActOut { id: number; name: string; base_price: number; }

export const DocumentHub: React.FC<DocumentHubProps> = ({ patientId, patientName, editData }) => {
  const [activeTab, setActiveTab] = useState<DocumentType>('ordonnance');
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);
  const [patientDetails, setPatientDetails] = useState<PatientDetails | null>(null);

  const [aiReport, setAiReport] = useState<string | null>(null);
  const [loadingAi, setLoadingAi] = useState(false);

  const [showPrintWarning, setShowPrintWarning] = useState(false);
  const [pendingPrint, setPendingPrint] = useState(false);

  const [drugs, setDrugs] = useState<DrugItem[]>([{ id: 1, name: '', dosage: '', forme: '', posologie: '' }]);
  const [hasChanges, setHasChanges] = useState(false);
  const [certifType, setCertifType] = useState('Repos médical'); 
  const [certifDays, setCertifDays] = useState(3);
  const [items, setItems] = useState<PriceItem[]>([]);
  const [paymentMode, setPaymentMode] = useState<PaymentMode>('Espèces');
  const [libreTitle, setLibreTitle] = useState('Note Médicale');
  const [libreContent, setLibreContent] = useState('');

  // Hydratation des données si en mode "Édition" (Regénération)
  useEffect(() => {
    if (editData && editData.clinical_data) {
      const type = editData.type.toLowerCase();
      const d = editData.clinical_data;
      
      if (type === 'ordonnance') {
        setActiveTab('ordonnance');
        if (d.medications && d.medications.length > 0) {
          setDrugs(d.medications.map((m: any, idx: number) => ({
            id: Date.now() + idx,
            name: m.nom || '',
            dosage: m.dosage || '',
            forme: m.forme || 'Sachets',
            posologie: m.posologie || ''
          })));
        }
        if (d.doc_date) setDocDate(d.doc_date);
      } 
      else if (type === 'certificat') {
        setActiveTab('certificat');
        if (d.reason) setCertifType(d.reason);
        if (d.days) setCertifDays(d.days);
        if (d.start_date) setDocDate(d.start_date);
      } 
      else if (type === 'libre') {
        setActiveTab('libre');
        if (d.title) setLibreTitle(d.title);
        if (d.content) setLibreContent(d.content);
        if (d.doc_date) setDocDate(d.doc_date);
      } 
      else if (type === 'devis' || type === 'note' || type === 'honoraires') {
        setActiveTab(type === 'devis' ? 'devis' : 'honoraires');
        const srcItems = d.items || d.payments || [];
        if (srcItems.length > 0) {
          setItems(srcItems.map((i: any, idx: number) => ({
            id: Date.now() + idx,
            description: i.acte || '',
            dent: i.dent || '0',
            price: i.prix_unitaire || i.montant || 0,
            toothNumbers: i.dents || []
          })));
        }
        if (d.doc_date) setDocDate(d.doc_date);
        if (srcItems.length > 0 && srcItems[0].mode_reglement) {
          setPaymentMode(srcItems[0].mode_reglement as PaymentMode);
        }
      }
    }
  }, [editData]);

  const [diagnosticQuery, setDiagnosticQuery] = useState('');
  const [smartSuggestion, setSmartSuggestion] = useState<any>(null);
  const [loadingSmart, setLoadingSmart] = useState(false);
  const [suggestedCategories, setSuggestedCategories] = useState<ClinicalCategory[]>([]);
  const [availableProtocols, setAvailableProtocols] = useState<ClinicalProtocol[]>([]);
  const [activeDrugSearchId, setActiveDrugSearchId] = useState<number | null>(null);
  const [medicationSuggestions, setMedicationSuggestions] = useState<MedicationOut[]>([]);
  const [activeActSearchId, setActiveActSearchId] = useState<number | null>(null);
  const [actSuggestions, setActSuggestions] = useState<ActOut[]>([]);

  const [selectedTeethFromOdontogram, setSelectedTeethFromOdontogram] = useState<SelectedSurfaceData[]>([]);
  const [odontogramMode, setOdontogramMode] = useState<'individual' | 'group'>('individual');
  const [sideStudioType, setSideStudioType] = useState<'NONE' | 'PREVIEW'>('NONE');
  const [showOdontoPanoramique, setShowOdontoPanoramique] = useState(true);
  const [groupSelectedTeeth, setGroupSelectedTeeth] = useState<number[]>([]);
  const [groupTreatmentName, setGroupTreatmentName] = useState('');
  const [groupTreatmentPrice, setGroupTreatmentPrice] = useState<number | ''>('');

  const handleTeethFromOdontogram = (teeth: SelectedSurfaceData[]) => {
    setSelectedTeethFromOdontogram(teeth);
    
    setItems(prevItems => {
      const activeKeys = new Set<string>();
      teeth.forEach(tooth => {
        tooth.treatments.forEach(tr => {
          activeKeys.add(`${tooth.toothNumber}::${tr.id}`);
        });
      });

      const surviving = prevItems.filter(item =>
        !item._odontogramKey || activeKeys.has(item._odontogramKey)
      );

      const existingKeys = new Set(surviving.map(i => i._odontogramKey).filter(Boolean));
      const newItems: PriceItem[] = [];
      teeth.forEach(tooth => {
        tooth.treatments.forEach(tr => {
          const key = `${tooth.toothNumber}::${tr.id}`;
          if (!existingKeys.has(key)) {
            newItems.push({
              id: Date.now() + Math.random(),
              description: tr.name,
              dent: tooth.toothNumber.toString(),
              price: tr.price,
              toothNumbers: [tooth.toothNumber as number],
              _odontogramKey: key,
            });
          }
        });
      });

      return [...surviving, ...newItems];
    });
  };

  // Chargement des détails du patient (pour l'âge et autres infos)
  useEffect(() => {
    if (!patientId) return;
    const fetchPatient = async () => {
      try {
        const res = await api.get(`/patients/${patientId}`);
        setPatientDetails(res.data);
      } catch (e) {
        console.error("Erreur chargement patient:", e);
      }
    };
    fetchPatient();
  }, [patientId]);

  // Calcul de l'âge à partir de la date de naissance
  const calculateAge = (dateNaissance?: string): number | undefined => {
    if (!dateNaissance) return undefined;
    const birth = new Date(dateNaissance);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    return age;
  };

  const handleGenerateAI = async () => {
    if (!patientId) return;
    setLoadingAi(true);
    
    window.dispatchEvent(new Event('ai-generation-start'));
    
    try {
      const res = await api.get(`/patients/${patientId}/ai-diagnostic`);
      setAiReport(res.data.report);
    } catch (error) {
      console.error("Erreur lors de la génération du rapport IA :", error);
    } finally {
      setLoadingAi(false);
      window.dispatchEvent(new Event('ai-generation-end'));
    }
  };

  useEffect(() => {
    const fetchCategories = async () => {
      if (diagnosticQuery.length < 2) {
        setSuggestedCategories([]);
        return;
      }
      try {
        const res = await api.get(`/prescriptions/categories/search?q=${diagnosticQuery}`);
        setSuggestedCategories(res.data);
      } catch (e) {
        setSuggestedCategories([]);
      }
    };
    const timeoutId = setTimeout(fetchCategories, 300);
    return () => clearTimeout(timeoutId);
  }, [diagnosticQuery]);

  const handleCategorySelect = async (category: ClinicalCategory) => {
    setDiagnosticQuery(category.label);
    setSuggestedCategories([]);
    try {
      const res = await api.get(`/prescriptions/suggest?category_id=${category.id}`);
      setAvailableProtocols(res.data);
    } catch (e) {
      console.error("Erreur récupération protocoles:", e);
    }
  };

  const applyProtocol = (protocol: ClinicalProtocol) => {
    const meds = protocol.medications_json || [];
    if (meds.length > 0) {
      const newDrugs = meds.map((m: any, idx: number) => ({
        id: Date.now() + idx,
        name: m.nom,
        dosage: m.dosage || '',
        forme: m.forme || 'Sachets',
        posologie: m.posologie || ''
      }));
      setDrugs(newDrugs);
    }
  };

  const handleDrugSearch = async (query: string, drugId: number) => {
    updateDrug(drugId, 'name', query);
    if (query.length < 2) {
      setMedicationSuggestions([]);
      setActiveDrugSearchId(null);
      return;
    }
    setActiveDrugSearchId(drugId);
    try {
      const res = await api.get(`/prescriptions/search?q=${query}`);
      setMedicationSuggestions(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const applyDrugSuggestion = (drugId: number, med: MedicationOut) => {
    const currentDrugs = [...drugs];
    const idx = currentDrugs.findIndex(d => d.id === drugId);
    if (idx !== -1) {
      currentDrugs[idx] = {
        ...currentDrugs[idx],
        name: med.nom,
        dosage: med.dosage || '',
        forme: med.forme || ''
      };
      setDrugs(currentDrugs);
    }
    setMedicationSuggestions([]);
    setActiveDrugSearchId(null);
  };

  const checkDuplicate = (name: string, currentIndex: number) => {
    if (!name) return false;
    const normalized = name.trim().toLowerCase();
    return drugs.some((d, idx) => idx !== currentIndex && d.name.trim().toLowerCase() === normalized);
  };

  const checkDuplicateAct = (description: string, dent: string, currentIndex: number) => {
    if (!description) return false;
    const normalizedDesc = description.trim().toLowerCase();
    const normalizedDent = String(dent).trim().toLowerCase();
    return items.some((i, idx) => 
      idx !== currentIndex && 
      i.description.trim().toLowerCase() === normalizedDesc &&
      String(i.dent).trim().toLowerCase() === normalizedDent
    );
  };

  const handleActSearch = async (query: string, itemId: number) => {
    // Mise à jour immédiate de la valeur (ne pas attendre l'API)
    updateItem(itemId, 'description', query);
    if (query.length < 2) {
      setActSuggestions([]);
      setActiveActSearchId(null);
      return;
    }
    setActiveActSearchId(itemId);
    try {
      const res = await api.get(`/actes/catalog/search?q=${query}`);
      // Vérifier que l'item ciblé est toujours en train d'être édité
      setActSuggestions(res.data);
    } catch (e) {
      console.error("Erreur recherche actes:", e);
    }
  };

  const applyActSuggestion = (itemId: number, act: ActOut) => {
    const currentItems = [...items];
    const idx = currentItems.findIndex(i => i.id === itemId);
    if (idx !== -1) {
      currentItems[idx] = {
        ...currentItems[idx],
        description: act.name,
        price: act.base_price || 0
      };
      setItems(currentItems);
    }
    setActSuggestions([]);
    setActiveActSearchId(null);
  };

  // ── Handlers traitement groupé ────────────────────────────────────────────

  const handleToothDirectClick = (toothNumber: number) => {
    setGroupSelectedTeeth(prev =>
      prev.includes(toothNumber)
        ? prev.filter(n => n !== toothNumber)
        : [...prev, toothNumber]
    );
  };

  const selectTeethGroup = (group: 'all' | 'maxillaire' | 'mandibule' | 'none') => {
    const maxillaire = [11,12,13,14,15,16,17,18,21,22,23,24,25,26,27,28];
    const mandibule  = [31,32,33,34,35,36,37,38,41,42,43,44,45,46,47,48];
    switch (group) {
      case 'all':        setGroupSelectedTeeth([...maxillaire, ...mandibule]); break;
      case 'maxillaire': setGroupSelectedTeeth(maxillaire); break;
      case 'mandibule':  setGroupSelectedTeeth(mandibule);  break;
      case 'none':       setGroupSelectedTeeth([]);          break;
    }
  };

  const applyGroupTreatment = () => {
    if (!groupTreatmentName.trim() || groupSelectedTeeth.length === 0) return;
    const sorted   = [...groupSelectedTeeth].sort((a, b) => a - b);
    const dentLabel = sorted.join('-');
    const newItem: PriceItem = {
      id: Date.now(),
      description: groupTreatmentName,
      dent: dentLabel,
      price: Number(groupTreatmentPrice) || 0,
      toothNumbers: sorted,
    };
    setItems(prev => [...prev, newItem]);
    
    // Synchronisation PDF
    setSelectedTeethFromOdontogram(prev => [
      ...prev,
      ...sorted.map(t => ({ 
        toothNumber: t, 
        surface: 'ALL' as ToothSurface,
        treatments: [{ 
          id: Date.now().toString(), 
          name: groupTreatmentName, 
          price: Number(groupTreatmentPrice) || 0,
          category: 'PROTHESE'
        } as any] 
      }))
    ]);

    setGroupSelectedTeeth([]);
    setGroupTreatmentName('');
    setGroupTreatmentPrice('');
  };

  const addDrug = () => setDrugs([...drugs, { id: Date.now(), name: '', dosage: '', forme: '', posologie: '' }]);
  const removeDrug = (id: number) => setDrugs(drugs.filter(d => d.id !== id));
  const updateDrug = (id: number, field: keyof DrugItem, value: string) => {
    setDrugs(drugs.map(d => d.id === id ? { ...d, [field]: value } : d));
  };

  const addEmptyAccountingRow = () => setItems([...items, { id: Date.now(), description: '', dent: '0', price: 0 }]);
  const removeItem = (id: number) => setItems(items.filter(i => i.id !== id));
  const updateItem = (id: number, field: keyof PriceItem, value: string | number) => {
    const finalValue = field === 'price' ? (Number(value) || 0) : value;
    setItems(items.map(i => i.id === id ? { ...i, [field]: finalValue } : i));
  };
  
  // --- CHARGEMENT SMART SUGGESTION ---
  useEffect(() => {
    if (activeTab === 'ordonnance' && patientId) {
      loadSmartSuggestion();
    }
  }, [activeTab, patientId]);

  const loadSmartSuggestion = async () => {
    try {
      setLoadingSmart(true);
      const res = await api.get(`/prescriptions/smart-suggest/${patientId}`);
      setSmartSuggestion(res.data);
    } catch (err) {
      console.error("Erreur smart suggestion:", err);
    } finally {
      setLoadingSmart(false);
    }
  };

  const applySmartSuggestion = () => {
    if (!smartSuggestion || !smartSuggestion.suggestions) return;
    
    const mappedDrugs = smartSuggestion.suggestions.map((s: any, idx: number) => ({
      id: idx + 1,
      name: s.nom,
      dosage: s.dosage,
      forme: s.forme,
      posologie: s.posologie
    }));
    
    setDrugs(mappedDrugs);
    setSmartSuggestion({ ...smartSuggestion, applied: true });
    setHasChanges(false);
  };

  // Détecter si l'utilisateur a modifié la suggestion appliquée
  useEffect(() => {
    if (smartSuggestion?.applied && drugs.length > 0) {
      setHasChanges(true); // Toute modif après application est considérée comme un changement potentiel de préférence
    }
  }, [drugs]);

  const handleSavePreference = async () => {
    if (!smartSuggestion?.protocol_name) return;
    try {
      await api.post('/api/prescriptions/preferences/', {
        act_code: smartSuggestion.protocol_name.replace(" ", "_").toUpperCase(),
        drugs: drugs.map(d => ({
          nom: d.name,
          dosage: d.dosage,
          forme: d.forme,
          posologie: d.posologie
        }))
      });
      setHasChanges(false);
      // Feedback toast simulé par l'IA
      alert("Protocole personnalisé enregistré ! Il sera utilisé lors de votre prochaine extraction.");
    } catch (err) {
      console.error("Erreur sauvegarde pref:", err);
    }
  };

  const calculateTotal = () => items.reduce((sum, item) => sum + (Number(item.price) || 0), 0);

  const handleGenerate = async (archive: boolean = false, print: boolean = false, isPreview: boolean = false, force: boolean = false) => {
    if (!patientId || activeTab === 'ai') return; 
    setLoading(true);
    if (print) setPendingPrint(true);

    try {
      const payload: any = {
        type: activeTab === 'honoraires' ? 'note' : activeTab,
        patient_id: parseInt(patientId, 10),
        data: {}
      };

      // ... (construction du payload identique)
      if (activeTab === 'ordonnance') {
        payload.data = { medications: drugs.map(d => ({ nom: d.name, dosage: d.dosage, forme: d.forme || "Sachets", posologie: d.posologie })), doc_date: docDate };
      } else if (activeTab === 'certificat') {
        payload.data = { reason: certifType, days: Number(certifDays) || 0, start_date: docDate, is_work_stop: certifType === 'Arrêt de travail' };
      } else if (activeTab === 'libre') {
        const age = calculateAge(patientDetails?.date_naissance);
        payload.data = { title: libreTitle, content: libreContent, doc_date: docDate, age, gender: patientDetails?.genre };
      } else if (activeTab === 'devis' || activeTab === 'honoraires') {
        const commonItems = items.map(i => ({ acte: i.description, dent: i.dent || "0", dents: i.toothNumbers || [], prix_unitaire: parseFloat(i.price.toString()) || 0, montant: parseFloat(i.price.toString()) || 0, date: docDate, mode_reglement: paymentMode }));
        const robustTeethData = selectedTeethFromOdontogram.map(t => ({ tooth_number: t.toothNumber, treatments: t.treatments.map(tr => ({ code: tr.code || "ACT", name: tr.name, price: tr.price || 0 })), surfaces: t.surface ? [t.surface as string] : [], notes: "" }));
        payload.data = activeTab === 'devis' ? { items: commonItems, doc_date: docDate, teeth_data: robustTeethData } : { payments: commonItems, doc_date: docDate, teeth_data: robustTeethData };
      }

      const response = await api.post(`/documents/generate?archive=${archive}&preview=${isPreview}&force=${force}`, payload);
      
      // RESTAURATION : Mise à jour de l'aperçu si URL présente
      if (response.data.pdf_url) {
        // Utilisation de l'URL relative propre retournée par le backend
        const baseUrl = api.defaults.baseURL || "http://localhost:8000";
        setPdfUrl(`${baseUrl}/${response.data.pdf_url}#view=FitH&t=${Date.now()}`);
      }

      if (archive) {
        alert("✅ Document archivé avec succès !");
      }
      
      // RESTAURATION : Apprentissage IA
      if (activeTab === 'ordonnance' && archive) {
        await api.post('/prescriptions/learn', { medications: payload.data.medications });
      }

      if ((activeTab === 'devis' || activeTab === 'honoraires') && archive) {
        const learnedActes = items.map(i => ({ name: i.description, price_applied: parseFloat(i.price.toString()) || 0 }));
        await api.post('/actes/catalog/learn', { acts: learnedActes });
      }
      
    } catch (error: any) { 
        const errorDetail = error.response?.data?.detail || "";
        console.error("Erreur complète:", error);
        
        if (errorDetail.includes("DOUBLE_DETECTED")) {
            if (window.confirm("⚠️ DOUBLON DÉTECTÉ\n\nUne note avec les mêmes actes existe déjà pour ce patient.\nVoulez-vous tout de même l'ajouter à la comptabilité ?")) {
                handleGenerate(archive, print, false, true); 
                return;
            }
        } else {
            console.error("Erreur lors de la génération :", error); 
            alert("Erreur de génération : " + errorDetail);
        }
    } finally { 
        setLoading(false); 
        setShowPrintWarning(false); 
    }
  };

  useEffect(() => {
    const isPreviewActive = sideStudioType === 'PREVIEW';
    if (!isPreviewActive || activeTab === 'ai') return;
    
    const timer = setTimeout(() => handleGenerate(false, false, true), 1500); 
    return () => clearTimeout(timer);
  }, [sideStudioType, drugs, items, certifType, certifDays, paymentMode, libreTitle, libreContent, docDate, activeTab, selectedTeethFromOdontogram, patientDetails]);

  useEffect(() => {
    if (pendingPrint && pdfUrl && activeTab !== 'ai') {
      const printTimer = setTimeout(async () => {
        try {
          const response = await fetch(pdfUrl);
          const blob = await response.blob();
          const localBlobUrl = URL.createObjectURL(blob);
          const printFrame = document.createElement('iframe');
          printFrame.style.display = 'none';
          printFrame.src = localBlobUrl;
          document.body.appendChild(printFrame);
          
          printFrame.onload = () => {
            if (printFrame.contentWindow) {
              printFrame.contentWindow.focus();
              printFrame.contentWindow.print();
            }
            setPendingPrint(false);
            setTimeout(() => {
              document.body.removeChild(printFrame);
              URL.revokeObjectURL(localBlobUrl);
            }, 10000);
          };
        } catch (error) {
          console.error("Erreur d'impression :", error);
          setPendingPrint(false);
        }
      }, 1000); 
      return () => clearTimeout(printTimer);
    }
  }, [pdfUrl, pendingPrint]);

  const inputClass = "w-full px-4 py-3 bg-white/70 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-[#003380]/20 focus:border-[#003380] transition-all duration-300 shadow-sm font-medium text-slate-800";
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1";
  const addButtonClass = "w-full py-4 border-2 border-dashed border-slate-200 text-slate-400 rounded-2xl flex items-center justify-center gap-2 hover:border-[#003380] hover:text-[#003380] hover:bg-blue-50/30 transition-all font-bold mt-2";

  return (
    <div className="relative w-full h-full overflow-hidden">
      
      {/* MAIN FORM - ALWAYS FULL WIDTH */}
      <div className="w-full h-full pr-0 transition-all duration-500">
        <div className="flex flex-col gap-6 bg-white/70 backdrop-blur-2xl border border-white/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2.5rem] p-8 h-full overflow-y-auto custom-scrollbar relative">

        <div className="sticky top-0 z-40 -mt-2 -mx-2 mb-4 p-2 bg-white/40 backdrop-blur-3xl rounded-3xl border border-white/50 flex justify-between items-start shrink-0 transition-all duration-300">
          <div>
            <h2 className="text-3xl font-black text-[#003380] tracking-tight leading-none">Studio Documentaire</h2>
            <p className="text-slate-500 mt-1 font-medium italic">Patient : <span className="font-bold text-slate-800 not-italic tracking-tight">{patientName}</span></p>
          </div>
          
          <div className="flex items-center gap-3">
            {(activeTab === 'honoraires' || activeTab === 'devis') && (
              <button
                onClick={() => setShowOdontoPanoramique(!showOdontoPanoramique)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all",
                  showOdontoPanoramique 
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/30" 
                    : "bg-white text-blue-600 border border-blue-100 hover:bg-blue-50"
                )}
              >
                <Calculator size={14} />
                {showOdontoPanoramique ? "Réduire Schéma" : "Afficher Schéma"}
                {selectedTeethFromOdontogram.length > 0 && (
                  <span className="bg-blue-500 text-white text-[9px] px-1.5 py-0.5 rounded-full ml-1 anima-pulse">
                    {selectedTeethFromOdontogram.length}
                  </span>
                )}
              </button>
            )}

            {activeTab !== 'ai' && (
              <button 
                onClick={() => {
                  const nextMode = sideStudioType === 'PREVIEW' ? 'NONE' : 'PREVIEW';
                  setSideStudioType(nextMode);
                  if (nextMode === 'PREVIEW') {
                    // Déclenchement immédiat de la première génération
                    handleGenerate(false, false, true);
                  }
                }}
                className={cn(
                  "flex items-center gap-2 px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border",
                  sideStudioType === 'PREVIEW' 
                    ? "bg-emerald-600 text-white border-emerald-500 shadow-lg shadow-emerald-500/30" 
                    : "bg-white text-slate-400 border-slate-200 hover:border-slate-300"
                )}
              >
                <Eye size={14}/>
                Aperçu Direct
              </button>
            )}

            <div className="bg-white/80 p-2.5 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-start gap-1">
              <label className="text-[9px] font-black text-slate-400 uppercase flex items-center gap-1 leading-none"><CalendarIcon size={10} /> Date</label>
              <input type="date" className="bg-transparent text-xs font-black text-slate-700 outline-none w-28 cursor-pointer" value={docDate} onChange={(e) => setDocDate(e.target.value)} />
            </div>
          </div>
        </div>

          {/* SECTION PANORAMIQUE DYNAMIQUE (ODONTOGRAMME) */}
          {(activeTab === 'honoraires' || activeTab === 'devis') && showOdontoPanoramique && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mb-8 bg-slate-50/50 rounded-[2.5rem] border border-slate-100 p-8 shadow-inner relative overflow-visible"
            >
              <div className="flex bg-slate-200/50 p-1.5 rounded-2xl gap-1 w-fit mb-8 transition-all">
                <button
                  onClick={() => setOdontogramMode('individual')}
                  className={cn(
                    "px-4 py-2 rounded-lg text-[10px] font-black uppercase transition-all",
                    odontogramMode === 'individual' ? "bg-white text-blue-600 shadow-sm" : "text-slate-500"
                  )}
                >
                  Acte Unitaire
                </button>
                <button
                  onClick={() => setOdontogramMode('group')}
                  className={cn(
                    "px-4 py-2 rounded-lg text-[10px] font-black uppercase transition-all",
                    odontogramMode === 'group' ? "bg-white text-emerald-600 shadow-sm" : "text-slate-500"
                  )}
                >
                  Bridge / PAP
                </button>
              </div>

              {odontogramMode === 'individual' ? (
                <div className="animate-in fade-in duration-500 overflow-visible flex-1 flex justify-center items-center py-2">
                  <div className="w-full max-w-[500px] mx-auto px-4">
                    <Odontogram
                      patientId={parseInt(patientId || '0', 10)}
                      mode="SELECT_FOR_DOCUMENT"
                      onChange={handleTeethFromOdontogram}
                      showLegend={false}
                      compact={true}
                      className="border-0 shadow-none bg-transparent"
                    />
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in duration-500 py-2">
                  <div className="bg-white p-4 rounded-[1.5rem] border border-slate-100 shadow-sm flex flex-col justify-center min-h-[180px] max-w-[450px] mx-auto w-full">
                    <OdontogramSVG
                      type="ADULT"
                      teethSurfaces={{}}
                      selectedTooth={null}
                      selectedSurface={null}
                      onSurfaceClick={() => {}}
                      multiSelectedTeeth={groupSelectedTeeth}
                      onToothDirectClick={handleToothDirectClick}
                      showNumbers={false}
                    />
                    <div className="flex flex-wrap gap-2 mt-4">
                      {(['all', 'maxillaire', 'mandibule', 'none'] as const).map((g) => (
                        <button
                          key={g}
                          onClick={() => selectTeethGroup(g)}
                          className="px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border border-emerald-100 text-emerald-600 hover:bg-emerald-50 bg-white transition-all shadow-sm"
                        >
                          {g === 'none' ? 'Réinitialiser' : g}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-6 flex flex-col justify-center bg-white/40 p-6 rounded-3xl border border-white/60">
                    <div>
                      <label className={labelClass}>Libellé du soin groupé</label>
                      <input
                        type="text"
                        className={inputClass}
                        placeholder="Ex: Bridge 3-éléments céramo-métallique"
                        value={groupTreatmentName}
                        onChange={(e) => setGroupTreatmentName(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className={labelClass}>Honoraires globaux (MAD)</label>
                      <input
                        type="number"
                        className={cn(inputClass, "font-mono text-right text-blue-700 font-black text-2xl")}
                        value={groupTreatmentPrice}
                        onChange={(e) => setGroupTreatmentPrice(e.target.value === '' ? '' : Number(e.target.value))}
                      />
                    </div>

                    <button
                      onClick={applyGroupTreatment}
                      disabled={!groupTreatmentName.trim() || groupSelectedTeeth.length === 0}
                      className="w-full py-5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white rounded-[1.5rem] font-black uppercase tracking-widest flex items-center justify-center gap-3 transition-all shadow-xl shadow-emerald-500/20"
                    >
                      <Plus size={24} />
                      Valider {groupSelectedTeeth.length} dent{groupSelectedTeeth.length > 1 ? 's' : ''}
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          )}

        <div className="flex bg-slate-200/50 p-1.5 rounded-2xl gap-1 overflow-x-auto shrink-0 relative z-30">
          <TabButton active={activeTab === 'ordonnance'} onClick={() => setActiveTab('ordonnance')} icon={<Pill size={16} />} label="Ordonnance" />
          <TabButton active={activeTab === 'certificat'} onClick={() => setActiveTab('certificat')} icon={<FileBadge size={16} />} label="Certificat" />
          <TabButton active={activeTab === 'devis'} onClick={() => setActiveTab('devis')} icon={<Calculator size={16} />} label="Devis" />
          <TabButton active={activeTab === 'honoraires'} onClick={() => setActiveTab('honoraires')} icon={<Receipt size={16} />} label="Note" />
          <TabButton active={activeTab === 'libre'} onClick={() => setActiveTab('libre')} icon={<Type size={16} />} label="Libre" />
          <TabButton active={activeTab === 'ai'} onClick={() => {setActiveTab('ai'); setSideStudioType('NONE');}} icon={<Brain size={16} className={activeTab === 'ai' ? "text-amber-300" : "text-slate-500"} />} label="Analyse IA" isAi />
        </div>

        <div className="flex-1 space-y-6 mt-4 relative">
          
          {activeTab === 'ai' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 h-full flex flex-col">
              <div className="bg-[#0f172a] rounded-[2rem] border border-blue-500/30 shadow-[0_0_40px_rgba(59,130,246,0.1)] p-8 flex-1 flex flex-col relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 rounded-full blur-[80px] pointer-events-none" />
                
                <div className="flex justify-between items-center mb-8 relative z-10 border-b border-slate-700/50 pb-6">
                  <div>
                    <h3 className="text-2xl font-black text-white flex items-center gap-3 tracking-tight">
                      <Brain className="text-blue-400" size={32} />
                      Intelligence Clinique
                    </h3>
                    <p className="text-slate-400 text-sm mt-1">Interprétation céphalométrique et plan de traitement généré par IA.</p>
                  </div>
                  
                  {!aiReport && !loadingAi && (
                    <button 
                      onClick={handleGenerateAI}
                      className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl shadow-[0_0_15px_rgba(37,99,235,0.4)] transition-all hover:scale-105 flex items-center gap-2"
                    >
                      <Zap size={18} /> Lancer l'Analyse
                    </button>
                  )}
                </div>


                <div className="flex-1 overflow-y-auto relative z-10 custom-scrollbar pr-4">
                  {loadingAi ? (
                    <div className="flex flex-col items-center justify-center h-full text-blue-400 space-y-4">
                      <Loader2 className="animate-spin" size={48} />
                      <p className="font-bold tracking-widest uppercase text-sm animate-pulse">Synthèse des données en cours...</p>
                    </div>
                  ) : aiReport ? (
                    <div className="text-slate-300 leading-relaxed 
                      [&_h1]:text-2xl [&_h1]:font-black [&_h1]:text-white [&_h1]:mb-6 [&_h1]:border-b [&_h1]:border-blue-900/50 [&_h1]:pb-2
                      [&_h2]:text-xl [&_h2]:font-bold [&_h2]:text-blue-300 [&_h2]:mt-8 [&_h2]:mb-4
                      [&_h3]:text-lg [&_h3]:font-bold [&_h3]:text-blue-200 [&_h3]:mt-6 [&_h3]:mb-3
                      [&_p]:mb-4 [&_p]:text-slate-300
                      [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:mb-6 [&_li]:mb-2 [&_li]:text-slate-300
                      [&_strong]:text-white [&_strong]:font-black
                      [&_em]:text-blue-200 [&_em]:not-italic [&_em]:bg-blue-900/30 [&_em]:px-2 [&_em]:py-0.5 [&_em]:rounded-md
                      [&_code]:bg-[#1e293b] [&_code]:text-emerald-400 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:font-mono [&_code]:text-sm
                    ">
                      <ReactMarkdown>{aiReport}</ReactMarkdown>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full text-slate-500 opacity-60">
                      <Brain size={64} className="mb-4" />
                      <p className="font-medium text-center max-w-sm">Le moteur IA est en attente. Cliquez sur lancer l'analyse pour interpréter le dernier cliché radiographique de ce patient.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'ordonnance' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              
              {/* SMART SUGGESTION CARD */}
              {loadingSmart ? (
                <div className="bg-blue-50/50 border border-blue-100/50 p-6 rounded-[2rem] flex items-center justify-center gap-4 animate-pulse">
                   <Loader2 className="animate-spin text-blue-500" size={20} />
                   <span className="text-xs font-black text-blue-500 uppercase tracking-widest">Analyse clinique en cours...</span>
                </div>
              ) : smartSuggestion && smartSuggestion.suggestions?.length > 0 && (
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 p-8 rounded-[2.5rem] shadow-xl shadow-blue-500/5 group relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                    <Zap size={120} />
                  </div>
                  
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
                    <div className="flex items-start gap-4">
                      <div className="w-14 h-14 bg-white rounded-2xl shadow-lg flex items-center justify-center text-blue-600 shrink-0">
                        <Brain size={28} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="bg-blue-600 text-[10px] font-black text-white px-2 py-0.5 rounded-md uppercase tracking-tighter">Suggestion IA</span>
                          <span className="text-slate-400 text-[10px] font-bold uppercase tracking-widest">• Protocole {smartSuggestion.protocol_name}</span>
                        </div>
                        <h4 className="text-lg font-black text-[#003380] leading-tight">Générer l'ordonnance type ?</h4>
                        <div className="flex gap-2 mt-2">
                          {smartSuggestion.suggestions.slice(0, 3).map((s:any) => (
                            <span key={s.nom} className="text-[10px] font-bold text-blue-500 bg-white/80 px-2 py-1 rounded-lg border border-blue-100">{s.nom}</span>
                          ))}
                          {smartSuggestion.suggestions.length > 3 && <span className="text-[10px] font-bold text-slate-400">+{smartSuggestion.suggestions.length - 3}</span>}
                        </div>
                      </div>
                    </div>

                    <button 
                      onClick={applySmartSuggestion}
                      className={cn(
                        "px-8 py-4 rounded-2xl font-black text-sm transition-all hover:scale-105 active:scale-95 flex items-center gap-2 shadow-xl",
                        smartSuggestion.applied ? "bg-emerald-500 text-white shadow-emerald-500/20" : "bg-[#003380] text-white shadow-blue-900/20"
                      )}
                    >
                      {smartSuggestion.applied ? <Check size={18} /> : <Plus size={18} />}
                      {smartSuggestion.applied ? "Protocole Appliqué" : "Appliquer en un clic"}
                    </button>
                  </div>

                  {hasChanges && smartSuggestion.applied && (
                    <div className="mt-6 flex items-center justify-between bg-white/60 backdrop-blur-md p-4 rounded-2xl border border-blue-200 animate-in zoom-in-95 duration-300">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center">
                          <Save size={18} />
                        </div>
                        <p className="text-xs font-bold text-[#003380]">
                          Vous avez personnalisé ce protocole. L'enregistrer pour vos prochaines consultations ?
                        </p>
                      </div>
                      <button 
                        onClick={handleSavePreference}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
                      >
                        Sauvegarder mon modèle
                      </button>
                    </div>
                  )}


                  {smartSuggestion.warnings?.length > 0 && (
                    <div className="mt-6 flex flex-col gap-2">
                      {smartSuggestion.warnings.map((w: string, i: number) => (
                        <div key={i} className="bg-amber-100/80 border border-amber-200 text-amber-800 p-4 rounded-xl text-xs font-bold flex items-center gap-3">
                          <AlertTriangle size={16} className="shrink-0" />
                          {w}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="bg-white/50 backdrop-blur-md p-6 rounded-[2rem] border border-blue-100/50 shadow-sm relative z-30">
                <label className="text-[10px] font-black text-[#003380] uppercase tracking-widest block mb-3 flex items-center gap-2">
                  <Zap size={14} className="text-amber-500"/> Assistant IA : Motif de consultation
                </label>
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                  <input 
                    type="text" 
                    className="w-full pl-12 pr-4 py-3.5 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:ring-4 focus:ring-[#003380]/10 focus:border-[#003380] transition-all duration-300 font-bold text-[#003380]" 
                    placeholder="Rechercher un protocole (ex: Extraction, Abcès...)"
                    value={diagnosticQuery}
                    onChange={(e) => setDiagnosticQuery(e.target.value)}
                  />
                  {suggestedCategories.length > 0 && (
                    <ul className="absolute left-0 right-0 top-full mt-2 bg-white rounded-xl border border-slate-200 shadow-xl overflow-hidden z-50">
                      {suggestedCategories.map(cat => (
                        <li key={cat.id} onClick={() => handleCategorySelect(cat)} className="px-5 py-3.5 hover:bg-blue-50 cursor-pointer font-black text-sm text-slate-700 transition-colors border-b border-slate-50 last:border-0">
                          {cat.label}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {availableProtocols.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2 animate-in fade-in slide-in-from-top-2">
                    {availableProtocols.map(prot => (
                      <button 
                        key={prot.id} 
                        onClick={() => applyProtocol(prot)}
                        className="px-4 py-2.5 bg-gradient-to-br from-[#003380] to-blue-900 text-white text-xs font-black rounded-xl shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all flex items-center gap-2"
                      >
                        <FileBadge size={14} /> {prot.variant_name}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-4 relative z-20">
                {drugs.map((drug, index) => {
                  const isDuplicate = checkDuplicate(drug.name, index);
                  return (
                    <div key={drug.id} className={cn(
                      "flex gap-3 items-start p-4 rounded-2xl border shadow-sm group transition-all relative",
                      isDuplicate ? "border-amber-400 bg-amber-50/50" : "bg-white border-slate-100"
                    )}>
                      {isDuplicate && (
                        <div className="absolute -top-3 right-4 bg-amber-100 text-amber-700 text-[9px] font-black px-2 py-0.5 rounded-md flex items-center gap-1 border border-amber-200 z-10">
                          <AlertCircle size={10}/> Doublon détecté
                        </div>
                      )}

                      <div className="flex-1 grid grid-cols-12 gap-3">
                        <div className="col-span-12 md:col-span-4 flex flex-col justify-end relative">
                          <label className={cn(labelClass, index > 0 && "md:hidden")}>Médicament</label>
                          <input 
                            type="text" 
                            className={cn(inputClass, isDuplicate && "border-amber-300 focus:border-amber-500 focus:ring-amber-500/20")} 
                            placeholder="Nom du médicament" 
                            value={drug.name} 
                            onChange={(e) => handleDrugSearch(e.target.value, drug.id)} 
                            onBlur={() => setTimeout(() => setActiveDrugSearchId(null), 200)}
                          />
                          {activeDrugSearchId === drug.id && medicationSuggestions.length > 0 && (
                            <ul className="absolute left-0 right-0 top-[100%] mt-1 bg-white rounded-xl border border-slate-200 shadow-xl overflow-hidden z-50 max-h-48 overflow-y-auto">
                              {medicationSuggestions.map(med => (
                                <li key={med.id} onMouseDown={() => applyDrugSuggestion(drug.id, med)} className="px-4 py-3 hover:bg-blue-50 cursor-pointer flex flex-col transition-colors border-b border-slate-50 last:border-0">
                                  <span className="font-black text-sm text-[#003380]">{med.nom}</span>
                                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{med.dosage} • {med.forme}</span>
                                 </li>
                              ))}
                            </ul>
                          )}
                        </div>
                        
                        <div className="col-span-6 md:col-span-4 flex flex-col justify-end">
                          <label className={cn(labelClass, index > 0 && "md:hidden")}>Dosage/Forme</label>
                          <div className="flex gap-2">
                            <input type="text" className={inputClass} placeholder="Dosage" value={drug.dosage} onChange={(e) => updateDrug(drug.id, 'dosage', e.target.value)} />
                            <input type="text" className={inputClass} placeholder="Forme" value={drug.forme} onChange={(e) => updateDrug(drug.id, 'forme', e.target.value)} />
                          </div>
                        </div>
                        
                        <div className="col-span-6 md:col-span-4 flex flex-col justify-end">
                          <label className={cn(labelClass, index > 0 && "md:hidden")}>Posologie</label>
                          <input type="text" className={inputClass} placeholder="Instructions de prise" value={drug.posologie} onChange={(e) => updateDrug(drug.id, 'posologie', e.target.value)} />
                        </div>
                      </div>
                      <button onClick={() => removeDrug(drug.id)} className="p-3 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all mb-0.5 opacity-50 group-hover:opacity-100 shrink-0 mt-6"><Trash2 size={20} /></button>
                    </div>
                  );
                })}
                <button onClick={addDrug} className={addButtonClass}><Plus size={20} /> Ajouter un médicament manuellement</button>
              </div>
            </div>
          )}

          {activeTab === 'certificat' && (
            <div className="space-y-6 p-8 bg-white rounded-[2rem] border border-slate-100 shadow-sm animate-in fade-in duration-500">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <label className={labelClass}>Nature du certificat</label>
                  <select value={certifType} onChange={(e) => setCertifType(e.target.value)} className={inputClass}>
                    <option value="Repos médical">Repos médical</option>
                    <option value="Arrêt de travail">Arrêt de travail</option>
                    <option value="Certificat d'aptitude">Certificat d'aptitude</option>
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Durée (Nombre de jours)</label>
                  <input type="number" min="1" value={certifDays} onChange={(e) => setCertifDays(parseInt(e.target.value) || 0)} className={cn(inputClass, "font-bold text-[#003380]")} />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'libre' && (
            <div className="space-y-6 animate-in fade-in duration-500">
              <div className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm space-y-5">
                <div><label className={labelClass}>Titre du document</label><input type="text" className={inputClass} value={libreTitle} onChange={(e) => setLibreTitle(e.target.value)} /></div>
                <div><label className={labelClass}>Contenu du message</label><textarea className={cn(inputClass, "min-h-[250px] resize-none leading-relaxed")} value={libreContent} onChange={(e) => setLibreContent(e.target.value)} /></div>
              </div>
            </div>
          )}

          {(activeTab === 'devis' || activeTab === 'honoraires') && (
            <div className="space-y-6 animate-in fade-in duration-500">
              <div className="flex justify-between items-center p-6 bg-gradient-to-br from-[#003380] to-blue-900 rounded-[2rem] text-white shadow-xl">
                <span className="text-sm font-bold uppercase tracking-widest text-blue-200">Total Estimé</span>
                <span className="text-3xl font-black tracking-tight">{calculateTotal().toLocaleString('fr-FR')} <span className="text-lg font-medium text-blue-300">MAD</span></span>
              </div>
              
              {activeTab === 'honoraires' && (
                <div className="p-6 bg-blue-50/50 border border-blue-100 rounded-2xl mb-2">
                  <label className={labelClass}>Mode de règlement</label>
                  <select className={inputClass} value={paymentMode} onChange={(e) => setPaymentMode(e.target.value as PaymentMode)}>
                    <option value="Espèces">Espèces</option>
                    <option value="Chèque">Chèque</option>
                    <option value="TPE">TPE (Carte)</option>
                    <option value="Virement">Virement</option>
                  </select>
                </div>
              )}


              <div className="flex justify-between items-center px-2">
                <h3 className="text-xs font-black text-[#003380] uppercase tracking-tighter flex items-center gap-2">
                  Détail des prestations
                  <span className="bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full text-[9px]">{items.length} ligne(s)</span>
                </h3>
                <div className="flex gap-2">
                  <button 
                    onClick={() => setItems([{ id: Date.now(), description: '', dent: '', price: 0 }])}
                    className="text-[10px] font-bold text-red-400 hover:text-red-600 transition-colors uppercase tracking-widest flex items-center gap-1"
                  >
                    <Trash2 size={12} /> Tout vider
                  </button>
                </div>
              </div>

              <div className="space-y-3 relative z-20">
                {items.map((item, index) => {
                  const isDuplicateAct = checkDuplicateAct(item.description, item.dent, index);
                  return (
                  <div key={item.id} className={cn(
                    "flex gap-3 items-end p-4 rounded-2xl border shadow-sm transition-all group relative",
                    isDuplicateAct ? "border-amber-400 bg-amber-50/50" : "bg-white border-slate-100 hover:border-blue-200 hover:shadow-md hover:translate-x-1"
                  )}>
                    {isDuplicateAct && (
                      <div className="absolute -top-3 right-4 bg-amber-100 text-amber-700 text-[9px] font-black px-2 py-0.5 rounded-md flex items-center gap-1 border border-amber-200 z-10">
                        <AlertCircle size={10}/> Doublon détecté sur cette dent
                      </div>
                    )}
                    <div className="flex-1 grid grid-cols-12 gap-3">
                      
                      <div className="col-span-12 md:col-span-6 flex flex-col justify-end relative">
                        <div className={cn(labelClass, index > 0 && "md:hidden", "flex items-center gap-2")}>
                          Désignation de l'acte
                          {item._odontogramKey && (
                            <span className="text-[8px] font-black px-2 py-0.5 rounded-lg bg-blue-600 text-white tracking-widest uppercase shadow-sm shadow-blue-500/20">Schéma</span>
                          )}
                          {item.toothNumbers && item.toothNumbers.length > 1 && (
                            <span className="text-[8px] font-black px-2 py-0.5 rounded-lg bg-emerald-600 text-white tracking-widest uppercase shadow-sm shadow-emerald-500/20">Groupé</span>
                          )}
                        </div>
                        <input 
                          type="text" 
                          className={cn(inputClass, isDuplicateAct && "border-amber-300 focus:border-amber-500 focus:ring-amber-500/20")} 
                          value={item.description} 
                          onChange={(e) => handleActSearch(e.target.value, item.id)} 
                          onBlur={() => setTimeout(() => setActiveActSearchId(null), 200)}
                          placeholder="Saisir ou rechercher un acte..."
                        />
                        {activeActSearchId === item.id && actSuggestions.length > 0 && (
                          <ul className="absolute left-0 right-0 top-[100%] mt-1 bg-white rounded-xl border border-slate-200 shadow-xl overflow-hidden z-50 max-h-48 overflow-y-auto">
                            {actSuggestions.map(act => (
                              <li 
                                key={act.id} 
                                onMouseDown={() => applyActSuggestion(item.id, act)} 
                                className="px-4 py-3 hover:bg-blue-50 cursor-pointer flex justify-between items-center transition-colors border-b border-slate-50 last:border-0"
                              >
                                <span className="font-black text-sm text-[#003380]">{act.name}</span>
                                <span className="text-xs font-bold text-blue-500 whitespace-nowrap ml-2">{act.base_price} MAD</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>

                      <div className="col-span-6 md:col-span-3 flex flex-col justify-end">
                        <label className={cn(labelClass, index > 0 && "md:hidden")}>Dent(s)</label>
                        <input
                          type="text"
                          className={inputClass}
                          value={item.dent}
                          onChange={(e) => updateItem(item.id, 'dent', e.target.value)}
                          placeholder="Ex: 16 ou 14-15-16"
                        />
                      </div>
                      <div className="col-span-6 md:col-span-3 flex flex-col justify-end">
                        <label className={cn(labelClass, index > 0 && "md:hidden whitespace-nowrap")}>Honoraires (MAD)</label>
                        <input
                          type="number"
                          className={cn(inputClass, "font-mono text-right text-blue-700 font-black text-base bg-blue-50/30 border-blue-100")}
                          value={item.price || ''}
                          onChange={(e) => updateItem(item.id, 'price', e.target.value)}
                          placeholder="0"
                        />
                      </div>
                    </div>
                    <button onClick={() => removeItem(item.id)} className="p-3 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all mb-0.5 opacity-50 group-hover:opacity-100 shrink-0">
                      <Trash2 size={20} />
                    </button>
                  </div>
                  );
                })}
                <button 
                  onClick={() => setItems([...items, { id: Date.now(), description: '', dent: '', price: 0 }])}
                  className="w-full py-4 border-2 border-dashed border-slate-100 text-slate-300 rounded-2xl flex items-center justify-center gap-2 hover:border-blue-400 hover:text-blue-500 hover:bg-blue-50 transition-all font-bold mt-2"
                >
                  <Plus size={18} /> Ajouter un acte manuel supplémentaire
                </button>
              </div>
              <button onClick={addEmptyAccountingRow} className={addButtonClass}><Plus size={20} /> Ajouter un acte manuellement</button>
            </div>
          )}
        </div>

        {activeTab !== 'ai' && (
          <div className="mt-4 pt-4 border-t border-slate-200/50 shrink-0 flex gap-4">
            <button 
              onClick={() => handleGenerate(true, true)} 
              disabled={loading} 
              className="flex-1 py-5 bg-[#003380] hover:bg-blue-900 text-white rounded-[1.5rem] font-black text-lg flex items-center justify-center gap-3 transition-all duration-300 shadow-xl shadow-[#003380]/30 hover:shadow-2xl hover:-translate-y-1"
            >
              {loading ? <Loader2 className="animate-spin" size={24} /> : <Archive size={22} />}
              {loading ? "Génération..." : "Archiver + Imprimer"}
            </button>

            <button 
              onClick={() => setShowPrintWarning(true)} 
              disabled={loading} 
              className="px-10 py-5 bg-white border-2 border-slate-200 text-slate-500 hover:text-[#003380] hover:border-[#003380] rounded-[1.5rem] font-black transition-all flex items-center gap-2"
            >
              <Printer size={22} /> Imprimer seul
            </button>
          </div>
        )}
      </div>
    </div>

      {showPrintWarning && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-slate-900/40 backdrop-blur-md animate-in fade-in duration-300">
          <div className="bg-white rounded-[2.5rem] p-10 max-w-md w-full shadow-2xl border border-white">
            <div className="absolute top-0 right-0 p-6">
               <button onClick={() => setShowPrintWarning(false)} className="text-slate-300 hover:text-slate-500 transition-colors"><X size={24} /></button>
            </div>
            <div className="w-20 h-20 bg-amber-50 text-amber-500 rounded-3xl flex items-center justify-center mb-6"><AlertTriangle size={40} /></div>
            <h3 className="text-2xl font-black text-slate-800 leading-tight">Attention : Sans Archivage</h3>
            <p className="text-slate-500 mt-3 font-medium leading-relaxed">Cette impression ne gardera aucune trace.</p>
            <div className="flex gap-4 mt-10">
              <button onClick={() => setShowPrintWarning(false)} className="flex-1 py-4 bg-slate-100 rounded-2xl font-bold transition-all">Annuler</button>
              <button onClick={() => handleGenerate(false, true)} className="flex-1 py-4 bg-[#003380] text-white rounded-2xl font-bold shadow-lg transition-all">Imprimer</button>
            </div>
          </div>
        </div>
      )}

      {/* OMEGA STUDIO - UNIFIED SIDE PANEL (PREVIEW ONLY NOW) */}
      <AnimatePresence>
        {sideStudioType === 'PREVIEW' && (
          <>
            <motion.div
              initial={{ x: '100%', opacity: 0.5 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: '100%', opacity: 0.5 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 bottom-0 w-[850px] max-w-[95vw] bg-white border-l border-slate-200 shadow-[-20px_0_60px_rgba(0,0,0,0.12)] z-[70] flex flex-col pt-16"
            >
              {/* Studio Header */}
              <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-emerald-50/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
                    <Eye className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-black text-slate-800 uppercase tracking-tight">Aperçu du Document</h3>
                    <p className="text-[10px] font-bold text-emerald-600 uppercase tracking-widest">Temps réel</p>
                  </div>
                </div>
                <button 
                  onClick={() => setSideStudioType('NONE')}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-xl transition-all text-slate-500 hover:text-slate-800 font-bold text-[10px] uppercase tracking-widest border border-slate-200"
                >
                  Fermer Aperçu
                  <ChevronRight size={14} className="mt-0.5" />
                </button>
              </div>

              {/* Studio Content */}
              <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                <div className="h-full animate-in fade-in slide-in-from-right-4 duration-300 flex flex-col">
                  {pdfUrl ? (
                    <div className="flex-1 rounded-2xl overflow-hidden border border-slate-200 shadow-inner bg-slate-800">
                      <iframe src={pdfUrl} className="w-full h-full border-none" title="Live Preview" />
                    </div>
                  ) : (
                    <div className="flex-1 flex flex-col items-center justify-center p-12 text-center text-slate-300">
                      <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                        <EyeOff size={32} className="text-slate-200" />
                      </div>
                      <p className="font-bold uppercase tracking-widest text-xs">Aucun aperçu disponible</p>
                      <p className="text-[10px] mt-2">Activez l'aperçu pour visualiser le PDF en temps réel.</p>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Studio Footer */}
              <div className="p-6 bg-slate-50/80 border-t border-slate-100">
                {(activeTab === 'devis' || activeTab === 'honoraires') && (
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Honoraires Totaux</span>
                    <span className="text-2xl font-black text-[#003380]">{calculateTotal().toLocaleString()} MAD</span>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-3">
                  <button 
                    onClick={() => {
                      handleGenerate(true, false, false);
                      setSideStudioType('NONE');
                    }}
                    className="py-4 bg-[#003380] text-white rounded-2xl font-black uppercase tracking-widest text-[10px] shadow-lg shadow-blue-900/20 active:scale-95 transition-all"
                  >
                    Finaliser & Archiver
                  </button>
                  <button 
                    onClick={() => {
                      handleGenerate(true, true, false);
                      setSideStudioType('NONE');
                    }}
                    className="py-4 bg-emerald-600 text-white rounded-2xl font-black uppercase tracking-widest text-[10px] shadow-lg shadow-emerald-900/20 active:scale-95 transition-all flex items-center justify-center gap-2"
                  >
                    <Printer size={14} />
                    Imprimer
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

const TabButton = ({ active, onClick, icon, label, isAi }: any) => (
  <button 
    onClick={onClick} 
    className={cn(
      "flex-1 flex items-center justify-center gap-2 px-3 py-3 rounded-xl text-sm font-bold transition-all duration-300", 
      active && !isAi ? "bg-[#003380] text-white shadow-lg scale-[1.02]" : "",
      active && isAi ? "bg-slate-900 text-white shadow-lg scale-[1.02] border border-blue-500/30" : "",
      !active ? "text-slate-500 hover:bg-slate-300/50 hover:text-slate-900" : ""
    )}
  >
    {icon} <span className="hidden sm:inline">{label}</span>
  </button>
);