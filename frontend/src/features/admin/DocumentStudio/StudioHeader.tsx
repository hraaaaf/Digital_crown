import React from 'react';
import { Calendar as CalendarIcon, Eye } from 'lucide-react';
import { cn } from '../../../utils/cn';

interface StudioHeaderProps {
  patientName: string;
  docDate: string;
  onDateChange: (date: string) => void;
  activeTab: string;
  sideStudioType: 'NONE' | 'PREVIEW';
  onTogglePreview: () => void;
  showOdontoPanoramique: boolean;
  onToggleOdonto: () => void;
}

export const StudioHeader: React.FC<StudioHeaderProps> = ({
  patientName,
  docDate,
  onDateChange,
  activeTab,
  sideStudioType,
  onTogglePreview,
  showOdontoPanoramique,
  onToggleOdonto
}) => {
  return (
    <div className="sticky top-0 z-[60] -mt-1 -mx-1 mb-2 p-3 bg-white/40 dark:bg-slate-900/40 backdrop-blur-3xl rounded-2xl border border-white/50 dark:border-white/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 shrink-0 transition-all duration-300 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center text-primary border border-primary/10" style={{ color: 'var(--primary)' }}>
          <Eye size={20} />
        </div>
        <div>
          <h2 className="text-lg font-black text-primary tracking-tight leading-none" style={{ color: 'var(--primary)' }}>
            Studio Documentaire
          </h2>
          <p className="text-slate-500 mt-1 text-[10px] font-medium uppercase tracking-widest flex items-center gap-2">
            Patient : <span className="font-black text-slate-800 tracking-tight">{patientName}</span>
          </p>
        </div>
      </div>
      
      <div className="flex flex-wrap items-center gap-3">
        {(activeTab === 'honoraires' || activeTab === 'devis') && (
          <button
            onClick={onToggleOdonto}
            className={cn(
              "flex items-center gap-2 px-5 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all",
              showOdontoPanoramique 
                ? "bg-primary text-white shadow-lg shadow-primary/30" 
                : "bg-white text-primary border border-primary/20 hover:bg-primary/5"
            )}
            style={showOdontoPanoramique ? { backgroundColor: 'var(--primary)' } : { color: 'var(--primary)', borderColor: 'var(--primary)' }}
          >
            {showOdontoPanoramique ? "Réduire Schéma" : "Afficher Schéma"}
          </button>
        )}

        {activeTab !== 'ai' && (
          <div className="flex items-center gap-2">
            <button 
              onClick={() => window.location.reload()}
              className="flex items-center gap-2 px-5 py-3 bg-white text-slate-400 border border-slate-200 rounded-xl text-[10px] font-black uppercase tracking-widest hover:border-primary hover:text-primary transition-all"
            >
              Actualiser
            </button>
            <button 
              onClick={() => window.history.back()}
              className="flex items-center gap-2 px-5 py-3 bg-red-50 text-red-600 border border-red-100 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-red-600 hover:text-white transition-all"
            >
              Quitter
            </button>
            <button 
              onClick={onTogglePreview}
              className={cn(
                "flex items-center gap-2 px-5 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border",
                sideStudioType === 'PREVIEW' 
                  ? "bg-emerald-600 text-white border-emerald-500 shadow-lg shadow-emerald-500/30" 
                  : "bg-white text-slate-400 border-slate-200 hover:border-slate-300"
              )}
            >
              <Eye size={14}/> {sideStudioType === 'PREVIEW' ? "Fermer l'Aperçu" : "Aperçu Direct"}
            </button>
          </div>
        )}

        <div className="bg-white/80 dark:bg-slate-900/50 p-2.5 rounded-2xl shadow-sm border border-slate-100 dark:border-white/10 flex flex-col items-start gap-1 min-w-[130px]">
          <label className="text-[9px] font-black text-slate-400 uppercase flex items-center gap-1 leading-none h-3">
            <CalendarIcon size={10} /> Date d'émission
          </label>
          <input 
            type="date" 
            className="bg-transparent text-xs font-black text-slate-700 dark:text-slate-200 outline-none w-full cursor-pointer h-5" 
            value={docDate} 
            onChange={(e) => onDateChange(e.target.value)} 
          />
        </div>
      </div>
    </div>
  );
};
