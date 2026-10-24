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
  const [selectedName, setSelectedName] = useState('');
  const [error, setError] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const requestId = useRef(0);
  const objectUrlRef = useRef<string | null>(null);

  const revokeViewer = () => {
    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    objectUrlRef.current = null;
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
    };
  }, [patientId]);

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
    } catch {
      if (requestId.current === request) setError(true);
    }
  };

  return (
    <section aria-label="BILAN historiques — lecture seule" data-testid="multiview-bilan-readonly"
      className="space-y-3 rounded-2xl border border-blue-100 bg-gradient-to-b from-blue-50/70 to-white p-3 sm:p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <span aria-hidden="true" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-900 text-white shadow-sm">
            <FileText size={20}/>
          </span>
          <div className="min-w-0">
            <h3 className="text-sm font-extrabold tracking-tight text-slate-900 sm:text-base">Bilans historiques</h3>
            <p className="text-xs leading-relaxed text-slate-600">Documents accessibles en lecture seule</p>
          </div>
        </div>
        <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-blue-200 bg-white px-2 py-1 text-[11px] font-bold text-blue-900">
          <ShieldCheck size={13}/> R
        </span>
      </div>
      {loading && <p role="status" className="rounded-xl bg-white p-4 text-sm text-slate-600">Vérification des documents autorisés…</p>}
      {error && <p role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm font-medium text-amber-900">
        Consultation BILAN indisponible ou refusée.
      </p>}
      {!loading && bilans.length === 0 && (
        <div className="rounded-xl border border-dashed border-blue-200 bg-white/85 px-4 py-5 text-center">
          <FileText size={25} className="mx-auto mb-2 text-blue-600" aria-hidden="true"/>
          <p className="font-semibold text-slate-800">Aucun bilan consultable.</p>
          <p className="mt-1 text-xs text-slate-500">Seuls les bilans classés et autorisés apparaissent ici.</p>
        </div>
      )}
      {bilans.length > 0 && (
        <div className="space-y-2" aria-label="Liste des bilans autorisés">
          {bilans.map(item => (
            <button key={item.id} type="button" onClick={() => void open(item)}
              aria-label={`Consulter : ${item.name}`}
              className="flex min-h-12 w-full items-center gap-3 rounded-xl border border-blue-100 bg-white px-3 py-2.5 text-left text-sm shadow-sm transition hover:border-blue-300 hover:bg-blue-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600">
              <FileText size={18} className="shrink-0 text-blue-700" aria-hidden="true"/>
              <span className="min-w-0 flex-1 truncate font-semibold text-slate-900">{item.name}</span>
              <span className="inline-flex shrink-0 items-center gap-1 text-xs font-bold text-blue-800"><Eye size={16}/> Lire</span>
            </button>
          ))}
        </div>
      )}
      {viewerUrl && (
        <div className="overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-blue-100 bg-slate-50 px-3 py-2">
            <span className="min-w-0 truncate text-xs font-bold text-slate-800">{selectedName}</span>
            <div className="flex items-center gap-1">
              <button type="button" onClick={() => setExpanded(true)}
                className="inline-flex min-h-9 items-center gap-1 rounded-lg px-2 text-xs font-semibold text-blue-900 hover:bg-blue-100">
                <Maximize2 size={15}/> Agrandir
              </button>
              <button type="button" onClick={() => { requestId.current += 1; setExpanded(false); revokeViewer(); }}
                className="inline-flex min-h-9 items-center gap-1 rounded-lg px-2 text-xs font-semibold text-slate-700 hover:bg-slate-200">
                <X size={15}/> Fermer l'aperçu
              </button>
            </div>
          </div>
          <iframe title={`Bilan historique : ${selectedName}`} src={viewerUrl}
            className="block h-[420px] w-full bg-white" />
        </div>
      )}
      {expanded && viewerUrl && createPortal(
        <div className="fixed inset-0 z-[750] flex flex-col bg-slate-950/80 p-3 backdrop-blur-sm sm:p-8"
          role="dialog" aria-modal="true" aria-label={`Bilan historique agrandi : ${selectedName}`}>
          <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
            <div className="flex items-center justify-between gap-3 border-b px-4 py-3">
              <span className="truncate font-bold text-slate-900">{selectedName} <span className="text-xs font-normal text-slate-500">· Lecture seule</span></span>
              <button type="button" autoFocus onClick={() => setExpanded(false)}
                className="inline-flex min-h-11 items-center gap-2 rounded-xl border px-3 text-sm font-semibold text-slate-900">
                <X size={17}/> Fermer
              </button>
            </div>
            <iframe title={`Aperçu agrandi du bilan historique : ${selectedName}`} src={viewerUrl}
              className="min-h-0 w-full flex-1 bg-white"/>
          </div>
        </div>, document.body
      )}
    </section>
  );
}
