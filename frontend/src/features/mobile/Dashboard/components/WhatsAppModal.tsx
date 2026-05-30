import { MessageSquare } from 'lucide-react';
import { cn } from '../../../../utils/cn';

export function WhatsAppModal({
  whatsappTemplate,
  setWhatsappTemplate,
  customMessage,
  setCustomMessage,
  onCancel,
  onSend,
}: {
  whatsappTemplate: string;
  setWhatsappTemplate: (t: 'rappel' | 'confirmation') => void;
  customMessage: string;
  setCustomMessage: (msg: string) => void;
  onCancel: () => void;
  onSend: () => void;
}) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-card border border-glass-border rounded-[24px] w-full max-w-sm overflow-hidden shadow-elite animate-in fade-in zoom-in-95 duration-200 p-5 space-y-4">
        <h3 className="font-outfit font-black text-primary flex items-center gap-2">
          <MessageSquare size={18} /> Rappel WhatsApp
        </h3>
        
        <div className="space-y-3">
          <div>
            <label className="text-[10px] font-black uppercase text-text-muted">Modèle de message</label>
            <div className="flex gap-2 mt-1">
              <button 
                onClick={() => setWhatsappTemplate('rappel')}
                className={cn(
                  "flex-1 py-2 text-[10px] font-black uppercase tracking-wider rounded-lg border transition-all",
                  whatsappTemplate === 'rappel' ? "bg-primary text-white border-primary" : "bg-white text-slate-600 border-slate-200"
                )}
              >
                Rappel RDV
              </button>
              <button 
                onClick={() => setWhatsappTemplate('confirmation')}
                className={cn(
                  "flex-1 py-2 text-[10px] font-black uppercase tracking-wider rounded-lg border transition-all",
                  whatsappTemplate === 'confirmation' ? "bg-primary text-white border-primary" : "bg-white text-slate-600 border-slate-200"
                )}
              >
                Confirmation
              </button>
            </div>
          </div>

          <div>
            <label className="text-[10px] font-black uppercase text-text-muted">Message à envoyer</label>
            <textarea 
              value={customMessage}
              onChange={e => setCustomMessage(e.target.value)}
              className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-xs outline-none focus:border-primary h-24 resize-none font-medium text-slate-800"
            />
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <button 
            onClick={onCancel} 
            className="flex-1 py-2.5 rounded-xl border border-glass-border font-bold text-xs text-text-main active:scale-95 transition-all"
          >
            Annuler
          </button>
          <button 
            onClick={onSend} 
            className="flex-1 py-2.5 rounded-xl bg-primary text-white font-bold text-xs shadow-md active:scale-95 transition-all flex items-center justify-center gap-1.5"
          >
            <MessageSquare size={14} /> Envoyer
          </button>
        </div>
      </div>
    </div>
  );
}
