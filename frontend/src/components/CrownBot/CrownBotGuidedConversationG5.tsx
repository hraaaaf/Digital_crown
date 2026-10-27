/**
 * CB-03 G5 — actual CrownBotChat conversation panel (NOT a detached form).
 *
 * Staff text -> deterministic G1 preparation -> backend-verified clinical
 * summary -> explicit checkbox AND click -> G2 confirmation -> durable G2 GET.
 * Deliberately NO LLM-created write command, no /bot/execute, no auto retry,
 * no local/session storage, and no clinical data in chat-history endpoints.
 *
 * Parent CrownBotChat + G5 + G3 + CB02 flags must ALL opt in. Backend G1/G2
 * separately refuses every action unless its own independent flags are on.
 */
import { useEffect, useRef, useState } from 'react';
import { api } from '../../services/api';

type Mode = 'appointment' | 'status';
type Patient = { id: number; prenom: string; nom: string; numero_dossier: string | null };
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
type Result = { appointment_id: number; status: string };
type Turn = { id: number; author: 'user' | 'bot'; text: string };
type Phase =
  | { kind: 'choose'; phrase: string; candidates: Patient[] }
  | { kind: 'prepared'; mode: Mode; receipt: Prepared }
  | { kind: 'uncertain'; mode: Mode; id: string }
  | { kind: 'finished'; mode: Mode; id: string; result: Result }
  | { kind: 'blocked'; mode: Mode; id: string; status: string };

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const POSITIVE = (v: unknown): v is number =>
  typeof v === 'number' && Number.isSafeInteger(v) && v > 0;
const person = (p: Patient) =>
  p.prenom + ' ' + p.nom + (p.numero_dossier ? ' · Dossier ' + p.numero_dossier : '');
const validPatient = (v: unknown): v is Patient => {
  if (!v || typeof v !== 'object') return false;
  const p = v as Partial<Patient>;
  return POSITIVE(p.id) && typeof p.nom === 'string' && typeof p.prenom === 'string'
    && (p.numero_dossier === null || typeof p.numero_dossier === 'string');
};
const validSummary = (value: unknown, mode: Mode): boolean => {
  if (!value || typeof value !== 'object') return false;
  const a = value as Partial<AppointmentSummary & StatusSummary>;
  if (!validPatient(a.patient) || typeof a.datetime_start !== 'string'
      || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(a.datetime_start)) return false;
  if (mode === 'appointment') {
    return POSITIVE(a.praticien_id) && (a.resource_id == null || POSITIVE(a.resource_id))
      && POSITIVE(a.duration_minutes) && typeof a.motif === 'string' && !!a.motif;
  }
  return POSITIVE(a.appointment_id) && typeof a.expected_status === 'string'
    && typeof a.new_status === 'string' && typeof a.new_status_label === 'string'
    && typeof a.expected_revision === 'number' && Number.isSafeInteger(a.expected_revision)
    && a.expected_revision >= 0;
};
function validatedPreparation(raw: unknown, mode: Mode): Prepared | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Partial<Prepared>;
  return r.status === 'prepared' && r.executable === false
    && UUID.test(String(r.preparation_id))
    && typeof r.expires_at === 'string' && !Number.isNaN(Date.parse(r.expires_at))
    && validSummary(r.summary, mode) ? r as Prepared : null;
}
function validResult(value: unknown, mode: Mode): value is Result {
  if (!value || typeof value !== 'object') return false;
  const r = value as Partial<Result>;
  return POSITIVE(r.appointment_id) && typeof r.status === 'string'
    && (mode === 'appointment' ? r.status === 'CREATED'
      : ['EN_SALLE_ATTENTE', 'EN_FAUTEUIL', 'TERMINE', 'ANNULE'].includes(r.status));
}
const codeOf = (e: unknown) =>
  (e as { response?: { status?: number } })?.response?.status;
function responseError(code?: number): string {
  if ([401, 403, 423].includes(code ?? 0)) return 'Accès refusé ou session verrouillée. Aucune donnée clinique conservée.';
  if (code === 404) return 'Dossier introuvable ou fonction désactivée. Aucun changement effectué.';
  if (code === 409) return 'Proposition obsolète ou conflit. Vérifiez son état ; ne confirmez pas une seconde fois.';
  if (code === 410) return 'Préparation expirée : aucune confirmation possible.';
  if (code === 422) return 'Demande incomplète ou invalide. Précisez la date, l’heure, le patient et le motif.';
  return 'Réponse serveur incertaine. Aucune relance automatique.';
}
const DENIED = new Set([401, 403, 423]);
const normalize = (s: string) => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
type Command =
  | { type: 'appointment'; phrase: string }
  | { type: 'status'; appointmentId: number; target: string }
  | { type: 'unsupported' };
