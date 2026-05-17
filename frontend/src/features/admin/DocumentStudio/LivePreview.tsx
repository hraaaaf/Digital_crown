import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, Loader2, Maximize, Printer, Download } from 'lucide-react';

interface LivePreviewProps {
  pdfUrl: string | null;
  loading: boolean;
  onClose: () => void;
  onRefresh?: () => void;
  title: string;
  inline?: boolean;
}

export const LivePreview: React.FC<LivePreviewProps> = ({ 
  pdfUrl, 
  loading, 
  onClose, 
  onRefresh, 
  title,
  inline = false
}) => {
  const [iframeReady, setIframeReady] = useState(false);

  // Reset skeleton whenever pdfUrl changes
  useEffect(() => {
    setIframeReady(false);
  }, [pdfUrl]);

  const showSkeleton = loading || (pdfUrl && !iframeReady);

  const containerContent = (
    <div className="w-full h-full flex flex-col bg-white relative">
      {/* TOOLBAR */}
      <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-white/40 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-emerald-500/10 text-emerald-600 rounded-2xl flex items-center justify-center">
            <Maximize size={20} />
          </div>
          <div>
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block leading-none mb-1">Aperçu Réel Studio</span>
            <span className="text-base font-black text-slate-800 tracking-tight">{title}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {onRefresh && (
            <button 
              onClick={onRefresh}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 bg-slate-50 text-slate-600 border border-slate-200 rounded-xl text-[11px] font-black uppercase tracking-widest hover:bg-primary hover:text-white hover:border-primary transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Maximize size={16} className="rotate-45" />}
              Actualiser
            </button>
          )}
          <button 
            onClick={onClose} 
            className="flex items-center gap-2 px-5 py-2.5 bg-red-50 text-red-600 border border-red-100 rounded-xl text-[11px] font-black uppercase tracking-widest hover:bg-red-600 hover:text-white transition-all shadow-sm"
          >
            <X size={18} />
            Fermer
          </button>
        </div>
      </div>

      {/* VIEWPORT */}
      <div className="flex-1 bg-slate-900/5 relative overflow-hidden">

        {/* Skeleton (Phase 2) */}
        {showSkeleton && (
          <div className="absolute inset-0 z-10 flex flex-col gap-4 p-8 bg-white animate-in fade-in duration-200">
            <div className="w-full h-12 bg-slate-100 rounded-2xl animate-pulse" />
            <div className="w-3/4 h-6 bg-slate-100 rounded-xl animate-pulse" />
            <div className="w-full h-px bg-slate-200 my-4" />
            <div className="flex flex-col gap-4 mt-2">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="flex gap-4 items-center">
                  <div className="w-8 h-8 rounded-full bg-slate-100 animate-pulse shrink-0" />
                  <div className="flex-1 h-5 bg-slate-100 rounded-xl animate-pulse" style={{ width: `${70 + i * 5}%` }} />
                </div>
              ))}
            </div>
            <div className="mt-8 w-full h-48 bg-slate-100 rounded-[2rem] animate-pulse" />
            <div className="mt-auto flex flex-col items-center gap-4 opacity-50 pb-8">
              <Loader2 className="animate-spin text-primary" size={32} style={{ color: 'var(--primary)' }} />
              <span className="text-[12px] font-black text-primary uppercase tracking-[0.4em]">
                {loading ? 'Intelligence en cours...' : 'Rendu Dynamique...'}
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
          <div className="w-full h-full flex flex-col items-center justify-center p-16 text-center">
            <div className="w-24 h-24 bg-slate-100 rounded-[2rem] flex items-center justify-center text-slate-300 mb-8 shadow-inner">
              <Printer size={48} />
            </div>
            <h4 className="text-base font-black text-slate-400 uppercase tracking-widest">En attente de génération</h4>
            <p className="text-sm text-slate-400 font-medium mt-4 max-w-xs">Complétez les données cliniques pour activer l'aperçu dynamique.</p>
          </div>
        ) : null}
      </div>

      {/* FOOTER ACTIONS */}
      <div className="p-6 border-t border-slate-200 bg-white/40 backdrop-blur-md flex justify-center gap-4">
        {pdfUrl && (
          <>
            <a
              href={pdfUrl.split('#')[0]}
              download
              className="flex items-center gap-3 px-6 py-3 bg-white border border-slate-200 rounded-2xl text-[11px] font-black uppercase tracking-widest text-slate-600 hover:border-primary hover:text-primary transition-all shadow-sm"
            >
              <Download size={18} /> Télécharger PDF
            </a>
            <button
              onClick={() => window.open(pdfUrl.split('#')[0], '_blank')}
              className="flex items-center gap-3 px-6 py-3 bg-primary text-white rounded-2xl text-[11px] font-black uppercase tracking-widest shadow-xl shadow-primary/20 hover:scale-105 transition-all"
              style={{ backgroundColor: 'var(--primary)' }}
            >
              <Maximize size={18} /> Plein Écran
            </button>
          </>
        )}
      </div>
    </div>
  );

  if (inline) {
    return (
      <div className="w-full h-full flex flex-col bg-white/90 backdrop-blur-3xl border border-slate-200/60 shadow-xl overflow-hidden rounded-[2.5rem] ring-1 ring-black/5 animate-in fade-in duration-300">
        {containerContent}
      </div>
    );
  }

  return createPortal(
    <div 
      className="fixed right-6 top-6 bottom-6 w-[600px] z-[20000] flex flex-col bg-white/90 backdrop-blur-3xl border border-slate-200/60 shadow-[0_32px_64px_rgba(0,0,0,0.2)] overflow-hidden rounded-[3rem] ring-1 ring-black/5 animate-in slide-in-from-right-12 duration-500"
      style={{ pointerEvents: 'auto' }}
    >
      {containerContent}
    </div>,
    document.body
  );
};
