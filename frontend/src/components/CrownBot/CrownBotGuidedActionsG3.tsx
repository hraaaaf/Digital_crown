import { useEffect, useRef, useState } from 'react';
import { CheckCircle2, Clock3, ShieldCheck, AlertTriangle, RotateCcw } from 'lucide-react';
import { api } from '../../services/api';

type Mode = 'appointment' | 'status';
type Patient = { id: number; nom: string; prenom: string; numero_dossier: string | null };
type AppointmentSummary = {
  patient: Patient; praticien_id: number; resource_id: number | null;
  datetime_start: string; duration_minutes: number; motif: string;
};
type StatusSummary = {
  patient: Patient; appointment_id: number; datetime_start: string;
  expected_status: string; expected_revision: number;
  new_status: string; new_status_label: string;
};
type Prepared = {
  status: 'prepared'; executable: false; preparation_id: string;
  expires_at: string; summary: AppointmentSummary | StatusSummary;
};
type Outcome = { appointment_id: number; status: string };
type Reconciliation = {
  preparation_id: string; action_type: 'CREATE_APPOINTMENT' | 'CHANGE_STATUS';
  status: string; result: Outcome | null;
  safe_to_retry_automatically: false; manual_reconciliation_required: boolean;
};
type Phase =
  | { kind: 'prepared'; mode: Mode; data: Prepared }
  | { kind: 'uncertain'; id: string; mode: Mode; note: string }
  | { kind: 'finished'; id: string; outcome: Outcome; mode: Mode }
  | { kind: 'blocked'; id: string; mode: Mode; status: string };

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const VALID_STATUSES = [
  { value: 'salle d attente', label: "En salle d'attente" },
  { value: 'fauteuil', label: 'En fauteuil' },
  { value: 'termine', label: 'Terminé' },
  { value: 'annule', label: 'Annulé' },
] as const;

const APPOINTMENT_RE = /^(?:\d{4}-\d{2}-\d{2})T\d{2}:\d{2}/;
const positiveInt = (v: unknown): v is number =>
  typeof v === 'number' && Number.isSafeInteger(v) && v > 0;
const validPatient = (p: unknown): p is Patient => {
  if (!p || typeof p !== 'object') return false;
  const a = p as Partial<Patient>;
  return positiveInt(a.id) && typeof a.nom === 'string' &&
    typeof a.prenom === 'string' &&
    (a.numero_dossier == null || typeof a.numero_dossier === 'string');
};
const isAppointment = (s: unknown): s is AppointmentSummary => {
  if (!s || typeof s !== 'object') return false;
  const a = s as Partial<AppointmentSummary>;
  return validPatient(a.patient) && positiveInt(a.praticien_id) &&
    (a.resource_id == null || positiveInt(a.resource_id)) &&
    typeof a.datetime_start === 'string' && APPOINTMENT_RE.test(a.datetime_start) &&
    positiveInt(a.duration_minutes) && typeof a.motif === 'string' && !!a.motif;
};
const isStatus = (s: unknown): s is StatusSummary => {
  if (!s || typeof s !== 'object') return false;
  const a = s as Partial<StatusSummary>;
  return validPatient(a.patient) && positiveInt(a.appointment_id) &&
    typeof a.datetime_start === 'string' && APPOINTMENT_RE.test(a.datetime_start) &&
    typeof a.expected_status === 'string' &&
    Number.isSafeInteger(a.expected_revision) && Number(a.expected_revision) >= 0 &&
    typeof a.new_status === 'string' && typeof a.new_status_label === 'string';
};
function verifiedPreparation(value: unknown, mode: Mode): Prepared | null {
  if (!value || typeof value !== 'object') return null;
  const a = value as Partial<Prepared>;
  if (a.status !== 'prepared' || a.executable !== false ||
      !UUID.test(String(a.preparation_id)) ||
      typeof a.expires_at !== 'string' || Number.isNaN(Date.parse(a.expires_at))) return null;
  if (mode === 'appointment' && !isAppointment(a.summary)) return null;
  if (mode === 'status' && !isStatus(a.summary)) return null;
  return a as Prepared;
}
function verifiedOutcome(value: unknown, mode: Mode): Outcome | null {
  if (!value || typeof value !== 'object') return null;
  const o = value as Partial<Outcome>;
  if (!positiveInt(o.appointment_id) || typeof o.status !== 'string') return null;
  if (mode === 'appointment' && o.status !== 'CREATED') return null;
  if (mode === 'status' && !['EN_SALLE_ATTENTE', 'EN_FAUTEUIL', 'TERMINE', 'ANNULE'].includes(o.status)) return null;
  return o as Outcome;
}
function errorCode(e: unknown): number | undefined {
  return (e as { response?: { status?: number } })?.response?.status;
}
function errorMessage(status?: number): string {
  if (status === 401 || status === 403 || status === 423) return 'Accès refusé ou session verrouillée. Aucun dossier affiché.';
  if (status === 404) return 'Action introuvable ou fonctionnalité désactivée.';
  if (status === 410) return 'Préparation expirée. Créez une nouvelle proposition.';
  if (status === 409) return 'Proposition obsolète ou déjà traitée. Vérifiez son état.';
  if (status === 422) return 'Demande invalide ou incomplète. Vérifiez les champs.';
  return 'Réponse du serveur indisponible ou incertaine. Aucune relance automatique.';
}
function parseId(value: string): number | null {
  if (!/^[1-9]\d{0,14}$/.test(value.trim())) return null;
  const parsed = Number(value);
  return positiveInt(parsed) ? parsed : null;
}
function wallClock(iso: string): string {
  // Cabinet-local wall clock from SQL. Never reinterpret as browser timezone.
  return iso.slice(0, 16).replace('T', ' à ');
}
function person(p: Patient): string {
  return [p.prenom, p.nom].join(' ') + (p.numero_dossier ? ' · Dossier ' + p.numero_dossier : '');
}

