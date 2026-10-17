import { useRef, useState } from 'react';
import { api } from '../../services/api';

type PreviewResponse = {
  status: string;
  message: string;
  proposal?: { type?: string; params?: Record<string, unknown> } | null;
  patient?: { id: number; nom: string; prenom: string; numero_dossier?: string | null };
  candidates?: Array<{ id: number; nom: string; prenom: string; numero_dossier: string | null }>;
};

// Stable, explicit UI intentions; only the two patient-facing commands are
// translated to their existing deterministic backend protocol.
const ACTIONS = [
  { key: 'programme', label: 'Mon programme' },
  { key: '/patient', label: 'Trouver un patient' },
  { key: '/rdv', label: 'Préparer un RDV' },
] as const;
const ACTION_LABELS: Record<string, string> = {
  '/patient': 'Trouver un patient',
  '/rdv': 'Préparer un RDV',
};
type ProgrammeAppointment = {
  id: number; datetime_start: string; patient_name?: string | null;
  motif?: string | null; status?: string | null;
};
const MAX_TURNS = 8;

/**
 * Flagged, explicitly NON-ACTIONABLE ZERO-LLM simulator.
 * This endpoint neither books appointments nor generates an executable UUID.
 * NEVER feed a preview proposal to /bot/execute.
 * Transcript lives only in component memory, not persistent chat history.
 */
