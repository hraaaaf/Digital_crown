import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Pill, 
  FileBadge, 
  Receipt, 
  Calculator, 
  Plus, 
  Trash2, 
  Printer, 
  Loader2, 
  FileText,
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
  ChevronUp,
  ChevronDown,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { cn } from '../../utils/cn';
import { api } from '../../services/api';
import { Odontogram } from '../../components/odontogram';
import { OdontogramSVG } from '../../components/odontogram/OdontogramSVG';
import type { SelectedSurfaceData } from '../../components/odontogram/types';

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
interface DocumentHubProps { patientId: string | undefined; patientName: string; }

interface ClinicalCategory { id: number; label: string; }
interface ClinicalProtocol { id: number; category_id: number; variant_name: string; medications_json: any; }
interface MedicationOut { id: number; nom: string; dosage: string; forme: string; usage_count: number; }
interface ActOut { id: number; name: string; base_price: number; }

export const DocumentHub: React.FC<DocumentHubProps> = ({ patientId, patientName }) => {
  const [activeTab, setActiveTab] = useState<DocumentType>('ordonnance');
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);

  const [aiReport, setAiReport] = useState<string | null>(null);
  const [loadingAi, setLoadingAi] = useState(false);

  const [showPreview, setShowPreview] = useState(false);
  const [showPrintWarning, setShowPrintWarning] = useState(false);
  const [pendingPrint, setPendingPrint] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const [drugs, setDrugs] = useState<DrugItem[]>([{ id: 1, name: '', dosage: '', forme: '', posologie: '' }]);
  const [certifType, setCertifType] = useState('Repos médical'); 
  const [certifDays, setCertifDays] = useState(3);
  const [items, setItems] = useState<PriceItem[]>([{ id: 1, description: 'Consultation spécialisée', dent: '0', price: 400 }]);
  const [paymentMode, setPaymentMode] = useState<PaymentMode>('Espèces');
  const [libreTitle, setLibreTitle] = useState('Note Médicale');
  const [libreContent, setLibreContent] = useState('');

  const [diagnosticQuery, setDiagnosticQuery] = useState('');
  const [suggestedCategories, setSuggestedCategories] = useState<ClinicalCategory[]>([]);
  const [availableProtocols, setAvailableProtocols] = useState<ClinicalProtocol[]>([]);
  const [activeDrugSearchId, setActiveDrugSearchId] = useState<number | null>(null);
  const [medicationSuggestions, setMedicationSuggestions] = useState<MedicationOut[]>([]);
  const [activeActSearchId, setActiveActSearchId] = useState<number | null>(null);
  const [actSuggestions, setActSuggestions] = useState<ActOut[]>([]);

  const [selectedTeethFromOdontogram, setSelectedTeethFromOdontogram] = useState<SelectedSurfaceData[]>([]);
  const [showOdontogram, setShowOdontogram] = useState(true);

  // ── Mode du schéma : acte individuel (via Odontogram) ou traitement groupé (bridge, PAP, totale) ──
  const [odontogramMode, setOdontogramMode] = useState<'individual' | 'group'>('individual');
  const [groupSelectedTeeth, setGroupSelectedTeeth] = useState<number[]>([]);
  const [groupTreatmentName, setGroupTreatmentName] = useState('');
  const [groupTreatmentPrice, setGroupTreatmentPrice] = useState<number | ''>('');

  const handleTeethFromOdontogram = useCallback((teeth: SelectedSurfaceData[]) => {
    setSelectedTeethFromOdontogram(teeth);

    // Utiliser la forme fonctionnelle pour éviter la dépendance à `items`
    setItems(prevItems => {
      // Clés stables des traitements actuellement sélectionnés
      const activeKeys = new Set<string>();
      teeth.forEach(tooth => {
        tooth.treatments.forEach(tr => {
          activeKeys.add(`${tooth.toothNumber}::${tr.id}`);
        });
      });

      // 1. Supprimer les items odontogramme désélectionnés
      // 2. Conserver les items modifiés manuellement (même ceux de l'odo)
      const surviving = prevItems.filter(item =>
        !item._odontogramKey || activeKeys.has(item._odontogramKey)
      );

      // 3. Ajouter uniquement les nouveaux traitements
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

      // Retirer la ligne "Consultation spécialisée" par défaut si on ajoute des actes
      const isDefault = (i: PriceItem) =>
        i.description === 'Consultation spécialisée' && i.price === 400 && i.dent === '0' && !i._odontogramKey;
      const base = newItems.length > 0 ? surviving.filter(i => !isDefault(i)) : surviving;

      return [...base, ...newItems];
    });
  }, []); // Pas de dépendance à items !

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
    setGroupSelectedTeeth([]);
    setGroupTreatmentName('');
    setGroupTreatmentPrice('');
  };

  const addDrug = () => setDrugs([...drugs, { id: Date.now(), name: '', dosage: '', forme: '', posologie: '' }]);
  const removeDrug = (id: number) => setDrugs(drugs.filter(d => d.id !== id));
  const updateDrug = (id: number, field: keyof DrugItem, value: string) => {
    setDrugs(drugs.map(d => d.id === id ? { ...d, [field]: value } : d));
  };

  const addItem = () => setItems([...items, { id: Date.now(), description: '', dent: '0', price: 0 }]);
  const removeItem = (id: number) => setItems(items.filter(i => i.id !== id));
  const updateItem = (id: number, field: keyof PriceItem, value: string | number) => {
    const finalValue = field === 'price' ? (Number(value) || 0) : value;
    setItems(items.map(i => i.id === id ? { ...i, [field]: finalValue } : i));
  };
  
  const calculateTotal = () => items.reduce((sum, item) => sum + (Number(item.price) || 0), 0);

  const handleGenerate = async (archive: boolean = false, print: boolean = false) => {
    if (!patientId || activeTab === 'ai') return; 
    setLoading(true);
    if (print) setPendingPrint(true);

    try {
      const payload: any = {
        type: activeTab === 'honoraires' ? 'note' : activeTab,
        patient_id: parseInt(patientId, 10),
        data: {}
      };

      if (activeTab === 'ordonnance') {
        payload.data = { medications: drugs.map(d => ({ nom: d.name, dosage: d.dosage, forme: d.forme || "Sachets", posologie: d.posologie })), doc_date: docDate };
      } else if (activeTab === 'certificat') {
        payload.data = { reason: certifType, days: Number(certifDays) || 0, start_date: docDate, is_work_stop: certifType === 'Arrêt de travail' };
      } else if (activeTab === 'libre') {
        payload.data = { title: libreTitle, content: libreContent, doc_date: docDate };
      } else if (activeTab === 'devis' || activeTab === 'honoraires') {
        const commonItems = items.map(i => ({ 
          acte: i.description, 
          dent: i.dent || "0", 
          dents: i.toothNumbers || [],
          prix_unitaire: parseFloat(i.price.toString()) || 0, 
          montant: parseFloat(i.price.toString()) || 0, 
          date: docDate, 
          mode_reglement: paymentMode 
        }));
        
        // surface est un string (ToothSurface), le backend attend List[str] → wrap dans un tableau
        const robustTeethData = selectedTeethFromOdontogram.map(t => {
          const extractedSurfaces: string[] = t.surface ? [t.surface as string] : [];
          return {
            tooth_number: t.toothNumber,
            treatments: t.treatments.map(tr => ({ code: tr.code || "ACT", name: tr.name, price: tr.price || 0 })),
            surfaces: extractedSurfaces,
            notes: ""
          };
        });

        payload.data = activeTab === 'devis' 
          ? { 
              items: commonItems, 
              doc_date: docDate,
              teeth_data: robustTeethData
            } 
          : { 
              payments: commonItems, 
              doc_date: docDate,
              teeth_data: robustTeethData
            };
      }

      const response = await api.post(`/documents/generate?archive=${archive}`, payload);
      
      if (response.data.pdf_url) {
        setPdfUrl(`http://localhost:8000/${response.data.pdf_url}?t=${Date.now()}`);
      }
      
      if (activeTab === 'ordonnance' && archive) {
        await api.post('/prescriptions/learn', { medications: payload.data.medications });
      }

      if ((activeTab === 'devis' || activeTab === 'honoraires') && archive) {
        const learnedActes = items.map(i => ({
          name: i.description,
          price_applied: parseFloat(i.price.toString()) || 0
        }));
        await api.post('/actes/catalog/learn', { acts: learnedActes });
      }

    } catch (error) { 
        console.error("Erreur lors de la génération :", error); 
    } finally { 
        setLoading(false); 
        setShowPrintWarning(false); 
    }
  };

  useEffect(() => {
    if (!showPreview || activeTab === 'ai') return;
    const timer = setTimeout(() => handleGenerate(false, false), 1500); 
    return () => clearTimeout(timer);
  }, [showPreview, drugs, items, certifType, certifDays, paymentMode, libreTitle, libreContent, docDate, activeTab, selectedTeethFromOdontogram]);

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
    <div className="flex flex-col xl:flex-row gap-8 w-full h-full">
      
      <div className={cn(
        "flex flex-col gap-6 bg-white/70 backdrop-blur-2xl border border-white/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2.5rem] p-8 overflow-y-auto transition-all duration-500",
        showPreview ? "w-full xl:w-1/2" : "w-full"
      )}>
        
        <div className="flex justify-between items-start mb-2 shrink-0">
          <div>
            <h2 className="text-3xl font-black text-[#003380] tracking-tight leading-none">Studio Documentaire</h2>
            <p className="text-slate-500 mt-1 font-medium italic">Patient : <span className="font-bold text-slate-800 not-italic tracking-tight">{patientName}</span></p>
          </div>
          
          <div className="flex items-center gap-3">
            {activeTab !== 'ai' && (
              <button 
                onClick={() => setShowPreview(!showPreview)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border",
                  showPreview ? "bg-blue-50 text-[#003380] border-blue-100 shadow-sm" : "bg-white text-slate-400 border-slate-200 hover:border-slate-300"
                )}
              >
                {showPreview ? <EyeOff size={14}/> : <Eye size={14}/>}
                {showPreview ? "Désactiver Live" : "Activer Live"}
              </button>
            )}

            <div className="bg-white/80 p-2.5 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-start gap-1">
              <label className="text-[9px] font-black text-slate-400 uppercase flex items-center gap-1 leading-none"><CalendarIcon size={10} /> Date</label>
              <input type="date" className="bg-transparent text-xs font-black text-slate-700 outline-none w-28 cursor-pointer" value={docDate} onChange={(e) => setDocDate(e.target.value)} />
            </div>
          </div>
        </div>

        <div className="flex bg-slate-200/50 p-1.5 rounded-2xl gap-1 overflow-x-auto shrink-0">
          <TabButton active={activeTab === 'ordonnance'} onClick={() => setActiveTab('ordonnance')} icon={<Pill size={16} />} label="Ordonnance" />
          <TabButton active={activeTab === 'certificat'} onClick={() => setActiveTab('certificat')} icon={<FileBadge size={16} />} label="Certificat" />
          <TabButton active={activeTab === 'devis'} onClick={() => setActiveTab('devis')} icon={<Calculator size={16} />} label="Devis" />
          <TabButton active={activeTab === 'honoraires'} onClick={() => setActiveTab('honoraires')} icon={<Receipt size={16} />} label="Note" />
          <TabButton active={activeTab === 'libre'} onClick={() => setActiveTab('libre')} icon={<Type size={16} />} label="Libre" />
          <TabButton active={activeTab === 'ai'} onClick={() => {setActiveTab('ai'); setShowPreview(false);}} icon={<Brain size={16} className={activeTab === 'ai' ? "text-amber-300" : "text-slate-500"} />} label="Analyse IA" isAi />
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

              {/* SCHÉMA DENTAIRE — acte individuel ou traitement groupé */}
              {patientId && (
                <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">

                  {/* En-tête du bloc */}
                  <div className="flex items-center justify-between p-5 bg-gradient-to-r from-slate-50 to-white border-b border-slate-100">
                    <button
                      onClick={() => setShowOdontogram(!showOdontogram)}
                      className="flex items-center gap-3 flex-1 text-left"
                    >
                      <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center shrink-0">
                        <Calculator className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-bold text-slate-800">Schéma dentaire</h3>
                        <p className="text-sm text-slate-500">
                          {odontogramMode === 'individual'
                            ? selectedTeethFromOdontogram.length > 0
                              ? `${selectedTeethFromOdontogram.reduce((s, t) => s + t.treatments.length, 0)} acte(s) ajouté(s)`
                              : 'Cliquez une dent pour ajouter un acte'
                            : groupSelectedTeeth.length > 0
                              ? `${groupSelectedTeeth.length} dent(s) sélectionnée(s) — Bridge, PAP, Totale...`
                              : 'Cliquez plusieurs dents pour un bridge, PAP ou totale'
                          }
                        </p>
                      </div>
                    </button>

                    {/* Toggle mode individuel / groupé */}
                    <div className="flex items-center gap-2 shrink-0">
                      <div className="flex bg-slate-100 p-1 rounded-xl gap-1">
                        <button
                          onClick={() => setOdontogramMode('individual')}
                          className={cn(
                            "px-3 py-1.5 rounded-lg text-xs font-bold transition-all",
                            odontogramMode === 'individual'
                              ? "bg-white text-[#003380] shadow-sm"
                              : "text-slate-400 hover:text-slate-600"
                          )}
                        >
                          Acte
                        </button>
                        <button
                          onClick={() => setOdontogramMode('group')}
                          className={cn(
                            "px-3 py-1.5 rounded-lg text-xs font-bold transition-all",
                            odontogramMode === 'group'
                              ? "bg-white text-emerald-600 shadow-sm"
                              : "text-slate-400 hover:text-slate-600"
                          )}
                        >
                          Groupé
                        </button>
                      </div>
                      {showOdontogram
                        ? <ChevronUp className="w-5 h-5 text-slate-400" />
                        : <ChevronDown className="w-5 h-5 text-slate-400" />
                      }
                    </div>
                  </div>

                  {showOdontogram && (
                    <div className="p-4 space-y-4">

                      {/* MODE ACTE INDIVIDUEL */}
                      {odontogramMode === 'individual' && (
                        <Odontogram
                          patientId={parseInt(patientId, 10)}
                          mode="SELECT_FOR_DOCUMENT"
                          onChange={handleTeethFromOdontogram}
                          showLegend={false}
                          compact={true}
                        />
                      )}

                      {/* MODE TRAITEMENT GROUPÉ */}
                      {odontogramMode === 'group' && (
                        <div className="space-y-4">

                          {/* Sélection rapide */}
                          <div className="flex flex-wrap gap-2">
                            {(['all', 'maxillaire', 'mandibule', 'none'] as const).map((g) => {
                              const labels = { all: 'Toutes (32)', maxillaire: 'Maxillaire', mandibule: 'Mandibule', none: 'Effacer' };
                              return (
                                <button
                                  key={g}
                                  onClick={() => selectTeethGroup(g)}
                                  className={cn(
                                    "px-3 py-1.5 rounded-xl text-xs font-bold border transition-all",
                                    g === 'none'
                                      ? "border-slate-200 text-slate-400 hover:border-red-300 hover:text-red-500 hover:bg-red-50"
                                      : "border-emerald-200 text-emerald-700 hover:bg-emerald-100 bg-emerald-50"
                                  )}
                                >
                                  {labels[g]}
                                </button>
                              );
                            })}
                          </div>

                          {/* Schéma cliquable — UN SEUL, multi-select vert */}
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

                          {/* Chips des dents sélectionnées */}
                          {groupSelectedTeeth.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 p-3 bg-emerald-50 rounded-xl border border-emerald-100">
                              {[...groupSelectedTeeth].sort((a, b) => a - b).map(n => (
                                <button
                                  key={n}
                                  onClick={() => handleToothDirectClick(n)}
                                  className="px-2 py-1 bg-white border border-emerald-300 text-emerald-700 text-xs font-black rounded-lg hover:bg-red-50 hover:border-red-300 hover:text-red-500 transition-all"
                                  title="Cliquer pour désélectionner"
                                >
                                  {n}
                                </button>
                              ))}
                            </div>
                          )}

                          {/* Formulaire traitement + prix */}
                          <div className="flex gap-3">
                            <div className="flex-1">
                              <label className={labelClass}>Traitement</label>
                              <input
                                type="text"
                                className={inputClass}
                                placeholder="Bridge 3 éléments, PAP totale résine, Totale bimaxillaire..."
                                value={groupTreatmentName}
                                onChange={(e) => setGroupTreatmentName(e.target.value)}
                              />
                            </div>
                            <div className="w-36 shrink-0">
                              <label className={labelClass}>Prix (MAD)</label>
                              <input
                                type="number"
                                className={cn(inputClass, "font-mono text-right text-[#003380] font-bold")}
                                value={groupTreatmentPrice}
                                onChange={(e) => setGroupTreatmentPrice(e.target.value === '' ? '' : Number(e.target.value))}
                              />
                            </div>
                          </div>

                          <button
                            onClick={applyGroupTreatment}
                            disabled={!groupTreatmentName.trim() || groupSelectedTeeth.length === 0}
                            className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-2xl font-bold flex items-center justify-center gap-2 transition-all shadow-md shadow-emerald-200"
                          >
                            <Plus size={18} />
                            Ajouter à la liste
                            {groupSelectedTeeth.length > 0 && (
                              <span className="bg-emerald-500 px-2 py-0.5 rounded-full text-xs">
                                {groupSelectedTeeth.length} dent{groupSelectedTeeth.length > 1 ? 's' : ''}
                              </span>
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              <div className="space-y-3 relative z-20">
                {items.map((item, index) => (
                  <div key={item.id} className="flex gap-3 items-end bg-white p-4 rounded-2xl border border-slate-100 shadow-sm transition-all group hover:border-[#003380]/30 hover:shadow-md">
                    <div className="flex-1 grid grid-cols-12 gap-3">
                      
                      <div className="col-span-12 md:col-span-6 flex flex-col justify-end relative">
                        <div className={cn(labelClass, index > 0 && "md:hidden", "flex items-center gap-2")}>
                          Acte / Soin
                          {item._odontogramKey && (
                            <span className="text-[8px] font-black px-1.5 py-0.5 rounded bg-blue-100 text-blue-500 tracking-wide">Odontogramme</span>
                          )}
                          {item.toothNumbers && item.toothNumbers.length > 1 && (
                            <span className="text-[8px] font-black px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-600 tracking-wide">Groupé</span>
                          )}
                        </div>
                        <input 
                          type="text" 
                          className={inputClass} 
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
                        <label className={cn(labelClass, index > 0 && "md:hidden whitespace-nowrap")}>Prix (MAD)</label>
                        <input
                          type="number"
                          className={cn(inputClass, "font-mono text-right text-[#003380] font-bold")}
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
                ))}
              </div>
              <button onClick={addItem} className={addButtonClass}><Plus size={20} /> Ajouter un acte manuellement</button>
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

      {showPreview && activeTab !== 'ai' && (
        <div className="w-full xl:w-1/2 bg-slate-200/50 rounded-[2.5rem] shadow-inner border border-slate-200/60 flex flex-col items-center justify-center overflow-hidden h-full animate-in slide-in-from-right-10 duration-500">
          {loading ? (
            <div className="text-center animate-pulse">
              <div className="w-24 h-24 bg-white rounded-3xl flex items-center justify-center mb-6 shadow-sm mx-auto"><Loader2 className="animate-spin text-[#003380]" size={40} /></div>
              <h3 className="text-xl font-bold text-slate-500 uppercase tracking-tighter">Mise à jour...</h3>
            </div>
          ) : pdfUrl ? (
            <iframe ref={iframeRef} src={`${pdfUrl}#toolbar=0&navpanes=0&scrollbar=1&view=FitH`} className="w-full h-full bg-white rounded-[2.5rem] shadow-2xl border-none relative z-10" title="Aperçu PDF" />
          ) : (
            <div className="text-center flex flex-col items-center justify-center text-slate-400 p-10 opacity-40">
              <FileText size={48} className="mb-4" />
              <h3 className="text-xl font-black">Mode Live Activé</h3>
              <p className="text-sm">Renseignez les champs pour voir l'aperçu.</p>
            </div>
          )}
        </div>
      )}

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