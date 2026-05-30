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
      <div className="bg-card border border-glass-border rounded-[24px] w-full max-w-sm overflow-hidden shadow-elite animate-in fade-in zoom-in-95 duration-200 p-5 space-y-4">
        <div className="flex justify-between items-start">
          <h3 className="font-outfit font-black text-primary flex items-center gap-2">
            <FileText size={18} /> Signature au Fauteuil
          </h3>
          <button onClick={onCancel} className="text-text-muted hover:text-rose-500">
            <XCircle size={18} />
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
              <p className="text-xs font-bold text-slate-600">Aucun devis trouvé pour ce patient</p>
              <p className="text-[10px] text-text-muted mt-0.5">Veuillez d'abord générer un devis sur le PC.</p>
            </div>
          ) : (
            <>
              <div>
                <label className="text-[10px] font-black uppercase text-text-muted">Document à signer</label>
                <select 
                  className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-xs outline-none focus:border-primary font-bold text-slate-800"
                  value={selectedDocId || ''}
                  onChange={e => setSelectedDocId(Number(e.target.value))}
                >
                  {sigDocs.map(d => (
                    <option key={d.id} value={d.id}>
                      {d.filename} ({d.signed ? 'SIGNÉ' : 'Non signé'})
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-2 border-t border-border-main">
                <label className="text-[10px] font-black uppercase text-text-muted block mb-2 font-black">Signature du Patient</label>
                {isSigning ? (
                  <div className="py-12 flex flex-col items-center justify-center gap-2">
                    <RefreshCw className="animate-spin text-primary" size={24} />
                    <p className="text-[10px] font-black uppercase text-text-muted">Enregistrement et génération du PDF...</p>
                  </div>
                ) : (
                  <SignaturePad 
                    onSave={onSaveSignature} 
                    onCancel={onCancel} 
                  />
                )}
              </div>
            </>
          )}
        </div>

        <div className="pt-2">
          <button 
            onClick={onCancel} 
            className="w-full py-2.5 rounded-xl border border-glass-border font-bold text-xs text-text-muted active:scale-95 transition-all bg-white"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}
