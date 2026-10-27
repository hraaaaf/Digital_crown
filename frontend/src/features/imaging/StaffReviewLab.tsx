import { useEffect, useRef, useState } from 'react';

export type LabStaffTarget = {
  patientId: number;
  label: string;
  appointments: { id: number; label: string }[];
};
export type LabCapturePreview = {
  device: string;
  capture: string;
  modality: string;
  claimedSha256: string;
  receivedAtLabel: string;
};
export type LabReviewInput = {
  workstation_id: string;
  device: string;
  capture: string;
  patient_id: number;
  appointment_id: number | null;
};
export type LabApproveInput = LabReviewInput & {
  explicit_staff_action: true;
  review_challenge: string;
};
export type LabReviewClient = {
  review: (input: LabReviewInput) => Promise<{
    status: string;
    review_challenge: string;
    expires_at: number;
    patient_id: number;
    appointment_id: number | null;
    server_confirmed: false;
  }>;
  approve: (input: LabApproveInput) => Promise<{
    status: string;
    server_confirmed: false;
  }>;
};

type Pending = {
  input: LabReviewInput;
  challenge: string;
  expiresAt: number;
};

function sameInput(a: LabReviewInput, b: LabReviewInput): boolean {
  return a.workstation_id === b.workstation_id &&
    a.device === b.device && a.capture === b.capture &&
    a.patient_id === b.patient_id && a.appointment_id === b.appointment_id;
}

