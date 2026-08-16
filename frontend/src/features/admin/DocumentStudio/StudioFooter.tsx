import React from 'react';
import { AlertTriangle, Eye, Archive, Printer } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { createPortal } from 'react-dom';

interface StudioFooterProps {
  loading: boolean;
  activeTab: import('../DocumentHub').HubDocumentType;
  onGenerate: (archive: boolean, print: boolean, isPreview: boolean, force: boolean) => void;
  showPrintWarning: boolean;
  onCloseWarning: () => void;
  hasChanges: boolean;
  onSavePreference?: () => void;
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

  const preparesFreshPdf = activeTab === 'certificat' || activeTab === 'libre';
  const isInstallmentPrint = activeTab === 'echeancier';
  const hasGlobalArchiveAction = !isInstallmentPrint;

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

      <div className={cn(
        'grid items-stretch gap-1.5 sm:flex sm:items-center sm:gap-3 w-full sm:w-auto min-w-0',
        hasGlobalArchiveAction ? 'grid-cols-3' : 'grid-cols-2'
      )}>
        {onTogglePreview && (
          <button type="button" onClick={onTogglePreview} className={cn(
            'min-w-0 flex items-center justify-center gap-1 sm:gap-2 px-1 sm:px-5 py-3 rounded-xl font-black uppercase text-[8px] sm:text-[10px] tracking-normal sm:tracking-widest whitespace-nowrap transition-all active:scale-95 border',
            sideStudioType === 'PREVIEW' ? 'bg-emerald-600 text-white border-emerald-500 shadow-emerald-500/30' : 'bg-white text-slate-500 border-slate-200 hover:border-slate-300 hover:text-slate-700'
          )}>
            <Eye size={14} className="shrink-0" /> <span>{sideStudioType === 'PREVIEW' ? 'Fermer' : 'Aperçu'}</span>
          </button>
        )}

        {hasGlobalArchiveAction && (
          <button type="button" onClick={() => onGenerate(true, false, false, false)} disabled={loading} className="min-w-0 flex items-center justify-center gap-1 sm:gap-2 px-1 sm:px-6 py-3 bg-white text-slate-600 border border-slate-200 rounded-xl text-[8px] sm:text-[10px] font-black uppercase tracking-normal sm:tracking-widest whitespace-nowrap hover:border-primary hover:text-primary transition-all active:scale-95 disabled:opacity-50 shadow-sm hover:shadow-md">
            <Archive size={14} className="shrink-0" /> <span>Enregistrer</span>
          </button>
        )}

        <button
          type="button"
          onClick={() => preparesFreshPdf
            ? onGenerate(true, false, false, false)
            : onGenerate(false, true, false, false)}
          disabled={loading}
          className="min-w-0 flex items-center justify-center gap-1 sm:gap-2 px-1 sm:px-8 py-3 bg-slate-800 text-white rounded-xl text-[8px] sm:text-[10px] font-black uppercase tracking-normal sm:tracking-widest whitespace-nowrap hover:bg-black transition-all shadow-lg shadow-slate-800/20 active:scale-95 disabled:opacity-50"
        >
          <Printer size={14} className="shrink-0" />
          <span>{preparesFreshPdf ? 'Préparer impression' : 'Imprimer'}</span>
        </button>
      </div>

      {showPrintWarning && !preparesFreshPdf && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 bg-white/95 backdrop-blur-sm z-[9999] flex items-center justify-center p-8 animate-in fade-in zoom-in-95 duration-300">
          <div className="flex flex-col items-center text-center max-w-sm bg-white p-8 rounded-3xl shadow-2xl border border-slate-100" role="dialog" aria-modal="true" aria-labelledby="direct-print-title">
            <AlertTriangle className="text-amber-500 mb-4" size={48} />
            <h4 id="direct-print-title" className="text-lg font-black text-slate-800 mb-2">
              {isInstallmentPrint ? 'Imprimer cet échéancier' : 'Attention : Impression Directe'}
            </h4>
            <p className="text-sm text-slate-500 font-medium mb-6">
              {isInstallmentPrint
                ? 'Cette impression génère un PDF du brouillon mais n’enregistre pas le plan de paiement. Utilisez « Enregistrer le nouveau plan » dans Suivi Paiement pour le persister.'
                : "Assurez-vous que votre imprimante est prête. Le document sera archivé avant l'impression."}
            </p>
            <div className="flex gap-4">
              <button type="button" onClick={onCloseWarning} className="px-6 py-2 text-slate-400 font-bold hover:text-slate-600 transition-colors">Annuler</button>
              <button
                type="button"
                onClick={() => onGenerate(!isInstallmentPrint, true, false, true)}
                className="px-8 py-2 bg-primary text-white rounded-xl font-black"
                style={{ backgroundColor: 'var(--primary)' }}
              >Confirmer</button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};