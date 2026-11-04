import { useEffect, useRef, useState } from 'react';
import { api } from '../../../services/api';

type Capture = { id: number; digest: string; size: number; mime: string; category: string };
type Inventory = {
  schema_version: 'dc06-product-unassigned-v1';
  state: 'NATIVE_IPC_NOT_CONNECTED' | 'UNASSIGNED_INVENTORY_READ_ONLY';
  clinical_receipt_authorized: false;
  patient_assigned: false;
  read_only: true;
  captures: Capture[];
};
type Review = {
  schema_version: 'dc06-product-review-v1';
  status: 'STAFF_REVIEW_REQUIRED';
  clinical_receipt_authorized: false;
  review_id: string; challenge: string;
  capture_id: number; capture_digest: string; capture_size: number;
  patient_id: number; nom: string; prenom: string;
  numero_dossier: string; date_naissance: string;
  expires_at: number; preview_url: string;
};

const safeCapture = (c: Capture) => Number.isSafeInteger(c.id) && c.id > 0 &&
  Number.isSafeInteger(c.size) && c.size > 0 && c.size <= 16384 &&
  c.mime === 'image/png' && /^[a-f0-9]{64}$/.test(c.digest);

const safeReview = (r: Review, c: Capture, patientId: number): boolean =>
  r.schema_version === 'dc06-product-review-v1' &&
  r.status === 'STAFF_REVIEW_REQUIRED' && r.clinical_receipt_authorized === false &&
  r.patient_id === patientId && r.capture_id === c.id &&
  r.capture_digest === c.digest && r.capture_size === c.size &&
  /^[A-Za-z0-9_-]{20,128}$/.test(r.review_id) &&
  /^[A-Za-z0-9_-]{24,128}$/.test(r.challenge) &&
  r.preview_url === '/imaging/acquisition/review/' + r.review_id + '/preview' &&
  typeof r.numero_dossier === 'string' && r.numero_dossier.length > 0 &&
  typeof r.date_naissance === 'string' && /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(r.date_naissance) &&
  r.expires_at > Math.floor(Date.now() / 1000);

