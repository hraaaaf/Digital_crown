import { useEffect, useRef, useState } from 'react';
import { FileText, Loader2 } from 'lucide-react';

interface MobilePdfCanvasProps {
  pdfUrl: string;
}

/**
 * Browser-independent mobile page preview of the EXACT PDF blob.
 * The native PDF iframe may paint a blank rectangle in Chromium mobile or
 * embedded WebViews. PDF.js is lazy-loaded only for this small-screen view.
 * No patient data are uploaded, proxied, or changed.
 */
export function MobilePdfCanvas({ pdfUrl }: MobilePdfCanvasProps) {
  const pagesRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');

  useEffect(() => {
    const pagesRoot = pagesRef.current;
    if (!pagesRoot) return;

    let disposed = false;
    let currentRender: { cancel: () => void } | null = null;
    let currentDocument: { destroy: () => Promise<void> } | null = null;
    pagesRoot.replaceChildren();
    setStatus('loading');

    const renderPages = async () => {
      try {
        // Vite copies this worker into the on-premise frontend bundle.
        // There is no external CDN dependency or patient-PDF upload.
        const [pdfjs, workerModule] = await Promise.all([
          import('pdfjs-dist'),
          import('pdfjs-dist/build/pdf.worker.min.mjs?url'),
        ]);
        if (disposed) return;
        pdfjs.GlobalWorkerOptions.workerSrc = workerModule.default;

        const task = pdfjs.getDocument({ url: pdfUrl, isEvalSupported: false });
        const document = await task.promise;
        currentDocument = document;
        if (disposed) return;

        for (let pageNo = 1; pageNo <= document.numPages; pageNo += 1) {
          if (disposed) return;
          const page = await document.getPage(pageNo);
          const reference = page.getViewport({ scale: 1 });
          const width = Math.max(120, pagesRoot.clientWidth - 8);
          const displayScale = width / reference.width;
          const density = Math.min(window.devicePixelRatio || 1, 2);
          const viewport = page.getViewport({ scale: displayScale * density });

          const canvas = document.createElement('canvas');
          canvas.width = Math.ceil(viewport.width);
          canvas.height = Math.ceil(viewport.height);
          canvas.style.width = `${Math.round(reference.width * displayScale)}px`;
          canvas.style.height = `${Math.round(reference.height * displayScale)}px`;
          canvas.className = 'block max-w-full bg-white shadow-md';
          canvas.setAttribute('role', 'img');
          canvas.setAttribute('aria-label', `Page ${pageNo} du bilan PDF`);
          const context = canvas.getContext('2d', { alpha: false });
          if (!context) throw new Error('Canvas PDF unavailable');

          const render = page.render({
            canvas,
            canvasContext: context,
            viewport,
            background: '#ffffff',
          });
          currentRender = render;
          await render.promise;
          currentRender = null;
          if (disposed) return;
          canvas.dataset.pdfRendered = 'true';
          canvas.dataset.pageNumber = String(pageNo);
          pagesRoot.appendChild(canvas);
        }

        if (!disposed) setStatus('ready');
      } catch {
        if (!disposed) setStatus('error');
      }
    };

    void renderPages();
    return () => {
      disposed = true;
      currentRender?.cancel();
      if (currentDocument) void currentDocument.destroy();
      pagesRoot.replaceChildren();
    };
  }, [pdfUrl]);

  return (
    <div className="h-full w-full overflow-y-auto bg-slate-200 p-3" aria-label="Aperçu des pages PDF sur mobile">
      {status === 'loading' && (
        <div role="status" className="flex items-center justify-center gap-3 py-8 text-sm text-slate-600">
          <Loader2 className="animate-spin" size={20} />
          Affichage du PDF…
        </div>
      )}
      {status === 'error' && (
        <div role="alert" className="flex flex-col items-center gap-3 rounded-lg bg-white p-6 text-center text-slate-700">
          <FileText size={28} />
          <p>Aperçu indisponible dans ce navigateur.</p>
          <a href={pdfUrl.split('#')[0]} target="_blank" rel="noopener noreferrer"
            className="rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-white">
            Ouvrir le PDF original
          </a>
        </div>
      )}
      <div ref={pagesRef} data-testid="mobile-pdf-pages"
        className="flex w-full flex-col items-center gap-3" />
    </div>
  );
}
