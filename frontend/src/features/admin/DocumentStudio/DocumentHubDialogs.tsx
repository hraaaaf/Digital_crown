import React from 'react';

interface DocumentHubDialogsProps {
  showDiscardDraft: boolean;
  onCancelDiscard: () => void;
  onConfirmDiscard: () => void;
  showDuplicate: boolean;
  onCancelDuplicate: () => void;
  onConfirmDuplicate: () => void;
}

export const DocumentHubDialogs: React.FC<DocumentHubDialogsProps> = ({
  showDiscardDraft,
  onCancelDiscard,
  onConfirmDiscard,
  showDuplicate,
  onCancelDuplicate,
  onConfirmDuplicate,
}) => (
  <>
    {showDiscardDraft && (
      <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={onCancelDiscard} />
        <div
          className="relative bg-white rounded-[2rem] p-8 w-80 shadow-2xl flex flex-col gap-5"
          role="dialog"
          aria-modal="true"
          aria-labelledby="document-studio-discard-dialog-title"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center text-amber-500 text-lg">⚠️</div>
            <div>
              <h3 id="document-studio-discard-dialog-title" className="text-sm font-black text-slate-800">Document en cours</h3>
              <p className="text-xs text-slate-400 font-bold mt-0.5">Le brouillon non enregistré sera abandonné.</p>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onCancelDiscard}
              className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest border border-slate-200 text-slate-500 hover:bg-slate-50 transition-all"
            >Annuler</button>
            <button
              type="button"
              onClick={onConfirmDiscard}
              className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest bg-slate-800 text-white hover:bg-primary transition-all"
              style={{ '--tw-bg-primary': 'var(--primary)' } as React.CSSProperties}
            >Continuer</button>
          </div>
        </div>
      </div>
    )}

    {showDuplicate && (
      <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={onCancelDuplicate} />
        <div
          className="relative bg-white rounded-[2rem] p-8 w-80 shadow-2xl flex flex-col gap-5"
          role="dialog"
          aria-modal="true"
          aria-labelledby="document-studio-duplicate-dialog-title"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-orange-50 rounded-xl flex items-center justify-center text-orange-500 text-lg">⚠️</div>
            <div>
              <h3 id="document-studio-duplicate-dialog-title" className="text-sm font-black text-slate-800">Doublon détecté</h3>
              <p className="text-xs text-slate-400 font-bold mt-0.5">Un document similaire existe déjà pour ce patient.</p>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onCancelDuplicate}
              className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest border border-slate-200 text-slate-500 hover:bg-slate-50 transition-all"
            >Annuler</button>
            <button
              type="button"
              onClick={onConfirmDuplicate}
              className="flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest bg-orange-500 text-white hover:bg-orange-600 transition-all"
            >Forcer</button>
          </div>
        </div>
      </div>
    )}
  </>
);
