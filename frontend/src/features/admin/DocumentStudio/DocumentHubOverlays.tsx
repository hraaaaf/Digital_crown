import React from 'react';

interface PendingNavigationDialogProps {
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function PendingNavigationDialog({ open, onCancel, onConfirm }: PendingNavigationDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={onCancel}
        aria-label="Fermer la confirmation de changement de document"
      />
      <div
        className="relative bg-white dark:bg-slate-950 rounded-[2rem] p-8 w-80 shadow-2xl flex flex-col gap-5"
        role="dialog"
        aria-modal="true"
        aria-labelledby="document-navigation-warning-title"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center text-amber-500 text-lg" aria-hidden="true">⚠️</div>
          <div>
            <h3 id="document-navigation-warning-title" className="text-sm font-black text-slate-800 dark:text-white">Document en cours</h3>
            <p className="text-xs text-slate-400 font-bold mt-0.5">Le brouillon non enregistré sera abandonné.</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900 transition-all"
          >Annuler</button>
          <button
            type="button"
            onClick={onConfirm}
            className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest bg-slate-800 text-white hover:bg-primary transition-all"
            style={{ '--tw-bg-primary': 'var(--primary)' } as React.CSSProperties}
          >Continuer</button>
        </div>
      </div>
    </div>
  );
}

interface DuplicateWarningDialogProps {
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function DuplicateWarningDialog({ open, onCancel, onConfirm }: DuplicateWarningDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={onCancel}
        aria-label="Fermer l'avertissement de doublon"
      />
      <div
        className="relative bg-white dark:bg-slate-950 rounded-[2rem] p-8 w-80 shadow-2xl flex flex-col gap-5"
        role="dialog"
        aria-modal="true"
        aria-labelledby="document-duplicate-warning-title"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-orange-50 rounded-xl flex items-center justify-center text-orange-500 text-lg" aria-hidden="true">⚠️</div>
          <div>
            <h3 id="document-duplicate-warning-title" className="text-sm font-black text-slate-800 dark:text-white">Doublon détecté</h3>
            <p className="text-xs text-slate-400 font-bold mt-0.5">Un document similaire existe déjà pour ce patient.</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900 transition-all"
          >Annuler</button>
          <button
            type="button"
            onClick={onConfirm}
            className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest bg-orange-500 text-white hover:bg-orange-600 transition-all"
          >Forcer</button>
        </div>
      </div>
    </div>
  );
}
