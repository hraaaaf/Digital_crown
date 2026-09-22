import { useCallback, useEffect, useMemo, useState } from 'react';
import { Loader2, MessageCircle, RefreshCcw, Send, ShieldCheck } from 'lucide-react';
import { api } from '../../../services/api';

type Access = { access_id: string; relationship_type: string; created_at: string };
type Message = {
  message_id: string;
  sender_kind: 'PATIENT' | 'STAFF';
  body: string;
  created_at: string;
  staff_read_at?: string | null;
  patient_received_at?: string | null;
  patient_read_at?: string | null;
};

const labels: Record<string, string> = { SELF: 'Patient', PARENT: 'Parent', GUARDIAN: 'Tuteur', CAREGIVER: 'Aidant' };

export const PatientCompanionMessagingPanel = ({ patientId }: { patientId: number }) => {
  const [accesses, setAccesses] = useState<Access[]>([]);
  const [selected, setSelected] = useState('');
  const [items, setItems] = useState<Message[]>([]);
  const [body, setBody] = useState('');
  const [maxBytes, setMaxBytes] = useState(4096);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [sendIntent, setSendIntent] = useState<{ body: string; clientMessageId: string } | null>(null);

  const load = useCallback(async (accessId?: string) => {
    setError('');
    const response = await api.get(`/patient-companion/admin/patients/${patientId}/messages`, {
      params: accessId ? { access_id: accessId } : undefined,
    });
    const nextAccesses = Array.isArray(response.data.accesses) ? response.data.accesses : [];
    setAccesses(nextAccesses);
    const resolved = response.data.selected_access_id || (nextAccesses.length === 1 ? nextAccesses[0].access_id : '');
    setSelected(resolved);
    setItems(Array.isArray(response.data.items) ? response.data.items : []);
    setMaxBytes(Number(response.data.max_body_bytes) || 4096);
    const unread = (response.data.items || []).filter((item: Message) => item.sender_kind === 'PATIENT' && !item.staff_read_at);
    if (resolved && unread.length) {
      await api.post(`/patient-companion/admin/patients/${patientId}/messages/read`, {
        access_id: resolved,
        message_ids: unread.map((item: Message) => item.message_id),
      });
      const refreshed = await api.get(`/patient-companion/admin/patients/${patientId}/messages`, { params: { access_id: resolved } });
      setItems(Array.isArray(refreshed.data.items) ? refreshed.data.items : []);
    }
  }, [patientId]);

  useEffect(() => { void load().catch(() => setError('Impossible de charger les messages sécurisés.')); }, [load]);

  const bytes = useMemo(() => new TextEncoder().encode(body.trim()).length, [body]);
  const canSend = Boolean(selected && body.trim() && bytes <= maxBytes && !busy);
  const selectedAccess = accesses.find(access => access.access_id === selected);
  const selectedLabel = selectedAccess ? (labels[selectedAccess.relationship_type] || selectedAccess.relationship_type) : '';

  const send = async () => {
    if (!canSend) return;
    setBusy(true);
    setError('');
    try {
      const text = body.trim();
      const intent = sendIntent?.body === text
        ? sendIntent
        : { body: text, clientMessageId: crypto.randomUUID() };
      setSendIntent(intent);
      await api.post(`/patient-companion/admin/patients/${patientId}/messages`, {
        access_id: selected,
        client_message_id: intent.clientMessageId,
        body: intent.body,
      });
      setBody('');
      setSendIntent(null);
      await load(selected);
    } catch {
      setError('Message non enregistré par le cabinet. Réessayez.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section data-pc08-staff-messaging className="rounded-2xl sm:rounded-[1.75rem] border border-border-main bg-card-bg shadow-elite p-4 sm:p-5 md:p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-primary"><ShieldCheck size={18} /><span className="text-[10px] font-black uppercase tracking-[0.16em]">Canal chiffré</span></div>
          <h3 className="mt-1 text-lg sm:text-xl font-black text-main">Messages sécurisés</h3>
          <p className="mt-1 text-xs sm:text-sm font-medium text-text-muted">Messagerie asynchrone. « Lu » apparaît uniquement après un accusé explicite.</p>
        </div>
        <button type="button" aria-label="Actualiser les messages" onClick={() => void load(selected || undefined)} className="min-h-11 min-w-11 rounded-xl border border-border-main inline-flex items-center justify-center text-text-muted"><RefreshCcw size={16} /></button>
      </div>

      {accesses.length > 1 && (
        <label className="mt-4 block">
          <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Accès destinataire</span>
          <select value={selected} onChange={event => { const value = event.target.value; setSelected(value); void load(value); }} className="mt-1.5 min-h-11 w-full rounded-xl border border-border-main bg-background px-3 text-sm font-bold">
            <option value="">Choisir un accès</option>
            {accesses.map(access => <option key={access.access_id} value={access.access_id}>{labels[access.relationship_type] || access.relationship_type}</option>)}
          </select>
        </label>
      )}
      {accesses.length === 1 && <div className="mt-4 inline-flex rounded-full border border-primary/15 bg-primary/5 px-3 py-1.5 text-xs font-black text-primary">{labels[accesses[0].relationship_type] || accesses[0].relationship_type}</div>}

      <div className="mt-4 max-h-[420px] overflow-y-auto rounded-2xl border border-border-main bg-background p-3 space-y-3">
        {!selected && <p className="py-8 text-center text-sm font-medium text-text-muted">Choisissez l’accès Patient Companion à contacter.</p>}
        {selected && !items.length && <div className="py-8 text-center"><MessageCircle className="mx-auto text-text-muted" size={28} /><p className="mt-2 text-sm font-black text-main">Aucun message</p><p className="mt-1 text-xs text-text-muted">Le patient synchronise ce canal depuis son appareil.</p></div>}
        {items.map(message => {
          const staff = message.sender_kind === 'STAFF';
          const status = staff
            ? message.patient_read_at ? 'Lu' : message.patient_received_at ? 'Reçu sur l’appareil' : 'Envoyé depuis le cabinet'
            : message.staff_read_at ? 'Lu par le cabinet' : 'Reçu par le cabinet';
          return <div key={message.message_id} className={`flex ${staff ? 'justify-end' : 'justify-start'}`}><div className={`max-w-[86%] rounded-2xl px-3.5 py-3 break-words [overflow-wrap:anywhere] ${staff ? 'bg-primary text-white' : 'border border-border-main bg-card-bg text-main'}`}>{!staff && selectedLabel && <p className="mb-1 text-[9px] font-black uppercase tracking-wider text-primary">{selectedLabel}</p>}<p className="whitespace-pre-wrap text-sm font-medium">{message.body}</p><p className={`mt-1.5 text-[10px] font-bold ${staff ? 'text-white/75' : 'text-text-muted'}`}>{new Date(message.created_at).toLocaleString('fr-MA')} · {status}</p></div></div>;
        })}
      </div>

      <div className="mt-3">
        <textarea value={body} onChange={event => { const value = event.target.value; setBody(value); if (sendIntent && sendIntent.body !== value.trim()) setSendIntent(null); }} disabled={!selected || busy} rows={3} placeholder={selected ? 'Écrire au patient…' : 'Choisissez un accès'} className="w-full resize-none rounded-2xl border border-border-main bg-background px-3.5 py-3 text-sm font-medium disabled:opacity-60" />
        <div className="mt-2 flex items-center justify-between gap-3">
          <p className={`text-[10px] font-bold ${bytes > maxBytes ? 'text-rose-700' : 'text-text-muted'}`}>{bytes}/{maxBytes} octets</p>
          <button type="button" disabled={!canSend} onClick={() => void send()} className="min-h-11 rounded-xl bg-primary px-4 text-xs font-black text-white inline-flex items-center gap-2 disabled:opacity-50">{busy ? <Loader2 className="animate-spin" size={15} /> : <Send size={15} />} Envoyer</button>
        </div>
        {error && <p role="alert" className="mt-2 text-xs font-black text-rose-700">{error}</p>}
      </div>
    </section>
  );
};