export function StaffReviewLab({
  capture, targets, workstationId, client,
}: {
  capture: LabCapturePreview;
  targets: LabStaffTarget[];
  workstationId: string;
  client: LabReviewClient;
}) {
  const [patientId, setPatientId] = useState('');
  const [appointmentId, setAppointmentId] = useState('');
  const [reason, setReason] = useState('');
  const [pending, setPending] = useState<Pending | null>(null);
  const [phase, setPhase] = useState<'select' | 'review' | 'approved'>('select');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const generation = useRef(0);
  const submitting = useRef(false);
  const captureKey = capture.device + ':' + capture.capture;

  const patient = targets.find(p => String(p.patientId) === patientId);
  const appointment = patient?.appointments.find(a => String(a.id) === appointmentId);
  const input: LabReviewInput | null = patient ? {
    workstation_id: workstationId,
    device: capture.device,
    capture: capture.capture,
    patient_id: patient.patientId,
    appointment_id: appointment?.id ?? null,
  } : null;

  function resetReview() {
    generation.current += 1;
    setPending(null);
    setPhase('select');
    setError('');
  }

  // New capture/workstation must not inherit any previous patient or token.
  useEffect(() => {
    generation.current += 1;
    setPatientId('');
    setAppointmentId('');
    setReason('');
    setPending(null);
    setPhase('select');
    setBusy(false);
    setError('');
    submitting.current = false;
  }, [captureKey, workstationId]);

  async function requestReview() {
    if (!input || phase !== 'select' || submitting.current) return;
    if (!appointment && !reason.trim()) {
      setError('Indiquez une justification pour une capture sans rendez-vous.');
      return;
    }
    submitting.current = true;
    setBusy(true);
    setError('');
    const request = { ...input };
    const stamp = ++generation.current;
    try {
      const response = await client.review(request);
      if (generation.current !== stamp) return;
      if (response.status !== 'STAFF_REVIEW_REQUIRED' ||
          response.server_confirmed !== false ||
          !response.review_challenge ||
          response.patient_id !== request.patient_id ||
          response.appointment_id !== request.appointment_id ||
          response.expires_at * 1000 <= Date.now()) {
        throw new Error('La demande de revue ne correspond pas au patient choisi.');
      }
      setPending({
        input: request,
        challenge: response.review_challenge,
        expiresAt: response.expires_at,
      });
      setPhase('review');
    } catch {
      if (generation.current === stamp) {
        setPending(null);
        setError('Revue refusée ou indisponible. Vérifiez la session et le patient.');
      }
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }

  async function confirm() {
    if (!pending || !input || phase !== 'review' || submitting.current) return;
    if (!sameInput(input, pending.input)) {
      resetReview();
      return;
    }
    if (pending.expiresAt * 1000 <= Date.now()) {
      resetReview();
      setError('Confirmation expirée. Relancez la revue.');
      return;
    }
    submitting.current = true;
    setBusy(true);
    setError('');
    const stamp = generation.current;
    try {
      const result = await client.approve({
        ...pending.input,
        review_challenge: pending.challenge,
        explicit_staff_action: true,
      });
      if (generation.current !== stamp) return;
      if (result.status !== 'APPROVED' || result.server_confirmed !== false) {
        throw new Error('Réponse serveur non autorisée.');
      }
      setPending(null);
      setPhase('approved');
    } catch {
      if (generation.current === stamp) {
        resetReview();
        setError('Confirmation refusée ou expirée. Recommencez la revue.');
      }
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }

  const choiceClass = 'mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:opacity-50';
  return (
    <main data-testid="lot06b-desktop-review" className="min-h-screen bg-slate-100 px-6 py-10 text-slate-900">
      <div className="mx-auto max-w-5xl">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-blue-700">Digital Crown · Imaging Acquisition</p>
            <h1 className="mt-2 text-2xl font-bold">Associer une capture au bon patient</h1>
          </div>
          <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-bold text-amber-900">
            LAB FICTIF · AUCUN REÇU CLINIQUE
          </span>
        </div>
        <p className="mt-3 text-sm text-slate-600">Revoyez l'identité avant toute confirmation. Aucun patient n'est présélectionné.</p>
        <div className="mt-7 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm" aria-label="Capture en attente">
            <h2 className="font-bold">Capture en attente</h2>
            <div className="mt-4 flex aspect-[4/3] items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50">
              <div className="text-center">
                <p className="text-4xl" aria-hidden="true">▧</p>
                <p className="mt-3 text-sm font-semibold">Aperçu non disponible dans ce LAB</p>
                <p className="mt-1 text-xs text-slate-500">Ne présumez pas du contenu de l'image.</p>
              </div>
            </div>
            <dl className="mt-5 grid grid-cols-[auto_1fr] gap-x-4 gap-y-3 text-sm">
              <dt className="font-semibold text-slate-500">Modalité</dt><dd>{capture.modality}</dd>
              <dt className="font-semibold text-slate-500">Connecteur</dt><dd>{capture.device}</dd>
              <dt className="font-semibold text-slate-500">Capture</dt><dd className="break-all font-mono text-xs">{capture.capture}</dd>
              <dt className="font-semibold text-slate-500">Reçue</dt><dd>{capture.receivedAtLabel}</dd>
            </dl>
            <p className="mt-5 rounded-lg bg-amber-50 p-3 text-xs text-amber-900">
              Empreinte déclarée par le connecteur, <strong>non vérifiée</strong> avant réception des octets.
            </p>
            <p className="mt-2 break-all font-mono text-[11px] text-slate-500">{capture.claimedSha256}</p>
          </section>
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm" aria-label="Revue du patient">
            <h2 className="font-bold">Confirmation opérateur</h2>
            <div className="mt-5 space-y-5">
              <label className="block text-sm font-semibold" htmlFor="lab-patient">
                Patient · choix obligatoire
                <select id="lab-patient" value={patientId} className={choiceClass}
                  disabled={busy || phase !== 'select'} onChange={e => {
                    resetReview(); setPatientId(e.target.value); setAppointmentId(''); setReason('');
                  }}>
                  <option value="">Sélectionner explicitement un patient</option>
                  {targets.map(t => <option key={t.patientId} value={t.patientId}>{t.label}</option>)}
                </select>
              </label>
              <label className="block text-sm font-semibold" htmlFor="lab-appointment">
                Rendez-vous · facultatif
                <select id="lab-appointment" value={appointmentId} className={choiceClass}
                  disabled={!patient || busy || phase !== 'select'}
                  onChange={e => { resetReview(); setAppointmentId(e.target.value); }}>
                  <option value="">Sans rendez-vous</option>
                  {patient?.appointments.map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
                </select>
              </label>
              {patient && !appointment && (
                <label className="block text-sm font-semibold" htmlFor="lab-reason">
                  Justification · obligatoire sans RDV
                  <input id="lab-reason" value={reason} maxLength={120} className={choiceClass}
                    placeholder="Ex. Consultation non programmée"
                    disabled={busy || phase !== 'select'} onChange={e => { resetReview(); setReason(e.target.value); }}/>
                  <span className="mt-2 block text-xs font-normal text-amber-800">
                    Justification affichée pour le test UI ; son audit serveur reste à implémenter.
                  </span>
                </label>
              )}
              {phase === 'review' && pending && (
                <div role="status" className="rounded-xl border border-blue-300 bg-blue-50 p-4 text-sm">
                  <p className="font-bold">Vérifier avant confirmation</p>
                  <p className="mt-2">Patient : <strong>{patient?.label}</strong></p>
                  <p>Rendez-vous : <strong>{appointment?.label ?? 'Aucun — patient uniquement'}</strong></p>
                  <p className="mt-2 text-xs text-blue-900">Revue serveur valable 5 min maximum. La confirmation ne crée pas de reçu clinique.</p>
                </div>
              )}
              {phase === 'approved' && (
                <div role="status" className="rounded-xl border border-emerald-300 bg-emerald-50 p-4 text-sm font-semibold text-emerald-900">
                  Association approuvée dans le LAB. Transfert et reçu clinique non confirmés.
                </div>
              )}
              {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm font-semibold text-red-700">{error}</p>}
              {phase === 'select' && (
                <button type="button" disabled={!patient || busy || (!appointment && !reason.trim())}
                  onClick={() => void requestReview()}
                  className="min-h-12 w-full rounded-xl bg-blue-700 px-4 py-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-slate-300">
                  {busy ? 'Vérification…' : 'Vérifier le lien patient'}
                </button>
              )}
              {phase === 'review' && (
                <div className="flex gap-3">
                  <button type="button" disabled={busy} onClick={resetReview}
                    className="min-h-12 flex-1 rounded-xl border border-slate-300 px-3 font-semibold">Annuler</button>
                  <button type="button" disabled={busy} onClick={() => void confirm()}
                    className="min-h-12 flex-[2] rounded-xl bg-blue-700 px-3 font-bold text-white disabled:bg-slate-300">
                    {busy ? 'Confirmation…' : 'Confirmer ce patient'}
                  </button>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
