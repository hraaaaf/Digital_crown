import React from 'react';
import { Calendar as CalendarIcon } from 'lucide-react';
import { cn } from '../../../utils/cn';

interface StudioHeaderProps {
  patientName: string;
  docDate: string;
  onDateChange: (date: string) => void;
  activeTab: string;
  showOdontoPanoramique: boolean;
  onToggleOdonto: () => void;
  onGenerate?: (archive: boolean, print: boolean, isPreview: boolean, force: boolean) => void;
  loading?: boolean;
  sideStudioType?: 'NONE' | 'PREVIEW';
  onTogglePreview?: () => void;
}

export const StudioHeader: React.FC<StudioHeaderProps> = ({
  patientName,
  docDate,
  onDateChange,
  activeTab,
  showOdontoPanoramique,
  onToggleOdonto,
  onGenerate,
  loading,
  sideStudioType,
  onTogglePreview
}) => {
  return (
    <div className="sticky top-0 z-[60] -mt-1 -mx-1 mb-2 p-2 bg-white/40 dark:bg-slate-900/40 backdrop-blur-3xl rounded-xl border border-white/50 dark:border-white/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-2 shrink-0 transition-all duration-300 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center text-primary border border-primary/10" style={{ color: 'var(--primary)' }}>
          <CalendarIcon size={16} />
        </div>
        <div>
          <h2 className="text-base font-black text-primary tracking-tight leading-none" style={{ color: 'var(--primary)' }}>
            Studio Documentaire
          </h2>
          <p className="text-slate-500 mt-1 text-[9px] font-medium uppercase tracking-widest flex items-center gap-2">
            Patient : <span className="font-black text-slate-800 tracking-tight">{patientName}</span>
          </p>
        </div>
      </div>
      
      <div className="flex flex-wrap items-center gap-2">
        {(activeTab === 'honoraires' || activeTab === 'devis') && (
          <button
            onClick={onToggleOdonto}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all",
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
              className="flex items-center gap-2 px-3 py-2 bg-white text-slate-400 border border-slate-200 rounded-lg text-[9px] font-black uppercase tracking-widest hover:border-primary hover:text-primary transition-all"
            >
              Actualiser
            </button>
            <button 
              onClick={() => window.history.back()}
              className="flex items-center gap-2 px-3 py-2 bg-red-50 text-red-600 border border-red-100 rounded-lg text-[9px] font-black uppercase tracking-widest hover:bg-red-600 hover:text-white transition-all"
            >
              Quitter
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