export function parseCB03ChatCommand(raw: string): Command {
  const phrase = raw.trim();
  const normalized = normalize(phrase).replace(/[’]/g, "'");
  // Deliberately strict. Unrecognized language cannot mutate clinical data.
  if (/\bstatut\b/.test(normalized)) {
    const match = normalized.match(/(?:^|\s)statut\s+(?:du\s+)?(?:rdv|rendez[\s-]?vous)\s*#?\s*(\d{1,15})\s+(?:en|a|vers)\s+(salle d'attente|fauteuil|termine|annule)\s*$/);
    if (!match) return { type: 'unsupported' };
    const appointmentId = Number(match[1]);
    if (!POSITIVE(appointmentId)) return { type: 'unsupported' };
    return { type: 'status', appointmentId, target: match[2] };
  }
  if (/\b(?:rdv|rendez[\s-]?vous)\b/.test(normalized)
    && /\b(?:prepare|preparer|cree|creer|planifie|planifier|reserve|reserver)\b/.test(normalized)) {
    return { type: 'appointment', phrase };
  }
  return { type: 'unsupported' };
}

export function CrownBotGuidedConversationG5({ practitionerId }: { practitionerId?: number } = {}) {
  const [turns, setTurns] = useState<Turn[]>([{
    id: 0, author: 'bot',
    text: 'Je peux préparer un rendez-vous ou un changement de statut, ici dans Crown Bot. Je vérifie les données auprès du serveur avant toute confirmation.',
  }]);
  const [draft, setDraft] = useState('');
  const [phase, setPhase] = useState<Phase | null>(null);
  const [checked, setChecked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const locked = useRef(false);
  const sequence = useRef(0);
  const epoch = useRef(0);
  const bottom = useRef<HTMLDivElement>(null);
  const add = (author: Turn['author'], text: string) =>
    setTurns(previous => [...previous, { id: ++sequence.current, author, text }]);
  useEffect(() => () => { epoch.current++; }, []);
  useEffect(() => { bottom.current?.scrollIntoView?.({ block: 'nearest' }); }, [turns, phase, error]);

  function scrub(): void {
    epoch.current++;
    setTurns([{ id: ++sequence.current, author: 'bot',
      text: 'Session verrouillée ou accès refusé. Ouvrez une nouvelle session autorisée.' }]);
    setPhase(null);
    setDraft('');
    setChecked(false);
    setBusy(false);
  }

  async function prepare(phrase: string, choiceId?: number) {
    if (locked.current || phrase.length > 160 || !phrase.trim()) return;
    const command = parseCB03ChatCommand(phrase);
    if (command.type === 'unsupported') {
      setError('');
      add('bot', 'Pour un RDV : « Prépare un RDV demain 10h pour Mme Benali contrôle ». Pour un statut : « Statut RDV 32 en fauteuil ». Je ne peux pas exécuter d’autres demandes dans ce pilote sécurisé.');
      return;
    }
    locked.current = true;
    const op = ++epoch.current;
    setBusy(true);
    setError('');
    setChecked(false);
    setPhase(null);
    try {
      const mode: Mode = command.type === 'appointment' ? 'appointment' : 'status';
      const endpoint = mode === 'appointment'
        ? '/bot/guided/prepare-appointment' : '/bot/guided/prepare-status';
      const payload = command.type === 'appointment'
        ? {
          utterance: command.phrase, duration_minutes: 30,
          ...(practitionerId && POSITIVE(practitionerId) ? { praticien_id: practitionerId } : {}),
          ...(choiceId && POSITIVE(choiceId) ? { chosen_patient_id: choiceId } : {}),
        }
        : {
          selected_appointment_id: command.appointmentId,
          utterance: 'Prépare le statut du RDV en ' + command.target,
        };
      const response = (await api.post(endpoint, payload)).data as unknown;
      if (op !== epoch.current) return;
      if (mode === 'appointment' && response && typeof response === 'object') {
        const value = response as { status?: unknown; message?: unknown; candidates?: unknown };
        if (value.status === 'disambiguation' || value.status === 'clarification') {
          const candidates = Array.isArray(value.candidates)
            ? value.candidates.filter(validPatient) : [];
          // Only ID choices explicitly returned by authenticated server.
          if (value.status === 'disambiguation' && candidates.length) {
            setPhase({ kind: 'choose', phrase, candidates });
          }
          add('bot', typeof value.message === 'string' ? value.message
            : 'Précisez le dossier ou reformulez la demande.');
          return;
        }
      }
      const prepared = validatedPreparation(response, mode);
      if (!prepared) throw Error('Invalid prepared response');
      setPhase({ kind: 'prepared', mode, receipt: prepared });
      add('bot', 'Le serveur a vérifié une proposition. Elle n’est pas encore exécutée : contrôlez les détails et confirmez explicitement.');
    } catch (err) {
      if (op !== epoch.current) return;
      if (DENIED.has(codeOf(err) ?? 0)) scrub();
      else {
        setPhase(null);
        setError(responseError(codeOf(err)));
      }
    } finally {
      if (op === epoch.current) { locked.current = false; setBusy(false); }
      else { locked.current = false; }
    }
  }

  function send() {
    const message = draft.trim();
    if (!message || busy || locked.current || message.length > 160) return;
    if (phase?.kind === 'prepared' || phase?.kind === 'uncertain' || phase?.kind === 'choose') {
      add('bot', 'Terminez ou abandonnez la proposition en cours avant de formuler une autre demande. Une confirmation incertaine doit être réconciliée.');
      return;
    }
    add('user', message);
    setDraft('');
    void prepare(message);
  }

  async function select(candidate: Patient) {
    if (phase?.kind !== 'choose' || locked.current
      || !phase.candidates.some(p => p.id === candidate.id)) return;
    const phrase = phase.phrase;
    add('user', 'J’ai choisi le dossier ' + person(candidate) + ' proposé par le serveur.');
    await prepare(phrase, candidate.id);
  }

  function discard() {
    if (locked.current || (phase?.kind !== 'prepared' && phase?.kind !== 'choose')) return;
    setPhase(null);setChecked(false);setError('');
    add('bot', 'Proposition abandonnée localement. Aucune exécution clinique. Toute préparation serveur non confirmée expirera.');
  }

  async function confirm() {
    if (locked.current || !checked || phase?.kind !== 'prepared') return;
    const { receipt, mode } = phase;
    locked.current = true;
    const op = ++epoch.current;
    setBusy(true);setChecked(false);setError('');
    // Lost response is ALWAYS unknown, never re-enable a confirm button.
    setPhase({ kind: 'uncertain', id: receipt.preparation_id, mode });
    add('bot', 'Confirmation envoyée. Résultat en attente de preuve serveur. Ne relancez pas cette confirmation.');
    try {
      const response = (await api.post('/bot/guided/confirm', {
        preparation_id: receipt.preparation_id, confirm: true,
      })).data as { status?: unknown; preparation_id?: unknown; result?: unknown };
      if (op !== epoch.current) return;
      if (response?.status !== 'executed'
          || response.preparation_id !== receipt.preparation_id
          || !validResult(response.result, mode)) throw Error('Unverified G2 receipt');
      const result = response.result as Result;
      setPhase({ kind: 'finished', id: receipt.preparation_id, mode, result });
      add('bot', 'Action exécutée et vérifiée · RDV #' + result.appointment_id
        + ' · ' + result.status + '.');
    } catch (err) {
      if (op !== epoch.current) return;
      if (DENIED.has(codeOf(err) ?? 0) || codeOf(err) === 404) scrub();
      else setError('Résultat incertain. Utilisez uniquement « Vérifier l’état » (GET). Ne confirmez pas deux fois.');
    } finally {
      if (op === epoch.current) { locked.current = false;setBusy(false); }
      else { locked.current = false; }
    }
  }

  async function reconcile() {
    if (locked.current || !phase || !['uncertain', 'finished'].includes(phase.kind)) return;
    const known = phase as Extract<Phase, { kind: 'uncertain' | 'finished' }>;
    locked.current = true;
    const op = ++epoch.current;
    setBusy(true);setError('');
    try {
      const data = (await api.get('/bot/guided/actions/' + encodeURIComponent(known.id))).data as {
        preparation_id?: unknown; action_type?: unknown; status?: unknown;
        safe_to_retry_automatically?: unknown; manual_reconciliation_required?: unknown;
        result?: unknown;
      };
      if (op !== epoch.current) return;
      if (!data || data.preparation_id !== known.id
          || data.action_type !== (known.mode === 'appointment' ? 'CREATE_APPOINTMENT' : 'CHANGE_STATUS')
          || data.safe_to_retry_automatically !== false
          || typeof data.manual_reconciliation_required !== 'boolean') {
        throw Error('Invalid read-only reconciliation response');
      }
      if (data.status === 'executed' && data.manual_reconciliation_required === false
          && validResult(data.result, known.mode)) {
        setPhase({ kind: 'finished', id: known.id, mode: known.mode, result: data.result });
        add('bot', 'Reçu retrouvé en lecture seule : action exécutée et vérifiée · RDV #'
          + data.result.appointment_id + ' · ' + data.result.status + '.');
      } else if (['expired', 'cancelled', 'failed'].includes(String(data.status))
          && data.result == null && data.manual_reconciliation_required === false) {
        setPhase({ kind: 'blocked', id: known.id, mode: known.mode, status: String(data.status) });
        add('bot', 'Action non exécutable, état : ' + String(data.status) + '.');
      } else {
        setPhase({ kind: 'uncertain', id: known.id, mode: known.mode });
        add('bot', 'État serveur : ' + String(data.status)
          + '. Aucune nouvelle confirmation automatique ; vérification manuelle si nécessaire.');
      }
    } catch (err) {
      if (op !== epoch.current) return;
      if (DENIED.has(codeOf(err) ?? 0) || codeOf(err) === 404) scrub();
      else setError('Lecture de suivi indisponible. Ne répétez pas la confirmation.');
    } finally {
      if (op === epoch.current) { locked.current = false;setBusy(false); }
      else { locked.current = false; }
    }
  }

  const prepared = phase?.kind === 'prepared' ? phase.receipt : null;
  const appointment = prepared && phase?.kind === 'prepared' && phase.mode === 'appointment'
    ? prepared.summary as AppointmentSummary : null;
  const status = prepared && phase?.kind === 'prepared' && phase.mode === 'status'
    ? prepared.summary as StatusSummary : null;
  const composerDisabled = busy || phase?.kind === 'prepared' || phase?.kind === 'choose'
    || phase?.kind === 'uncertain';

  return (
    <section aria-label="Conversation Crown Bot — actions guidées CB-03"
      className="flex min-h-0 min-w-0 flex-1 flex-col bg-slate-50 text-slate-900">
      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-3" role="log"
        aria-label="Échanges Crown Bot sécurisés" aria-live="polite" aria-relevant="additions">
        {turns.map(turn => (
          <div key={turn.id} className={turn.author === 'user' ? 'flex justify-end' : 'flex justify-start'}>
            <div className={'max-w-[92%] min-w-0 rounded-xl px-3 py-2 text-sm break-words whitespace-pre-wrap ' +
              (turn.author === 'user' ? 'bg-indigo-700 text-white' :
                'bg-white border border-slate-200 text-slate-800')}>
              <span className="sr-only">{turn.author === 'user' ? 'Vous : ' : 'Crown Bot : '}</span>{turn.text}
            </div>
          </div>
        ))}
        {phase?.kind === 'choose' && (
          <div className="rounded-xl border border-amber-300 bg-amber-50 p-3 space-y-2">
            <p className="text-xs font-bold">Quel dossier souhaitez-vous utiliser ?</p>
            {phase.candidates.map(p => (
              <button type="button" key={p.id} disabled={busy}
                onClick={() => { void select(p); }}
                className="block min-h-11 w-full rounded-lg border border-amber-300 bg-white px-2 text-left text-xs font-medium">
                {person(p)}
              </button>
            ))}
            <button type="button" disabled={busy} onClick={discard}
              className="min-h-11 text-xs font-semibold underline">Annuler la proposition</button>
          </div>
        )}
        {prepared && (
          <div className="rounded-xl border border-amber-300 bg-amber-50 p-3 space-y-2"
            aria-label="Récapitulatif vérifié par le serveur">
            <p className="text-sm font-bold">Préparation vérifiée · non exécutée</p>
            <dl className="space-y-1 text-xs">
              <div><dt className="inline font-semibold">Patient : </dt>
                <dd className="inline">{person(prepared.summary.patient)}</dd></div>
              <div><dt className="inline font-semibold">Début : </dt>
                <dd className="inline">{prepared.summary.datetime_start.slice(0,16).replace('T',' à ')}</dd></div>
              {appointment && <>
                <div><dt className="inline font-semibold">Motif : </dt>
                  <dd className="inline">{appointment.motif}</dd></div>
                <div><dt className="inline font-semibold">Durée : </dt>
                  <dd className="inline">{appointment.duration_minutes} min</dd></div>
                <div><dt className="inline font-semibold">Praticien : </dt>
                  <dd className="inline">#{appointment.praticien_id}</dd></div>
              </>}
              {status && <>
                <div><dt className="inline font-semibold">RDV : </dt>
                  <dd className="inline">#{status.appointment_id}</dd></div>
                <div><dt className="inline font-semibold">État initial : </dt>
                  <dd className="inline">{status.expected_status} (révision {status.expected_revision})</dd></div>
                <div><dt className="inline font-semibold">Nouvel état : </dt>
                  <dd className="inline">{status.new_status_label}</dd></div>
              </>}
              <div><dt className="inline font-semibold">Expiration : </dt>
                <dd className="inline">{prepared.expires_at.slice(0,19).replace('T',' ')} UTC</dd></div>
            </dl>
            <label className="flex min-h-11 items-start gap-2 rounded-lg bg-white p-2 text-xs font-medium">
              <input type="checkbox" disabled={busy} checked={checked} onChange={e=>setChecked(e.target.checked)}
                className="mt-0.5 h-4 w-4 shrink-0"/>
              J’ai vérifié le patient, la date, le rendez-vous et l’opération.
            </label>
            <button type="button" onClick={()=>{ void confirm(); }} disabled={!checked || busy}
              className="min-h-11 w-full rounded-lg bg-emerald-700 px-2 py-2 text-xs font-bold text-white disabled:opacity-50">
              Confirmer explicitement cette action
            </button>
            <button type="button" disabled={busy} onClick={discard}
              className="min-h-11 w-full text-xs font-semibold underline">Abandonner sans exécuter</button>
          </div>
        )}
        {(phase?.kind === 'uncertain' || phase?.kind === 'finished') && (
          <div className="rounded-xl border border-slate-300 bg-white p-3 space-y-2">
            <p className="text-xs font-semibold">
              {phase.kind === 'uncertain' ? 'Résultat à réconcilier · ne pas confirmer une deuxième fois'
                : 'Exécution déjà vérifiée · aucune répétition'}
            </p>
            <p className="text-xs break-all">Identifiant de suivi : {phase.id}</p>
            <button type="button" disabled={busy} onClick={()=>{void reconcile();}}
              className="min-h-11 w-full rounded-lg border border-indigo-300 bg-indigo-50 p-2 text-xs font-bold text-indigo-900">
              Vérifier l’état (lecture seule)
            </button>
          </div>
        )}
        {phase?.kind === 'blocked' && <p role="status"
          className="rounded-lg border border-slate-300 bg-slate-100 p-2 text-xs">
          Action terminée sans exécution : {phase.status}
        </p>}
        {!!error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-xs text-rose-800">{error}</p>}
        {busy && <p role="status" className="text-xs text-slate-600">Vérification en cours…</p>}
        <div ref={bottom}/>
      </div>
      <div className="shrink-0 border-t border-slate-200 bg-white p-3">
        <div className="flex gap-2 overflow-x-auto pb-2">
          <button type="button" disabled={composerDisabled}
            onClick={()=>setDraft('Prépare un RDV ')}
            className="min-h-11 shrink-0 rounded-full border border-indigo-200 px-3 text-xs font-semibold">
            Préparer un RDV
          </button>
          <button type="button" disabled={composerDisabled}
            onClick={()=>setDraft('Statut RDV ')}
            className="min-h-11 shrink-0 rounded-full border border-indigo-200 px-3 text-xs font-semibold">
            Changer un statut
          </button>
        </div>
        <form onSubmit={e=>{e.preventDefault();send();}} className="flex items-end gap-2">
          <label htmlFor="cb03-g5-input" className="sr-only">Votre message à Crown Bot</label>
          <textarea id="cb03-g5-input" rows={2} maxLength={160} disabled={composerDisabled}
            value={draft} onChange={e=>setDraft(e.target.value)}
            placeholder="Décrivez votre demande…"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            onKeyDown={e=>{
              if(e.key==='Enter'&&!e.shiftKey){
                e.preventDefault();send();
              }
            }} />
          <button type="submit" disabled={composerDisabled||!draft.trim()}
            className="min-h-11 shrink-0 rounded-lg bg-indigo-700 px-3 py-2 text-xs font-bold text-white disabled:opacity-50">
            Envoyer
          </button>
        </form>
        <p className="mt-2 text-[11px] leading-relaxed text-slate-600">
          Pilote déterministe · actions serveur vérifiées · aucun envoi sans confirmation.
        </p>
      </div>
    </section>
  );
}
