import React, { useCallback, useEffect, useState } from 'react';
import { api } from '../../services/api';
import toast from 'react-hot-toast';
import {
  Calendar,
  ChevronRight,
  Activity,
  FileText,
  Loader2,
  Clock,
  ExternalLink,
  Trash2,
  RotateCcw,
  AlertTriangle,
  Archive,
} from 'lucide-react';

interface CephaloAnalysis {
  id: number;
  image_original_path: string;
  angles_data?: any;
  created_at: string;
  deleted_at?: string | null;
}

interface CephaloHistoryProps {
  patientId: number;
  onSelect: (analysis: CephaloAnalysis) => void;
  onDelete?: (analysisId: number) => void;
}

type HistoryView = 'active' | 'trash';

export const CephaloHistory: React.FC<CephaloHistoryProps> = ({ patientId, onSelect, onDelete }) => {
  const [analyses, setAnalyses] = useState<CephaloAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [view, setView] = useState<HistoryView>('active');
  const [reloadKey, setReloadKey] = useState(0);

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(false);
      if (view === 'trash') {
        const response = await api.get(`/ia/patients/${patientId}/cephalo-trash`);
        setAnalyses(response.data);
      } else {
        const [activeResponse, trashResponse] = await Promise.all([
          api.get(`/ia/patients/${patientId}/cephalo-analyses`),
          api.get(`/ia/patients/${patientId}/cephalo-trash`),
        ]);
        const trashedIds = new Set<number>((trashResponse.data as CephaloAnalysis[]).map(item => item.id));
        setAnalyses((activeResponse.data as CephaloAnalysis[]).filter(item => !trashedIds.has(item.id)));
      }
    } catch (fetchError) {
      console.error('Erreur chargement historique céphalométrique:', fetchError);
      setAnalyses([]);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [patientId, view]);

  useEffect(() => {
    void fetchHistory();
  }, [fetchHistory, reloadKey]);

  const moveToTrash = async (analysis: CephaloAnalysis) => {
    if (!window.confirm('Mettre cette analyse céphalométrique à la corbeille ? L’image restera récupérable.')) return;
    try {
      await api.delete(`/ia/cephalo/${analysis.id}`);
      setAnalyses(prev => prev.filter(item => item.id !== analysis.id));
      toast.success('Analyse placée dans la corbeille.');
      onDelete?.(analysis.id);
    } catch (deleteError) {
      console.error(deleteError);
      toast.error('Impossible de mettre cette analyse à la corbeille.');
    }
  };

  const restore = async (analysis: CephaloAnalysis) => {
    try {
      await api.post(`/ia/cephalo/${analysis.id}/restore`);
      setAnalyses(prev => prev.filter(item => item.id !== analysis.id));
      toast.success('Analyse restaurée dans l’historique.');
    } catch (restoreError) {
      console.error(restoreError);
      toast.error('Impossible de restaurer cette analyse.');
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-500" />
        <p className="text-slate-400 text-xs font-black uppercase tracking-widest">Chargement de l'historique...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
          <Activity size={16} />
          {view === 'active' ? `Historique des analyses (${analyses.length})` : `Corbeille (${analyses.length})`}
        </h3>
        <div className="inline-flex rounded-xl border border-slate-200 bg-slate-100 p-1">
          <button type="button" onClick={() => setView('active')} className={`px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-colors ${view === 'active' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500'}`}>Historique</button>
          <button type="button" onClick={() => setView('trash')} className={`px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-colors flex items-center gap-1.5 ${view === 'trash' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500'}`}><Archive size={13} /> Corbeille</button>
        </div>
      </div>

      {error ? (
        <div className="flex flex-col items-center justify-center py-16 gap-4 text-center bg-rose-50/60 rounded-[2rem] border border-rose-100">
          <AlertTriangle className="w-10 h-10 text-rose-400" />
          <div>
            <h4 className="font-black text-slate-700">Impossible de charger {view === 'active' ? "l'historique" : 'la corbeille'}</h4>
            <p className="text-sm text-slate-500 mt-1">Aucun état vide n'est déduit tant que le backend ne répond pas.</p>
          </div>
          <button type="button" onClick={() => setReloadKey(key => key + 1)} className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-black uppercase tracking-widest">Réessayer</button>
        </div>
      ) : analyses.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 bg-slate-50/50 rounded-[2rem] border-2 border-dashed border-slate-200">
          <Clock className="w-12 h-12 text-slate-300 mb-4" />
          <h3 className="text-lg font-black text-slate-400 uppercase tracking-tight">{view === 'active' ? 'Aucun historique céphalométrique' : 'Corbeille vide'}</h3>
          <p className="text-sm text-slate-400 mt-2">{view === 'active' ? 'Importez une première radiographie céphalométrique.' : 'Aucune analyse céphalométrique supprimée à restaurer.'}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {analyses.map((analysis) => {
            const dateStr = new Date(analysis.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' });
            return (
              <div key={analysis.id} onClick={() => view === 'active' && onSelect(analysis)} className={`group bg-white border border-slate-200/60 rounded-[1.5rem] p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all duration-300 ${view === 'active' ? 'cursor-pointer hover:bg-slate-50 hover:shadow-xl hover:shadow-slate-200/40 hover:-translate-y-1 active:scale-[0.98]' : ''}`}>
                <div className="flex min-w-0 items-center gap-4 sm:gap-6">
                  <div className="w-12 h-12 sm:w-14 sm:h-14 shrink-0 bg-indigo-50 rounded-2xl flex items-center justify-center text-indigo-600 shadow-sm group-hover:bg-indigo-600 group-hover:text-white transition-colors duration-300"><Calendar size={24} /></div>
                  <div className="min-w-0">
                    <h4 className="font-black text-slate-800 text-base sm:text-lg tracking-tight">Analyse du {dateStr}</h4>
                    <div className="flex flex-wrap items-center gap-2 sm:gap-4 mt-1">
                      <span className="flex items-center gap-1.5 text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg"><Activity size={14} className="text-indigo-500" /> Analyse enregistrée</span>
                      <span className="flex items-center gap-1.5 text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg"><FileText size={14} className="text-emerald-500" /> Données céphalométriques enregistrées</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-end gap-3 sm:gap-4">
                  {view === 'active' ? (
                    <>
                      <button type="button" onClick={(event) => { event.stopPropagation(); void moveToTrash(analysis); }} className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 hover:bg-rose-500 hover:text-white flex items-center justify-center transition-all border border-rose-100/50 hover:border-rose-500 shadow-sm active:scale-95 z-10" title="Mettre à la corbeille" aria-label="Mettre l'analyse céphalométrique à la corbeille"><Trash2 size={16} /></button>
                      <div className="hidden sm:flex opacity-0 group-hover:opacity-100 transition-opacity items-center gap-2 text-indigo-600 font-black text-[10px] uppercase tracking-widest">Ouvrir dans le studio <ExternalLink size={14} /></div>
                      <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 group-hover:bg-indigo-600 group-hover:text-white transition-all"><ChevronRight size={20} /></div>
                    </>
                  ) : (
                    <button type="button" onClick={(event) => { event.stopPropagation(); void restore(analysis); }} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-50 text-emerald-700 hover:bg-emerald-600 hover:text-white border border-emerald-100 transition-colors text-xs font-black"><RotateCcw size={15} /> Restaurer</button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
