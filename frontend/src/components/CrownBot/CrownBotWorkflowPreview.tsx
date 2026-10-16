import { useRef, useState } from 'react';
import { api } from '../../services/api';

type PreviewResponse = {
  status: string;
  message: string;
  proposal?: { type?: string; params?: Record<string, unknown> } | null;
  patient?: { id: number; nom: string; prenom: string; numero_dossier?: string | null };
  candidates?: Array<{ id: number; nom: string; prenom: string; numero_dossier: string | null }>;
};

const COMMANDS = ['/patient', '/rdv', '/devis'] as const;
const MAX_TURNS = 8;

/**
 * Flagged, explicitly NON-ACTIONABLE ZERO-LLM simulator.
 * This endpoint neither books appointments nor generates an executable UUID.
 * NEVER feed a preview proposal to /bot/execute.
 * Transcript lives only in component memory, not persistent chat history.
 */
export function CrownBotWorkflowPreview() {
  const [transcript, setTranscript] = useState<string[]>([]);
  const [answer, setAnswer] = useState<PreviewResponse | null>(null);
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);

  const reset = () => {
    if (inFlight.current) return;
    setTranscript([]);
    setAnswer(null);
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
    try {
      const response = await api.post<PreviewResponse>('/bot/workflows/preview', {
        messages: next,
      });
      setTranscript(next);
      setAnswer(response.data);
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
    <section aria-label="Simulation ZERO-LLM Crown Bot"
      className="flex min-h-0 min-w-0 flex-1 flex-col gap-3 overflow-y-auto bg-slate-50 p-3 sm:p-4">
      <div className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-amber-900">
        <p className="text-sm font-bold">Simulation ZERO-LLM — aucune écriture</p>
        <p className="mt-1 text-xs leading-relaxed">
          Les propositions ne réservent aucun créneau et ne créent ni devis ni dossier.
          Une validation métier et une confirmation serveur restent indispensables.
        </p>
      </div>
      <div className="flex flex-wrap gap-2" aria-label="Parcours disponibles">
        {COMMANDS.map(command => (
          <button key={command} type="button" disabled={busy}
            onClick={() => { void send(command, true); }}
            className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-800 disabled:opacity-50">
            {command}
          </button>
        ))}
      </div>
      {transcript.length > 0 && (
        <div className="min-w-0 rounded-lg bg-white p-3 text-xs text-slate-700 shadow-sm">
          <p className="mb-2 font-semibold">Étapes saisies : {transcript.length}/{MAX_TURNS}</p>
          <ol className="list-inside list-decimal space-y-1 break-words">
            {transcript.map((turn, index) => <li key={index}>{turn}</li>)}
          </ol>
        </div>
      )}
      {answer && (
        <div role="status" className="min-w-0 rounded-lg border border-slate-200 bg-white p-3">
          <p className="break-words text-sm text-slate-800">{answer.message}</p>
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
              Proposition {answer.proposal.type || ''} : simulation uniquement, non exécutable.
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
