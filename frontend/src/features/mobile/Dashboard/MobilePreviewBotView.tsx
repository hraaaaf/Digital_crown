import { Bot, BrainCircuit, MessageSquare, Send } from 'lucide-react';

export function MobilePreviewBotView() {
  return (
    <div data-dc-preview-bot className="-mx-6 h-[calc(100dvh-180px)] flex flex-col overflow-hidden">
      <div className="flex flex-col h-full bg-card shadow-2xl rounded-t-[24px] sm:rounded-[24px] overflow-hidden border border-border-main relative z-50">
        <div className="flex flex-col bg-primary text-white shrink-0">
          <div className="flex items-center justify-between px-4 pt-4 pb-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-9 h-9 rounded-xl bg-white/15 border border-white/20 flex items-center justify-center shrink-0">
                <Bot size={18} />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-black tracking-wide">Crown Bot</p>
                <p className="text-[9px] text-white/70 font-bold">Preview locale · données fictives</p>
              </div>
            </div>
            <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center">
              <MessageSquare size={16} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-1 p-2 pt-1">
            <div className="min-h-10 rounded-xl bg-white text-primary flex items-center justify-center gap-1.5 text-[10px] font-black">
              <BrainCircuit size={13} /> Assistant
            </div>
            <div className="min-h-10 rounded-xl text-white/70 flex items-center justify-center gap-1.5 text-[10px] font-black">
              <MessageSquare size={13} /> Historique
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/70">
          <div className="max-w-[86%] rounded-[18px] rounded-bl-md border border-border-main bg-white p-3 shadow-sm">
            <p className="text-[11px] font-bold leading-relaxed text-slate-700">
              Bonjour. Cette Preview montre l’interface Crown Bot sans charger de session cabinet ni contacter le backend.
            </p>
          </div>
          <div className="ml-auto max-w-[82%] rounded-[18px] rounded-br-md bg-primary p-3 text-white shadow-sm">
            <p className="text-[11px] font-bold leading-relaxed">Montre-moi le programme de cet après-midi.</p>
          </div>
          <div className="max-w-[86%] rounded-[18px] rounded-bl-md border border-border-main bg-white p-3 shadow-sm">
            <p className="text-[11px] font-bold leading-relaxed text-slate-700">
              La démonstration contient uniquement les rendez-vous fictifs visibles dans l’Agenda.
            </p>
          </div>
        </div>

        <div className="border-t border-border-main bg-white p-3 shrink-0">
          <div className="min-h-[52px] rounded-2xl border border-border-main bg-slate-50 px-4 flex items-center gap-3 text-text-muted">
            <span className="flex-1 text-[11px] font-bold">Assistant désactivé dans la Preview</span>
            <div className="w-9 h-9 rounded-xl bg-slate-200 text-slate-400 flex items-center justify-center" aria-hidden="true">
              <Send size={15} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
