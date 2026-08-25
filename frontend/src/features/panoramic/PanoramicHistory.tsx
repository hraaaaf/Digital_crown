import React, { useCallback, useEffect, useState } from 'react';
import { api } from '../../services/api';
import toast from 'react-hot-toast';
import { Calendar, ChevronRight, Activity, FileText, Loader2, Clock, ExternalLink, Trash2, AlertTriangle } from 'lucide-react';
import { PanoramicMobileBridge } from './PanoramicMobileBridge';

interface PanoramicAnalysis {
  id: number;
  image_path: string;
  detections_data: any;
  report_narrative: string;
  created_at: string;
}

interface PanoramicHistoryProps {
  patientId: number;
  onSelect: (analysis: any) => void;
  onDelete?: (analysisId: number) => void;
}

export const PanoramicHistory: React.FC<PanoramicHistoryProps> = ({ patientId, onSelect, onDelete }) => {
  const [analyses, setAnalyses] = useState<PanoramicAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(false);
      const response = await api.get(`/ia/patients/${patientId}/panoramic-analyses`);
      setAnalyses(response.data as PanoramicAnalysis[]);
    } catch (fetchError) {
      console.error('Erreur chargement historique panoramique:', fetchError);
      setAnalyses([]);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => { void fetchHistory(); }, [fetchHistory, reloadKey]);

  const deletePermanently = async (analysis: PanoramicAnalysis) => {
    if (!window.confirm('Supprimer définitivement cet examen panoramique ? Cette action supprime aussi le fichier et ne peut pas être annulée.')) return;
    try {
      await api.delete(`/ia/panoramic/${analysis.id}`);
      setAnalyses(prev => prev.filter(item => item.id !== analysis.id));
      toast.success('Examen panoramique supprimé définitivement.');
      onDelete?.(analysis.id);
    } catch (deleteError) {
      console.error(deleteError);
      toast.error('Impossible de supprimer cet examen panoramique.');
    }
  };

  if (loading) {
    return <div className="flex flex-col items-center justify-center py-20 gap-4"><Loader2 className="w-10 h-10 animate-spin text-indigo-500"/><p className="text-slate-400 text-xs font-black uppercase tracking-widest">Chargement de l'historique...</p></div>;
  }

  return (
    <div className="space-y-4" data-m4b-history>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2"><Activity size={16}/>Historique des examens ({analyses.length})</h3>
        <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Suppression définitive</p>
      </div>

      {error ? (
        <div className="flex flex-col items-center justify-center py-16 gap-4 text-center bg-rose-50/60 rounded-[2rem] border border-rose-100">
          <AlertTriangle className="w-10 h-10 text-rose-400"/>
          <div><h4 className="font-black text-slate-700">Impossible de charger l'historique</h4><p className="text-sm text-slate-500 mt-1">Aucun état vide n'est déduit tant que le backend ne répond pas.</p></div>
          <button data-m4b-touch type="button" onClick={() => setReloadKey(key => key + 1)} className="min-h-11 px-4 rounded-xl bg-indigo-600 text-white text-xs font-black uppercase tracking-widest">Réessayer</button>
        </div>
      ) : analyses.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 bg-slate-50/50 rounded-[2rem] border-2 border-dashed border-slate-200"><Clock className="w-12 h-12 text-slate-300 mb-4"/><h3 className="text-lg font-black text-slate-400 uppercase tracking-tight">Aucun historique</h3><p className="text-sm text-slate-400 mt-2">Commencez par importer une première radiographie.</p></div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {analyses.map((analysis) => {
            const landmarksCount = analysis.detections_data?.detections?.length || 0;
            const date = new Date(analysis.created_at);
            const dateStr = date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' });
            return (
              <div key={analysis.id} onClick={() => onSelect(analysis)} className="group bg-white border border-slate-200/60 rounded-[1.5rem] p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all duration-300 cursor-pointer hover:bg-slate-50 hover:shadow-xl hover:shadow-slate-200/40 hover:-translate-y-1 active:scale-[0.98]">
                <div className="flex min-w-0 items-center gap-4 sm:gap-6">
                  <div className="w-12 h-12 sm:w-14 sm:h-14 shrink-0 bg-indigo-50 rounded-2xl flex items-center justify-center text-indigo-600 shadow-sm group-hover:bg-indigo-600 group-hover:text-white transition-colors duration-300"><Calendar size={24}/></div>
                  <div className="min-w-0"><h4 className="font-black text-slate-800 text-base sm:text-lg tracking-tight">Examen du {dateStr}</h4><div className="flex flex-wrap items-center gap-2 sm:gap-4 mt-1"><span className="flex items-center gap-1.5 text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg"><Activity size={14} className="text-indigo-500"/>{landmarksCount} repère{landmarksCount > 1 ? 's' : ''} dentaire{landmarksCount > 1 ? 's' : ''}</span><span className="flex items-center gap-1.5 text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg"><FileText size={14} className="text-emerald-500"/> Rapport enregistré</span></div></div>
                </div>
                <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-3">
                  <PanoramicMobileBridge analysisId={analysis.id} examLabel={dateStr}/>
                  <button data-m4b-touch type="button" onClick={(event) => { event.stopPropagation(); void deletePermanently(analysis); }} className="min-w-11 min-h-11 rounded-xl bg-rose-50 text-rose-600 hover:bg-rose-500 hover:text-white flex items-center justify-center transition-all border border-rose-100/50 hover:border-rose-500 shadow-sm active:scale-95 z-10" title="Supprimer définitivement" aria-label="Supprimer définitivement l'examen panoramique"><Trash2 size={16}/></button>
                  <div className="hidden lg:flex opacity-0 group-hover:opacity-100 transition-opacity items-center gap-2 text-indigo-600 font-black text-[10px] uppercase tracking-widest">Ouvrir dans le studio <ExternalLink size={14}/></div>
                  <div className="min-w-11 min-h-11 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 group-hover:bg-indigo-600 group-hover:text-white transition-all"><ChevronRight size={20}/></div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
