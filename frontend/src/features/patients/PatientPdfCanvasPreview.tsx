import { useEffect, useRef, useState } from 'react';
import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

// Keep document bytes inside the authenticated React patient boundary: do not
// create blob: URLs or open detached native PDF tabs to render a patient PDF.
GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

type RenderState = 'loading' | 'rendering' | 'ready' | 'error';

export const PatientPdfCanvasPreview = ({blob}: {blob: Blob}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null);
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [renderState, setRenderState] = useState<RenderState>('loading');

  useEffect(() => {
    let cancelled = false;
    let loadingTask: ReturnType<typeof getDocument> | null = null;
    const load = async () => {
      try {
        setRenderState('loading');
        const bytes = new Uint8Array(await blob.arrayBuffer());
        if (cancelled) return;
        loadingTask = getDocument({data: bytes, isEvalSupported: false});
        const opened = await loadingTask.promise;
        if (cancelled) {
          await opened.destroy();
          return;
        }
        if (opened.numPages < 1 || opened.numPages > 100) {
          await opened.destroy();
          throw Error('Document PDF sans pages ou trop volumineux pour l’aperçu');
        }
        setNumPages(opened.numPages);
        setPageNumber(1);
        setPdf(opened);
      } catch (error) {
        if (!cancelled) {
          console.error('Échec de la lecture PDF dans le dossier patient:', error);
          setRenderState('error');
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
      // PDF.js worker, loading and document references must not survive A -> B.
      void loadingTask?.destroy();
    };
  }, [blob]);

  useEffect(() => {
    if (!pdf) return;
    let cancelled = false;
    let task: ReturnType<PDFPageProxy['render']> | null = null;
    const render = async () => {
      try {
        setRenderState('rendering');
        const pdfPage = await pdf.getPage(pageNumber);
        if (cancelled) return;
        const canvas = canvasRef.current;
        const context = canvas?.getContext('2d', {alpha: false});
        if (!canvas || !context) throw Error('Canvas PDF non disponible');
        const viewport = pdfPage.getViewport({scale: 1.45});
        const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.ceil(viewport.width * pixelRatio);
        canvas.height = Math.ceil(viewport.height * pixelRatio);
        canvas.style.width = viewport.width + 'px';
        canvas.style.height = viewport.height + 'px';
        task = pdfPage.render({
          canvas, canvasContext: context, viewport,
          transform: pixelRatio === 1 ? undefined : [pixelRatio, 0, 0, pixelRatio, 0, 0],
        });
        await task.promise;
        if (!cancelled) setRenderState('ready');
      } catch (error: unknown) {
        const message = error instanceof Error ? error.name : '';
        if (!cancelled && message !== 'RenderingCancelledException') {
          console.error('Échec du rendu PDF dans le dossier patient:', error);
          setRenderState('error');
        }
      }
    };
    void render();
    return () => {
      cancelled = true;
      task?.cancel();
    };
  }, [pdf, pageNumber]);

  return (
    <div className="flex min-h-0 flex-1 flex-col" data-pdf-viewer="canvas">
      <div className="flex shrink-0 items-center justify-center gap-3 border-b border-border-main bg-card px-3 py-2">
        <button type="button" onClick={() => setPageNumber(n => Math.max(1,n - 1))}
          disabled={pageNumber <= 1 || renderState !== 'ready'}
          className="rounded-lg border border-border-main px-3 py-1.5 text-xs font-bold disabled:opacity-40"
          aria-label="Page PDF précédente">Précédente</button>
        <span className="text-xs font-semibold text-text-main" aria-live="polite">
          Page {pageNumber} / {numPages || '…'}
        </span>
        <button type="button" onClick={() => setPageNumber(n => Math.min(numPages,n + 1))}
          disabled={pageNumber >= numPages || renderState !== 'ready'}
          className="rounded-lg border border-border-main px-3 py-1.5 text-xs font-bold disabled:opacity-40"
          aria-label="Page PDF suivante">Suivante</button>
      </div>
      <div className="min-h-0 flex-1 overflow-auto bg-slate-200 p-3 text-center sm:p-5">
        {renderState === 'error' && (
          <p role="alert" className="mx-auto max-w-lg rounded-xl bg-card p-5 text-sm font-bold text-danger">
            Impossible d’afficher ce PDF. Utilisez « Fichier » pour le télécharger.
          </p>
        )}
        {renderState !== 'ready' && renderState !== 'error' && (
          <p role="status" className="p-4 text-sm font-semibold text-text-muted">Préparation de l’aperçu PDF…</p>
        )}
        <canvas ref={canvasRef} data-testid="patient-pdf-page-canvas"
          data-pdf-rendered={renderState === 'ready' ? 'true' : 'false'}
          aria-label={`Page ${pageNumber} du document PDF`}
          className="mx-auto bg-white shadow-lg"
          style={{display: renderState === 'ready' ? 'block' : 'none'}} />
      </div>
    </div>
  );
};
