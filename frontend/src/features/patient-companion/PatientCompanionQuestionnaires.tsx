import { useEffect, useMemo, useState } from 'react';
import { ClipboardList, Loader2 } from 'lucide-react';
import { API_BASE } from '../../services/api';
import type { PatientPairing } from './PatientCompanionStorage';

type Question = {
  id: string;
  label: string;
  type: 'yes_no' | 'single_choice' | 'short_text';
  required: boolean;
  options: string[];
};

type QuestionnaireItem = {
  assignment_id: string;
  questionnaire_id: string;
  title: string;
  version: number;
  questions: Question[];
  state: 'ASSIGNED' | 'PENDING_REVIEW' | 'REVIEWED' | 'REJECTED' | 'EXPIRED';
  assigned_at: string;
  expires_at?: string | null;
  submitted_at?: string | null;
  reviewed_at?: string | null;
};

const stateLabel = (state: QuestionnaireItem['state']) => {
  if (state === 'ASSIGNED') return 'À compléter';
  if (state === 'PENDING_REVIEW') return 'Envoyé · en attente de revue';
  if (state === 'REVIEWED') return 'Revu par le cabinet';
  if (state === 'REJECTED') return 'Revue à reprendre avec le cabinet';
  return 'Expiré';
};

export const PatientCompanionQuestionnaires = ({ pairing, enabled }: { pairing: PatientPairing; enabled: boolean }) => {
  const [items, setItems] = useState<QuestionnaireItem[]>([]);
  const [openId, setOpenId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');

  const openItem = useMemo(
    () => items.find(item => item.assignment_id === openId) || null,
    [items, openId],
  );

  const load = async () => {
    setLoading(true);
    setMessage('');
    try {
      const accessId = encodeURIComponent(pairing.context.access_id);
      const response = await fetch(`${API_BASE}/api/patient-companion/contexts/${accessId}/questionnaires`, {
        headers: { Authorization: `Bearer ${pairing.accessToken}` },
        cache: 'no-store',
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok || !Array.isArray(body.items)) throw new Error('Questionnaires indisponibles.');
      setItems(body.items);
    } catch {
      setMessage('Cabinet non joignable · aucun questionnaire n’a été marqué comme envoyé.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!enabled) return;
    void load();
  // Re-fetch only when the authorized patient context is online/synchronized.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, pairing.context.access_id, pairing.accessToken]);

  const openForm = (item: QuestionnaireItem) => {
    if (item.state !== 'ASSIGNED') return;
    setOpenId(item.assignment_id);
    setAnswers({});
    setMessage('');
  };

  const submit = async () => {
    if (!openItem || openItem.state !== 'ASSIGNED') return;
    for (const question of openItem.questions) {
      if (question.required && !(question.id in answers)) {
        setMessage('Complétez toutes les questions obligatoires.');
        return;
      }
    }
    setSubmitting(true);
    setMessage('');
    try {
      const accessId = encodeURIComponent(pairing.context.access_id);
      const assignmentId = encodeURIComponent(openItem.assignment_id);
      const response = await fetch(
        `${API_BASE}/api/patient-companion/contexts/${accessId}/questionnaires/${assignmentId}/submit`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${pairing.accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ answers }),
        },
      );
      const body = await response.json().catch(() => ({}));
      if (!response.ok || body.status !== 'PENDING_REVIEW' || body.clinical_record_updated !== false) {
        throw new Error(body.detail || 'Envoi impossible.');
      }
      setOpenId(null);
      setAnswers({});
      await load();
      setMessage('Envoyé au cabinet · en attente de revue. Vos réponses restent déclaratives jusqu’à validation du praticien.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Envoi impossible · aucune confirmation cabinet reçue.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section data-pc03-questionnaires className="mt-4 rounded-[1.5rem] border border-border-main bg-card-bg p-4" aria-label="Questionnaires médicaux">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.14em] text-primary">Santé</p>
          <h3 className="mt-0.5 text-lg font-black">Questionnaires médicaux</h3>
        </div>
        <ClipboardList className="text-primary" size={22} />
      </div>
      <p className="mt-2 text-[11px] font-bold text-text-muted">
        Vos réponses sont transmises au cabinet pour revue. Elles ne modifient pas automatiquement votre dossier clinique.
      </p>

      {!enabled && <p className="mt-3 text-xs font-bold text-text-muted">Synchronisez votre espace pour vérifier les questionnaires à compléter.</p>}

      {enabled && loading && <div className="mt-3 flex min-h-[48px] items-center gap-2 text-xs font-black text-text-muted"><Loader2 className="animate-spin" size={16} /> Chargement…</div>}

      {enabled && !loading && items.length === 0 && !message && (
        <p className="mt-3 text-xs font-bold text-text-muted">Aucun questionnaire à compléter.</p>
      )}

      <div className="mt-3 grid gap-2">
        {items.map(item => (
          <article key={item.assignment_id} className="rounded-2xl border border-border-main bg-background p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-black">{item.title}</p>
                <p className="mt-1 text-[10px] font-bold text-text-muted">Version {item.version}</p>
              </div>
              <span className="max-w-[48%] rounded-full bg-primary/5 px-2.5 py-1 text-right text-[10px] font-black text-primary">{stateLabel(item.state)}</span>
            </div>
            {item.state === 'ASSIGNED' && (
              <button onClick={() => openForm(item)} className="mt-3 min-h-[48px] w-full rounded-xl bg-primary text-xs font-black text-white">
                Remplir
              </button>
            )}
            {item.state !== 'ASSIGNED' && item.submitted_at && (
              <p className="mt-2 text-[10px] font-bold text-text-muted">Envoyé le {new Date(item.submitted_at).toLocaleString()}</p>
            )}
          </article>
        ))}
      </div>

      {openItem && (
        <div data-pc03-form className="mt-3 rounded-2xl border border-primary/15 bg-primary/5 p-4">
          <p className="font-black">{openItem.title}</p>
          <p className="mt-1 text-[11px] font-bold text-text-muted">* réponse obligatoire</p>
          <div className="mt-3 grid gap-4">
            {openItem.questions.map(question => (
              <fieldset key={question.id} className="min-w-0">
                <legend className="text-xs font-black">{question.label}{question.required ? ' *' : ''}</legend>
                {question.type === 'yes_no' && (
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    {[['Oui', true], ['Non', false]].map(([label, value]) => (
                      <button
                        type="button"
                        key={String(label)}
                        onClick={() => setAnswers(current => ({ ...current, [question.id]: value }))}
                        className={`min-h-[48px] rounded-xl border text-xs font-black ${answers[question.id] === value ? 'border-primary bg-primary text-white' : 'border-border-main bg-card-bg'}`}
                      >
                        {label as string}
                      </button>
                    ))}
                  </div>
                )}
                {question.type === 'single_choice' && (
                  <select
                    value={typeof answers[question.id] === 'string' ? String(answers[question.id]) : ''}
                    onChange={event => setAnswers(current => ({ ...current, [question.id]: event.target.value }))}
                    className="mt-2 min-h-[48px] w-full rounded-xl border border-border-main bg-card-bg px-3 text-sm font-bold"
                  >
                    <option value="">Choisir</option>
                    {question.options.map(option => <option key={option} value={option}>{option}</option>)}
                  </select>
                )}
                {question.type === 'short_text' && (
                  <textarea
                    maxLength={1000}
                    value={typeof answers[question.id] === 'string' ? String(answers[question.id]) : ''}
                    onChange={event => setAnswers(current => ({ ...current, [question.id]: event.target.value }))}
                    className="mt-2 min-h-[96px] w-full resize-y rounded-xl border border-border-main bg-card-bg p-3 text-sm"
                  />
                )}
              </fieldset>
            ))}
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2">
            <button type="button" disabled={submitting} onClick={() => { setOpenId(null); setAnswers({}); }} className="min-h-[48px] rounded-xl border border-border-main bg-card-bg text-xs font-black">Annuler</button>
            <button type="button" disabled={submitting} onClick={() => void submit()} className="min-h-[48px] rounded-xl bg-primary text-xs font-black text-white disabled:opacity-60">
              {submitting ? 'Envoi…' : 'Envoyer'}
            </button>
          </div>
        </div>
      )}

      {message && <p role="status" className="mt-3 rounded-xl bg-amber-50 px-3 py-2.5 text-[11px] font-black text-amber-800">{message}</p>}
    </section>
  );
};
