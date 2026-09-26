import React from 'react';
import { AlertTriangle, Eye, Archive, Printer } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { createPortal } from 'react-dom';
import type { CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';
import { useAccountingStore } from '../store/useAccountingStore';

interface StudioFooterProps {
  loading: boolean;
  activeTab: CertifiableDocumentStudioTab;
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
  const preparesFreshPdf = activeTab === 'certificat' || activeTab === 'libre';
  const isAccounting = activeTab === 'devis' || activeTab === 'honoraires';
  const isHonoraires = activeTab === 'honoraires';

  const paymentStatus = useAccountingStore(s => s.paymentStatus);
  const setPaymentStatus = useAccountingStore(s => s.setPaymentStatus);
  const paymentMode = useAccountingStore(s => s.paymentMode);
  const setPaymentMode = useAccountingStore(s => s.setPaymentMode);
  const paymentStatusGuardMessage = useAccountingStore(s => s.paymentStatusGuardMessage);
  const clearPaymentStatusGuard = useAccountingStore(s => s.clearPaymentStatusGuard);

  return (
    <div
      data-testid={isAccounting ? 'document-studio-accounting-footer' : undefined}
      className={cn(
        "flex flex-col gap-2.5 p-2.5 sm:p-3 bg-white/95 dark:bg-slate-950/92 backdrop-blur-2xl rounded-2xl border border-slate-200/80 dark:border-white/10 shadow-lg relative overflow-hidden w-full shrink-0",
        !isAccounting && "mt-2"
      )}
    >
      {isHonoraires && paymentStatusGuardMessage && (
        <div role="alert" className="flex items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-amber-900">
          <span className="min-w-0 text-[10px] font-bold leading-snug">
            <strong className="font-black">Paiement partiel :</strong> {paymentStatusGuardMessage}
          </span>
          <button
            type="button"
            onClick={clearPaymentStatusGuard}
            className="shrink-0 rounded-lg border border-amber-300 bg-white px-2.5 py-1.5 text-[9px] font-black uppercase tracking-wide"
          >
            Compris
          </button>
        </div>
      )}

      <div className={cn(
        "grid items-center gap-2",
        isHonoraires ? "grid-cols-1 xl:grid-cols-[auto_minmax(270px,0.8fr)_minmax(350px,1fr)]" : "grid-cols-1 sm:grid-cols-[auto_1fr]"
      )}>
        {(activeTab === 'devis' || activeTab === 'honoraires') && typeof total === 'number' ? (
          <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-900">
            <span className="text-[8px] sm:text-[9px] font-black text-slate-400 uppercase tracking-widest leading-tight">Total</span>
            <span className="text-base sm:text-lg font-black text-slate-900 dark:text-white tracking-tighter leading-tight">
              {total.toLocaleString('fr-FR')} <span className="text-[9px] opacity-50">MAD</span>
            </span>
          </div>
        ) : (
          <div className="hidden sm:block" />
        )}

        {isHonoraires && (
          <>
            <div aria-label="Statut de règlement" className="grid grid-cols-3 gap-1 rounded-xl bg-slate-100 p-1 dark:bg-slate-900">
              {[
                { id: 'EN_ATTENTE', label: 'À régler' },
                { id: 'PARTIEL', label: 'Partiel' },
                { id: 'PAYE', label: 'Payé' },
              ].map(status => (
                <button
                  key={status.id}
                  type="button"
                  onClick={() => setPaymentStatus(status.id)}
                  aria-pressed={paymentStatus === status.id}
                  className={cn(
                    "min-h-9 rounded-lg px-2 text-[8px] sm:text-[9px] font-black uppercase tracking-wide transition-all",
                    paymentStatus === status.id
                      ? "bg-white text-primary shadow-sm dark:bg-slate-800"
                      : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white"
                  )}
                >
                  {status.label}
                </button>
              ))}
            </div>

            <div aria-label="Mode de paiement" className="grid grid-cols-4 gap-1 rounded-xl bg-slate-100 p-1 dark:bg-slate-900">
              {(['Espèces', 'TPE', 'Chèque', 'Virement'] as const).map(mode => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setPaymentMode(mode)}
                  aria-pressed={paymentMode === mode}
                  className={cn(
                    "min-h-9 rounded-lg px-1.5 text-[8px] sm:text-[9px] font-black uppercase tracking-normal sm:tracking-wide transition-all",
                    paymentMode === mode
                      ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white"
                      : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white"
                  )}
                >
                  {mode}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      <div className="grid grid-cols-3 items-stretch gap-1.5 sm:flex sm:items-center sm:justify-end sm:gap-2.5 w-full min-w-0">
        {onTogglePreview && (
          <button
            type="button"
            onClick={onTogglePreview}
            aria-pressed={sideStudioType === 'PREVIEW'}
            className={cn(
              'min-h-11 min-w-0 flex items-center justify-center gap-1.5 sm:gap-2 px-2 sm:px-4 py-2.5 rounded-xl font-black uppercase text-[9px] sm:text-[10px] tracking-normal sm:tracking-wider whitespace-nowrap transition-all active:scale-95 border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
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
          className="min-h-11 min-w-0 flex items-center justify-center gap-1.5 sm:gap-2 px-2 sm:px-5 py-2.5 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-white/10 rounded-xl text-[9px] sm:text-[10px] font-black uppercase tracking-normal sm:tracking-wider whitespace-nowrap hover:border-primary hover:text-primary transition-all active:scale-95 disabled:opacity-50 shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
        >
          <Archive size={14} className="shrink-0" /> <span>{activeTab === 'echeancier' ? 'Générer PDF' : 'Enregistrer'}</span>
        </button>

        <button
          type="button"
          onClick={() => preparesFreshPdf
            ? onGenerate(true, false, false, true)
            : onGenerate(false, true, false, false)}
          disabled={loading}
          className="min-h-11 min-w-0 flex items-center justify-center gap-1.5 sm:gap-2 px-2 sm:px-6 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-950 rounded-xl text-[9px] sm:text-[10px] font-black uppercase tracking-normal sm:tracking-wider whitespace-nowrap hover:bg-black dark:hover:bg-slate-100 transition-all shadow-md active:scale-95 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500"
        >
          <Printer size={14} className="shrink-0" />
          <span>{preparesFreshPdf ? 'Préparer impression' : 'Imprimer'}</span>
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
