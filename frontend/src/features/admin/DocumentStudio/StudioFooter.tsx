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
        className="flex items-center gap-3 rounded-[2rem] border border-amber-200 bg-amber-50/80 p-5 text-amber-800"
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
    <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-8 p-3 bg-slate-50/80 backdrop-blur-xl rounded-[1.5rem] border border-slate-100 mt-2 shadow-sm relative overflow-hidden w-full shrink-0">
      <div className="flex items-center gap-6">
        {(activeTab === 'devis' || activeTab === 'honoraires') && typeof total === 'number' && (
          <div className="flex items-center gap-4 px-6 border-r border-slate-200">
            <div className="flex flex-col items-center">
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-tight">Total Document</span>
              <span className="text-xl font-black text-slate-900 tracking-tighter leading-tight">{total.toLocaleString('fr-FR')} <span className="text-[10px] opacity-40">MAD</span></span>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 items-stretch gap-1.5 sm:flex sm:items-center sm:gap-3 w-full sm:w-auto min-w-0">
        {onTogglePreview && (
          <button
            type="button"
            onClick={onTogglePreview}
            aria-pressed={sideStudioType === 'PREVIEW'}
            className={cn(
              'min-h-11 min-w-0 flex items-center justify-center gap-1 sm:gap-2 px-1 sm:px-5 py-3 rounded-xl font-black uppercase text-[9px] sm:text-[10px] tracking-normal sm:tracking-widest whitespace-nowrap transition-all active:scale-95 border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
              sideStudioType === 'PREVIEW' ? 'bg-emerald-600 text-white border-emerald-500 shadow-emerald-500/30' : 'bg-white text-slate-500 border-slate-200 hover:border-slate-300 hover:text-slate-700'
            )}
          >
            <Eye size={14} className="shrink-0" /> <span>{sideStudioType === 'PREVIEW' ? 'Fermer' : 'Aperçu'}</span>
          </button>
        )}

        <button
          type="button"
          onClick={() => onGenerate(true, false, false, false)}
          disabled={loading}
          className="min-h-11 min-w-0 flex items-center justify-center gap-1 sm:gap-2 px-1 sm:px-6 py-3 bg-white text-slate-600 border border-slate-200 rounded-xl text-[9px] sm:text-[10px] font-black uppercase tracking-normal sm:tracking-widest whitespace-nowrap hover:border-primary hover:text-primary transition-all active:scale-95 disabled:opacity-50 shadow-sm hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
        >
          <Archive size={14} className="shrink-0" /> <span>Enregistrer</span>
        </button>

        <button
          type="button"
          onClick={() => preparesFreshPdf
            ? onGenerate(true, false, false, false)
            : onGenerate(false, true, false, false)}
          disabled={loading}
          className="min-h-11 min-w-0 flex items-center justify-center gap-1 sm:gap-2 px-1 sm:px-8 py-3 bg-slate-800 text-white rounded-xl text-[9px] sm:text-[10px] font-black uppercase tracking-normal sm:tracking-widest whitespace-nowrap hover:bg-black transition-all shadow-lg shadow-slate-800/20 active:scale-95 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500"
        >
          <Printer size={14} className="shrink-0" />
          <span>{preparesFreshPdf ? 'Préparer impression' : 'Imprimer'}</span>
        </button>
      </div>

      {showPrintWarning && !preparesFreshPdf && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 bg-white/95 backdrop-blur-sm z-[9999] flex items-center justify-center p-4 sm:p-8 animate-in fade-in zoom-in-95 duration-300">
          <div
            className="flex flex-col items-center text-center max-w-sm bg-white p-6 sm:p-8 rounded-3xl shadow-2xl border border-slate-100"
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-studio-print-warning-title"
          >
            <AlertTriangle className="text-amber-500 mb-4" size={48} />
            <h4 id="document-studio-print-warning-title" className="text-lg font-black text-slate-800 mb-2">Attention : Impression Directe</h4>
            <p className="text-sm text-slate-500 font-medium mb-6">Assurez-vous que votre imprimante est prête. Le document sera archivé automatiquement après l'impression.</p>
            <div className="flex flex-wrap justify-center gap-3 sm:gap-4">
              <button type="button" onClick={onCloseWarning} className="min-h-11 px-6 py-2 text-slate-500 font-bold hover:text-slate-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 rounded-xl">Annuler</button>
              <button type="button" onClick={() => onGenerate(true, true, false, true)} className="min-h-11 px-8 py-2 bg-primary text-white rounded-xl font-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50" style={{ backgroundColor: 'var(--primary)' }}>Confirmer</button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};