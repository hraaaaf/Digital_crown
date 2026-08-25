import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../../services/api';
import { usePatientStore } from '../../stores/usePatientStore';
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
  RefreshCcw,
  MoreHorizontal,
  Monitor,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { DocumentMobileBridge } from './DocumentMobileBridge';

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
  const [fetchError, setFetchError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionsOpenFor, setActionsOpenFor] = useState<string | null>(null);

  useEffect(() => {
    const fetchDocs = async () => {
      setLoading(true);
      setFetchError(false);
      try {
        const res = await api.get(`/patients/${id}/documents`);
        setDocs(res.data);
      } catch (err) {
        console.error('Erreur archives:', err);
        setDocs([]);
        setFetchError(true);
      } finally {
        setLoading(false);
      }
    };
    void fetchDocs();
  }, [id, reloadKey]);

  const handleDelete = async (docId: string) => {
    if (docId.startsWith('legacy:')) return;
    if (window.confirm('Êtes-vous sûr de vouloir mettre ce document à la corbeille ?')) {
      try {
        await api.post(`/documents/${docId}/trash`);
        setDocs(current => current.filter(d => d.id !== docId));
        setActionsOpenFor(null);
      } catch (err) {
        console.error('Erreur suppression:', err);
        alert('Erreur lors de la mise à la corbeille.');
      }
    }
  };

  const setEditingDoc = usePatientStore(state => state.setEditingDoc);

  const handleEdit = (doc: DocumentInfo) => {
    setActionsOpenFor(null);
    if (doc.id.startsWith('legacy:')) return;
    if (!doc.clinical_data) {
      alert('Ce document ne possède pas de données structurées pour être régénéré.');
      return;
    }
    setEditingDoc(doc);
  };

  const handleView = async (docId: string) => {
    try {
      const res = await api.get(`/documents/${encodeURIComponent(docId)}/download`, { responseType: 'blob' });
      const blobUrl = URL.createObjectURL(res.data);
      const opened = window.open(blobUrl, '_blank', 'noopener,noreferrer');
      if (!opened) URL.revokeObjectURL(blobUrl);
      else window.setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
    } catch (err) {
      console.error('Erreur lors de la visualisation:', err);
      alert("Impossible d'ouvrir le document.");
    }
  };

  const handleDownload = async (docId: string, filename: string) => {
    try {
      const res = await api.get(`/documents/${encodeURIComponent(docId)}/download`, { responseType: 'blob' });
      const a = document.createElement('a');
      const blobUrl = URL.createObjectURL(res.data);
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.setTimeout(() => URL.revokeObjectURL(blobUrl), 1_000);
    } catch (err) {
      console.error('Erreur lors du téléchargement:', err);
      alert('Impossible de télécharger le document.');
    }
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
      if (signatures.has(fullSig)) isDuplicate = true;
      else signatures.add(fullSig);
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

  if (fetchError) {
    return (
      <div className="flex flex-col items-center justify-center py-28 gap-4 text-center">
        <ArchiveX size={40} className="text-rose-400" />
        <div>
          <h3 className="text-slate-800 font-black text-lg">Impossible de charger l'historique</h3>
          <p className="text-slate-400 text-sm mt-1">Aucun état vide n'est déduit tant que le backend ne répond pas.</p>
        </div>
        <button type="button" onClick={() => setReloadKey(key => key + 1)} className="min-h-11 flex items-center gap-2 px-4 rounded-xl bg-primary text-white font-black text-xs uppercase tracking-widest">
          <RefreshCcw size={15} /> Réessayer
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-700 h-full flex flex-col">
      <div className="flex items-center gap-4 bg-white/40 backdrop-blur-md p-3 rounded-2xl border border-white/60 shadow-sm shrink-0">
        <div className="relative group flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input type="text" placeholder="Rechercher dans l'historique..." className="w-full pl-12 pr-4 py-3 bg-white/60 backdrop-blur-md border border-slate-200 rounded-2xl text-sm font-bold focus:ring-4 outline-none transition-all" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
        </div>
        <div className="flex items-center gap-2 px-4 py-3 bg-primary/5 rounded-xl border border-primary/10 shadow-sm text-primary">
          <Archive size={18} />
          <span className="text-xs font-black uppercase tracking-widest">{filtered.length} Documents</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {docsWithDuplicates.map((doc) => {
          const isLegacy = doc.id.startsWith('legacy:');
          const canonicalId = !isLegacy && /^\d+$/.test(doc.id) ? Number(doc.id) : null;
          return (
            <div key={doc.id} data-document-kind={isLegacy ? 'legacy' : 'canonical'} className={cn(
              'group backdrop-blur-xl p-6 rounded-[2.5rem] shadow-[0_4px_20px_rgb(0,0,0,0.03)] hover:-translate-y-1.5 transition-all duration-500 relative overflow-visible',
              doc.isDuplicate
                ? 'bg-rose-50/80 border-2 border-rose-300 shadow-[0_4px_20px_rgba(225,29,72,0.1)]'
                : doc.file_exists === false
                  ? 'bg-amber-50/60 border border-amber-200 opacity-80'
                  : 'bg-card border border-border-main hover:shadow-[0_8px_30px_rgba(var(--primary-rgb),0.12)]'
            )}>
              {doc.isDuplicate && <div className="absolute top-0 inset-x-0 bg-rose-500 text-white text-[9px] font-black py-1.5 text-center tracking-widest uppercase z-20 shadow-md rounded-t-[2.5rem]">Contenu similaire à vérifier</div>}
              {doc.file_exists === false && !doc.isDuplicate && <div className="absolute top-0 inset-x-0 bg-amber-400 text-amber-900 text-[9px] font-black py-1.5 text-center tracking-widest uppercase z-20 flex items-center justify-center gap-1.5 rounded-t-[2.5rem]"><FileX2 size={10} /> Fichier physique manquant</div>}

              <div className="flex justify-between items-start mb-6 relative z-30">
                <div className={cn('w-14 h-14 rounded-2xl flex items-center justify-center shadow-sm transition-colors duration-500', doc.isDuplicate ? 'bg-rose-100 text-rose-600' : 'bg-gradient-to-br from-primary/5 to-white text-primary border border-primary/20 group-hover:bg-primary group-hover:text-white')}>
                  {getDocIcon(doc.type, 'w-7 h-7')}
                </div>
                <div className="flex items-center gap-2 relative">
                  {!isLegacy && (
                    <div className="relative">
                      <button data-m4c-touch type="button" onClick={() => setActionsOpenFor(current => current === doc.id ? null : doc.id)} aria-label={`Actions du document ${doc.name}`} className="min-w-11 min-h-11 rounded-xl bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100 inline-flex items-center justify-center transition-all shadow-sm">
                        <MoreHorizontal size={19} />
                      </button>
                      {actionsOpenFor === doc.id && (
                        <div className="absolute right-0 top-12 z-50 w-52 rounded-2xl border border-border-main bg-card-bg shadow-2xl p-2">
                          <button data-m4c-touch type="button" onClick={() => handleEdit(doc)} className="w-full min-h-11 px-3 rounded-xl hover:bg-orange-50 text-orange-700 font-black text-xs inline-flex items-center gap-2"><Edit size={16} /> Modifier</button>
                          <button data-m4c-touch type="button" onClick={() => void handleDelete(doc.id)} className="w-full min-h-11 px-3 rounded-xl hover:bg-rose-50 text-rose-700 font-black text-xs inline-flex items-center gap-2"><Trash2 size={16} /> Mettre à la corbeille</button>
                        </div>
                      )}
                    </div>
                  )}
                  <span className={cn('px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest border', isLegacy ? 'bg-slate-100 text-slate-500 border-slate-200' : doc.type.toUpperCase() === 'NOTE' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-primary/10 text-primary border-primary/20')}>{doc.type}</span>
                </div>
              </div>

              <div className="relative z-10 mb-6">
                <h3 className="font-black text-text-main text-lg truncate pr-4 leading-tight">{doc.name}</h3>
                <div className="flex items-center gap-2 text-slate-400 text-[11px] font-bold mt-2 uppercase tracking-wide"><Calendar size={14} className="text-primary/60" /> {isLegacy ? 'Ancien format · desktop uniquement' : `Généré le ${doc.date}`}</div>
              </div>

              <div className="grid grid-cols-2 gap-3 relative z-10">
                {doc.file_exists === false ? (
                  <div className="col-span-2 min-h-[48px] flex items-center justify-center gap-2 bg-amber-50 border border-amber-200 text-amber-600 rounded-2xl font-black text-xs uppercase tracking-widest"><FileX2 size={16} /> Fichier introuvable</div>
                ) : (
                  <>
                    <button data-m4c-touch onClick={() => void handleView(doc.id)} className="min-h-[48px] flex items-center justify-center gap-2 bg-slate-50 border border-slate-100 hover:bg-slate-100 text-slate-600 rounded-2xl font-black text-xs uppercase tracking-widest transition-all active:scale-95"><Eye size={16} /> Voir</button>
                    <button data-m4c-touch onClick={() => void handleDownload(doc.id, doc.name)} className="min-h-[48px] flex items-center justify-center gap-2 bg-gradient-to-br from-primary to-secondary text-white rounded-2xl font-black text-xs uppercase tracking-widest transition-all shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95"><Download size={16} /> Fichier</button>
                  </>
                )}
              </div>

              <div className="relative z-10 mt-3">
                {canonicalId !== null && doc.file_exists !== false ? (
                  <DocumentMobileBridge documentId={canonicalId} documentName={doc.name} documentType={doc.type} />
                ) : isLegacy ? (
                  <div data-m4c-legacy-only className="min-h-[52px] rounded-2xl border border-slate-200 bg-slate-50 text-slate-400 inline-flex w-full items-center justify-center gap-2 font-black text-[10px] uppercase tracking-widest"><Monitor size={15} /> Non portable sur mobile</div>
                ) : null}
              </div>
            </div>
          );
        })}

        {filtered.length === 0 && (
          <div className="col-span-full py-20 text-center flex flex-col items-center">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-[2.5rem] bg-slate-50 border border-slate-100 mb-6 text-slate-300 shadow-inner"><ArchiveX size={40} /></div>
            <h3 className="text-slate-800 font-black text-xl mb-1">Aucune archive médicale</h3>
            <p className="text-slate-400 font-medium text-sm">Les documents générés apparaîtront ici.</p>
          </div>
        )}
      </div>
    </div>
  );
};
