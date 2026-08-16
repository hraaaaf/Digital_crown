import React from 'react';
import { AlertTriangle, Eye, Archive, Printer } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { createPortal } from 'react-dom';
import type { CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';

interface StudioFooterProps {
  loading: boolean;
  activeTab: CertifiableDocumentStudioTab | 'ai';
  onGenerate: (archive: boolean, print: boolean, isPreview: boolean, force: boolean) => void;
  showPrintWarning: boolean;
  onCloseWarning: () => void;
  hasChanges: boolean;
  onSavePreference?: () => void;
  aiReport?: string | null;
  onGenerateAI?: () => void;
  loadingAi?: boolean;
  total?: number;
  sideStudioType: 'NONE' | 'PREVIEW';
  onTogglePreview: () => void;
}

export const StudioFooter: React.FC<StudioFooterProps> = ({
  loading,
  activeTab,
  onGenerate,
  showPrintWarning,
  onCloseWarning,
  total,
  sideStudioType,
  onTogglePreview
}) => {
  if (activeTab === 'plan') return null;

  if (activeTab === 'ai') {
    return (
      <div
        className="flex items-center gap-3 rounded-2xl border border-amber-200 dark:border-amber-400/20 bg-amber-50/90 dark:bg-amber-950/30 p-4 text-amber-800 dark:text-amber-200"
        role="status"
        aria-live="polite"
      >
        <AlertTriangle size={18} className="shrink-0" />
        <div>
          <div className="text-[10px] font-black uppercase tracking-widest">Fonction clinique désactivée</div>
          <p className="mt-1 text-xs font-semibold">
            L’analyse clinique automatisée n’est pas disponible dans le Document Studio certifiable. Une validation scientifique dédiée est requise avant toute réactivation.
          </p>
        </div>
      </div>
    );
  }

  const preparesFreshPdf = activeTab === 'certificat' || activeTab === 'libre';

  return (
    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 sm:gap-5 p-3 bg-white/90 dark:bg-slate-950/85 backdrop-blur-xl rounded-2xl border border-slate-200/70 dark:border-white/10 mt-2 shadow-sm relative overflow-hidden w-full shrink-0">
      {(activeTab === 'devis' || activeTab === 'honoraires') && typeof total === 'number' ? (
        <div className="flex items-center justify-between sm:justify-start gap-4 px-2 sm:px-3 py-1 sm:border-r sm:border-slate-200 dark:sm:border-white/10 sm:pr-5">
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-tight">Total document</span>
          <span className="text-lg sm:text-xl font-black text-slate-900 dark:text-white tracking-tighter leading-tight">
            {total.toLocaleString('fr-FR')} <span className="text-[10px] opacity-50">MAD</span>
          </span>
        </div>
      ) : (
        <div className="hidden sm:block" />
      )}

      <div className="grid grid-cols-3 items-stretch gap-1.5 sm:flex sm:items-center sm:justify-end sm:gap-2.5 w-full sm:w-auto min-w-0">
        {onTogglePreview && (
          <button
            type="button"
            onClick={onTogglePreview}
            aria-pressed={sideStudioType === 'PREVIEW'}
            className={cn(
              'min-h-11 min-w-0 flex items-center justify-center gap-1.5 sm:gap-2 px-2 sm:px-4 py-3 rounded-xl font-black uppercase text-[9px] sm:text-[10px] tracking-normal sm:tracking-wider whitespace-nowrap transition-all active:scale-95 border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
              sideStudioType === 'PREVIEW'
                ? 'bg-emerald-600 text-white border-emerald-500 shadow-sm'
                : 'bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20'
            )}
          >
            <Eye size={14} className="shrink-0" />
            <span>{sideStudioType === 'PREVIEW' ? 'Fermer' : 'Aperçu'}</span>
          </button>
        )}

        <button
          type="button"
          onClick={() => onGenerate(true, false, false, false)}
          disabled={loading}
          className="min-h-11 min-w-0 flex items-center justify-center gap-1.5 sm:gap-2 px-2 sm:px-5 py-3 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-white/10 rounded-xl text-[9px] sm:text-[10px] font-black uppercase tracking-normal sm:tracking-wider whitespace-nowrap hover:border-primary hover:text-primary transition-all active:scale-95 disabled:opacity-50 shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
        >
          <Archive size={14} className="shrink-0" /> <span>Enregistrer</span>
        </button>

        <button
          type="button"
          onClick={() => preparesFreshPdf
            ? onGenerate(true, false, false, false)
            : onGenerate(false, true, false, false)}
          disabled={loading}
          className="min-h-11 min-w-0 flex items-center justify-center gap-1.5 sm:gap-2 px-2 sm:px-6 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-950 rounded-xl text-[9px] sm:text-[10px] font-black uppercase tracking-normal sm:tracking-wider whitespace-nowrap hover:bg-black dark:hover:bg-slate-100 transition-all shadow-md active:scale-95 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500"
        >
          <Printer size={14} className="shrink-0" />
          <span>{preparesFreshPdf ? 'Préparer' : 'Imprimer'}</span>
        </button>
      </div>

      {showPrintWarning && !preparesFreshPdf && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4 sm:p-8 animate-in fade-in zoom-in-95 duration-300">
          <div
            className="flex flex-col items-center text-center max-w-sm bg-white dark:bg-slate-950 p-6 sm:p-8 rounded-3xl shadow-2xl border border-slate-100 dark:border-white/10"
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-studio-print-warning-title"
          >
            <AlertTriangle className="text-amber-500 mb-4" size={48} />
            <h4 id="document-studio-print-warning-title" className="text-lg font-black text-slate-800 dark:text-white mb-2">Attention : Impression Directe</h4>
            <p className="text-sm text-slate-500 dark:text-slate-400 font-medium mb-6">Assurez-vous que votre imprimante est prête. Le document sera archivé automatiquement après l'impression.</p>
            <div className="flex flex-wrap justify-center gap-3 sm:gap-4">
              <button type="button" onClick={onCloseWarning} className="min-h-11 px-6 py-2 text-slate-500 dark:text-slate-300 font-bold hover:text-slate-700 dark:hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 rounded-xl">Annuler</button>
              <button type="button" onClick={() => onGenerate(true, true, false, true)} className="min-h-11 px-8 py-2 bg-primary text-white rounded-xl font-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50" style={{ backgroundColor: 'var(--primary)' }}>Confirmer</button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};