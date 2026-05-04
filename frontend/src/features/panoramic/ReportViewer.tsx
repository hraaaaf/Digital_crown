import React from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, Printer, Share2, Loader2, ShieldCheck } from 'lucide-react';

interface ReportViewerProps {
  markdown: string;
  isGenerating: boolean;
  engineName?: string;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({ markdown, isGenerating, engineName }) => {
  if (isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-6 border-2 border-dashed border-indigo-100 rounded-3xl bg-indigo-50/30 backdrop-blur-sm animate-pulse">
        <div className="relative">
          <Loader2 className="animate-spin text-indigo-600" size={40} />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-2 h-2 bg-indigo-600 rounded-full animate-ping" />
          </div>
        </div>
        <div className="text-center">
          <p className="text-indigo-900 font-black text-sm tracking-widest uppercase">OralGPT en cours d'analyse...</p>
          <p className="text-slate-400 text-[10px] mt-1 font-mono italic">Inférence locale Llama 3.2 • Phase 4</p>
        </div>
      </div>
    );
  }

  if (!markdown && !isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-slate-300 opacity-50">
        <FileText size={48} strokeWidth={1} />
        <p className="text-xs font-bold mt-4 uppercase tracking-tighter">Aucun rapport généré</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-[2.5rem] shadow-2xl shadow-indigo-100/50 border border-slate-200/60 overflow-hidden flex flex-col h-full print:shadow-none print:border-none print:rounded-none">
      {/* Header Actions - Ghost Elite Style */}
      <div className="bg-slate-50/80 backdrop-blur-md px-8 py-5 border-b border-slate-100 flex justify-between items-center print:hidden shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-200">
            <FileText size={16} className="text-white" />
          </div>
          <div>
            <span className="block font-black text-slate-800 text-xs tracking-[0.15em] uppercase">Intelligence Clinique</span>
            <span className="block text-[9px] text-indigo-500 font-bold uppercase tracking-widest">{engineName || "Moteur OralGPT v4.0"}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => window.print()}
            className="p-2.5 hover:bg-white hover:shadow-md rounded-xl transition-all text-slate-500 hover:text-indigo-600 active:scale-90"
            title="Imprimer le diagnostic"
          >
            <Printer size={18} />
          </button>
          <button className="p-2.5 hover:bg-white hover:shadow-md rounded-xl transition-all text-slate-500 hover:text-indigo-600 active:scale-90">
            <Share2 size={18} />
          </button>
        </div>
      </div>

      {/* Markdown Content */}
      <div className="p-8 overflow-y-auto flex-1 custom-scrollbar">
        <div className="prose prose-slate max-w-none 
          prose-headings:text-indigo-950 prose-headings:font-black
          prose-h3:text-sm prose-h3:uppercase prose-h3:tracking-[0.1em] prose-h3:border-l-4 prose-h3:border-indigo-500 prose-h3:pl-3
          prose-p:text-slate-700 prose-p:leading-relaxed prose-p:text-[13px]
          prose-strong:text-indigo-700 prose-strong:font-black
          prose-ul:space-y-1 prose-li:text-slate-600 prose-li:text-[13px]">
          
          <ReactMarkdown>{markdown}</ReactMarkdown>
        </div>
        
        {/* Certification / Validation Badge */}
        <div className="mt-8 p-4 bg-emerald-50/50 border border-emerald-100 rounded-2xl flex items-center gap-4 print:bg-slate-50 print:border-slate-200">
          <div className="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center shrink-0 shadow-lg shadow-emerald-100">
            <ShieldCheck size={20} className="text-white" />
          </div>
          <div>
            <p className="text-[11px] font-black text-emerald-900 uppercase tracking-wider">Analyse Certifiée IA</p>
            <p className="text-[10px] text-emerald-700/80 leading-tight">Vérifié par Loki-Silvres (Détection) & OralGPT (Interprétation)</p>
          </div>
        </div>

        {/* Footer Automatique (Compliance) */}
        <div className="mt-12 pt-6 border-t border-slate-100 text-[9px] text-slate-400 italic leading-relaxed font-medium">
          Ce rapport est généré par un système d'intelligence artificielle (OralGPT) basé sur les détections du modèle Loki-Silvres. 
          Il ne remplace en aucun cas l'expertise clinique finale du praticien responsable. Digital Crown - SANINOVA Edition.
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #f1f5f9;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #e2e8f0;
        }
      `}</style>
    </div>
  );
};
