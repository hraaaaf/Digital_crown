import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Loader2, Maximize, Printer, Download, RefreshCcw } from 'lucide-react';

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
  inline = false,
}) => {
  const [iframeReady, setIframeReady] = useState(false);
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIframeReady(false);
  }, [pdfUrl]);

  useEffect(() => {
    if (inline) return;
    closeButtonRef.current?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [inline, onClose]);

  const showSkeleton = loading || Boolean(pdfUrl && !iframeReady);

  const containerContent = (
    <div className="relative flex h-full w-full flex-col bg-white">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white/80 p-4 backdrop-blur-md sm:p-5">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600">
            <Maximize size={20} />
          </div>
          <div className="min-w-0">
            <span className="mb-1 block text-[10px] font-black uppercase leading-none tracking-widest text-slate-400">Aperçu document</span>
            <span
              id={inline ? undefined : 'document-studio-live-preview-title'}
              className="block truncate text-base font-black tracking-tight text-slate-800"
            >
              {title}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              disabled={loading}
              className="flex min-h-11 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-slate-600 transition-all hover:border-primary hover:bg-primary hover:text-white disabled:opacity-50 sm:text-[11px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            >
              {loading ? <Loader2 size={15} className="animate-spin" /> : <RefreshCcw size={15} />}
              Actualiser
            </button>
          )}
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="flex min-h-11 items-center gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-red-600 shadow-sm transition-all hover:bg-red-600 hover:text-white sm:text-[11px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
          >
            <X size={16} />
            Fermer
          </button>
        </div>
      </div>

      <div className="relative flex-1 overflow-hidden bg-slate-900/5">
        {showSkeleton && (
          <div className="absolute inset-0 z-10 flex flex-col gap-4 bg-white p-5 animate-in fade-in duration-200 sm:p-8" role="status" aria-live="polite">
            <div className="h-12 w-full animate-pulse rounded-2xl bg-slate-100" />
            <div className="h-6 w-3/4 animate-pulse rounded-xl bg-slate-100" />
            <div className="my-4 h-px w-full bg-slate-200" />
            <div className="mt-2 flex flex-col gap-4">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="flex items-center gap-4">
                  <div className="h-8 w-8 shrink-0 animate-pulse rounded-full bg-slate-100" />
                  <div className="h-5 flex-1 animate-pulse rounded-xl bg-slate-100" />
                </div>
              ))}
            </div>
            <div className="mt-8 h-48 w-full animate-pulse rounded-[2rem] bg-slate-100" />
            <div className="mt-auto flex flex-col items-center gap-4 pb-8 opacity-60">
              <Loader2 className="animate-spin text-primary" size={30} style={{ color: 'var(--primary)' }} />
              <span className="text-center text-[11px] font-black uppercase tracking-[0.28em] text-primary sm:text-[12px]">
                {loading ? 'Génération du document…' : 'Chargement du PDF…'}
              </span>
            </div>
          </div>
        )}

        {pdfUrl ? (
          <iframe
            src={pdfUrl}
            className="h-full w-full border-none"
            title={`Aperçu PDF — ${title}`}
            onLoad={() => setIframeReady(true)}
          />
        ) : !loading ? (
          <div className="flex h-full w-full flex-col items-center justify-center p-8 text-center sm:p-16">
            <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-[2rem] bg-slate-100 text-slate-300 shadow-inner sm:h-24 sm:w-24">
              <Printer size={44} />
            </div>
            <h4 className="text-sm font-black uppercase tracking-widest text-slate-500 sm:text-base">Aperçu non généré</h4>
            <p className="mt-3 max-w-xs text-sm font-medium text-slate-400">Actualisez l’aperçu pour générer le PDF en lecture seule.</p>
          </div>
        ) : null}
      </div>

      <div className="flex flex-wrap justify-center gap-3 border-t border-slate-200 bg-white/80 p-4 backdrop-blur-md sm:p-5">
        {pdfUrl && (
          <>
            <a
              href={pdfUrl.split('#')[0]}
              download={`${title}.pdf`}
              className="flex min-h-11 items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-2.5 text-[10px] font-black uppercase tracking-widest text-slate-600 shadow-sm transition-all hover:border-primary hover:text-primary sm:text-[11px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            >
              <Download size={17} /> Télécharger PDF
            </a>
            <button
              type="button"
              onClick={() => window.open(pdfUrl.split('#')[0], '_blank')}
              className="flex min-h-11 items-center gap-2 rounded-2xl bg-primary px-5 py-2.5 text-[10px] font-black uppercase tracking-widest text-white shadow-xl shadow-primary/20 transition-all hover:scale-[1.02] sm:text-[11px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
              style={{ backgroundColor: 'var(--primary)' }}
            >
              <Maximize size={17} /> Plein écran
            </button>
          </>
        )}
      </div>
    </div>
  );

  if (inline) {
    return (
      <div
        className="flex h-full w-full flex-col overflow-hidden rounded-[2rem] border border-slate-200/60 bg-white/90 shadow-xl ring-1 ring-black/5 backdrop-blur-3xl animate-in fade-in duration-300 sm:rounded-[2.5rem]"
        role="region"
        aria-label={`Aperçu PDF — ${title}`}
      >
        {containerContent}
      </div>
    );
  }

  return createPortal(
    <>
      <style>{`
        body:has(.document-studio-live-preview) .fixed.right-2.top-2.bottom-2.w-\\[550px\\].z-\\[11000\\] {
          pointer-events: none;
        }
        @media (max-width: 1023px) {
          body:has(.document-studio-live-preview) div:has(> [data-tour="document-hub-content"]) {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
          }
        }
      `}</style>
      <div
        className="document-studio-live-preview fixed inset-x-3 bottom-3 top-3 z-[20000] flex flex-col overflow-hidden rounded-[2rem] border border-slate-200/60 bg-white shadow-[0_32px_64px_rgba(0,0,0,0.2)] ring-1 ring-black/5 animate-in slide-in-from-right-12 duration-500 sm:inset-y-4 sm:left-auto sm:right-4 sm:w-[min(600px,calc(100vw-2rem))] sm:rounded-[3rem]"
        style={{ pointerEvents: 'auto' }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="document-studio-live-preview-title"
      >
        {containerContent}
      </div>
    </>,
    document.body,
  );
};
