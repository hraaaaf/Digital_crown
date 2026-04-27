import React, { useState, useEffect } from 'react';
import { X, Loader2, Maximize, Printer, Download } from 'lucide-react';

interface LivePreviewProps {
  pdfUrl: string | null;
  loading: boolean;
  onClose: () => void;
  title: string;
}

export const LivePreview: React.FC<LivePreviewProps> = ({ pdfUrl, loading, onClose, title }) => {
  const [iframeReady, setIframeReady] = useState(false);

  // Reset skeleton whenever pdfUrl changes
  useEffect(() => {
    setIframeReady(false);
  }, [pdfUrl]);

  const showSkeleton = loading || (pdfUrl && !iframeReady);

  return (
    <div className="w-[500px] h-full flex flex-col bg-white/80 backdrop-blur-3xl border-l border-slate-200 shadow-2xl relative overflow-hidden animate-in slide-in-from-right duration-500 z-[100]">

      {/* TOOLBAR */}
      <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-white/40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-emerald-500/10 text-emerald-600 rounded-lg flex items-center justify-center">
            <Maximize size={16} />
          </div>
          <div>
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block leading-none mb-1">Aperçu Réel</span>
            <span className="text-sm font-black text-slate-800 tracking-tight">{title}</span>
          </div>
        </div>
        <button onClick={onClose} className="p-2 text-slate-400 hover:bg-slate-100 rounded-xl transition-all">
          <X size={20} />
        </button>
      </div>

      {/* VIEWPORT */}
      <div className="flex-1 bg-slate-900/5 relative overflow-hidden">

        {/* Skeleton (Phase 2) */}
        {showSkeleton && (
          <div className="absolute inset-0 z-10 flex flex-col gap-4 p-6 bg-white animate-in fade-in duration-200">
            {/* Page simulée */}
            <div className="w-full h-8 bg-slate-100 rounded-xl animate-pulse" />
            <div className="w-3/4 h-4 bg-slate-100 rounded-lg animate-pulse" />
            <div className="w-full h-px bg-slate-200 my-2" />
            <div className="flex flex-col gap-3 mt-2">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="flex gap-3 items-center">
                  <div className="w-6 h-6 rounded-full bg-slate-100 animate-pulse shrink-0" />
                  <div className="flex-1 h-4 bg-slate-100 rounded-lg animate-pulse" style={{ width: `${70 + i * 5}%` }} />
                </div>
              ))}
            </div>
            <div className="mt-4 w-full h-32 bg-slate-100 rounded-2xl animate-pulse" />
            <div className="mt-auto flex items-center justify-center gap-2 opacity-50">
              <Loader2 className="animate-spin text-primary" size={16} style={{ color: 'var(--primary)' }} />
              <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em]">
                {loading ? 'Génération...' : 'Chargement...'}
              </span>
            </div>
          </div>
        )}

        {pdfUrl ? (
          <iframe
            src={pdfUrl}
            className="w-full h-full border-none"
            title="PDF Preview"
            onLoad={() => setIframeReady(true)}
          />
        ) : !loading ? (
          <div className="w-full h-full flex flex-col items-center justify-center p-12 text-center">
            <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center text-slate-300 mb-6">
              <Printer size={40} />
            </div>
            <h4 className="text-sm font-black text-slate-400 uppercase tracking-widest">En attente de données</h4>
            <p className="text-xs text-slate-400 font-medium mt-2">Commencez à remplir le formulaire pour voir le rendu en temps réel.</p>
          </div>
        ) : null}
      </div>

      {/* FOOTER ACTIONS */}
      <div className="p-4 border-t border-slate-200 bg-slate-50/50 flex justify-center gap-3">
        {pdfUrl && (
          <>
            <a
              href={pdfUrl.split('#')[0]}
              download
              className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-600 hover:border-primary hover:text-primary transition-all shadow-sm"
            >
              <Download size={14} /> Télécharger
            </a>
            <button
              onClick={() => window.open(pdfUrl.split('#')[0], '_blank')}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-primary/20 hover:scale-105 transition-all"
              style={{ backgroundColor: 'var(--primary)' }}
            >
              <Maximize size={14} /> Plein Écran
            </button>
          </>
        )}
      </div>
    </div>
  );
};