/**
 * CB-03 G3: one explicitly opted-in UI for separately flagged G1/G2 APIs.
 * Browser drafts NEVER contain trusted patient/status/revision; those values
 * appear only after the server returns a validated prepared summary.
 *
 * No localStorage/sessionStorage, no background POST retry, no optimistic
 * success, no resurrection of old actions through chat history.
 */
export function CrownBotGuidedActionsG3({ practitionerId }: { practitionerId?: number } = {}) {
  const [mode, setMode] = useState<Mode>('appointment');
  const [utterance, setUtterance] = useState('');
  const [chosenPatientId, setChosenPatientId] = useState<string>('');
  const [practitioner, setPractitioner] = useState(positiveInt(practitionerId) ? String(practitionerId) : '');
  const [resource, setResource] = useState('');
  const [duration, setDuration] = useState('30');
  const [appointmentId, setAppointmentId] = useState('');
  const [targetStatus, setTargetStatus] = useState<(typeof VALID_STATUSES)[number]['value']>('salle d attente');
  const [phase, setPhase] = useState<Phase | null>(null);
  const [candidates, setCandidates] = useState<Patient[]>([]);
  const [acknowledged, setAcknowledged] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const epoch = useRef(0);
  const busyRef = useRef(false);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => () => { epoch.current += 1; }, []);
  useEffect(() => {
    if (phase || error || candidates.length) {
      resultRef.current?.scrollIntoView?.({ block: 'nearest', behavior: 'auto' });
    }
  }, [phase, error, candidates.length]);

  const reset = (nextMode = mode) => {
    if (busyRef.current) return;
    epoch.current += 1;
    setMode(nextMode);
    setPhase(null);
    setCandidates([]);
    setAcknowledged(false);
    setError('');
    setInfo('');
    setUtterance('');
    setChosenPatientId('');
    setAppointmentId('');
  };
  const edit = (setter: (s: string) => void, value: string) => {
    if (busyRef.current) return;
    // A changed draft cannot retain a previous patient's verified summary.
    setPhase(null);
    setCandidates([]);
    setAcknowledged(false);
    setInfo('');
    setError('');
    setter(value);
  };
  const prepare = async (choiceId?: number) => {
    if (busyRef.current || phase) return;
    const payload: Record<string, unknown> = {};
    if (mode === 'appointment') {
      if (!utterance.trim() || utterance.trim().length > 160) {
        setError('Renseignez une demande de rendez-vous en français (160 caractères maximum).');
        return;
      }
      const chosenId = choiceId || (chosenPatientId ? parseId(chosenPatientId) : null);
      if (chosenPatientId && !chosenId) { setError('Identifiant patient invalide.'); return; }
      const practitionerIdValue = practitioner ? parseId(practitioner) : null;
      if (practitioner && !practitionerIdValue) { setError('Identifiant praticien invalide.'); return; }
      const resourceIdValue = resource ? parseId(resource) : null;
      if (resource && !resourceIdValue) { setError('Identifiant de ressource invalide.'); return; }
      const minutes = parseId(duration);
      if (!minutes || minutes < 5 || minutes > 480) { setError('Durée entre 5 et 480 minutes requise.'); return; }
      payload.utterance = utterance.trim();
      payload.duration_minutes = minutes;
      if (chosenId) payload.chosen_patient_id = chosenId;
      if (practitionerIdValue) payload.praticien_id = practitionerIdValue;
      if (resourceIdValue) payload.resource_id = resourceIdValue;
    } else {
      const id = parseId(appointmentId);
      if (!id) { setError('Sélectionnez un identifiant de rendez-vous valide.'); return; }
      payload.selected_appointment_id = id;
      payload.utterance = 'Prépare le statut du RDV en ' + targetStatus;
    }

    busyRef.current = true;
    const op = ++epoch.current;
    setBusy(true);
    setError('');
    setInfo('');
    setCandidates([]);
    try {
      const endpoint = mode === 'appointment' ? '/bot/guided/prepare-appointment' : '/bot/guided/prepare-status';
      const response = (await api.post(endpoint, payload)).data as unknown;
      if (op !== epoch.current) return;
      if (mode === 'appointment' && response && typeof response === 'object') {
        const r = response as { status?: string; candidates?: unknown; message?: unknown };
        if ((r.status === 'clarification' || r.status === 'disambiguation') &&
            typeof r.message === 'string') {
          const list = Array.isArray(r.candidates) ? r.candidates.filter(validPatient) : [];
          setCandidates(list);
          setInfo(r.message);
          return;
        }
      }
      const prepared = verifiedPreparation(response, mode);
      if (!prepared) throw new Error('Invalid CB-03 preparation');
      setAcknowledged(false);
      setPhase({ kind: 'prepared', mode, data: prepared });
    } catch (err) {
      if (op !== epoch.current) return;
      setPhase(null);
      setCandidates([]);
      setError(errorMessage(errorCode(err)));
    } finally {
      if (op === epoch.current) { busyRef.current = false; setBusy(false); }
    }
  };

  const confirm = async () => {
    if (busyRef.current || !acknowledged || phase?.kind !== 'prepared') return;
    const { preparation_id: id } = phase.data;
    const confirmedMode = phase.mode;
    busyRef.current = true;
    const op = ++epoch.current;
    setBusy(true);
    setError('');
    setInfo('');
    // Lock the UI immediately; never resend blindly on a lost ACK.
    setPhase({ kind: 'uncertain', id, mode: confirmedMode, note: 'Confirmation envoyée. Résultat à vérifier.' });
    setAcknowledged(false);
    try {
      const data = (await api.post('/bot/guided/confirm', {
        preparation_id: id, confirm: true,
      })).data as { status?: unknown; preparation_id?: unknown; result?: unknown };
      if (op !== epoch.current) return;
      const outcome = verifiedOutcome(data?.result, confirmedMode);
      if (data?.status !== 'executed' || data.preparation_id !== id || !outcome) {
        throw new Error('Unverifiable confirmation response');
      }
      setPhase({ kind: 'finished', mode: confirmedMode, id, outcome });
      setInfo('Exécution confirmée par le serveur.');
    } catch (err) {
      if (op !== epoch.current) return;
      const status = errorCode(err);
      if (status === 401 || status === 403 || status === 404 || status === 423) {
        // Never retain clinical summary/action IDs after access is revoked.
        setPhase(null);
        setError(errorMessage(status));
      } else {
        setPhase({ kind: 'uncertain', id, mode: confirmedMode,
          note: 'Résultat non prouvé. Consultez l’état avant toute nouvelle demande.' });
        setError(errorMessage(status));
      }
    } finally {
      if (op === epoch.current) { busyRef.current = false; setBusy(false); }
    }
  };

  const checkState = async () => {
    if (busyRef.current || !phase || phase.kind === 'prepared') return;
    const { id, mode: readMode } = phase;
    busyRef.current = true;
    const op = ++epoch.current;
    setBusy(true);
    setError('');
    try {
      const data = (await api.get<Reconciliation>(
        '/bot/guided/actions/' + encodeURIComponent(id),
      )).data;
      if (op !== epoch.current) return;
      if (!data || data.preparation_id !== id ||
          data.safe_to_retry_automatically !== false ||
          data.action_type !== (readMode === 'appointment' ? 'CREATE_APPOINTMENT' : 'CHANGE_STATUS')) {
        throw new Error('Invalid reconciliation');
      }
      if (data.status === 'executed' && !data.manual_reconciliation_required) {
        const outcome = verifiedOutcome(data.result, readMode);
        if (!outcome) throw new Error('Missing receipt');
        setPhase({ kind: 'finished', id, mode: readMode, outcome });
        setInfo('Exécution vérifiée dans le journal serveur.');
      } else if (['expired', 'cancelled', 'failed'].includes(data.status)
                 && data.result == null && !data.manual_reconciliation_required) {
        setPhase({ kind: 'blocked', id, mode: readMode, status: data.status });
        setInfo('Cette action n’est plus exécutable.');
      } else {
        // "prepared" after an uncertain POST never re-enables Confirm.
        setPhase({ kind: 'uncertain', id, mode: readMode,
          note: data.manual_reconciliation_required
            ? 'Vérification manuelle requise avant toute nouvelle action.'
            : 'Aucune exécution prouvée. Ne relancez pas automatiquement.' });
        setInfo('État serveur : ' + data.status + '.');
      }
    } catch (err) {
      if (op !== epoch.current) return;
      const status = errorCode(err);
      if (status === 401 || status === 403 || status === 404 || status === 423) {
        setPhase(null);
      }
      setError(errorMessage(status));
    } finally {
      if (op === epoch.current) { busyRef.current = false; setBusy(false); }
    }
  };

  return (
    <section aria-label="CB-03 G3 — actions guidées"
      className="min-w-0 space-y-3 rounded-2xl border border-indigo-200 bg-white p-3 text-slate-900 shadow-sm">
      <div className="flex min-w-0 items-start gap-2">
        <ShieldCheck size={20} className="mt-0.5 shrink-0 text-indigo-700" aria-hidden="true" />
        <div className="min-w-0">
          <h3 className="text-sm font-bold">Actions guidées · confirmation sécurisée</h3>
          <p className="mt-1 text-xs leading-relaxed text-slate-600">
            Expérimental, autorisé uniquement si le serveur l’active. Une préparation ne réserve
            aucun créneau et ne modifie aucun statut. Vérifiez le récapitulatif avant toute confirmation.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2" aria-label="Choisir une action CB-03">
        <button type="button" disabled={busy} aria-pressed={mode === 'appointment'}
          onClick={() => reset('appointment')}
          className={'min-h-11 rounded-lg border px-3 py-2 text-left text-xs font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 ' +
            (mode === 'appointment' ? 'border-indigo-600 bg-indigo-50 text-indigo-900' : 'border-slate-300 bg-white text-slate-700')}>
          Préparer un nouveau RDV
        </button>
        <button type="button" disabled={busy} aria-pressed={mode === 'status'}
          onClick={() => reset('status')}
          className={'min-h-11 rounded-lg border px-3 py-2 text-left text-xs font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 ' +
            (mode === 'status' ? 'border-indigo-600 bg-indigo-50 text-indigo-900' : 'border-slate-300 bg-white text-slate-700')}>
          Changer le statut d’un RDV
        </button>
      </div>

      {!phase && (
        <form aria-label="Préparer une action CB-03" className="space-y-3" onSubmit={e => {
          e.preventDefault();
          void prepare();
        }}>
          {mode === 'appointment' ? (
            <>
              <label htmlFor="cb03-utterance" className="block text-xs font-semibold">Votre demande en français</label>
              <textarea id="cb03-utterance" rows={2} maxLength={160} required disabled={busy}
                value={utterance} onChange={e => edit(setUtterance, e.target.value)}
                placeholder="Prépare un RDV demain 10h pour Mme Benali contrôle"
                className="w-full min-w-0 rounded-lg border border-slate-300 p-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600" />
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <label className="block text-xs font-medium">Patient ID (si dossier choisi)
                  <input inputMode="numeric" type="text" disabled={busy} value={chosenPatientId}
                    onChange={e => edit(setChosenPatientId, e.target.value)}
                    className="mt-1 min-h-11 w-full min-w-0 rounded-lg border border-slate-300 p-2 text-sm" />
                </label>
                <label className="block text-xs font-medium">Praticien ID
                  <input inputMode="numeric" type="text" disabled={busy} value={practitioner}
                    onChange={e => edit(setPractitioner, e.target.value)}
                    className="mt-1 min-h-11 w-full min-w-0 rounded-lg border border-slate-300 p-2 text-sm" />
                </label>
                <label className="block text-xs font-medium">Durée en minutes
                  <input inputMode="numeric" type="text" disabled={busy} value={duration}
                    onChange={e => edit(setDuration, e.target.value)}
                    className="mt-1 min-h-11 w-full min-w-0 rounded-lg border border-slate-300 p-2 text-sm" />
                </label>
                <label className="block text-xs font-medium">Ressource ID (facultatif)
                  <input inputMode="numeric" type="text" disabled={busy} value={resource}
                    onChange={e => edit(setResource, e.target.value)}
                    className="mt-1 min-h-11 w-full min-w-0 rounded-lg border border-slate-300 p-2 text-sm" />
                </label>
              </div>
            </>
          ) : (
            <>
              <label className="block text-xs font-semibold">Identifiant du RDV sélectionné dans l’agenda
                <input type="text" inputMode="numeric" required disabled={busy} value={appointmentId}
                  onChange={e => edit(setAppointmentId, e.target.value)}
                  placeholder="ID du rendez-vous"
                  className="mt-1 min-h-11 w-full min-w-0 rounded-lg border border-slate-300 p-2 text-sm" />
              </label>
              <label className="block text-xs font-semibold">Nouveau statut demandé
                <select disabled={busy} value={targetStatus}
                  onChange={e => { if (!busyRef.current) { setTargetStatus(e.target.value as typeof targetStatus); setError(''); } }}
                  className="mt-1 min-h-11 w-full rounded-lg border border-slate-300 bg-white p-2 text-sm">
                  {VALID_STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </label>
              <p className="text-xs text-slate-600">Le serveur vérifie le patient, le statut initial, la révision et la transition autorisée.</p>
            </>
          )}
          <button type="submit" disabled={busy}
            className="min-h-11 w-full rounded-lg bg-indigo-700 px-3 py-2 text-sm font-bold text-white hover:bg-indigo-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-700 disabled:opacity-50">
            {busy ? 'Préparation…' : 'Vérifier et préparer · aucune écriture clinique'}
          </button>
        </form>
      )}
      <div ref={resultRef} className="space-y-2" aria-live="polite" aria-atomic="true">
        {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-xs font-medium text-rose-900">{error}</p>}
        {info && <p role="status" className="rounded-lg border border-slate-200 bg-slate-50 p-2 text-xs text-slate-800">{info}</p>}
        {candidates.length > 0 && !phase && (
          <fieldset className="space-y-2 rounded-lg border border-amber-200 bg-amber-50 p-2">
            <legend className="text-xs font-semibold text-amber-900">Sélectionnez explicitement le dossier</legend>
            {candidates.map(p => <button key={p.id} type="button" disabled={busy}
              onClick={() => { setChosenPatientId(String(p.id)); void prepare(p.id); }}
              className="block min-h-11 w-full rounded-lg border border-amber-300 bg-white p-2 text-left text-xs text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-700">
              {person(p)}
            </button>)}
          </fieldset>
        )}
        {phase?.kind === 'prepared' && (
          <div className="space-y-3 rounded-xl border border-amber-300 bg-amber-50 p-3" aria-label="Récapitulatif de préparation vérifiée">
            <div className="flex items-center gap-2">
              <Clock3 size={16} aria-hidden="true" className="text-amber-800" />
              <h4 className="text-sm font-bold text-amber-950">Préparation prête · non exécutée</h4>
            </div>
            <dl className="grid min-w-0 grid-cols-1 gap-1 text-xs text-slate-800">
              <div><dt className="inline font-bold">Patient : </dt><dd className="inline">{person(phase.data.summary.patient)}</dd></div>
              {phase.mode === 'appointment' && isAppointment(phase.data.summary) ? <>
                <div><dt className="inline font-bold">Début : </dt><dd className="inline">{wallClock(phase.data.summary.datetime_start)}</dd></div>
                <div><dt className="inline font-bold">Durée : </dt><dd className="inline">{phase.data.summary.duration_minutes} minutes</dd></div>
                <div><dt className="inline font-bold">Motif : </dt><dd className="inline">{phase.data.summary.motif}</dd></div>
                <div><dt className="inline font-bold">Praticien ID : </dt><dd className="inline">{phase.data.summary.praticien_id}</dd></div>
              </> : phase.mode === 'status' && isStatus(phase.data.summary) ? <>
                <div><dt className="inline font-bold">Rendez-vous : </dt><dd className="inline">#{phase.data.summary.appointment_id}</dd></div>
                <div><dt className="inline font-bold">Début : </dt><dd className="inline">{wallClock(phase.data.summary.datetime_start)}</dd></div>
                <div><dt className="inline font-bold">Statut initial : </dt><dd className="inline">{phase.data.summary.expected_status}</dd></div>
                <div><dt className="inline font-bold">Statut proposé : </dt><dd className="inline">{phase.data.summary.new_status_label}</dd></div>
                <div><dt className="inline font-bold">Révision initiale : </dt><dd className="inline">{phase.data.summary.expected_revision}</dd></div>
              </> : null}
              <div><dt className="inline font-bold">Expiration : </dt>
                <dd className="inline">{phase.data.expires_at.replace('T', ' ').slice(0, 19)} UTC</dd>
              </div>
            </dl>
            <label className="flex min-h-11 items-start gap-2 rounded-lg bg-white p-2 text-xs font-semibold text-slate-800">
              <input type="checkbox" disabled={busy} checked={acknowledged}
                onChange={e => setAcknowledged(e.target.checked)}
                className="mt-0.5 h-4 w-4 shrink-0 accent-indigo-700" />
              J’ai vérifié le patient, le rendez-vous et l’opération ; je demande son exécution.
            </label>
            <button type="button" disabled={busy || !acknowledged} onClick={() => void confirm()}
              className="min-h-11 w-full rounded-lg bg-emerald-700 px-3 py-2 text-sm font-bold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-700 disabled:opacity-50">
              {busy ? 'Confirmation en cours…' : 'Confirmer explicitement cette action'}
            </button>
          </div>
        )}
        {phase?.kind === 'uncertain' && (
          <div className="space-y-2 rounded-xl border border-amber-300 bg-amber-50 p-3">
            <p className="flex items-center gap-2 text-sm font-bold text-amber-950"><AlertTriangle size={16} aria-hidden="true" /> Résultat à réconcilier</p>
            <p className="text-xs text-amber-950">{phase.note}</p>
            <p className="text-xs">Aucune deuxième confirmation automatique n’est possible.</p>
          </div>
        )}
        {phase?.kind === 'finished' && (
          <div role="status" className="flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
            <CheckCircle2 size={18} className="shrink-0" aria-hidden="true" />
            <span>Action exécutée et vérifiée · RDV #{phase.outcome.appointment_id} · {phase.outcome.status}</span>
          </div>
        )}
        {phase?.kind === 'blocked' && (
          <p className="rounded-xl border border-slate-300 bg-slate-50 p-3 text-xs font-semibold">
            Action non exécutable · état : {phase.status}
          </p>
        )}
        {phase && phase.kind !== 'prepared' && (
          <button type="button" disabled={busy} onClick={() => void checkState()}
            className="min-h-11 w-full rounded-lg border border-indigo-300 bg-white px-3 py-2 text-xs font-semibold text-indigo-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-700 disabled:opacity-50">
            {busy ? 'Vérification serveur…' : 'Vérifier l’état par identifiant (lecture seule)'}
          </button>
        )}
        {phase && <button type="button" disabled={busy} onClick={() => reset()}
          className="flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-slate-300 bg-slate-50 px-3 text-xs font-semibold text-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-700 disabled:opacity-50">
          <RotateCcw size={14} aria-hidden="true" /> Nouvelle préparation
        </button>}
      </div>
      <p className="text-xs text-slate-600">
        Aucun historique patient ni identifiant d’action conservé sur ce poste après fermeture.
        Si le réseau interrompt une confirmation, consultez son état avant de réessayer une nouvelle demande.
      </p>
    </section>
  );
}
