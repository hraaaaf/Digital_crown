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
        "flex flex-col gap-1.5 p-1.5 sm:p-2 bg-card/95 dark:bg-slate-950/92 backdrop-blur-2xl rounded-2xl border border-border-main/80 dark:border-white/10 shadow-lg relative overflow-hidden w-full shrink-0",
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
            className="shrink-0 rounded-lg border border-amber-300 bg-card px-2.5 py-1.5 text-[9px] font-black uppercase tracking-wide"
          >
            Compris
          </button>
        </div>
      )}

      <div className={cn(
        "grid items-center gap-2",
        isHonoraires ? "grid-cols-[92px_1fr] sm:grid-cols-[120px_minmax(260px,0.8fr)_minmax(320px,1fr)]" : "grid-cols-1 sm:grid-cols-[auto_1fr]"
      )}>
        {(activeTab === 'devis' || activeTab === 'honoraires') && typeof total === 'number' ? (
          <div className="flex h-full min-h-9 items-center justify-between gap-2 rounded-xl bg-background px-2 py-1 dark:bg-slate-900">
            <span className="text-[8px] sm:text-[9px] font-black text-text-muted uppercase tracking-widest leading-tight">Total</span>
            <span className="text-base sm:text-lg font-black text-text-main dark:text-white tracking-tighter leading-tight">
              {total.toLocaleString('fr-FR')} <span className="text-[9px] opacity-50">MAD</span>
            </span>
          </div>
        ) : (
          <div className="hidden sm:block" />
        )}

        {isHonoraires && (
          <>
            <div aria-label="Statut de règlement" className="grid grid-cols-3 gap-1 rounded-xl bg-input-field p-1 dark:bg-slate-900">
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
                    "min-h-8 rounded-lg px-2 text-[8px] sm:text-[9px] font-black uppercase tracking-wide transition-all",
                    paymentStatus === status.id
                      ? "bg-card text-primary shadow-sm dark:bg-slate-800"
                      : "text-text-muted hover:text-text-main dark:text-text-muted dark:hover:text-white"
                  )}
                >
                  {status.label}
                </button>
              ))}
            </div>

            <div aria-label="Mode de paiement" className="col-span-2 grid grid-cols-4 gap-1 rounded-xl bg-input-field p-1 dark:bg-slate-900 sm:col-span-1">
              {(['Espèces', 'TPE', 'Chèque', 'Virement'] as const).map(mode => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setPaymentMode(mode)}
                  aria-pressed={paymentMode === mode}
                  className={cn(
                    "min-h-8 rounded-lg px-1.5 text-[8px] sm:text-[9px] font-black uppercase tracking-normal sm:tracking-wide transition-all",
                    paymentMode === mode
                      ? "bg-card text-text-main shadow-sm dark:bg-slate-800 dark:text-white"
                      : "text-text-muted hover:text-text-main dark:text-text-muted dark:hover:text-white"
                  )}
                >
                  {mode}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      <div className="grid grid-cols-3 items-stretch gap-1 sm:flex sm:items-center sm:justify-end sm:gap-1.5 w-full min-w-0">
        {onTogglePreview && (
          <button
            type="button"
            onClick={onTogglePreview}
            aria-pressed={sideStudioType === 'PREVIEW'}
            className={cn(
              'min-h-9 min-w-0 flex items-center justify-center gap-1.5 sm:gap-2 px-2 sm:px-4 py-1.5 rounded-xl font-black uppercase text-[9px] sm:text-[10px] tracking-normal sm:tracking-wider whitespace-nowrap transition-all active:scale-95 border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
              sideStudioType === 'PREVIEW'
                ? 'bg-emerald-600 text-white border-emerald-500 shadow-sm'
                : 'bg-background dark:bg-slate-900 text-text-muted dark:text-text-muted border-border-main dark:border-white/10 hover:border-border-hover dark:hover:border-white/20'
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
          className="min-h-9 min-w-0 flex items-center justify-center gap-1.5 sm:gap-2 px-2 sm:px-5 py-1.5 bg-card dark:bg-slate-900 text-text-main dark:text-text-muted border border-border-main dark:border-white/10 rounded-xl text-[9px] sm:text-[10px] font-black uppercase tracking-normal sm:tracking-wider whitespace-nowrap hover:border-primary hover:text-primary transition-all active:scale-95 disabled:opacity-50 shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
        >
          <Archive size={14} className="shrink-0" /> <span>{activeTab === 'echeancier' ? 'Générer PDF' : 'Enregistrer'}</span>
        </button>

        <button
          type="button"
          onClick={() => preparesFreshPdf
            ? onGenerate(true, false, false, true)
            : onGenerate(false, true, false, false)}
          disabled={loading}
          className="min-h-9 min-w-0 flex items-center justify-center gap-1.5 sm:gap-2 px-2 sm:px-6 py-1.5 bg-slate-900 dark:bg-card text-white dark:text-text-main rounded-xl text-[9px] sm:text-[10px] font-black uppercase tracking-normal sm:tracking-wider whitespace-nowrap hover:bg-black dark:hover:bg-input-field transition-all shadow-md active:scale-95 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500"
        >
          <Printer size={14} className="shrink-0" />
          <span>{preparesFreshPdf ? 'Préparer impression' : 'Imprimer'}</span>
        </button>
      </div>

      {showPrintWarning && !preparesFreshPdf && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4 sm:p-8 animate-in fade-in zoom-in-95 duration-300">
          <div
            className="flex flex-col items-center text-center max-w-sm bg-card dark:bg-slate-950 p-6 sm:p-8 rounded-3xl shadow-2xl border border-border-main dark:border-white/10"
            role="dialog"
            aria-modal="true"
            aria-labelledby="document-studio-print-warning-title"
          >
            <AlertTriangle className="text-amber-500 mb-4" size={48} />
            <h4 id="document-studio-print-warning-title" className="text-lg font-black text-text-main dark:text-white mb-2">Attention : Impression Directe</h4>
            <p className="text-sm text-text-muted dark:text-text-muted font-medium mb-6">Assurez-vous que votre imprimante est prête. Le document sera archivé automatiquement après l'impression.</p>
            <div className="flex flex-wrap justify-center gap-3 sm:gap-4">
              <button type="button" onClick={onCloseWarning} className="min-h-11 px-6 py-2 text-text-muted dark:text-text-muted font-bold hover:text-text-main dark:hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 rounded-xl">Annuler</button>
              <button type="button" onClick={() => onGenerate(true, true, false, true)} className="min-h-11 px-8 py-2 bg-primary text-white rounded-xl font-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50" style={{ backgroundColor: 'var(--primary)' }}>Confirmer</button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};
