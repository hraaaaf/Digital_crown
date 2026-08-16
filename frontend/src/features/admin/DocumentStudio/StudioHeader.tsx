import React from 'react';
import { Calendar as CalendarIcon } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { DOCUMENT_STUDIO_LABELS, type CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';

interface StudioHeaderProps {
  patientName: string;
  docDate: string;
  onDateChange: (date: string) => void;
  activeTab: CertifiableDocumentStudioTab | 'ai';
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
}) => {
  const documentLabel = activeTab === 'ai' ? 'Fonction désactivée' : DOCUMENT_STUDIO_LABELS[activeTab];

  return (
    <div className="sticky top-0 z-[60] -mt-1 -mx-1 mb-2 p-2.5 sm:p-3 bg-white/85 dark:bg-slate-950/80 backdrop-blur-3xl rounded-2xl border border-slate-200/70 dark:border-white/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 shrink-0 transition-all duration-300 shadow-sm">
      <div className="flex min-w-0 items-center gap-3">
        <div className="w-9 h-9 shrink-0 bg-primary/10 rounded-xl flex items-center justify-center text-primary border border-primary/10" style={{ color: 'var(--primary)' }}>
          <CalendarIcon size={17} />
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <h2 className="text-sm sm:text-base font-black text-primary tracking-tight leading-none" style={{ color: 'var(--primary)' }}>
              Studio Documentaire
            </h2>
            <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-1 text-[9px] font-black uppercase tracking-wider text-slate-500 dark:text-slate-300">
              {documentLabel}
            </span>
          </div>
          <p className="mt-1.5 flex min-w-0 items-center gap-2 text-[10px] font-bold text-slate-500 dark:text-slate-400">
            <span className="shrink-0 uppercase tracking-widest">Patient actif</span>
            <span aria-hidden="true" className="text-slate-300 dark:text-slate-700">•</span>
            <span className="truncate font-black tracking-tight text-slate-900 dark:text-white">{patientName}</span>
          </p>
        </div>
      </div>

      <div className="flex w-full flex-wrap items-center gap-2 md:w-auto md:justify-end">
        {(activeTab === 'honoraires' || activeTab === 'devis') && (
          <button
            type="button"
            onClick={onToggleOdonto}
            aria-pressed={showOdontoPanoramique}
            className={cn(
              "flex min-h-11 items-center gap-2 px-3 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
              showOdontoPanoramique
                ? "bg-primary text-white shadow-lg shadow-primary/30"
                : "bg-white dark:bg-slate-900 text-primary border border-primary/20 hover:bg-primary/5"
            )}
            style={showOdontoPanoramique ? { backgroundColor: 'var(--primary)' } : { color: 'var(--primary)', borderColor: 'var(--primary)' }}
          >
            {showOdontoPanoramique ? "Réduire Schéma" : "Afficher Schéma"}
          </button>
        )}

        <div className="min-w-[140px] flex-1 md:flex-none bg-white dark:bg-slate-900 p-2.5 rounded-xl shadow-sm border border-slate-200 dark:border-white/10 flex flex-col items-start gap-1">
          <label htmlFor="document-studio-date" className="text-[9px] font-black text-slate-400 uppercase flex items-center gap-1 leading-none h-3">
            <CalendarIcon size={10} /> Date d'émission
          </label>
          <input
            id="document-studio-date"
            type="date"
            className="bg-transparent text-xs font-black text-slate-700 dark:text-slate-200 outline-none w-full cursor-pointer min-h-8 focus-visible:ring-2 focus-visible:ring-primary/40 rounded-md"
            value={docDate}
            onChange={(e) => onDateChange(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
};