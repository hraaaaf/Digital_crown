import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../../services/api';
import { 
  FileText, 
  Eye, 
  Search, 
  Loader2, 
  Calendar, 
  Download,
  Filter,
  ArchiveX,
  Pill,
  Calculator,
  FileBadge,
  Receipt
} from 'lucide-react';
import { cn } from '../../utils/cn';

// NOUVELLE INTERFACE ALIGNÉE AVEC LE BACKEND
interface DocumentInfo {
  id: string;
  name: string;
  type: string;
  date: string;
  url: string;
}

export const PatientDocuments = () => {
  const { id } = useParams();
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        // Nouvelle Route Backend : Scanne le disque dur
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

  const filteredDocs = docs.filter(d => 
    d.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.date.includes(searchTerm)
  );

  const getDocIcon = (type: string, className: string) => {
    switch (type.toUpperCase()) {
      case 'ORDONNANCE': return <Pill className={className} />;
      case 'DEVIS': return <Calculator className={className} />;
      case 'CERTIFICAT': return <FileBadge className={className} />;
      case 'NOTE': return <Receipt className={className} />;
      default: return <FileText className={className} />;
    }
  };

  if (loading) return (
    <div className="py-20 flex flex-col items-center justify-center gap-4">
      <Loader2 className="animate-spin text-[#003380]" size={40} />
      <p className="text-slate-400 font-black uppercase tracking-widest text-[10px]">Ouverture du coffre-fort...</p>
    </div>
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-700 p-2">
      
      {/* BARRE DE RECHERCHE ARCHIVES */}
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="relative w-full md:w-96 group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-[#003380] transition-colors" size={18} />
          <input 
            type="text" 
            placeholder="Filtrer par type (Note, Devis...)" 
            className="w-full pl-12 pr-4 py-3 bg-white/60 backdrop-blur-md border border-slate-200 rounded-2xl text-sm font-bold focus:ring-4 focus:ring-[#003380]/5 outline-none transition-all placeholder:text-slate-400"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2 px-4 py-3 bg-blue-50 text-[#003380] rounded-xl border border-blue-100 shadow-sm">
          <Filter size={16} />
          <span className="text-xs font-black uppercase tracking-widest">{filteredDocs.length} Documents</span>
        </div>
      </div>

      {/* GRILLE DE DOCUMENTS PREMIUM */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredDocs.map((doc) => (
          <div key={doc.id} className="group bg-white/70 backdrop-blur-xl p-6 rounded-[2.5rem] border border-white shadow-[0_4px_20px_rgb(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgb(0,51,128,0.12)] hover:-translate-y-1.5 transition-all duration-500 relative overflow-hidden">
            
            {/* Effet visuel de fond pour le type de doc */}
            <div className="absolute -right-4 -top-4 opacity-[0.03] group-hover:opacity-[0.06] transition-opacity">
               {getDocIcon(doc.type, "w-[120px] h-[120px]")}
            </div>

            <div className="flex justify-between items-start mb-6 relative z-10">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-50 to-white text-[#003380] rounded-2xl flex items-center justify-center border border-blue-100 shadow-sm group-hover:bg-[#003380] group-hover:text-white transition-colors duration-500">
                {getDocIcon(doc.type, "w-7 h-7")}
              </div>
              <span className={cn(
                "px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest border",
                doc.type.toUpperCase() === 'NOTE' ? "bg-emerald-50 text-emerald-600 border-emerald-100" : "bg-blue-50 text-blue-600 border-blue-100"
              )}>
                {doc.type}
              </span>
            </div>
            
            <div className="relative z-10 mb-8">
              <h3 className="font-black text-slate-800 text-lg truncate pr-4 leading-tight" title={doc.name}>{doc.name}</h3>
              <div className="flex items-center gap-2 text-slate-400 text-[11px] font-bold mt-2 uppercase tracking-wide">
                <Calendar size={14} className="text-blue-400" /> 
                Généré le {doc.date}
              </div>
            </div>

            {/* ACTIONS RAPIDES */}
            <div className="grid grid-cols-2 gap-3 relative z-10">
              <a 
                href={`http://localhost:8000/${doc.url}`} 
                target="_blank" 
                rel="noreferrer" 
                className="flex items-center justify-center gap-2 py-3.5 bg-slate-50 border border-slate-100 hover:bg-slate-100 text-slate-600 rounded-2xl font-black text-xs uppercase tracking-widest transition-all active:scale-95"
              >
                <Eye size={16} /> Voir
              </a>
              <a 
                href={`http://localhost:8000/${doc.url}`} 
                download={doc.name}
                className="flex items-center justify-center gap-2 py-3.5 bg-gradient-to-br from-[#003380] to-blue-900 hover:shadow-lg text-white rounded-2xl font-black text-xs uppercase tracking-widest transition-all active:scale-95"
              >
                <Download size={16} /> Fichier
              </a>
            </div>
          </div>
        ))}

        {/* EMPTY STATE ARCHIVES */}
        {filteredDocs.length === 0 && (
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