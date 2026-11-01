import { useEffect, useState } from 'react';

/**
 * LAB-only review surface. Deliberately NOT mounted in App.tsx or patient routes.
 * Server owns identity, patient/digest binding, approval and audit.
 * This component only collects a human's explicit confirmation; it never
 * commits media, guesses the patient, or consumes a capture receipt.
 */
export interface LabAcquisitionReview {
  status: 'STAFF_REVIEW_REQUIRED';
  lab_only: true;
  clinical_receipt_authorized: false;
  challenge: string;
  capture: string;
  capture_digest: string;
  capture_size: number;
  patient_id: number;
  nom: string;
  prenom: string;
  numero_dossier: string;
  date_naissance: string;
  expires_at: number;
  preview_url: string;
}

export interface LabAcquisitionConfirmation {
  challenge: string;
  selected_patient_id: number;
  dossier: string;
  date_naissance: string;
  capture_digest: string;
  explicit_confirmation: true;
}

interface Props {
  review: LabAcquisitionReview;
  previewUrl: string;
  onConfirm: (confirmation: LabAcquisitionConfirmation) => Promise<void>;
  onCancel: () => void;
}

export function ImagingAcquisitionReviewPanelV15({ review, previewUrl, onConfirm, onCancel }: Props) {
  const [dossier, setDossier] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [checked, setChecked] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [approved, setApproved] = useState(false);
  const [now] = useState(() => Math.floor(Date.now() / 1000));

  useEffect(() => {
    // A new capture or patient invalidates every former local UI confirmation.
    setDossier('');
    setBirthDate('');
    setChecked(false);
    setError('');
    setApproved(false);
  }, [review.capture, review.capture_digest, review.patient_id, review.challenge]);

  const sane =
    review.status === 'STAFF_REVIEW_REQUIRED' &&
    review.lab_only === true && review.clinical_receipt_authorized === false &&
    /^([a-f0-9]{64})$/.test(review.capture_digest) &&
    Boolean(review.numero_dossier && review.date_naissance && review.capture && review.challenge);

  const matches =
    dossier.trim() === review.numero_dossier &&
    birthDate === review.date_naissance;
  const canConfirm = sane && !pending && !approved && checked && matches &&
    review.expires_at > now;

  const confirm = async () => {
    if (!canConfirm) return;
    setPending(true);
    setError('');
    try {
      await onConfirm({
        challenge: review.challenge,
        selected_patient_id: review.patient_id,
        dossier: review.numero_dossier,
        date_naissance: review.date_naissance,
        capture_digest: review.capture_digest,
        explicit_confirmation: true,
      });
      setApproved(true);
    } catch {
      // Never show PHI or an attacker-controlled exception in a visible error.
      setError('La confirmation a été refusée. Vérifiez la session et recommencez.');
    } finally {
      setPending(false);
    }
  };

  if (!sane) return <p role="alert">Capture indisponible. Aucun transfert autorisé.</p>;
  if (approved) return <p role="status">Revue enregistrée en laboratoire. Publication clinique non autorisée.</p>;

  return (
    <section aria-labelledby="dc06-review-title" className="w-full max-w-5xl rounded-xl border border-border bg-card p-4 sm:p-6">
      <div className="mb-4">
        <p className="mb-1 text-sm font-semibold text-amber-700">LAB uniquement — aucune publication clinique automatique</p>
        <h2 id="dc06-review-title" className="text-lg font-semibold">Confirmer le patient et la capture</h2>
        <p className="text-sm text-text-muted">Vérifiez l'image et saisissez deux identifiants avant de confirmer.</p>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="overflow-hidden rounded-lg border border-border bg-background">
          <img src={previewUrl} alt="Aperçu de la capture à associer au patient" className="h-auto max-h-[540px] w-full object-contain" />
          <p className="break-all px-3 py-2 text-xs text-text-muted">
            Empreinte SHA-256 : {review.capture_digest}
          </p>
        </div>
        <div className="space-y-4">
          <dl className="grid grid-cols-1 gap-2 rounded-lg border border-border p-3 text-sm">
            <div><dt className="text-text-muted">Patient sélectionné</dt><dd className="font-semibold">{review.prenom} {review.nom}</dd></div>
            <div><dt className="text-text-muted">Numéro de dossier</dt><dd>{review.numero_dossier}</dd></div>
            <div><dt className="text-text-muted">Date de naissance</dt><dd>{review.date_naissance}</dd></div>
          </dl>

          <div>
            <label htmlFor="dc06-confirm-dossier" className="mb-1 block font-medium">Ressaisir le numéro de dossier</label>
            <input id="dc06-confirm-dossier" type="text" autoComplete="off"
              value={dossier} onChange={event => setDossier(event.target.value)}
              className="w-full rounded-md border border-border bg-background p-3" />
          </div>
          <div>
            <label htmlFor="dc06-confirm-birthdate" className="mb-1 block font-medium">Ressaisir la date de naissance</label>
            <input id="dc06-confirm-birthdate" type="date" value={birthDate}
              onChange={event => setBirthDate(event.target.value)}
              className="w-full rounded-md border border-border bg-background p-3" />
          </div>

          <label className="flex items-start gap-3 text-sm">
            <input type="checkbox" className="mt-1 h-5 w-5 shrink-0" checked={checked}
              onChange={event => setChecked(event.target.checked)} />
            <span>J'ai contrôlé l'image et vérifié personnellement l'identité du patient. Je demande uniquement une approbation LAB.</span>
          </label>
          {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
          <div className="flex flex-wrap gap-3">
            <button type="button" disabled={!canConfirm} onClick={() => void confirm()}
              className="min-h-11 rounded-lg bg-blue-700 px-4 py-2 font-medium text-white disabled:cursor-not-allowed disabled:opacity-40">
              {pending ? 'Vérification en cours…' : 'Confirmer la revue'}
            </button>
            <button type="button" disabled={pending} onClick={onCancel}
              className="min-h-11 rounded-lg border border-border px-4 py-2">
              Annuler
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
