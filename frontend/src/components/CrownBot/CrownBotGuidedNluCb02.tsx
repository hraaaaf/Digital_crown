import { useRef, useState } from 'react';
import { api } from '../../services/api';

type PatientChoice = { id: number; nom: string; prenom: string; numero_dossier: string | null };
type Field = { value: string; source: string; rule: string };
type GuidedResponse = {
  status: 'refused' | 'clarification' | 'requires_server_authorization'
    | 'preview_only' | 'read' | 'disambiguation';
  intent: 'AGENDA_READ' | 'PATIENT_LOOKUP' | 'RDV_PREPARE' | null;
  fields: Record<string, Field>;
  message: string;
  proposal: null;
  executable: false;
  patient?: PatientChoice;
  candidates?: PatientChoice[];
};
const VALID_STATUS = new Set([
  'refused', 'clarification', 'requires_server_authorization',
  'preview_only', 'read', 'disambiguation',
]);
const FIELD_NAMES: Record<string, string> = {
  patient: 'Patient', date: 'Date', time: 'Heure', motif: 'Motif',
};
const SOURCE_NAMES: Record<string, string> = {
  explicit_unverified: 'mention non vérifiée',
  deterministic_relative_or_explicit: 'déduite du texte (date cabinet)',
  explicit: 'saisie explicitement',
  server_verified: 'vérifiée par le serveur du cabinet',
};
function isResponse(value: GuidedResponse): boolean {
  return !!value && VALID_STATUS.has(value.status)
    && value.proposal === null && value.executable === false
    && typeof value.message === 'string'
    && value.fields !== null && typeof value.fields === 'object';
}

/** CB-02 read-only experimental input, no /execute route or action UUID. */
export function CrownBotGuidedNluCb02() {
  const [utterance, setUtterance] = useState('');
  const [result, setResult] = useState<GuidedResponse | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);

  const edit = (next: string) => {
    if (inFlight.current) return;
    setUtterance(next);
    setResult(null);
    setError('');
  };
  const check = async (chosenPatientId?: number) => {
    const text = utterance.trim();
    if (inFlight.current || text.length < 1 || text.length > 160) return;
    inFlight.current = true;
    setBusy(true);
    setResult(null);
    setError('');
    try {
      const data = (await api.post<GuidedResponse>('/bot/guided/preview', {
        utterance: text,
        ...(chosenPatientId ? { chosen_patient_id: chosenPatientId } : {}),
      })).data;
      if (!isResponse(data)) throw new Error('Invalid preview response');
      setResult(data);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      setResult(null);
      setError(status === 403 ? 'Accès refusé pour ce compte.'
        : status === 404 ? 'Aucun dossier correspondant ou aperçu indisponible.'
        : status === 409 ? 'Sélection obsolète. Reformulez votre demande.'
        : status === 422 ? 'Demande invalide. Reformulez-la.'
        : status === 423 ? 'Poste verrouillé. Aucune donnée affichée.'
        : 'Serveur indisponible. Aucun changement effectué.');
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  };
  return (
    <section aria-label="Français guidé Crown Bot CB-02"
      className="rounded-lg border border-sky-200 bg-white p-3 text-sm text-slate-800">
      <h3 className="font-semibold">Demande en français — aperçu expérimental</h3>
      <p className="mt-1 text-xs leading-relaxed">
        Exemple : « Prépare un RDV demain 10h pour Mme Benali contrôle ».
        Aucune réservation ni action clinique. Les identités sont vérifiées
        uniquement par le serveur du cabinet.
      </p>
      <form className="mt-2 space-y-2" onSubmit={event => {
        event.preventDefault();
        void check();
      }}>
        <label htmlFor="cb02-utterance" className="block text-xs font-medium">
          Votre demande (modifiable avant une nouvelle vérification)
        </label>
        <textarea id="cb02-utterance" aria-label="Votre demande en français"
          rows={2} maxLength={160} disabled={busy} value={utterance}
          onChange={event => edit(event.target.value)}
          className="w-full min-w-0 rounded-md border border-slate-300 p-2 text-sm"
          placeholder="Mon agenda demain" />
        <button type="submit" disabled={busy || !utterance.trim()}
          className="min-h-11 rounded-md bg-sky-800 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">
          {busy ? 'Vérification…' : 'Comprendre la demande'}
        </button>
      </form>
      {error && <p role="alert" className="mt-2 rounded-md border border-rose-200 p-2 text-xs text-rose-800">{error}</p>}
      {result && <div role="status" className="mt-3 space-y-2 rounded-md border border-slate-200 p-2">
        <p className="font-medium">{result.message}</p>
        <p className="text-xs font-semibold text-amber-800">
          Prévisualisation sans écriture · Aucune action disponible.
        </p>
        <dl className="space-y-1">
          {Object.entries(result.fields).map(([key, field]) => (
            <div key={key} className="text-xs">
              <dt className="inline font-semibold">{FIELD_NAMES[key] || key} : </dt>
              <dd className="inline">{field.value} · {SOURCE_NAMES[field.source] || 'valeur à vérifier'}</dd>
            </div>
          ))}
        </dl>
        {result.patient && (
          <p className="text-xs" data-cb02-server-patient>
            Identité vérifiée par le serveur : {result.patient.prenom} {result.patient.nom}
            {result.patient.numero_dossier ? ' — Dossier ' + result.patient.numero_dossier : ''}
          </p>
        )}
        {result.status === 'disambiguation' && !!result.candidates?.length && (
          <div aria-label="Choix du dossier vérifié par le serveur"
            className="grid gap-2">
            {result.candidates.map(choice => (
              <button key={choice.id} type="button" disabled={busy}
                onClick={() => { void check(choice.id); }}
                className="min-h-11 rounded-md border border-slate-300 p-2 text-left text-xs">
                {choice.prenom} {choice.nom} — Dossier {choice.numero_dossier || 'non renseigné'}
              </button>
            ))}
          </div>
        )}
      </div>}
    </section>
  );
}
