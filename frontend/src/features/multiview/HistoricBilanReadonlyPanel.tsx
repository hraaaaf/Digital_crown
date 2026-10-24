/** DEC-R2-01 + DEC-R2-02 — R-only MultiView adapter.
 * No mutation handlers, no unsanitized file URLs, and no global editor state.
 */
import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { api } from '../../services/api';
import { Eye, FileText, ShieldCheck, Maximize2, X } from 'lucide-react';

type BilanIndexItem = Readonly<{ id: number; name: string }>;

export function HistoricBilanReadonlyPanel({ patientId }: { patientId: number }) {
  const [bilans, setBilans] = useState<readonly BilanIndexItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewerUrl, setViewerUrl] = useState<string | null>(null);
  const [pageImageUrl, setPageImageUrl] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageCount, setPageCount] = useState(1);
  const [selectedName, setSelectedName] = useState('');
  const [error, setError] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const requestId = useRef(0);
  const objectUrlRef = useRef<string | null>(null);
  const pageUrlRef = useRef<string | null>(null);

  const revokeViewer = () => {
    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    objectUrlRef.current = null;
    if (pageUrlRef.current) URL.revokeObjectURL(pageUrlRef.current);
    pageUrlRef.current = null;
    setPageImageUrl(null);
    setSelectedId(null);
    setCurrentPage(1);
    setPageCount(1);
    setViewerUrl(null);
  };

  // Each patient switch and unmount invalidates outstanding list/PDF replies.
  useEffect(() => {
    let live = true;
    requestId.current += 1;
    setBilans([]);
    setLoading(true);
    setError(false);
    revokeViewer();
    setExpanded(false);

    api.get(`/patients/${patientId}/documents`)
      .then(({ data }) => {
        if (!live) return;
        const list = Array.isArray(data) ? data : [];
        const safe = list
          .filter((entry): entry is Record<string, unknown> => (
            entry !== null && typeof entry === 'object' && !Array.isArray(entry)))
          .filter(entry => entry.type === 'BILAN' && /^\d+$/.test(String(entry.id)))
          .map(entry => ({
            id: Number(entry.id),
            name: typeof entry.name === 'string' ? entry.name : 'Bilan',
          }))
          .filter(entry => Number.isSafeInteger(entry.id) && entry.id > 0);
        setBilans(safe);
      })
      .catch(() => { if (live) setError(true); })
      .finally(() => { if (live) setLoading(false); });

    return () => {
      live = false;
      requestId.current += 1;
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
      if (pageUrlRef.current) URL.revokeObjectURL(pageUrlRef.current);
      pageUrlRef.current = null;
    };
  }, [patientId]);

  const fetchPage = async (documentId: number, targetPage: number, request: number) => {
    try {
      const result = await api.get(`/documents/bilan/${documentId}/page`, {
        responseType: 'blob', params: { page: targetPage },
      });
      if (requestId.current !== request) return;
      const png = result.data instanceof Blob ? result.data : new Blob([result.data], { type: 'image/png' });
      if (png.type !== 'image/png') return; // Native authenticated PDF viewer fallback.
      const uri = URL.createObjectURL(png);
      if (pageUrlRef.current) URL.revokeObjectURL(pageUrlRef.current);
      pageUrlRef.current = uri;
      setPageImageUrl(uri);
      setCurrentPage(targetPage);
      const count = Number(result.headers?.['x-bilan-page-count'] ?? 1);
      setPageCount(Number.isSafeInteger(count) && count >= 1 ? Math.min(count, 100) : 1);
    } catch {
      // A PDF whose page cannot be rendered is still available through the
      // original authenticated inline PDF URL; never use an unauthenticated CDN.
    }
  };

  const changePage = (targetPage: number) => {
    if (!selectedId || targetPage < 1 || targetPage > pageCount) return;
    const request = ++requestId.current;
    void fetchPage(selectedId, targetPage, request);
  };

  const open = async (item: BilanIndexItem) => {
    requestId.current += 1;
    const request = requestId.current;
    revokeViewer();
    setExpanded(false);
    setError(false);
    try {
      const result = await api.get(`/documents/bilan/${item.id}/view`, { responseType: 'blob' });
      if (requestId.current !== request) return;
      const blob = result.data instanceof Blob ? result.data : new Blob([result.data], { type: 'application/pdf' });
      if (blob.type !== 'application/pdf') { setError(true); return; }
      const url = URL.createObjectURL(blob);
      objectUrlRef.current = url;
      setViewerUrl(url);
      setSelectedName(item.name);
      setSelectedId(item.id);
      await fetchPage(item.id, 1, request);
    } catch {
      if (requestId.current === request) setError(true);
    }
  };

  return (
    <section aria-label="BILAN historiques — lecture seule" data-testid="multiview-bilan-readonly"
      className="space-y-3 rounded-2xl border border-border-main bg-gradient-to-b from-medical-pearl/70 to-card p-3 sm:p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <span aria-hidden="true" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary text-on-primary shadow-sm">
            <FileText size={20}/>
          </span>
          <div className="min-w-0">
            <h3 className="text-sm font-extrabold tracking-tight text-text-main sm:text-base">Bilans historiques</h3>
            <p className="text-xs leading-relaxed text-text-muted">Documents accessibles en lecture seule</p>
          </div>
        </div>
        <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-border-hover bg-card px-2 py-1 text-[11px] font-bold text-primary-ink">
          <ShieldCheck size={13}/> R
        </span>
      </div>
      {loading && <p role="status" className="rounded-xl bg-card p-4 text-sm text-text-muted">Vérification des documents autorisés…</p>}
      {error && <p role="alert" className="rounded-xl border border-warning-border bg-warning-surface p-3 text-sm font-medium text-warning">
        Consultation BILAN indisponible ou refusée.
      </p>}
      {!loading && bilans.length === 0 && (
        <div className="rounded-xl border border-dashed border-border-hover bg-card/85 px-4 py-5 text-center">
          <FileText size={25} className="mx-auto mb-2 text-primary" aria-hidden="true"/>
          <p className="font-semibold text-text-main">Aucun bilan consultable.</p>
          <p className="mt-1 text-xs text-text-muted">Seuls les bilans classés et autorisés apparaissent ici.</p>
        </div>
      )}
      {bilans.length > 0 && (
        <div className="space-y-2" aria-label="Liste des bilans autorisés">
          {bilans.map(item => (
            <button key={item.id} type="button" onClick={() => void open(item)}
              aria-label={`Consulter : ${item.name}`}
              className="flex min-h-12 w-full items-center gap-3 rounded-xl border border-border-main bg-card px-3 py-2.5 text-left text-sm shadow-sm transition hover:border-border-hover hover:bg-medical-pearl focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
              <FileText size={18} className="shrink-0 text-primary" aria-hidden="true"/>
              <span className="min-w-0 flex-1 truncate font-semibold text-text-main">{item.name}</span>
              <span className="inline-flex shrink-0 items-center gap-1 text-xs font-bold text-primary-ink"><Eye size={16}/> Lire</span>
            </button>
          ))}
        </div>
      )}
      {viewerUrl && (
        <div className="overflow-hidden rounded-2xl border border-border-main bg-card shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border-main bg-medical-pearl px-3 py-2">
            <span className="min-w-0 truncate text-xs font-bold text-text-main">{selectedName}</span>
            <div className="flex items-center gap-1">
              <button type="button" onClick={() => setExpanded(true)}
                className="inline-flex min-h-9 items-center gap-1 rounded-lg px-2 text-xs font-semibold text-primary-ink hover:bg-medical-pearl">
                <Maximize2 size={15}/> Agrandir
              </button>
              <button type="button" onClick={() => { requestId.current += 1; setExpanded(false); revokeViewer(); }}
                className="inline-flex min-h-9 items-center gap-1 rounded-lg px-2 text-xs font-semibold text-text-main hover:bg-medical-pearl">
                <X size={15}/> Fermer l'aperçu
              </button>
            </div>
          </div>
          {pageCount > 1 && <nav aria-label="Pages du bilan historique" className="flex items-center justify-center gap-2 border-b border-border-main py-2">
            <button type="button" onClick={() => changePage(currentPage - 1)} disabled={currentPage <= 1}
              className="min-h-9 rounded-lg border px-3 text-xs font-semibold disabled:opacity-40">Page précédente</button>
            <span className="text-xs font-semibold text-text-main">Page {currentPage} / {pageCount}</span>
            <button type="button" onClick={() => changePage(currentPage + 1)} disabled={currentPage >= pageCount}
              className="min-h-9 rounded-lg border px-3 text-xs font-semibold disabled:opacity-40">Page suivante</button>
          </nav>}
          {pageImageUrl
            ? <div className="h-[420px] overflow-auto bg-medical-pearl p-2 text-center">
                <img data-testid="bilan-page-image" src={pageImageUrl}
                  alt={`Page ${currentPage} du bilan historique ${selectedName}`}
                  className="mx-auto h-auto max-w-full bg-card shadow-md" />
              </div>
            : <iframe title={`Bilan historique : ${selectedName}`} src={viewerUrl}
                className="block h-[420px] w-full bg-card" />}
        </div>
      )}
      {expanded && viewerUrl && createPortal(
        <div className="fixed inset-0 z-[750] flex flex-col bg-background/90 p-3 backdrop-blur-sm sm:p-8"
          role="dialog" aria-modal="true" aria-label={`Bilan historique agrandi : ${selectedName}`}>
          <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col overflow-hidden rounded-2xl bg-card shadow-2xl">
            <div className="flex items-center justify-between gap-3 border-b px-4 py-3">
              <span className="truncate font-bold text-text-main">{selectedName} <span className="text-xs font-normal text-text-muted">· Lecture seule</span></span>
              <button type="button" autoFocus onClick={() => setExpanded(false)}
                className="inline-flex min-h-11 items-center gap-2 rounded-xl border px-3 text-sm font-semibold text-text-main">
                <X size={17}/> Fermer
              </button>
            </div>
            {pageCount > 1 && <nav aria-label="Navigation des pages agrandies" className="flex items-center justify-center gap-3 border-b px-3 py-2">
              <button type="button" disabled={currentPage <= 1} onClick={() => changePage(currentPage - 1)}
                className="min-h-10 rounded-lg border px-3 text-sm disabled:opacity-40">Précédente</button>
              <span className="text-xs font-bold">Page {currentPage} sur {pageCount}</span>
              <button type="button" disabled={currentPage >= pageCount} onClick={() => changePage(currentPage + 1)}
                className="min-h-10 rounded-lg border px-3 text-sm disabled:opacity-40">Suivante</button>
            </nav>}
            {pageImageUrl
              ? <div className="min-h-0 flex-1 overflow-auto bg-medical-pearl p-3 text-center sm:p-5">
                  <img data-testid="bilan-page-image-expanded" src={pageImageUrl}
                    alt={`Page ${currentPage} agrandie du bilan historique ${selectedName}`}
                    className="mx-auto h-auto max-w-full bg-card shadow-xl"/>
                </div>
              : <iframe title={`Aperçu agrandi du bilan historique : ${selectedName}`} src={viewerUrl}
                  className="min-h-0 w-full flex-1 bg-card"/>}
          </div>
        </div>, document.body
      )}
    </section>
  );
}
