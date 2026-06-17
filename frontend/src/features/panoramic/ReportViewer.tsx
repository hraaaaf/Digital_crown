import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, Printer, Share2, Loader2, ShieldCheck, Download, Eye, Pencil, Check, X, Plus, Trash2 } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ReportViewerProps {
  markdown: string;
  isGenerating: boolean;
  engineName?: string;
  onDownload?: () => void;
  isDownloading?: boolean;
  onPreview?: () => void;
  onSaveEdit?: (markdown: string) => void;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({
  markdown,
  isGenerating,
  engineName,
  onDownload,
  isDownloading,
  onPreview,
  onSaveEdit,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [lines, setLines] = useState<string[]>([]);

  // Re-synchronise l'éditeur lorsque le bilan change (régénération, sélection historique).
  useEffect(() => {
    setLines((markdown || '').split('\n'));
  }, [markdown]);

  const isHeading = (line: string) => line.trim().startsWith('#');

  const updateLine = (idx: number, value: string) => {
    setLines(prev => prev.map((l, i) => (i === idx ? value : l)));
  };
  const deleteLine = (idx: number) => {
    setLines(prev => prev.filter((_, i) => i !== idx));
  };
  const addLine = (idx: number) => {
    setLines(prev => {
      const next = [...prev];
      next.splice(idx + 1, 0, '- ');
      return next;
    });
  };

  const handleSave = () => {
    onSaveEdit?.(lines.join('\n').replace(/\n{3,}/g, '\n\n').trim());
    setIsEditing(false);
  };
  const handleCancel = () => {
    setLines((markdown || '').split('\n'));
    setIsEditing(false);
  };

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
          <p className="text-indigo-900 font-black text-sm tracking-widest uppercase">Génération du rapport déterministe...</p>
          <p className="text-slate-400 text-[10px] mt-1 font-mono italic">Moteur Panoramique SOTA • Zéro-Hallucination</p>
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
            <span className="block text-[9px] text-indigo-500 font-bold uppercase tracking-widest">{engineName || "Générateur Déterministe"}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isEditing ? (
            <>
              <button
                onClick={handleSave}
                className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl transition-all text-[11px] font-black active:scale-90"
                title="Enregistrer les modifications"
              >
                <Check size={15} /> Enregistrer
              </button>
              <button
                onClick={handleCancel}
                className="p-2.5 hover:bg-white hover:shadow-md rounded-xl transition-all text-slate-500 hover:text-rose-600 active:scale-90"
                title="Annuler"
              >
                <X size={18} />
              </button>
            </>
          ) : (
            <>
              {onSaveEdit && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="p-2.5 hover:bg-white hover:shadow-md rounded-xl transition-all text-slate-500 hover:text-indigo-600 active:scale-90"
                  title="Modifier le bilan (ligne par ligne)"
                >
                  <Pencil size={18} />
                </button>
              )}
              <button
                onClick={onPreview}
                className="p-2.5 hover:bg-white hover:shadow-md rounded-xl transition-all text-slate-500 hover:text-indigo-600 active:scale-90"
                title="Aperçu Live PDF"
              >
                <Eye size={18} />
              </button>
              <button
                onClick={() => window.print()}
                className="p-2.5 hover:bg-white hover:shadow-md rounded-xl transition-all text-slate-500 hover:text-indigo-600 active:scale-90"
                title="Imprimer le diagnostic"
              >
                <Printer size={18} />
              </button>
              <button
                onClick={onDownload}
                disabled={isDownloading}
                className="p-2.5 hover:bg-white hover:shadow-md rounded-xl transition-all text-slate-500 hover:text-indigo-600 active:scale-90 disabled:opacity-50"
                title="Télécharger le bilan PDF"
              >
                {isDownloading ? <Loader2 size={18} className="animate-spin" /> : <Download size={18} />}
              </button>
              <button className="p-2.5 hover:bg-white hover:shadow-md rounded-xl transition-all text-slate-500 hover:text-indigo-600 active:scale-90">
                <Share2 size={18} />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Content : édition ligne/paragraphe OU rendu markdown */}
      <div className="p-8 overflow-y-auto flex-1 custom-scrollbar">
        {isEditing ? (
          <div className="space-y-2">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">
              Modifiez chaque ligne. Les titres commencent par <code className="bg-slate-100 px-1 rounded">###</code>, les puces par <code className="bg-slate-100 px-1 rounded">-</code>.
            </p>
            {lines.map((line, idx) => (
              <div key={idx} className="flex items-center gap-2 group">
                <input
                  value={line}
                  onChange={(e) => updateLine(idx, e.target.value)}
                  placeholder="(ligne vide)"
                  className={cn(
                    "flex-1 rounded-lg px-3 py-2 text-[13px] outline-none border transition-all",
                    isHeading(line)
                      ? "font-black text-indigo-900 bg-indigo-50/50 border-indigo-200 focus:border-indigo-400"
                      : "text-slate-700 bg-slate-50 border-slate-200 focus:border-indigo-300 focus:bg-white"
                  )}
                />
                <button
                  onClick={() => addLine(idx)}
                  className="p-1.5 text-slate-300 hover:text-indigo-600 transition-all opacity-0 group-hover:opacity-100"
                  title="Ajouter une ligne en dessous"
                >
                  <Plus size={15} />
                </button>
                <button
                  onClick={() => deleteLine(idx)}
                  className="p-1.5 text-slate-300 hover:text-rose-500 transition-all opacity-0 group-hover:opacity-100"
                  title="Supprimer cette ligne"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
            <button
              onClick={() => addLine(lines.length - 1)}
              className="mt-3 flex items-center gap-1.5 text-[11px] font-bold text-indigo-600 hover:text-indigo-800 transition-all"
            >
              <Plus size={14} /> Ajouter une ligne
            </button>
          </div>
        ) : (
          <>
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
                <p className="text-[11px] font-black text-emerald-900 uppercase tracking-wider">Bilan Déterministe</p>
                <p className="text-[10px] text-emerald-700/80 leading-tight">Rédigé sans LLM — éditable et validé par le praticien</p>
              </div>
            </div>

            {/* Footer Automatique (Compliance) */}
            <div className="mt-12 pt-6 border-t border-slate-100 text-[9px] text-slate-400 italic leading-relaxed font-medium">
              Ce rapport est généré déterministement à partir des dents nommées par l'IA et des annotations cliniques du praticien.
              Il ne remplace en aucun cas l'expertise clinique finale du praticien responsable. Digital Crown - SANINOVA Edition.
            </div>
          </>
        )}
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
