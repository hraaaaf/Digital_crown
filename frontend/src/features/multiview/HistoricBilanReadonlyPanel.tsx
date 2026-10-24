/** DEC-R2-01 + DEC-R2-02 — R-only MultiView adapter.
 * No mutation handlers, no unsanitized file URLs, and no global editor state.
 */
import { useEffect, useRef, useState } from 'react';
import { api } from '../../services/api';

type BilanIndexItem = Readonly<{ id: number; name: string }>;

export function HistoricBilanReadonlyPanel({ patientId }: { patientId: number }) {
  const [bilans, setBilans] = useState<readonly BilanIndexItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewerUrl, setViewerUrl] = useState<string | null>(null);
  const [selectedName, setSelectedName] = useState('');
  const [error, setError] = useState(false);
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
      className="space-y-2 border-t border-border-main pt-3">
      <p className="font-semibold">Bilans historiques · consultation uniquement</p>
      {loading && <p role="status">Recherche des bilans autorisés…</p>}
      {error && <p role="alert">Consultation BILAN indisponible ou refusée.</p>}
      {!loading && bilans.length === 0 && <p className="text-text-muted">Aucun bilan consultable.</p>}
      {bilans.map(item => (
        <button key={item.id} type="button" onClick={() => void open(item)}
          className="block rounded-lg border border-border-main px-3 py-2 text-left text-sm">
          Consulter : {item.name}
        </button>
      ))}
      {viewerUrl && <div className="space-y-2">
        <button type="button" onClick={() => { requestId.current += 1; revokeViewer(); }}
          className="rounded-lg border px-2 py-1 text-sm">Fermer l'aperçu</button>
        <iframe title={`Bilan historique : ${selectedName}`} src={viewerUrl}
          className="min-h-[360px] w-full border" />
      </div>}
    </section>
  );
}
