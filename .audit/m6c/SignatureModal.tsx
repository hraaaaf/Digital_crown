import { FileText, XCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import { SignaturePad } from './SignaturePad';

export function SignatureModal({
  sigPatientName,
  isLoadingDocs,
  sigDocs,
  selectedDocId,
  setSelectedDocId,
  isSigning,
  onSaveSignature,
  onCancel,
}: {
  sigPatientName: string;
  isLoadingDocs: boolean;
  sigDocs: any[];
  selectedDocId: number | null;
  setSelectedDocId: (id: number) => void;
  isSigning: boolean;
  onSaveSignature: (dataUrl: string) => void;
  onCancel: () => void;
}) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-card border border-glass-border rounded-[24px] w-full max-w-sm max-h-[calc(100dvh-2rem)] overflow-y-auto shadow-elite animate-in fade-in zoom-in-95 duration-200 p-5 space-y-4">
        <div className="flex justify-between items-center gap-3">
          <h3 className="font-outfit font-black text-primary flex items-center gap-2">
            <FileText size={18} /> Signature au Fauteuil
          </h3>
          <button type="button" onClick={onCancel} aria-label="Fermer la signature" className="w-12 h-12 shrink-0 rounded-2xl inline-flex items-center justify-center text-text-muted hover:text-rose-500 hover:bg-rose-500/5 transition-colors">
            <XCircle size={20} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-xs text-text-muted">
              Patient : <span className="font-black text-text-main">{sigPatientName}</span>
            </p>
          </div>

          {isLoadingDocs ? (
            <div className="py-6 flex flex-col items-center justify-center gap-2">
              <RefreshCw className="animate-spin text-primary" size={24} />
              <p className="text-[10px] font-black uppercase text-text-muted">Chargement des documents...</p>
            </div>
          ) : sigDocs.length === 0 ? (
            <div className="py-6 text-center border border-dashed border-border-main rounded-2xl bg-slate-50/50">
              <AlertTriangle className="mx-auto text-amber-500 mb-1" size={24} />
              <p className="text-xs font-bold text-slate-600">Aucun devis à signer pour ce patient</p>
              <p className="text-[10px] text-text-muted mt-0.5">Les devis déjà signés ne sont pas reproposés.</p>
            </div>
          ) : (
            <>
              <div>
                <label className="text-[10px] font-black uppercase text-text-muted">Document à signer</label>
                <select className="w-full min-h-12 mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 text-xs outline-none focus:border-primary font-bold text-slate-800" value={selectedDocId || ''} onChange={e => setSelectedDocId(Number(e.target.value))}>
                  {sigDocs.map(d => (
                    <option key={d.id} value={d.id}>{d.filename}</option>
                  ))}
                </select>
              </div>

              <div className="pt-2 border-t border-border-main">
                <label className="text-[10px] font-black uppercase text-text-muted block mb-2">Signature du Patient</label>
                {isSigning ? (
                  <div className="py-12 flex flex-col items-center justify-center gap-2">
                    <RefreshCw className="animate-spin text-primary" size={24} />
                    <p className="text-[10px] font-black uppercase text-text-muted">Enregistrement et génération du PDF...</p>
                  </div>
                ) : (
                  <SignaturePad onSave={onSaveSignature} onCancel={onCancel} />
                )}
              </div>
            </>
          )}
        </div>

        <div className="pt-2">
          <button type="button" onClick={onCancel} className="w-full min-h-12 rounded-xl border border-glass-border font-bold text-xs text-text-muted active:scale-95 transition-all bg-white">Fermer</button>
        </div>
      </div>
    </div>
  );
}