/** Product staff review; NO automatic association, upload or clinical ACK. */
export function ImagingAcquisitionProductReviewV15({ patientId }: { patientId: number }) {
  const epoch = useRef(0);
  const [capture, setCapture] = useState<Capture | null>(null);
  const [review, setReview] = useState<Review | null>(null);
  const [busy, setBusy] = useState(false);
  const [dossier, setDossier] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [checked, setChecked] = useState(false);
  const [verified, setVerified] = useState<{ key: string; url: string } | null>(null);
  const [loadedKey, setLoadedKey] = useState('');
  const [result, setResult] = useState<'ready' | 'unavailable' | 'confirmed' | 'failed'>('ready');

  useEffect(() => {
    const current = ++epoch.current;
    setReview(null); setCapture(null); setBusy(false);
    setDossier(''); setBirthDate(''); setChecked(false);
    setVerified(null); setLoadedKey(''); setResult('ready');
    void api.get<Inventory>('/imaging/acquisition/unassigned')
      .then(({ data }) => {
        if (current !== epoch.current) return;
        if (data.schema_version === 'dc06-product-unassigned-v1' &&
            data.state === 'UNASSIGNED_INVENTORY_READ_ONLY' &&
            data.read_only === true && data.patient_assigned === false &&
            data.clinical_receipt_authorized === false &&
            Array.isArray(data.captures) && data.captures.length === 1 &&
            safeCapture(data.captures[0])) {
          setCapture(data.captures[0]);
        }
      })
      .catch(() => { if (current === epoch.current) setResult('unavailable'); });
    return () => { epoch.current++; };
  }, [patientId]);

  const context = review
    ? [review.review_id, review.challenge, review.patient_id, review.capture_digest].join(':')
    : '';

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;
    setVerified(null); setLoadedKey('');
    if (!review || !capture || !safeReview(review, capture, patientId)) return;
    void api.get<ArrayBuffer>(review.preview_url, {
      responseType: 'arraybuffer',
      headers: { 'X-DC-Review-Challenge': review.challenge },
    }).then(async ({ data, headers }) => {
      if (!active || !(data instanceof ArrayBuffer)) return;
      const mime = String(headers?.['content-type'] ?? '').split(';', 1)[0].trim();
      if (mime !== 'image/png' || data.byteLength !== capture.size ||
          !globalThis.crypto?.subtle) return;
      const digest = await globalThis.crypto.subtle.digest('SHA-256', data);
      const actual = Array.from(new Uint8Array(digest), value =>
        value.toString(16).padStart(2, '0')).join('');
      if (!active || actual !== capture.digest) return;
      const url = URL.createObjectURL(new Blob([data], { type: mime }));
      if (!active) { URL.revokeObjectURL(url); return; }
      objectUrl = url;
      setVerified({ key: context, url });
    }).catch(() => { /* fail closed */ });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [context, review, capture, patientId]);

  const start = async () => {
    if (!capture || busy || review || result === 'confirmed') return;
    const current = epoch.current;
    setBusy(true); setResult('ready');
    try {
      const response = await api.post<Review>('/imaging/acquisition/review', {
        selected_patient_id: patientId, capture_id: capture.id,
        capture_digest: capture.digest,
      });
      if (current !== epoch.current) return;
      if (!safeReview(response.data, capture, patientId)) {
        setResult('failed'); return;
      }
      setDossier(''); setBirthDate(''); setChecked(false);
      setReview(response.data);
    } catch {
      if (current === epoch.current) setResult('failed');
    } finally {
      if (current === epoch.current) setBusy(false);
    }
  };

  const cancel = async () => {
    const current = epoch.current;
    if (review) {
      try {
        await api.delete('/imaging/acquisition/review/' + review.review_id, {
          headers: { 'X-DC-Review-Challenge': review.challenge },
        });
      } catch {
        if (current === epoch.current) setResult('failed');
      }
    }
    if (current === epoch.current) {
      setReview(null); setVerified(null); setChecked(false);
      setDossier(''); setBirthDate(''); setLoadedKey('');
    }
  };

  const canConfirm = !!review && !!capture && safeReview(review, capture, patientId) &&
    verified?.key === context && loadedKey === context &&
    dossier.trim() === review.numero_dossier &&
    birthDate === review.date_naissance &&
    checked && !busy && result !== 'confirmed';

  const confirm = async () => {
    if (!review || !canConfirm || review.expires_at <= Math.floor(Date.now() / 1000)) return;
    const current = epoch.current;
    setBusy(true); setResult('ready');
    try {
      const { data } = await api.post('/imaging/acquisition/review/' + review.review_id + '/confirm', {
        challenge: review.challenge, selected_patient_id: patientId,
        dossier: dossier.trim(), date_naissance: birthDate,
        capture_digest: review.capture_digest, explicit_confirmation: true,
      });
      if (current !== epoch.current) return;
      if (data?.status !== 'STAFF_REVIEW_VERIFIED_TRANSIENT_ONLY' ||
          data?.clinical_receipt_authorized !== false ||
          data?.patient_assigned !== false || data?.media_published !== false) {
        setResult('failed'); return;
      }
      setResult('confirmed'); setReview(null);
    } catch {
      if (current === epoch.current) setResult('failed');
    } finally {
      if (current === epoch.current) setBusy(false);
    }
  };

  if (!capture && result !== 'unavailable') return null;
  return (
    <section aria-label="Revue d'acquisition non attribuée"
      className="mx-1 mb-3 rounded-xl border border-border-main bg-card-bg p-4 text-text-main">
      <h3 className="text-sm font-bold">Revue de capture non attribuée</h3>
      {result === 'unavailable' && <p role="alert" className="text-sm text-text-muted">Acquisition indisponible : aucune association autorisée.</p>}
      {result === 'failed' && <p role="alert" className="text-sm text-text-muted">Vérification refusée. Réessayez avec une session et une capture valides.</p>}
      {result === 'confirmed' && <p role="status" className="text-sm text-text-muted">
        Revue temporaire vérifiée. Aucun média publié ni associé au patient.
      </p>}
      {capture && !review && result !== 'confirmed' && (
        <div className="mt-3">
          <p className="text-sm text-text-muted">Une capture est en attente. Elle n'est liée à aucun patient.</p>
          <button type="button" disabled={busy} onClick={() => void start()}
            className="mt-2 min-h-11 rounded-lg border border-border-main bg-card px-4 py-2 text-text-main disabled:opacity-40">
            {busy ? 'Ouverture sécurisée…' : 'Examiner cette capture pour ce patient'}
          </button>
        </div>
      )}
      {review && capture && (
        <div className="mt-3 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div>
            {verified?.key === context && (
              <img src={verified.url} alt="Aperçu sécurisé de la capture"
                className="max-h-[480px] w-full object-contain"
                onLoad={() => setLoadedKey(context)}
                onError={() => setLoadedKey('')} />
            )}
            {loadedKey !== context && <p role="alert" className="text-xs text-text-muted">
              Aperçu non vérifié : confirmation désactivée.
            </p>}
            <p className="mt-1 break-all text-xs text-text-muted">SHA-256 : {capture.digest}</p>
          </div>
          <div className="space-y-3">
            <p className="font-semibold">{review.prenom} {review.nom}</p>
            <p className="text-sm text-text-muted">Dossier : {review.numero_dossier} — Naissance : {review.date_naissance}</p>
            <label className="block text-sm">
              Ressaisir le numéro de dossier
              <input type="text" autoComplete="off" value={dossier}
                onChange={event => setDossier(event.target.value)}
                className="mt-1 block w-full rounded-md border border-border-main bg-card p-2" />
            </label>
            <label className="block text-sm">
              Ressaisir la date de naissance
              <input type="date" value={birthDate}
                onChange={event => setBirthDate(event.target.value)}
                className="mt-1 block w-full rounded-md border border-border-main bg-card p-2" />
            </label>
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" checked={checked}
                onChange={event => setChecked(event.target.checked)} />
              Je confirme avoir vérifié l'image et ces deux identifiants. Cette revue ne publie aucun média.
            </label>
            <div className="flex flex-wrap gap-2">
              <button type="button" disabled={!canConfirm} onClick={() => void confirm()}
                className="min-h-11 rounded-lg border border-border-main bg-card px-4 py-2 disabled:opacity-40">
                {busy ? 'Contrôle…' : 'Confirmer la revue temporaire'}
              </button>
              <button type="button" disabled={busy} onClick={() => void cancel()}
                className="min-h-11 rounded-lg border border-border-main px-4 py-2">Annuler</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
