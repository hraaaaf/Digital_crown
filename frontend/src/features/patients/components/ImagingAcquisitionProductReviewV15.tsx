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
  durable_commit_available?: boolean;
};

/** French display/entry only; clinical API continues to use canonical ISO dates. */
const formatBirthDateFr = (iso: string): string => {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  return match ? match[3] + '/' + match[2] + '/' + match[1] : '';
};

const parseBirthDateFr = (value: string): string | null => {
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(value);
  if (!match) return null;
  const day = Number(match[1]);
  const month = Number(match[2]);
  const year = Number(match[3]);
  if (year < 1 || month < 1 || month > 12) return null;
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (day < 1 || day > days[month - 1]) return null;
  return match[3] + '-' + match[2] + '-' + match[1];
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
  r.expires_at > Math.floor(Date.now() / 1000) &&
  (r.durable_commit_available === undefined || typeof r.durable_commit_available === 'boolean');

type DurableAck = {
  schema_version: 'dc06-b06-ack-v1'; status: 'DURABLE_MEDIA_ACK';
  receipt_id: string; signature: string; signer_public_key: string;
  asset_id: number; capture_id: number; capture_digest: string;
  patient_id: number; patient_assigned: true; media_published: true;
  clinical_receipt_authorized: false;
};

const safeAck = (a: DurableAck, r: Review): boolean =>
  a?.schema_version === 'dc06-b06-ack-v1' &&
  a.status === 'DURABLE_MEDIA_ACK' &&
  /^DC06-[a-f0-9]{32}$/.test(a.receipt_id) &&
  /^[a-f0-9]{128}$/.test(a.signature) &&
  /^[a-f0-9]{64}$/.test(a.signer_public_key) &&
  Number.isSafeInteger(a.asset_id) && a.asset_id > 0 &&
  a.capture_id === r.capture_id && a.capture_digest === r.capture_digest &&
  a.patient_id === r.patient_id && a.patient_assigned === true &&
  a.media_published === true && a.clinical_receipt_authorized === false;

/** Product staff review, optionally durable only after trusted backend provisioning. */
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
  const [result, setResult] = useState<'ready' | 'unavailable' | 'confirmed' | 'persisted' | 'failed'>('ready');

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
    if (!capture || busy || review || result === 'confirmed' || result === 'persisted') return;
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

  const birthDateIso = parseBirthDateFr(birthDate);
  const canConfirm = !!review && !!capture && safeReview(review, capture, patientId) &&
    verified?.key === context && loadedKey === context &&
    dossier.trim() === review.numero_dossier &&
    birthDateIso !== null && birthDateIso === review.date_naissance &&
    checked && !busy && result !== 'confirmed' && result !== 'persisted';

  const confirm = async () => {
    if (!review || !canConfirm || review.expires_at <= Math.floor(Date.now() / 1000)) return;
    const current = epoch.current;
    setBusy(true); setResult('ready');
    try {
      const endpoint = '/imaging/acquisition/review/' + review.review_id +
        (review.durable_commit_available === true ? '/commit' : '/confirm');
      const { data } = await api.post(endpoint, {
        challenge: review.challenge, selected_patient_id: patientId,
        dossier: dossier.trim(), date_naissance: review.date_naissance,
        capture_digest: review.capture_digest, explicit_confirmation: true,
      });
      if (current !== epoch.current) return;
      if (review.durable_commit_available === true) {
        if (!safeAck(data as DurableAck, review)) { setResult('failed'); return; }
        setResult('persisted'); setReview(null);
      } else {
        if (data?.status !== 'STAFF_REVIEW_VERIFIED_TRANSIENT_ONLY' ||
            data?.clinical_receipt_authorized !== false ||
            data?.patient_assigned !== false || data?.media_published !== false) {
          setResult('failed'); return;
        }
        setResult('confirmed'); setReview(null);
      }
    } catch {
      // Lost HTTP reply after DB commit must not cause a second patient asset.
      // Verify the existing signed ACK on the same backend instead of re-upload.
      if (review.durable_commit_available === true) {
        try {
          const { data } = await api.get<DurableAck>(
            '/imaging/acquisition/receipts/' + review.capture_id, {
              params: {
                selected_patient_id: patientId,
                capture_digest: review.capture_digest,
              },
            },
          );
          if (current !== epoch.current) return;
          if (safeAck(data, review)) {
            setResult('persisted'); setReview(null);
            return;
          }
        } catch { /* lost ACK remains unverified */ }
      }
      if (current === epoch.current) setResult('failed');
    } finally {
      if (current === epoch.current) setBusy(false);
    }
  };

  if (!capture && result !== 'unavailable') return null;
  return (
    <section aria-label="Revue d'acquisition non attribuée"
      className="mx-0 mb-4 min-w-0 rounded-2xl border border-border-main bg-card p-3 text-text-main shadow-sm sm:mx-1 sm:p-5 lg:p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div className="space-y-1">
          <h3 className="text-base font-bold sm:text-lg">Capture en attente de vérification</h3>
          <p className="text-sm text-text-muted">
            Vérifiez l'image et l'identité du patient avant toute association au dossier.
          </p>
        </div>
      </div>
      {result === 'unavailable' && <p role="alert" className="rounded-lg border border-danger-border bg-danger-surface p-3 text-sm text-danger">Acquisition indisponible : aucune association autorisée.</p>}
      {result === 'failed' && <p role="alert" className="rounded-lg border border-danger-border bg-danger-surface p-3 text-sm text-danger">Vérification refusée. Réessayez avec une session et une capture valides.</p>}
      {result === 'confirmed' && <p role="status" className="rounded-lg border border-info-border bg-info-surface p-3 text-sm text-info">
        Vérification terminée. Cette capture n'a pas été ajoutée au dossier.
      </p>}
      {result === 'persisted' && <p role="status" className="rounded-lg border border-success-border bg-success-surface p-3 text-sm text-success">
        Image enregistrée dans le dossier du patient.
      </p>}
      {capture && !review && result !== 'confirmed' && result !== 'persisted' && (
        <div className="space-y-3 rounded-xl border border-border-main bg-background p-4 sm:p-5">
          <p className="text-sm text-text-muted">
            Une image est disponible. Elle n'est pas encore associée au dossier de ce patient.
          </p>
          <button type="button" disabled={busy} onClick={() => void start()}
            className="inline-flex min-h-11 w-full items-center justify-center rounded-lg bg-primary px-5 py-3 text-sm font-semibold text-on-primary transition-colors hover:bg-secondary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-40 sm:w-auto">
            {busy ? 'Ouverture sécurisée…' : 'Examiner cette capture pour ce patient'}
          </button>
        </div>
      )}
      {review && capture && (
        <div className="grid min-w-0 grid-cols-1 gap-3 sm:gap-5 lg:grid-cols-2 lg:gap-6">
          <div className="min-w-0 space-y-3" aria-label="Étape 1 : contrôle de l'image">
            <h4 className="text-sm font-semibold sm:text-base">1. Contrôler l'image</h4>
            <div className="min-w-0 overflow-hidden rounded-xl border border-border-main bg-background p-2 sm:p-4">
              {verified?.key === context && (
                <img src={verified.url} alt="Aperçu sécurisé de la capture"
                  className="mx-auto block max-h-[480px] w-full object-contain"
                  onLoad={() => setLoadedKey(context)}
                  onError={() => setLoadedKey('')} />
              )}
              {loadedKey !== context && (
                <p role="alert" className="rounded-lg border border-warning-border bg-warning-surface p-3 text-sm text-warning">
                  Image non vérifiée ou indisponible : confirmation désactivée.
                </p>
              )}
            </div>
            <p className="text-xs text-text-muted">
              Vérifiez visuellement que cette image correspond au patient sélectionné.
            </p>
          </div>
          <div className="min-w-0 space-y-3 sm:space-y-4" aria-label="Étape 2 : vérification d'identité">
            <h4 className="text-sm font-semibold sm:text-base">2. Vérifier l'identité du patient</h4>
            <div className="min-w-0 rounded-xl border border-border-main bg-background p-3 sm:p-4">
              <p className="font-semibold text-text-main">{review.prenom} {review.nom}</p>
              <p className="mt-1 text-sm text-text-muted">
                Dossier : {review.numero_dossier} — Naissance : {formatBirthDateFr(review.date_naissance)}
              </p>
            </div>
            <div className="min-w-0 space-y-3">
              <p className="text-sm text-text-muted">
                Pour éviter une erreur d'attribution, ressaisissez ces deux informations.
              </p>
              <label className="block text-sm font-medium">
                Ressaisir le numéro de dossier
                <input type="text" autoComplete="off" value={dossier}
                  onChange={event => setDossier(event.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-lg border border-border-main bg-card p-3 text-text-main focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary" />
              </label>
              <label className="block text-sm font-medium">
                Ressaisir la date de naissance
                <input type="text" inputMode="numeric" autoComplete="off"
                  placeholder="JJ/MM/AAAA" maxLength={10} spellCheck={false}
                  value={birthDate} onChange={event => setBirthDate(event.target.value)}
                  className="mt-1.5 min-h-11 w-full min-w-0 rounded-lg border border-border-main bg-card p-3 text-text-main focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary" />
                <span className="mt-1 block text-xs text-text-muted">Format : JJ/MM/AAAA</span>
              </label>
            </div>
            <label className="flex min-w-0 items-start gap-2 rounded-xl border border-border-main bg-background p-2 text-sm sm:gap-3 sm:p-3">
              <input type="checkbox" checked={checked}
                onChange={event => setChecked(event.target.checked)}
                className="mt-0.5 h-5 w-5 shrink-0 accent-primary" />
              <span className="min-w-0 break-words leading-relaxed">{review.durable_commit_available === true
                ? "J'ai vérifié l'image et les deux identifiants du patient. L'image sera enregistrée dans ce dossier."
                : "J'ai vérifié l'image et les deux identifiants du patient. Cette image ne sera pas ajoutée au dossier."}</span>
            </label>
            <div className="flex flex-col-reverse gap-2 border-t border-border-main pt-4 sm:flex-row sm:flex-wrap sm:justify-end">
              <button type="button" disabled={busy} onClick={() => void cancel()}
                className="min-h-11 min-w-0 whitespace-normal break-words rounded-lg border border-border-main bg-card px-3 py-3 text-sm font-medium leading-snug text-text-main transition-colors hover:bg-background focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-40 sm:px-5">
                Annuler
              </button>
              <button type="button" disabled={!canConfirm} onClick={() => void confirm()}
                className="min-h-11 min-w-0 whitespace-normal break-words rounded-lg bg-primary px-3 py-3 text-sm font-semibold leading-snug text-on-primary transition-colors hover:bg-secondary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-40 sm:px-5">
                {busy ? 'Contrôle…' : review.durable_commit_available === true
                  ? 'Ajouter l’image au dossier' : 'Terminer la vérification'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