export function CrownBotWorkflowPreview({ practitionerId }: {
  practitionerId?: number;
} = {}) {
  const [transcript, setTranscript] = useState<string[]>([]);
  const [answer, setAnswer] = useState<PreviewResponse | null>(null);
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [lastPreviewReadAt, setLastPreviewReadAt] = useState<string | null>(null);
  const [programme, setProgramme] = useState<{
    items: ProgrammeAppointment[]; day: string; consultedAt: string;
  } | null>(null);
  const inFlight = useRef(false);

  // Canonical read-only Agenda route; this response is scoped server-side by
  // require_permission("agenda") and employer_id. Never cache across principals.
  const readProgramme = async () => {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError('');
    setAnswer(null);
    setLastPreviewReadAt(null);
    setProgramme(null);
    setTranscript([]);
    setInput('');
    try {
      const now = new Date();
      const start = new Date(now);
      start.setHours(0, 0, 0, 0);
      const end = new Date(now);
      end.setHours(23, 59, 59, 999);
      const response = await api.get<ProgrammeAppointment[]>('/appointments/', {
        params: {
          start_date: start.toISOString(), end_date: end.toISOString(),
          ...(practitionerId && Number.isSafeInteger(practitionerId)
            ? { praticien_id: practitionerId } : {}),
        },
      });
      if (!Array.isArray(response.data) || !response.data.every(item =>
        Number.isSafeInteger(item?.id) && typeof item.datetime_start === 'string')) {
        throw new Error('Invalid agenda read contract');
      }
      setProgramme({
        items: [...response.data].sort((a, b) =>
          a.datetime_start.localeCompare(b.datetime_start)),
        day: now.toLocaleDateString('fr-FR', {
          day: 'numeric', month: 'long', year: 'numeric',
        }),
        consultedAt: new Date().toLocaleTimeString('fr-FR', {
          hour: '2-digit', minute: '2-digit',
        }),
      });
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      setError(status === 403 ? 'Accès Agenda refusé pour votre compte.'
        : status === 423 ? 'Poste verrouillé. Aucune donnée Agenda affichée.'
        : 'Impossible de consulter le programme. Aucune donnée périmée affichée.');
    } finally {
      setBusy(false);
      inFlight.current = false;
    }
  };

  const reset = () => {
    if (inFlight.current) return;
    setTranscript([]);
    setAnswer(null);
    setLastPreviewReadAt(null);
    setProgramme(null);
    setError('');
    setInput('');
  };

  const send = async (raw: string, newWorkflow = false, replacePatient = false) => {
    const text = raw.trim();
    if (!text || text.length > 80 || inFlight.current) return;
    // An ambiguous name must be replaced by the selected, server-scoped ID;
    // never append a new identity as if it were a date or procedure slot.
    const retryPatient = replacePatient || (
      transcript.length === 2 && answer?.status === 'disambiguation'
    ) || (
      transcript.length === 2 && answer?.status === 'clarification'
      && answer.message.startsWith('Plusieurs correspondances')
    );
    const next = newWorkflow ? [text]
      : retryPatient ? [transcript[0], text] : [...transcript, text];
    if (next.length > MAX_TURNS) {
      setError('Limite de simulation atteinte. Réinitialisez le parcours.');
      return;
    }
    inFlight.current = true;
    setBusy(true);
    setError('');
    setProgramme(null);
    setLastPreviewReadAt(null);
    // Never show an old patient's successful result as the result of a new
    // workflow (or a subsequent request that fails). Preserve only validated
    // steps when retrying within the same workflow.
    setAnswer(null);
    if (newWorkflow) {
      setTranscript([]);
      setInput('');
    }
    try {
      const response = await api.post<PreviewResponse>('/bot/workflows/preview', {
        messages: next,
      });
      setTranscript(next);
      setAnswer(response.data);
      setLastPreviewReadAt(new Date().toLocaleTimeString('fr-FR', {
        hour: '2-digit', minute: '2-digit',
      }));
      setInput('');
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number; data?: { detail?: string } } })?.response?.status;
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(
        status === 404 && detail === 'Patient introuvable.'
          ? 'Aucun dossier correspondant dans votre cabinet. Vérifiez le nom ou le numéro de dossier.'
          : status === 404 ? 'Simulation indisponible sur ce serveur.'
          : status === 403 ? 'Accès refusé pour ce parcours.'
          : status === 409 ? 'Demande modifiée. Réinitialisez avant de reprendre.'
          : status === 422 ? 'Réponse invalide. Vérifiez le format demandé.'
          : 'Vérification serveur impossible. Aucune action effectuée.',
      );
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  };

  const completed = ['read', 'proposal_only', 'cancelled'].includes(answer?.status || '');
  const full = transcript.length >= MAX_TURNS;
  return (
    <section aria-label="Assistant Crown Bot — consultation"
      className="flex min-h-0 min-w-0 flex-1 flex-col gap-3 overflow-y-auto bg-slate-50 p-3 sm:p-4">
      <div className="rounded-xl border border-slate-200 bg-white p-3 text-slate-800">
        <p className="text-sm font-bold">Que souhaitez-vous consulter ?</p>
        <p className="mt-1 text-xs leading-relaxed">
          Aperçu en lecture seule : aucune écriture. Préparer un RDV ne réserve aucun créneau.
          Les informations proviennent du serveur de votre cabinet après contrôle de vos droits.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3" aria-label="Actions métier disponibles">
        {ACTIONS.map(action => (
          <button key={action.key} type="button" disabled={busy}
            onClick={() => {
              if (action.key === 'programme') void readProgramme();
              else void send(action.key, true);
            }}
            className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-800 text-left hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary disabled:opacity-50">
            {action.label}
          </button>
        ))}
      </div>
      {programme && (
        <div role="status" aria-label="Programme du jour" className="rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-800">
          <p className="font-semibold">Programme du {programme.day}</p>
          <p className="mt-1 text-xs text-slate-500">
            Source : Agenda du cabinet · Lecture serveur à {programme.consultedAt}
          </p>
          {programme.items.length === 0 ? (
            <p className="mt-2 text-sm">Aucun rendez-vous dans ce programme aujourd’hui.</p>
          ) : (
            <div className="mt-2 space-y-2">
              <p className="text-xs font-semibold">{programme.items.length} rendez-vous dans l’Agenda du cabinet</p>
              <ol className="space-y-1">
                {programme.items.slice(0, 8).map(item => (
                  <li key={item.id} className="rounded-md border border-slate-100 bg-slate-50 p-2 text-xs">
                    {item.datetime_start.slice(11, 16)} — {item.patient_name || 'Patient non renseigné'}
                    {item.motif ? ` · ${item.motif}` : ''}
                    {item.status ? ` · ${item.status}` : ''}
                  </li>
                ))}
              </ol>
              {programme.items.length > 8 && (
                <p className="text-xs text-slate-500">Affichage des 8 premiers rendez-vous. Ouvrez l’Agenda pour la liste complète.</p>
              )}
            </div>
          )}
        </div>
      )}
      {transcript.length > 0 && (
        <div className="min-w-0 rounded-lg bg-white p-3 text-xs text-slate-700 shadow-sm">
          <p className="mb-2 font-semibold">Étapes saisies : {transcript.length}/{MAX_TURNS}</p>
          <ol className="list-inside list-decimal space-y-1 break-words">
            {transcript.map((turn, index) => (
              <li key={index}>{ACTION_LABELS[turn] || (turn.startsWith('id:')
                ? 'Dossier choisi' : turn)}</li>
            ))}
          </ol>
        </div>
      )}
      {answer && (
        <div role="status" className="min-w-0 rounded-lg border border-slate-200 bg-white p-3">
          <p className="break-words text-sm text-slate-800">{answer.message}</p>
          <p className="mt-1 text-xs text-slate-500">
            Source : consultation du serveur du cabinet
            {lastPreviewReadAt ? ` · Réponse reçue à ${lastPreviewReadAt}` : ''}
            {' · Aucun changement enregistré'}
          </p>
          {answer.patient && (
            <p className="mt-2 break-words text-xs">
              Patient identifié : {answer.patient.prenom} {answer.patient.nom}
              {answer.patient.numero_dossier ? ` — Dossier ${answer.patient.numero_dossier}` : ''}
            </p>
          )}
          {answer.status === 'disambiguation' && !!answer.candidates?.length && (
            <div className="mt-3 grid gap-2" aria-label="Choisir le dossier patient">
              {answer.candidates.map(candidate => (
                <button key={candidate.id} type="button" disabled={busy}
                  onClick={() => { void send(`id:${candidate.id}`, false, true); }}
                  className="min-h-11 rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-left text-xs text-slate-800 hover:bg-slate-100 disabled:opacity-50">
                  {candidate.prenom} {candidate.nom} — Dossier {candidate.numero_dossier || 'non renseigné'}
                </button>
              ))}
            </div>
          )}
          {answer.proposal && (
            <p className="mt-2 rounded-md bg-amber-50 p-2 text-xs font-semibold text-amber-900">
              {answer.proposal.type === 'CREATE_APPOINTMENT'
                ? 'Rendez-vous proposé' : 'Brouillon proposé'} : aperçu uniquement, non enregistré et non exécutable.
            </p>
          )}
        </div>
      )}
      {error && <p role="alert" className="break-words rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">{error}</p>}
      {!completed && transcript.length > 0 && !full && (
        <form className="flex min-w-0 gap-2"
          onSubmit={event => { event.preventDefault(); void send(input); }}>
          <input aria-label="Votre réponse de simulation" value={input}
            onChange={event => setInput(event.target.value)}
            maxLength={80} autoComplete="off"
            placeholder={transcript.length === 1
              ? 'Nom, prénom, n° dossier ou ID patient'
              : 'Réponse demandée par Crown Bot'}
            disabled={busy}
            className="min-h-11 min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 text-sm"
          />
          <button type="submit" disabled={busy || !input.trim()}
            className="min-h-11 shrink-0 rounded-lg bg-slate-800 px-3 text-xs font-semibold text-white disabled:opacity-50">
            {busy ? 'Vérification…' : 'Envoyer'}
          </button>
        </form>
      )}
      <button type="button" onClick={reset} disabled={busy}
        className="min-h-11 self-start rounded-lg border border-slate-300 bg-white px-3 text-xs font-semibold text-slate-700 disabled:opacity-50">
        Réinitialiser la simulation
      </button>
    </section>
  );
}
