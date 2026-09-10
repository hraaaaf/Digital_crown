import React from 'react';
import { Calendar as CalendarIcon } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { DOCUMENT_STUDIO_LABELS, type CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';

interface StudioHeaderProps {
  patientName: string;
  docDate: string;
  onDateChange: (date: string) => void;
  activeTab: CertifiableDocumentStudioTab;
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
  const documentLabel = DOCUMENT_STUDIO_LABELS[activeTab];
  const compactHonorairesMobile = activeTab === 'honoraires';

  return (
    <div className={cn(
      "sticky top-0 z-[60] -mt-1 -mx-1 mb-2 bg-white/85 dark:bg-slate-950/80 backdrop-blur-3xl rounded-2xl border border-slate-200/70 dark:border-white/10 flex flex-col md:flex-row justify-between items-start md:items-center shrink-0 transition-all duration-300 shadow-sm",
      compactHonorairesMobile ? "p-2 gap-2 sm:p-3 sm:gap-3" : "p-2.5 sm:p-3 gap-3",
    )}>
      <div className={cn("flex min-w-0 items-center", compactHonorairesMobile ? "gap-2 sm:gap-3" : "gap-3")}>
        <div className={cn(
          "shrink-0 bg-primary/10 rounded-xl flex items-center justify-center text-primary border border-primary/10",
          compactHonorairesMobile ? "w-8 h-8 sm:w-9 sm:h-9" : "w-9 h-9",
        )} style={{ color: 'var(--primary)' }}>
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
          <p className={cn(
            "flex min-w-0 items-center gap-2 text-[10px] font-bold text-slate-500 dark:text-slate-400",
            compactHonorairesMobile ? "mt-1 sm:mt-1.5" : "mt-1.5",
          )}>
            <span className="shrink-0 uppercase tracking-widest">Patient actif</span>
            <span aria-hidden="true" className="text-slate-300 dark:text-slate-700">•</span>
            <span className="truncate font-black tracking-tight text-slate-900 dark:text-white">{patientName}</span>
          </p>
        </div>
      </div>

      <div className={cn(
        "flex w-full flex-wrap items-center md:w-auto md:justify-end",
        compactHonorairesMobile ? "gap-1.5 sm:gap-2" : "gap-2",
      )}>
        {(activeTab === 'honoraires' || activeTab === 'devis') && (
          <button
            type="button"
            onClick={onToggleOdonto}
            aria-pressed={showOdontoPanoramique}
            className={cn(
              "flex min-h-11 items-center gap-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
              compactHonorairesMobile ? "px-2.5 sm:px-3 py-2" : "px-3 py-2",
              showOdontoPanoramique
                ? "bg-primary text-white shadow-lg shadow-primary/30"
                : "bg-white dark:bg-slate-900 text-primary border border-primary/20 hover:bg-primary/5"
            )}
            style={showOdontoPanoramique ? { backgroundColor: 'var(--primary)' } : { color: 'var(--primary)', borderColor: 'var(--primary)' }}
          >
            {showOdontoPanoramique ? "Réduire Schéma" : "Afficher Schéma"}
          </button>
        )}

        <div className={cn(
          "min-w-[140px] flex-1 md:flex-none bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10",
          compactHonorairesMobile
            ? "h-11 px-2 py-0 flex flex-row items-center gap-1.5 sm:h-auto sm:p-2.5 sm:flex-col sm:items-start sm:gap-1"
            : "p-2.5 flex flex-col items-start gap-1",
        )}>
          <label
            htmlFor="document-studio-date"
            className={cn(
              "text-[9px] font-black text-slate-400 uppercase items-center gap-1 leading-none h-3",
              compactHonorairesMobile ? "sr-only sm:not-sr-only sm:flex" : "flex",
            )}
          >
            <CalendarIcon size={10} /> Date d'émission
          </label>
          <input
            id="document-studio-date"
            type="date"
            aria-label={compactHonorairesMobile ? "Date d'émission" : undefined}
            className={cn(
              "bg-transparent text-xs font-black text-slate-700 dark:text-slate-200 outline-none w-full cursor-pointer focus-visible:ring-2 focus-visible:ring-primary/40 rounded-md",
              compactHonorairesMobile ? "min-h-11 sm:min-h-8" : "min-h-8",
            )}
            value={docDate}
            onChange={(e) => onDateChange(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
};