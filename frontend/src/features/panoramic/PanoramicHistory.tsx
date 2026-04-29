import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { 
  Calendar, 
  ChevronRight, 
  Activity, 
  FileText,
  Loader2,
  Clock,
  ExternalLink
} from 'lucide-react';
import { cn } from '../../utils/cn';

interface PanoramicAnalysis {
  id: number;
  image_path: str;
  detections_data: any;
  report_narrative: string;
  created_at: string;
}

interface PanoramicHistoryProps {
  patientId: number;
  onSelect: (analysis: any) => void;
}

export const PanoramicHistory: React.FC<PanoramicHistoryProps> = ({ patientId, onSelect }) => {
  const [analyses, setAnalyses] = useState<PanoramicAnalysis[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/ia/patients/${patientId}/panoramic-analyses`);
        setAnalyses(response.data);
      } catch (error) {
        console.error("Erreur chargement historique panoramique:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [patientId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-500" />
        <p className="text-slate-400 text-xs font-black uppercase tracking-widest">Chargement de l'historique...</p>
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 bg-slate-50/50 rounded-[2rem] border-2 border-dashed border-slate-200">
        <Clock className="w-12 h-12 text-slate-300 mb-4" />
        <h3 className="text-lg font-black text-slate-400 uppercase tracking-tight">Aucun historique</h3>
        <p className="text-sm text-slate-400 mt-2">Commencez par importer une première radiographie.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
        <Activity size={16} />
        Historique des Examens ({analyses.length})
      </h3>

      <div className="grid grid-cols-1 gap-4">
        {analyses.map((analysis) => {
          const detectionsCount = analysis.detections_data?.detections?.length || 0;
          const dateStr = new Date(analysis.created_at).toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          });

          return (
            <div 
              key={analysis.id}
              onClick={() => onSelect(analysis)}
              className="group bg-white hover:bg-slate-50 border border-slate-200/60 rounded-[1.5rem] p-5 flex items-center justify-between transition-all duration-300 cursor-pointer hover:shadow-xl hover:shadow-slate-200/40 hover:-translate-y-1 active:scale-[0.98]"
            >
              <div className="flex items-center gap-6">
                <div className="w-14 h-14 bg-indigo-50 rounded-2xl flex items-center justify-center text-indigo-600 shadow-sm group-hover:bg-indigo-600 group-hover:text-white transition-colors duration-300">
                  <Calendar size={24} />
                </div>
                
                <div>
                  <h4 className="font-black text-slate-800 text-lg tracking-tight">Examen du {dateStr}</h4>
                  <div className="flex items-center gap-4 mt-1">
                    <span className="flex items-center gap-1.5 text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg">
                      <Activity size={14} className="text-indigo-500" />
                      {detectionsCount} anomalie{detectionsCount > 1 ? 's' : ''} détectée{detectionsCount > 1 ? 's' : ''}
                    </span>
                    <span className="flex items-center gap-1.5 text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-lg">
                      <FileText size={14} className="text-emerald-500" />
                      Rapport généré
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2 text-indigo-600 font-black text-[10px] uppercase tracking-widest">
                  Ouvrir dans le studio
                  <ExternalLink size={14} />
                </div>
                <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 group-hover:bg-indigo-600 group-hover:text-white transition-all">
                  <ChevronRight size={20} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
