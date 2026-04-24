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
  Archive,
  AlertTriangle,
  X,
  Zap,
  AlertCircle,
  Brain,
  Save,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { cn } from '../../utils/cn';
import { api } from '../../services/api';
import { AccountingStudio } from './AccountingStudio';
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

  const [smartSuggestion, setSmartSuggestion] = useState<any>(null);
  const [loadingSmart, setLoadingSmart] = useState(false);
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

  // Chargement des détails du patient
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

  const handleActSearch = async (query: string, itemId: number) => {
    updateItem(itemId, 'description', query);
    if (query.length < 2) {
      setActSuggestions([]);
      setActiveActSearchId(null);
      return;
    }
    setActiveActSearchId(itemId);
    try {
      const res = await api.get(`/actes/catalog/search?q=${query}`);
      setActSuggestions(res.data);
    } catch (e) {
      console.error("Erreur recherche actes:", e);
    }
  };

  const applyActSuggestion = (itemId: number, act: ActOut) => {
    const currentItems = [...items];
    const idx = currentItems.findIndex(i => i.id === itemId);
    if (idx !== -1) {
      currentItems[idx] = { ...currentItems[idx], description: act.name, price: act.base_price || 0 };
      setItems(currentItems);
    }
    setActSuggestions([]);
    setActiveActSearchId(null);
  };

  const handleToothDirectClick = (toothNumber: number) => {
    setGroupSelectedTeeth(prev => prev.includes(toothNumber) ? prev.filter(n => n !== toothNumber) : [...prev, toothNumber]);
  };

  const selectTeethGroup = (group: 'all' | 'maxillaire' | 'mandibule' | 'none') => {
    const maxillaire = [11,12,13,14,15,16,17,18,21,22,23,24,25,26,27,28];
    const mandibule  = [31,32,33,34,35,36,37,38,41,42,43,44,45,46,47,48];
    switch (group) {
      case 'all': setGroupSelectedTeeth([...maxillaire, ...mandibule]); break;
      case 'maxillaire': setGroupSelectedTeeth(maxillaire); break;
      case 'mandibule': setGroupSelectedTeeth(mandibule); break;
      case 'none': setGroupSelectedTeeth([]); break;
    }
  };

  const applyGroupTreatment = () => {
    if (!groupTreatmentName.trim() || groupSelectedTeeth.length === 0) return;
    const sorted = [...groupSelectedTeeth].sort((a, b) => a - b);
    const dentLabel = sorted.join('-');
    const newItem: PriceItem = { id: Date.now(), description: groupTreatmentName, dent: dentLabel, price: Number(groupTreatmentPrice) || 0, toothNumbers: sorted };
    setItems(prev => [...prev, newItem]);
    setSelectedTeethFromOdontogram(prev => [
      ...prev,
      ...sorted.map(t => ({ 
        toothNumber: t, 
        surface: 'ALL' as ToothSurface,
        treatments: [{ id: Date.now().toString(), name: groupTreatmentName, price: Number(groupTreatmentPrice) || 0, category: 'PROTHESE' } as any] 
      }))
    ]);
    setGroupSelectedTeeth([]); setGroupTreatmentName(''); setGroupTreatmentPrice('');
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
  
  useEffect(() => {
    if (activeTab === 'ordonnance' && patientId) loadSmartSuggestion();
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
    const mappedDrugs = smartSuggestion.suggestions.map((s: any, idx: number) => ({ id: idx + 1, name: s.nom, dosage: s.dosage, forme: s.forme, posologie: s.posologie }));
    setDrugs(mappedDrugs);
    setSmartSuggestion({ ...smartSuggestion, applied: true });
    setHasChanges(false);
  };

  useEffect(() => {
    if (smartSuggestion?.applied && drugs.length > 0) setHasChanges(true);
  }, [drugs]);

  const handleSavePreference = async () => {
    if (!smartSuggestion?.protocol_name) return;
    try {
      await api.post('/prescriptions/preferences/', {
        act_code: smartSuggestion.protocol_name.replace(" ", "_").toUpperCase(),
        drugs: drugs.map(d => ({ nom: d.name, dosage: d.dosage, forme: d.forme, posologie: d.posologie }))
      });
      setHasChanges(false);
      alert("Protocole personnalisé enregistré !");
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
      const payload: any = { type: activeTab === 'honoraires' ? 'note' : activeTab, patient_id: parseInt(patientId, 10), data: {} };
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
      if (response.data.pdf_url) {
        const baseUrl = api.defaults.baseURL || "http://localhost:8000";
        setPdfUrl(`${baseUrl}/${response.data.pdf_url}#view=FitH&t=${Date.now()}`);
      }
      if (archive) alert("✅ Document archivé !");
    } catch (error: any) { 
        const errorDetail = error.response?.data?.detail || "";
        if (errorDetail.includes("DOUBLE_DETECTED")) {
            if (window.confirm("⚠️ DOUBLON DÉTECTÉ\nVoulez-vous tout de même l'ajouter ?")) {
                handleGenerate(archive, print, false, true); return;
            }
        } else alert("Erreur : " + errorDetail);
    } finally { setLoading(false); setShowPrintWarning(false); }
  };

  useEffect(() => {
    if (sideStudioType !== 'PREVIEW' || activeTab === 'ai') return;
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
          printFrame.style.display = 'none'; printFrame.src = localBlobUrl; document.body.appendChild(printFrame);
          printFrame.onload = () => {
            if (printFrame.contentWindow) { printFrame.contentWindow.focus(); printFrame.contentWindow.print(); }
            setPendingPrint(false); setTimeout(() => { document.body.removeChild(printFrame); URL.revokeObjectURL(localBlobUrl); }, 10000);
          };
        } catch (error) { console.error("Erreur d'impression :", error); setPendingPrint(false); }
      }, 1000); 
      return () => clearTimeout(printTimer);
    }
  }, [pdfUrl, pendingPrint]);

  const inputClass = "w-full px-4 py-3 bg-white/70 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-300 shadow-sm font-medium text-slate-800";
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 ml-1";
  const addButtonClass = "w-full py-4 border-2 border-dashed border-slate-200 text-slate-400 rounded-2xl flex items-center justify-center gap-2 hover:border-primary hover:text-primary hover:bg-primary/5 transition-all font-bold mt-2";

  const QUICK_PRESCRIPTIONS = [
    { label: 'Post-Op Standard', color: 'rose', drugs: [
      { name: 'PARACETAMOL', dosage: '1g', forme: 'Gélules (Bte de 16)', posologie: '1 gel x 3 / jour pendant 4 jours' },
      { name: 'IBUPROFENE', dosage: '400mg', forme: 'Comprimés (Bte de 20)', posologie: '1 comp x 3 / jour si douleur' }
    ]},
    { label: 'Infection / Abcès', color: 'emerald', drugs: [
      { name: 'AMOXICILLINE', dosage: '1g', forme: 'Gélules (Bte de 12)', posologie: '1 gel Matin et Soir pendant 7 jours' },
      { name: 'METRONIDAZOLE', dosage: '500mg', forme: 'Comprimés (Bte de 20)', posologie: '1 comp x 3 / jour pendant 7 jours' }
    ]},
    { label: 'Parodontie', color: 'blue', drugs: [
      { name: 'BAIN DE BOUCHE', dosage: '0.12%', forme: 'Flacon', posologie: '2 rincages / jour pendant 10 jours' },
      { name: 'GEL BUCCAL', dosage: '-', forme: 'Tube', posologie: 'Application locale soir' }
    ]},
    { label: 'Urgence Douleur', color: 'amber', drugs: [
      { name: 'KETOPROFENE', dosage: '100mg', forme: 'Comprimés', posologie: '1 comp x 2 / jour au milieu des repas' }
    ]}
  ];

  const applyPrescriptionShortcut = (preset: any) => {
    const newDrugs = preset.drugs.map((d: any, idx: number) => ({
      id: Date.now() + idx,
      name: d.name,
      dosage: d.dosage,
      forme: d.forme,
      posologie: d.posologie
    }));
    setDrugs(newDrugs);
    setHasChanges(true);
  };

  return (
    <div className="relative w-full h-full overflow-hidden">
      <div className="w-full h-full pr-0 transition-all duration-500">
        <div className="flex flex-col gap-6 bg-white/70 backdrop-blur-2xl border border-white/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2.5rem] p-8 h-full overflow-y-auto custom-scrollbar relative">

        <div className="sticky top-0 z-[60] -mt-2 -mx-2 mb-4 p-2 bg-white/40 backdrop-blur-3xl rounded-3xl border border-white/50 flex justify-between items-start shrink-0 transition-all duration-300">
          <div>
            <h2 className="text-3xl font-black text-primary tracking-tight leading-none" style={{ color: 'var(--primary)' }}>Studio Documentaire</h2>
            <p className="text-slate-500 mt-1 font-medium italic">Patient : <span className="font-bold text-slate-800 not-italic tracking-tight">{patientName}</span></p>
          </div>
          
          <div className="flex items-center gap-3">
            {(activeTab === 'honoraires' || activeTab === 'devis') && (
              <button
                onClick={() => setShowOdontoPanoramique(!showOdontoPanoramique)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all",
                  showOdontoPanoramique 
                    ? "bg-primary text-white shadow-lg shadow-primary/30" 
                    : "bg-white text-primary border border-primary/20 hover:bg-primary/5"
                )}
                style={showOdontoPanoramique ? { backgroundColor: 'var(--primary)' } : { color: 'var(--primary)', borderColor: 'var(--primary)' }}
              >
                <Calculator size={14} />
                {showOdontoPanoramique ? "Réduire Schéma" : "Afficher Schéma"}
              </button>
            )}

            {activeTab !== 'ai' && (
              <button 
                onClick={() => {
                  const nextMode = sideStudioType === 'PREVIEW' ? 'NONE' : 'PREVIEW';
                  setSideStudioType(nextMode);
                  if (nextMode === 'PREVIEW') handleGenerate(false, false, true);
                }}
                className={cn(
                  "flex items-center gap-2 px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border",
                  sideStudioType === 'PREVIEW' 
                    ? "bg-emerald-600 text-white border-emerald-500 shadow-lg shadow-emerald-500/30" 
                    : "bg-white text-slate-400 border-slate-200 hover:border-slate-300"
                )}
              >
                <Eye size={14}/> Aperçu Direct
              </button>
            )}

            <div className="bg-white/80 p-2.5 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-start gap-1">
              <label className="text-[9px] font-black text-slate-400 uppercase flex items-center gap-1 leading-none"><CalendarIcon size={10} /> Date</label>
              <input type="date" className="bg-transparent text-xs font-black text-slate-700 outline-none w-28 cursor-pointer" value={docDate} onChange={(e) => setDocDate(e.target.value)} />
            </div>
          </div>
        </div>

        <div className="flex bg-slate-200/50 p-1.5 rounded-2xl gap-1 overflow-x-auto shrink-0 relative z-50">
          <TabButton active={activeTab === 'ordonnance'} onClick={() => setActiveTab('ordonnance')} icon={<Pill size={16} />} label="Ordonnance" />
          <TabButton active={activeTab === 'certificat'} onClick={() => setActiveTab('certificat')} icon={<FileBadge size={16} />} label="Certificat" />
          <TabButton active={activeTab === 'devis'} onClick={() => setActiveTab('devis')} icon={<Calculator size={16} />} label="Devis" />
          <TabButton active={activeTab === 'honoraires'} onClick={() => setActiveTab('honoraires')} icon={<Receipt size={16} />} label="Note" />
          <TabButton active={activeTab === 'libre'} onClick={() => setActiveTab('libre')} icon={<Type size={16} />} label="Libre" />
          <TabButton active={activeTab === 'ai'} onClick={() => {setActiveTab('ai'); setSideStudioType('NONE');}} icon={<Brain size={16} className={activeTab === 'ai' ? "text-amber-300" : "text-slate-500"} />} label="Analyse IA" isAi />
        </div>

        <div className="flex-1 space-y-6 mt-4 relative">
          
          {activeTab === 'ordonnance' && (
            <div className="space-y-6 animate-in fade-in duration-500">
               
               {/* BARRE DE RACCOURCIS ELITE (ORDO) */}
               <div className="flex flex-wrap gap-3 p-5 bg-slate-50/50 rounded-[2rem] border border-slate-100 shadow-sm relative overflow-hidden group/bar">
                  <div className="flex items-center gap-4 px-4 mr-2 border-r border-slate-200 relative z-10">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/10">
                      <Zap size={16} />
                    </div>
                    <div className="hidden sm:block">
                      <span className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400 block leading-none mb-1">Raccourcis</span>
                      <span className="text-[10px] font-black uppercase tracking-widest text-primary">Protocoles Rapides</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 relative z-10">
                    {QUICK_PRESCRIPTIONS.map(preset => (
                      <button
                        key={preset.label}
                        onClick={() => applyPrescriptionShortcut(preset)}
                        className={cn(
                          "group px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 border flex items-center gap-2",
                          preset.color === 'rose' ? "bg-rose-50 border-rose-100 text-rose-600 hover:bg-rose-600 hover:text-white" :
                          preset.color === 'emerald' ? "bg-emerald-50 border-emerald-100 text-emerald-600 hover:bg-emerald-600 hover:text-white" :
                          preset.color === 'blue' ? "bg-blue-50 border-blue-100 text-blue-600 hover:bg-blue-600 hover:text-white" :
                          "bg-amber-50 border-amber-100 text-amber-600 hover:bg-amber-600 hover:text-white"
                        )}
                      >
                        <div className="w-1.5 h-1.5 rounded-full bg-current opacity-40 group-hover:opacity-100" />
                        {preset.label}
                      </button>
                    ))}
                  </div>
               </div>

               <AnimatePresence>
                {(loadingSmart || (smartSuggestion && !smartSuggestion.applied)) && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                    <div className="bg-primary/5 border border-primary/10 rounded-[1.5rem] p-4 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center text-primary">
                          {loadingSmart ? <Loader2 className="animate-spin" size={20} /> : <Zap size={20} />}
                        </div>
                        <div>
                          <h4 className="text-sm font-black text-primary uppercase tracking-tight">
                            {loadingSmart ? "Analyse du dossier..." : "Suggestion IA"}
                          </h4>
                          <p className="text-xs text-slate-500 font-medium">
                            {loadingSmart ? "Recherche du meilleur protocole..." : <>Protocole détecté : <span className="font-bold text-primary">{smartSuggestion?.protocol_name}</span></>}
                          </p>
                        </div>
                      </div>
                      {smartSuggestion && !smartSuggestion.applied && !loadingSmart && (
                        <button onClick={applySmartSuggestion} className="px-5 py-2 bg-primary text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-primary/20 hover:scale-105 transition-all">Appliquer</button>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="space-y-4">
                <div className="grid grid-cols-12 gap-4 px-4">
                  <div className="col-span-4"><label className={labelClass}>Médicament</label></div>
                  <div className="col-span-3"><label className={labelClass}>Dosage</label></div>
                  <div className="col-span-4"><label className={labelClass}>Posologie</label></div>
                </div>
                <div className="space-y-4">
                  {drugs.map((drug) => (
                    <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} key={drug.id} className="bg-white/40 p-5 rounded-[2rem] border border-white/60 hover:bg-white/80 transition-all group relative">
                      <div className="grid grid-cols-12 gap-6 items-start">
                        <div className="col-span-4 relative">
                          <input type="text" className={cn(inputClass, "font-black text-primary text-base")} style={{ color: 'var(--primary)' }} placeholder="MÉDICAMENT..." value={drug.name} onChange={(e) => updateDrug(drug.id, 'name', e.target.value.toUpperCase())} />
                        </div>
                        <div className="col-span-3">
                          <input type="text" className={cn(inputClass, "font-medium")} placeholder="Dose (ex: 1g, 500mg...)" value={drug.dosage} onChange={(e) => updateDrug(drug.id, 'dosage', e.target.value)} />
                        </div>
                        <div className="col-span-4">
                          <input type="text" className={cn(inputClass, "font-medium")} placeholder="Posologie (ex: 1x3/jour...)" value={drug.posologie} onChange={(e) => updateDrug(drug.id, 'posologie', e.target.value)} />
                        </div>
                        <div className="col-span-1 flex justify-center pt-3">
                          <button onClick={() => removeDrug(drug.id)} className="p-2 text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"><Trash2 size={18} /></button>
                        </div>
                      </div>

                      {/* STUDIO DE FORME ELITE v2.0 */}
                      <div className="mt-6 p-4 bg-slate-50/50 rounded-2xl border border-slate-100/50 relative overflow-hidden group/form">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                            <Zap size={12} className="text-primary" /> Architecture de la Forme
                          </span>
                          <div className="flex gap-1">
                            {['12', '16', '20', '30'].map(q => {
                              const isSelected = drug.forme.includes(`Bte de ${q}`);
                              return (
                                <button
                                  key={q}
                                  onClick={() => {
                                    const base = drug.forme.split(' (')[0] || 'Comprimés';
                                    updateDrug(drug.id, 'forme', `${base} (Bte de ${q})`);
                                  }}
                                  className={cn(
                                    "px-2 py-1 rounded-md text-[9px] font-black transition-all border",
                                    isSelected 
                                      ? "bg-emerald-600 text-white border-emerald-500 shadow-sm" 
                                      : "bg-white text-slate-400 border-slate-200 hover:border-primary/30 hover:text-primary"
                                  )}
                                >
                                  {q}
                                </button>
                              );
                            })}
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                          {[
                            { label: 'Sachets', icon: '📦' },
                            { label: 'Comprimés', icon: '💊' },
                            { label: 'Gélules', icon: '💊' },
                            { label: 'Flacon', icon: '🧪' },
                            { label: 'Bain de bouche', icon: '🧴' },
                            { label: 'Gel buccal', icon: '🧪' },
                            { label: 'Spray', icon: '💨' },
                            { label: 'Ampoules', icon: '💉' }
                          ].map(f => {
                            const isSelected = drug.forme.startsWith(f.label);
                            return (
                              <button
                                key={f.label}
                                onClick={() => {
                                  const suffix = drug.forme.includes(' (Bte') ? ` (${drug.forme.split(' (')[1]}` : "";
                                  updateDrug(drug.id, 'forme', f.label + suffix);
                                }}
                                className={cn(
                                  "group/btn flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] font-bold transition-all border relative",
                                  isSelected
                                    ? "bg-white text-primary border-primary shadow-md shadow-primary/10 ring-2 ring-primary/5"
                                    : "bg-white/50 text-slate-500 border-slate-200 hover:border-primary/40 hover:bg-white"
                                )}
                              >
                                <span className={cn("text-xs transition-transform group-hover/btn:scale-125", isSelected ? "scale-110" : "grayscale")}>{f.icon}</span>
                                {f.label}
                                {isSelected && <motion.div layoutId={`active-forme-${drug.id}`} className="absolute -top-1 -right-1 w-2 h-2 bg-primary rounded-full shadow-[0_0_8px_var(--primary)]" />}
                              </button>
                            );
                          })}
                          
                          <div className="h-8 w-[1px] bg-slate-200 mx-1" />
                          
                          <div className="relative flex-1 min-w-[120px]">
                            <input 
                              type="text" 
                              placeholder="Forme personnalisée..."
                              className="w-full bg-white/80 border border-dashed border-slate-300 px-3 py-2 rounded-xl text-[11px] font-bold text-primary outline-none focus:border-primary focus:ring-4 focus:ring-primary/5 transition-all placeholder:text-slate-300"
                              value={drug.forme.includes(' (Bte') ? "" : (['Sachets', 'Comprimés', 'Gélules', 'Flacon', 'Bain de bouche', 'Gel buccal', 'Spray', 'Ampoules'].some(x => drug.forme.startsWith(x)) ? "" : drug.forme)}
                              onChange={(e) => updateDrug(drug.id, 'forme', e.target.value)}
                            />
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
                <button onClick={addDrug} className={addButtonClass}><Plus size={18} /> Ajouter une prescription</button>
              </div>
            </div>
          )}

          {activeTab === 'certificat' && (
             <div className="space-y-8 animate-in fade-in duration-500 max-w-2xl mx-auto py-8">
              <div className="bg-primary/5 rounded-[2.5rem] border border-primary/10 p-10 space-y-8">
                <div>
                  <label className={labelClass}>Type de certificat</label>
                  <div className="grid grid-cols-2 gap-3">
                    {['Repos médical', 'Arrêt de travail', 'Certificat d\'aptitude'].map((type) => (
                      <button key={type} onClick={() => setCertifType(type)} className={cn("px-6 py-4 rounded-2xl text-xs font-black uppercase tracking-widest transition-all border", certifType === type ? "bg-primary text-white border-primary shadow-lg shadow-primary/20" : "bg-white text-slate-500 border-slate-100 hover:border-primary/30")}>
                        {type}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="pt-4">
                  <div className="flex justify-between items-center mb-4"><label className={labelClass + " mb-0"}>Durée : {certifDays} jours</label></div>
                  <input type="range" min="1" max="30" step="1" value={certifDays} onChange={(e) => setCertifDays(parseInt(e.target.value))} className="w-full h-3 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-primary" />
                </div>
              </div>
            </div>
          )}

          {(activeTab === 'devis' || activeTab === 'honoraires') && (
            <AccountingStudio 
              patientId={patientId || '0'}
              items={items}
              setItems={setItems}
              paymentMode={paymentMode}
              setPaymentMode={(mode) => setPaymentMode(mode as PaymentMode)}
              showOdontoPanoramique={showOdontoPanoramique}
              odontogramMode={odontogramMode}
              setOdontogramMode={setOdontogramMode}
              groupSelectedTeeth={groupSelectedTeeth}
              handleToothDirectClick={handleToothDirectClick}
              selectTeethGroup={selectTeethGroup}
              groupTreatmentName={groupTreatmentName}
              setGroupTreatmentName={setGroupTreatmentName}
              groupTreatmentPrice={groupTreatmentPrice}
              setGroupTreatmentPrice={setGroupTreatmentPrice}
              applyGroupTreatment={applyGroupTreatment}
              handleTeethFromOdontogram={handleTeethFromOdontogram}
              addEmptyRow={addEmptyAccountingRow}
              removeItem={removeItem}
              updateItem={updateItem}
              handleActSearch={handleActSearch}
              activeActSearchId={activeActSearchId}
              actSuggestions={actSuggestions}
              applyActSuggestion={applyActSuggestion}
              calculateTotal={calculateTotal}
            />
          )}

          {activeTab === 'libre' && (
            <div className="space-y-6 animate-in fade-in duration-500 h-full flex flex-col">
              <div><label className={labelClass}>Titre</label><input type="text" className={cn(inputClass, "font-black text-lg")} value={libreTitle} onChange={(e) => setLibreTitle(e.target.value)} /></div>
              <div className="flex-1"><label className={labelClass}>Contenu</label><textarea className={cn(inputClass, "h-96 resize-none custom-scrollbar leading-relaxed text-base")} value={libreContent} onChange={(e) => setLibreContent(e.target.value)} /></div>
            </div>
          )}

          {activeTab === 'ai' && (
            <div className="animate-in fade-in zoom-in-95 duration-700 flex-1 flex flex-col min-h-0 bg-slate-900 rounded-[2.5rem] p-8 shadow-2xl border border-blue-500/20">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-2xl flex items-center justify-center text-blue-400 border border-blue-500/30">
                    <Brain size={28} />
                  </div>
                  <div>
                    <h3 className="text-xl font-black text-white tracking-tight">Rapport Clinique Intelligent</h3>
                    <p className="text-blue-400 text-[10px] font-black uppercase tracking-widest">Analyse motorisée par SANINOVA AI</p>
                  </div>
                </div>
                {!aiReport && !loadingAi && (
                  <button 
                    onClick={handleGenerateAI}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-black uppercase tracking-widest transition-all shadow-lg shadow-blue-600/30 flex items-center gap-2"
                  >
                    <Zap size={16} /> Lancer l'Analyse
                  </button>
                )}
              </div>
              <div className="flex-1 overflow-y-auto custom-scrollbar pr-4 text-slate-300 prose prose-invert max-w-none prose-headings:text-blue-400 prose-strong:text-white">
                {loadingAi ? (
                  <div className="h-full flex flex-col items-center justify-center gap-4">
                    <Loader2 className="w-12 h-12 animate-spin text-blue-500" />
                    <p className="text-sm font-black text-blue-400 uppercase tracking-widest animate-pulse">Synthèse neuronale en cours...</p>
                  </div>
                ) : aiReport ? (
                  <ReactMarkdown>{aiReport}</ReactMarkdown>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-4 opacity-50">
                    <AlertCircle size={48} />
                    <p className="font-bold text-center">Cliquez sur "Lancer l'Analyse" pour générer un diagnostic assisté.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="mt-8 flex items-center justify-between pt-8 border-t border-slate-100 shrink-0 relative z-30">
          <div className="flex items-center gap-4">
            <button onClick={() => handleGenerate(true)} disabled={loading || activeTab === 'ai'} className="flex items-center gap-3 px-8 py-4 bg-primary text-white rounded-2xl font-black uppercase text-[12px] tracking-widest shadow-xl shadow-primary/20 hover:-translate-y-1 transition-all active:scale-95 disabled:opacity-40" style={{ backgroundColor: 'var(--primary)' }}>
              {loading && !pendingPrint ? <Loader2 className="animate-spin" size={18} /> : <Archive size={18} />}
              Archiver
            </button>
            <button onClick={() => handleGenerate(true, true)} disabled={loading || activeTab === 'ai'} className="flex items-center gap-3 px-8 py-4 bg-slate-800 text-white rounded-2xl font-black uppercase text-[12px] tracking-widest shadow-xl shadow-slate-800/20 hover:-translate-y-1 transition-all active:scale-95 disabled:opacity-40">
              {loading && pendingPrint ? <Loader2 className="animate-spin" size={18} /> : <Printer size={18} />}
              Archiver & Imprimer
            </button>
          </div>
          {activeTab === 'ordonnance' && hasChanges && (
            <button onClick={handleSavePreference} className="flex items-center gap-2 text-emerald-600 font-bold text-xs hover:underline"><Save size={14} /> Enregistrer mes préférences</button>
          )}
        </div>
      </div>
      </div>

      <AnimatePresence>
        {sideStudioType === 'PREVIEW' && pdfUrl && (
          <motion.div 
            initial={{ x: 600, opacity: 0 }} 
            animate={{ x: 0, opacity: 1 }} 
            exit={{ x: 600, opacity: 0 }} 
            className="fixed top-0 right-0 w-[650px] h-full bg-white shadow-[-30px_0_100px_rgba(0,0,0,0.15)] z-[100] flex flex-col border-l border-slate-200"
          >
            <div className="p-8 border-b border-slate-100 flex items-center justify-between bg-white relative z-10">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary border border-primary/10">
                  <Eye size={24} />
                </div>
                <div>
                  <h3 className="font-black text-slate-900 uppercase tracking-tight text-lg">Aperçu Haute-Fidélité</h3>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Rendu Temps Réel Elite Edition</p>
                </div>
              </div>
              <button 
                onClick={() => setSideStudioType('NONE')} 
                className="w-12 h-12 flex items-center justify-center rounded-2xl bg-slate-50 text-slate-400 hover:bg-rose-50 hover:text-rose-500 transition-all active:scale-95"
              >
                <X size={24} />
              </button>
            </div>
            
            <div className="flex-1 bg-slate-800/5 relative p-4 flex flex-col">
              <div className="flex-1 rounded-3xl overflow-hidden shadow-2xl border border-slate-200 bg-white relative">
                <iframe 
                  src={pdfUrl} 
                  className="w-full h-full border-none" 
                  title="PDF Preview" 
                />
                {loading && (
                  <div className="absolute inset-0 bg-white/80 backdrop-blur-md flex flex-col items-center justify-center gap-4 animate-in fade-in duration-300">
                    <div className="relative">
                      <Loader2 className="animate-spin text-primary" size={64} />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <Zap size={24} className="text-primary animate-pulse" />
                      </div>
                    </div>
                    <span className="text-[10px] font-black text-primary uppercase tracking-[0.3em] animate-pulse">Génération Elite...</span>
                  </div>
                )}
              </div>
            </div>

            <div className="p-8 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Connecté au moteur de rendu v5.5</span>
              </div>
              <div className="text-[10px] font-bold text-slate-300 italic">SANINOVA Intelligence Hub</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {showPrintWarning && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-slate-900/40 backdrop-blur-md">
          <div className="bg-white rounded-[2.5rem] p-10 max-w-md w-full shadow-2xl border border-white relative">
            <button onClick={() => setShowPrintWarning(false)} className="absolute top-6 right-6 text-slate-300 hover:text-slate-500"><X size={24} /></button>
            <div className="w-20 h-20 bg-amber-50 text-amber-500 rounded-3xl flex items-center justify-center mb-6"><AlertTriangle size={40} /></div>
            <h3 className="text-2xl font-black text-slate-800 leading-tight">Attention : Sans Archivage</h3>
            <p className="text-slate-500 mt-3 font-medium">L'impression seule ne conserve aucune trace historique.</p>
            <div className="flex gap-4 mt-10">
              <button onClick={() => setShowPrintWarning(false)} className="flex-1 py-4 bg-slate-100 rounded-2xl font-bold">Annuler</button>
              <button onClick={() => handleGenerate(false, true)} className="flex-1 py-4 bg-[#003380] text-white rounded-2xl font-bold">Imprimer</button>
            </div>
          </div>
        </div>
      )}
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