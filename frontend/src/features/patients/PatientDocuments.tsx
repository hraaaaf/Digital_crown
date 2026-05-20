import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api, API_BASE } from '../../services/api';
import {
  FileText,
  Eye,
  Search,
  Loader2,
  Calendar,
  Download,
  Archive,
  ArchiveX,
  Pill,
  Calculator,
  FileBadge,
  Receipt,
  Trash2,
  Edit,
  FileX2,
} from 'lucide-react';
import { cn } from '../../utils/cn';

// INTERFACE ALIGNÉE AVEC LE BACKEND
interface DocumentInfo {
  id: string;
  name: string;
  type: string;
  date: string;
  url: string;
  file_exists?: boolean;
  clinical_data?: any;
  isDuplicate?: boolean;
}

export const PatientDocuments = () => {
  const { id } = useParams();
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const res = await api.get(`/patients/${id}/documents`);
        setDocs(res.data);
      } catch (err) {
        console.error("Erreur archives:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDocs();
  }, [id]);

  const handleDelete = async (docId: string) => {
    if (window.confirm("Êtes-vous sûr de vouloir supprimer ce document ?")) {
      try {
        await api.post(`/documents/${docId}/trash`);
        setDocs(docs.filter(d => d.id !== docId));
      } catch (err) {
        console.error("Erreur suppression:", err);
        alert("Erreur lors de la suppression.");
      }
    }
  };

  const handleEdit = (doc: DocumentInfo) => {
    if (!doc.clinical_data) {
      alert("Ce document ne possède pas de données structurées pour être régénéré.");
      return;
    }
    window.dispatchEvent(new CustomEvent('edit_document', { detail: doc }));
  };

  const getDocIcon = (type: string, className: string) => {
    switch (type.toUpperCase()) {
      case 'ORDONNANCE': return <Pill className={className} />;
      case 'DEVIS': return <Calculator className={className} />;
      case 'CERTIFICAT': return <FileBadge className={className} />;
      case 'NOTE': return <Receipt className={className} />;
      default: return <FileText className={className} />;
    }
  };

  // Logique de filtrage et détection de doublons
  const filtered = docs.filter(d => 
    d.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.date.includes(searchTerm)
  );

  const getActsSignature = (data: any) => {
    if (!data) return null;
    const items = data.items || data.payments || [];
    if (items.length === 0) return null;
    const acts = items.map((i: any) => `${(i.acte || i.description || '').trim().toLowerCase()}:${String(i.dent || '0').trim().toLowerCase()}`).sort();
    return acts.join('|');
  };

  const signatures = new Set<string>();
  const docsWithDuplicates = filtered.map(doc => {
    let isDuplicate = false;
    const sig = getActsSignature(doc.clinical_data);
    if (sig) {
      const fullSig = `${doc.type}-${sig}`;
      if (signatures.has(fullSig)) {
        isDuplicate = true;
      } else {
        signatures.add(fullSig);
      }
    }
    return { ...doc, isDuplicate };
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-40 gap-4">
        <Loader2 className="animate-spin text-primary" size={40} />
        <p className="text-slate-400 font-black uppercase tracking-widest text-[10px]">Chargement de la bibliothèque...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-700 h-full flex flex-col">
      
      <div className="flex items-center gap-4 bg-white/40 backdrop-blur-md p-3 rounded-2xl border border-white/60 shadow-sm shrink-0">
        <div className="relative group flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text" 
            placeholder="Rechercher dans l'historique..." 
            className="w-full pl-12 pr-4 py-3 bg-white/60 backdrop-blur-md border border-slate-200 rounded-2xl text-sm font-bold focus:ring-4 outline-none transition-all"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2 px-4 py-3 bg-primary/5 rounded-xl border border-primary/10 shadow-sm text-primary">
          <Archive size={18} />
          <span className="text-xs font-black uppercase tracking-widest">{filtered.length} Documents</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {docsWithDuplicates.map((doc) => (
          <div key={doc.id} className={cn(
            "group backdrop-blur-xl p-6 rounded-[2.5rem] shadow-[0_4px_20px_rgb(0,0,0,0.03)] hover:-translate-y-1.5 transition-all duration-500 relative overflow-hidden",
            doc.isDuplicate
              ? "bg-rose-50/80 border-2 border-rose-300 shadow-[0_4px_20px_rgba(225,29,72,0.1)]"
              : doc.file_exists === false
                ? "bg-amber-50/60 border border-amber-200 opacity-80"
                : "bg-card border border-border-main hover:shadow-[0_8px_30px_rgba(var(--primary-rgb),0.12)]"
          )}>

            {doc.isDuplicate && (
              <div className="absolute top-0 inset-x-0 bg-rose-500 text-white text-[9px] font-black py-1.5 text-center tracking-widest uppercase z-20 shadow-md">
                Doublon de contenu détecté
              </div>
            )}

            {doc.file_exists === false && !doc.isDuplicate && (
              <div className="absolute top-0 inset-x-0 bg-amber-400 text-amber-900 text-[9px] font-black py-1.5 text-center tracking-widest uppercase z-20 flex items-center justify-center gap-1.5">
                <FileX2 size={10} /> Fichier physique manquant
              </div>
            )}

            <div className="flex justify-between items-start mb-6 relative z-10">
              <div className={cn(
                "w-14 h-14 rounded-2xl flex items-center justify-center shadow-sm transition-colors duration-500",
                doc.isDuplicate ? "bg-rose-100 text-rose-600" : "bg-gradient-to-br from-primary/5 to-white text-primary border border-primary/20 group-hover:bg-primary group-hover:text-white"
              )}>
                {getDocIcon(doc.type, "w-7 h-7")}
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => handleEdit(doc)} className="p-1.5 rounded-lg bg-orange-50 text-orange-600 border border-orange-100 hover:bg-orange-600 hover:text-white transition-all shadow-sm">
                  <Edit size={14} />
                </button>
                <button onClick={() => handleDelete(doc.id)} className="p-1.5 rounded-lg bg-rose-50 text-rose-600 border border-rose-100 hover:bg-rose-600 hover:text-white transition-all shadow-sm">
                  <Trash2 size={14} />
                </button>
                <span className={cn(
                  "px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest border",
                  doc.type.toUpperCase() === 'NOTE' ? "bg-emerald-50 text-emerald-600 border-emerald-100" : "bg-primary/10 text-primary border-primary/20"
                )}>
                  {doc.type}
                </span>
              </div>
            </div>
            
            <div className="relative z-10 mb-8">
              <h3 className="font-black text-text-main text-lg truncate pr-4 leading-tight">{doc.name}</h3>
              <div className="flex items-center gap-2 text-slate-400 text-[11px] font-bold mt-2 uppercase tracking-wide">
                <Calendar size={14} className="text-primary/60" /> Généré le {doc.date}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 relative z-10">
              {doc.file_exists === false ? (
                <div className="col-span-2 flex items-center justify-center gap-2 py-3.5 bg-amber-50 border border-amber-200 text-amber-600 rounded-2xl font-black text-xs uppercase tracking-widest">
                  <FileX2 size={16} /> Fichier introuvable
                </div>
              ) : (
                <>
                  <a
                    href={`${API_BASE}/api/${doc.url.startsWith('/') ? doc.url.substring(1) : doc.url}`}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center justify-center gap-2 py-3.5 bg-slate-50 border border-slate-100 hover:bg-slate-100 text-slate-600 rounded-2xl font-black text-xs uppercase tracking-widest transition-all active:scale-95"
                  >
                    <Eye size={16} /> Voir
                  </a>
                  <a
                    href={`${API_BASE}/api/${doc.url.startsWith('/') ? doc.url.substring(1) : doc.url}`}
                    download={doc.name}
                    className="flex items-center justify-center gap-2 py-3.5 bg-gradient-to-br from-primary to-secondary text-white rounded-2xl font-black text-xs uppercase tracking-widest transition-all shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95"
                  >
                    <Download size={16} /> Fichier
                  </a>
                </>
              )}
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="col-span-full py-20 text-center flex flex-col items-center">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-[2.5rem] bg-slate-50 border border-slate-100 mb-6 text-slate-300 shadow-inner">
              <ArchiveX size={40} />
            </div>
            <h3 className="text-slate-800 font-black text-xl mb-1">Aucune archive médicale</h3>
            <p className="text-slate-400 font-medium text-sm">Les documents générés apparaîtront ici.</p>
          </div>
        )}
      </div>
    </div>
  );
};