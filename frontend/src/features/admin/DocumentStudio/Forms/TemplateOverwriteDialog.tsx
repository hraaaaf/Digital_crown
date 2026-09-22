import React from 'react';

interface TemplateOverwriteDialogProps {
  modelName: string;
  scopeLabel: string;
  onCancel: () => void;
  onConfirm: () => void;
}

export const TemplateOverwriteDialog: React.FC<TemplateOverwriteDialogProps> = ({
  modelName,
  scopeLabel,
  onCancel,
  onConfirm,
}) => (
  <div
    className="fixed inset-0 z-[140] flex items-center justify-center bg-slate-950/40 p-4"
    role="dialog"
    aria-modal="true"
    aria-labelledby="template-overwrite-title"
  >
    <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl">
      <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">{scopeLabel}</p>
      <h3 id="template-overwrite-title" className="mt-1 text-lg font-black text-slate-900">
        Remplacer le brouillon actuel ?
      </h3>
      <p className="mt-3 text-sm font-medium leading-relaxed text-slate-600">
        Le modèle « {modelName} » remplacera les champs qu’il contient. Vous pourrez encore les modifier avant génération.
      </p>
      <div className="mt-5 flex flex-wrap justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="min-h-10 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600"
        >
          Conserver mon brouillon
        </button>
        <button
          type="button"
          onClick={onConfirm}
          className="min-h-10 rounded-xl bg-primary px-4 py-2 text-sm font-black text-white"
        >
          Remplacer par le modèle
        </button>
      </div>
    </div>
  </div>
);
