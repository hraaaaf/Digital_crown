import { useEffect, useRef, useState } from 'react';
import { API_BASE } from '../../services/api';
import type { PatientPairing } from './PatientCompanionStorage';

type StationDocument = { documentId: number; kind: 'care_sheet' | 'presence_receipt' };

export const PatientCompanionStationDocuments = ({
  sessionId,
  pairing,
  onClose,
}: {
  sessionId: string;
  pairing: PatientPairing;
  onClose: (serverRevoked: boolean) => void;
}) => {
  const [documents, setDocuments] = useState<StationDocument[]>([]);
  const [busy, setBusy] = useState(true);
  const [downloadingKey, setDownloadingKey] = useState<string | null>(null);
  const [closing, setClosing] = useState(false);
  const [error, setError] = useState('');
  const closingRef = useRef(false);
  const endpoint = `${API_BASE}/api/patient-companion/station-session/${encodeURIComponent(sessionId)}/documents`;
  const access = `accessId=${encodeURIComponent(pairing.context.access_id)}`;

  useEffect(() => {
    let cancelled = false;
    setBusy(true);
    setError('');
    void fetch(`${endpoint}?${access}`, {
      headers: { Authorization: `Bearer ${pairing.accessToken}` },
      cache: 'no-store',
    }).then(async response => {
      if (!response.ok) throw new Error('SESSION_UNAVAILABLE');
      return response.json() as Promise<{ documents: StationDocument[] }>;
    }).then(result => {
      if (!cancelled && !closingRef.current) setDocuments(result.documents);
    }).catch(() => {
      if (!cancelled && !closingRef.current) {
        setDocuments([]);
        setError('Session expirée ou indisponible. Réidentifiez-vous sur la borne.');
      }
    }).finally(() => {
      if (!cancelled && !closingRef.current) setBusy(false);
    });
    return () => { cancelled = true; };
  }, [sessionId, pairing.context.access_id, pairing.accessToken]);

  const download = async (item: StationDocument) => {
    if (downloadingKey !== null) return;
    setError('');
    setDownloadingKey(`${item.kind}:${item.documentId}`);
    const path = item.kind === 'care_sheet' ? 'care-sheet' : 'presence-receipt';
    try {
      const response = await fetch(`${endpoint}/${path}/${item.documentId}?${access}`, {
        headers: { Authorization: `Bearer ${pairing.accessToken}` },
        cache: 'no-store',
      });
      if (!response.ok || !response.headers.get('content-type')?.startsWith('application/pdf')) {
        throw new Error('PDF_NOT_AVAILABLE');
      }
      const payload = await response.blob();
      if (!payload.size) throw new Error('PDF_EMPTY');
      const url = URL.createObjectURL(payload);
      try {
        const link = document.createElement('a');
        link.href = url;
        link.download = `${path}-${item.documentId}.pdf`;
        document.body.appendChild(link);
        link.click();
        link.remove();
      } finally {
        window.setTimeout(() => URL.revokeObjectURL(url), 30000);
      }
    } catch {
      setError('Téléchargement refusé ou connexion interrompue. Recommencez l’identification si nécessaire.');
    } finally {
      setDownloadingKey(null);
    }
  };

  const closeSession = async () => {
    if (closing || downloadingKey !== null) return;
    closingRef.current = true;
    setClosing(true);
    // Client-side privacy wipe must not wait for a stalled/offline network.
    setDocuments([]);
    setError('');
    setBusy(false);
    let revoked = false;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 5000);
    try {
      const response = await fetch(
        `${API_BASE}/api/patient-companion/station-session/${encodeURIComponent(sessionId)}/purge?${access}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${pairing.accessToken}` },
          cache: 'no-store',
          signal: controller.signal,
        },
      );
      revoked = response.status === 204;
    } catch {
      // The UI must still clear sensitive content locally if the LAN is down.
      // Report a possible server-side pending expiry to the parent.
    } finally {
      window.clearTimeout(timeout);
      setDocuments([]);
      onClose(revoked);
      setClosing(false);
    }
  };

  return (
    <section data-pc-station-documents className="mb-4 rounded-2xl border border-primary/25 bg-card-bg p-5 shadow-sm">
      <h2 className="text-lg font-black text-primary">Mes documents à retirer</h2>
      <p className="mt-2 text-sm font-semibold text-text-muted">
        Les documents sont remis directement sur votre téléphone personnel, jamais téléchargés sur la borne du cabinet.
      </p>
      {busy && <p role="status" className="mt-3 text-sm">Recherche de documents autorisés…</p>}
      {!busy && !error && documents.length === 0 && (
        <p className="mt-3 text-sm">Aucun document disponible pour cette session.</p>
      )}
      {documents.map((document) => (
        <button
          key={`${document.kind}:${document.documentId}`}
          type="button"
          disabled={downloadingKey !== null || closing}
          data-pc-care-sheet-download={document.kind === 'care_sheet' ? document.documentId : undefined}
          data-pc-presence-receipt-download={document.kind === 'presence_receipt' ? document.documentId : undefined}
          onClick={() => void download(document)}
          className="mt-3 min-h-12 w-full rounded-xl bg-primary px-4 text-sm font-black text-white disabled:opacity-50"
        >
          {downloadingKey === `${document.kind}:${document.documentId}`
            ? 'Téléchargement sécurisé…'
            : document.kind === 'care_sheet' ? 'Télécharger ma feuille de soins' : 'Télécharger mon justificatif de présence'}
        </button>
      ))}
      {documents.length > 0 && (
        <p className="mt-2 text-xs font-semibold text-text-muted">
          Votre téléphone peut conserver le fichier dans Téléchargements. Protégez l’accès à votre appareil.
        </p>
      )}
      {error && <p role="alert" className="mt-3 text-sm font-bold text-rose-700">{error}</p>}
      <button type="button" disabled={closing || downloadingKey !== null}
        className="mt-4 min-h-11 w-full rounded-xl border border-border-main text-sm font-bold disabled:opacity-50"
        onClick={() => void closeSession()}>
        {closing ? 'Révocation de la session…' : 'Terminer et effacer ma session'}
      </button>
    </section>
  );
};
