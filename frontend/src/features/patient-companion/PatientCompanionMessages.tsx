import { useCallback, useEffect, useMemo, useState } from 'react';
import { ChevronDown, Loader2, MessageSquareText, RefreshCcw, Send, ShieldCheck, Trash2 } from 'lucide-react';

import type {
  PatientPairing,
  PatientPendingMessage,
  PatientSecureMessage,
} from './PatientCompanionStorage';
import { PatientCompanionStorage } from './PatientCompanionStorage';
import { sendMessageCommand } from './PatientCompanionMessageTransport';

type ServerMessage = {
  message_id: string;
  client_message_id: string;
  sender_kind: 'PATIENT' | 'STAFF';
  body: string;
  created_at: string;
  staff_read_at?: string | null;
  patient_received_at?: string | null;
  patient_read_at?: string | null;
};

const MAX_BODY_BYTES = 4096;

const toLocalMessage = (item: ServerMessage): PatientSecureMessage => ({
  messageId: item.message_id,
  clientMessageId: item.client_message_id,
  senderKind: item.sender_kind,
  body: item.body,
  createdAt: item.created_at,
  staffReadAt: item.staff_read_at ?? null,
  patientReceivedAt: item.patient_received_at ?? null,
  patientReadAt: item.patient_read_at ?? null,
});

const mergeMessages = (
  current: PatientSecureMessage[],
  incoming: PatientSecureMessage[],
): PatientSecureMessage[] => {
  const byId = new Map<string, PatientSecureMessage>();
  for (const item of current) byId.set(item.messageId, item);
  for (const item of incoming) byId.set(item.messageId, { ...byId.get(item.messageId), ...item });
  return [...byId.values()].sort(
    (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
  );
};

const isServerMessageArray = (value: unknown): value is ServerMessage[] =>
  Array.isArray(value)
  && value.every(item => (
    item
    && typeof item === 'object'
    && typeof (item as ServerMessage).message_id === 'string'
    && typeof (item as ServerMessage).client_message_id === 'string'
    && ((item as ServerMessage).sender_kind === 'PATIENT' || (item as ServerMessage).sender_kind === 'STAFF')
    && typeof (item as ServerMessage).body === 'string'
    && typeof (item as ServerMessage).created_at === 'string'
  ));

const byteLength = (value: string) => new TextEncoder().encode(value.trim()).byteLength;

const formatTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString([], {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const canonicalStatus = (item: PatientSecureMessage) => {
  if (item.senderKind === 'PATIENT') {
    return item.staffReadAt ? 'Lu par le cabinet' : 'Reçu par le cabinet';
  }
  if (item.patientReadAt) return 'Lu';
  if (item.patientReceivedAt) return 'Reçu sur cet appareil';
  return 'Envoyé depuis le cabinet';
};

const pendingStatus = (item: PatientPendingMessage) => {
  if (item.state === 'remote_pending') return 'Envoyé · réponse cabinet en attente';
  if (item.state === 'rejected') return item.errorCode ? `Refusé · ${item.errorCode}` : 'Refusé par le cabinet';
  return 'Enregistré localement · non envoyé';
};

export function PatientCompanionMessages({
  pairing,
  enabled,
}: {
  pairing: PatientPairing;
  enabled: boolean;
}) {
  const accessId = pairing.context.access_id;
  const [messages, setMessages] = useState<PatientSecureMessage[]>([]);
  const [pending, setPending] = useState<PatientPendingMessage[]>([]);
  const [beforeCursor, setBeforeCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [threadOpen, setThreadOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  const bytes = useMemo(() => byteLength(draft), [draft]);
  const transportReady = Boolean(pairing.remoteTransport);
  const canSend = transportReady && bytes > 0 && bytes <= MAX_BODY_BYTES && !busy;

  const refreshFromStorage = useCallback(async () => {
    const state = await PatientCompanionStorage.load();
    const wallet = state.cache[accessId];
    const nextMessages = wallet?.secureMessages || [];
    const nextPending = wallet?.pendingMessages || [];
    setMessages(nextMessages);
    setPending(nextPending);
    setBeforeCursor(wallet?.messageBeforeCursor ?? null);
    setHasMore(Boolean(wallet?.messageHasMore));
    return {
      messages: nextMessages,
      pending: nextPending,
      beforeCursor: wallet?.messageBeforeCursor ?? null,
      hasMore: Boolean(wallet?.messageHasMore),
    };
  }, [accessId]);

  const persist = useCallback(async (patch: Parameters<typeof PatientCompanionStorage.saveMessagingState>[1]) => {
    const state = await PatientCompanionStorage.saveMessagingState(accessId, patch);
    const wallet = state.cache[accessId];
    setMessages(wallet?.secureMessages || []);
    setPending(wallet?.pendingMessages || []);
    setBeforeCursor(wallet?.messageBeforeCursor ?? null);
    setHasMore(Boolean(wallet?.messageHasMore));
    return wallet;
  }, [accessId]);

  const mergeAckItems = useCallback(async (value: unknown) => {
    if (!isServerMessageArray(value)) return;
    const stored = await PatientCompanionStorage.load();
    const current = stored.cache[accessId]?.secureMessages || [];
    await persist({ secureMessages: mergeMessages(current, value.map(toLocalMessage)) });
  }, [accessId, persist]);

  const sendReceipt = useCallback(async (
    operation: 'message.received' | 'message.read',
    messageIds: string[],
  ) => {
    if (!messageIds.length || !pairing.remoteTransport) return;
    try {
      const result = await sendMessageCommand(
        pairing,
        operation,
        { message_ids: messageIds },
        crypto.randomUUID(),
      );
      if (result.status !== 'ACCEPTED') return;
      await mergeAckItems(result.result.items);
    } catch {
      // Receipt truth stays unchanged. A later sync/open retries from canonical state.
    }
  }, [mergeAckItems, pairing]);

  const applySync = useCallback(async (result: Record<string, unknown>, appendOlder = false) => {
    if (result.code !== 'MESSAGE_SYNC' || !isServerMessageArray(result.items)) {
      throw new Error(String(result.code || 'Synchronisation des messages refusée.'));
    }
    const incoming = result.items.map(toLocalMessage);
    const stored = await PatientCompanionStorage.load();
    const current = stored.cache[accessId]?.secureMessages || [];
    const merged = mergeMessages(current, incoming);
    const cursor = typeof result.before_cursor === 'string' ? result.before_cursor : null;
    await persist({
      secureMessages: merged,
      messageBeforeCursor: cursor || (appendOlder ? stored.cache[accessId]?.messageBeforeCursor ?? null : null),
      messageHasMore: result.has_more === true,
    });

    const newlyStoredStaff = incoming
      .filter(item => item.senderKind === 'STAFF' && !item.patientReceivedAt)
      .map(item => item.messageId);
    if (newlyStoredStaff.length) {
      await sendReceipt('message.received', newlyStoredStaff);
    }
    if (threadOpen) {
      const unread = incoming
        .filter(item => item.senderKind === 'STAFF' && !item.patientReadAt)
        .map(item => item.messageId);
      if (unread.length) await sendReceipt('message.read', unread);
    }
  }, [accessId, persist, sendReceipt, threadOpen]);

  const retryPending = useCallback(async () => {
    if (!pairing.remoteTransport || !enabled) return;
    const state = await PatientCompanionStorage.load();
    const wallet = state.cache[accessId];
    const queue = wallet?.pendingMessages || [];
    let nextPending = [...queue];
    let nextMessages = wallet?.secureMessages || [];

    for (const item of queue) {
      if (item.state === 'rejected') continue;
      try {
        const result = await sendMessageCommand(
          pairing,
          'message.send',
          { client_message_id: item.clientMessageId, body: item.body },
          item.idempotencyKey,
        );
        if (result.status === 'ACCEPTED' && result.result.code === 'MESSAGE_STORED') {
          const raw = result.result.message;
          if (raw && typeof raw === 'object' && isServerMessageArray([raw])) {
            nextMessages = mergeMessages(nextMessages, [toLocalMessage(raw as ServerMessage)]);
          }
          nextPending = nextPending.filter(candidate => candidate.clientMessageId !== item.clientMessageId);
        } else {
          nextPending = nextPending.map(candidate => (
            candidate.clientMessageId === item.clientMessageId
              ? {
                  ...candidate,
                  state: 'rejected',
                  updatedAt: new Date().toISOString(),
                  errorCode: String(result.result.code || 'REJECTED'),
                }
              : candidate
          ));
        }
      } catch (error) {
        const remotePending = Boolean((error as { remotePending?: boolean } | null)?.remotePending);
        nextPending = nextPending.map(candidate => (
          candidate.clientMessageId === item.clientMessageId
            ? {
                ...candidate,
                state: remotePending ? 'remote_pending' : 'local_queued',
                updatedAt: new Date().toISOString(),
              }
            : candidate
        ));
      }
      await persist({ secureMessages: nextMessages, pendingMessages: nextPending });
    }
  }, [accessId, enabled, pairing, persist]);

  const syncLatest = useCallback(async () => {
    await refreshFromStorage();
    if (!pairing.remoteTransport || !enabled) return;
    setBusy(true);
    setMessage('');
    try {
      await retryPending();
      const result = await sendMessageCommand(pairing, 'message.sync', {});
      if (result.status !== 'ACCEPTED') {
        throw new Error(String(result.result.code || 'Synchronisation refusée.'));
      }
      await applySync(result.result);
      setMessage('Messages synchronisés avec le cabinet.');
    } catch (error) {
      const remotePending = Boolean((error as { remotePending?: boolean } | null)?.remotePending);
      setMessage(
        remotePending
          ? 'Synchronisation transmise · réponse cabinet en attente.'
          : error instanceof Error
            ? error.message
            : 'Synchronisation des messages indisponible.',
      );
    } finally {
      setBusy(false);
    }
  }, [applySync, enabled, pairing, refreshFromStorage, retryPending]);

  useEffect(() => {
    let cancelled = false;
    const hydrate = async () => {
      try {
        if (enabled) {
          await syncLatest();
        } else {
          await refreshFromStorage();
        }
      } catch (error) {
        if (!cancelled) {
          setMessage(error instanceof Error ? error.message : 'Chargement local des messages indisponible.');
        }
      }
    };
    void hydrate();
    return () => { cancelled = true; };
  }, [accessId, enabled, refreshFromStorage, syncLatest]);

  useEffect(() => {
    if (!threadOpen || !pairing.remoteTransport || !enabled) return;
    const unread = messages
      .filter(item => item.senderKind === 'STAFF' && !item.patientReadAt)
      .map(item => item.messageId);
    if (unread.length) void sendReceipt('message.read', unread);
  }, [enabled, messages, pairing.remoteTransport, sendReceipt, threadOpen]);

  const sendDraft = async () => {
    const body = draft.trim();
    if (!body || byteLength(body) > MAX_BODY_BYTES) return;

    const now = new Date().toISOString();
    const queued: PatientPendingMessage = {
      clientMessageId: crypto.randomUUID(),
      idempotencyKey: crypto.randomUUID(),
      body,
      state: 'local_queued',
      createdAt: now,
      updatedAt: now,
    };
    const stored = await PatientCompanionStorage.load();
    const queue = [...(stored.cache[accessId]?.pendingMessages || []), queued];
    await persist({ pendingMessages: queue });
    setDraft('');

    if (!transportReady || !enabled) {
      setMessage('Message chiffré enregistré sur cet appareil · non envoyé.');
      return;
    }

    setBusy(true);
    setMessage('');
    try {
      await retryPending();
      setMessage('Message traité par le canal sécurisé.');
    } finally {
      setBusy(false);
    }
  };

  const retryOne = async (item: PatientPendingMessage) => {
    const stored = await PatientCompanionStorage.load();
    const queue = (stored.cache[accessId]?.pendingMessages || []).map(candidate => (
      candidate.clientMessageId === item.clientMessageId
        ? { ...candidate, state: 'local_queued' as const, errorCode: undefined, updatedAt: new Date().toISOString() }
        : candidate
    ));
    await persist({ pendingMessages: queue });
    if (enabled) await retryPending();
  };

  const discardOne = async (item: PatientPendingMessage) => {
    const stored = await PatientCompanionStorage.load();
    const queue = (stored.cache[accessId]?.pendingMessages || [])
      .filter(candidate => candidate.clientMessageId !== item.clientMessageId);
    await persist({ pendingMessages: queue });
  };

  const loadOlder = async () => {
    if (!beforeCursor || !hasMore || !pairing.remoteTransport || !enabled || busy) return;
    setBusy(true);
    try {
      const result = await sendMessageCommand(
        pairing,
        'message.sync',
        { before_message_id: beforeCursor },
      );
      if (result.status !== 'ACCEPTED') throw new Error(String(result.result.code || 'Historique indisponible.'));
      await applySync(result.result, true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Historique indisponible.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section
      data-pc08-secure-messaging
      className="mt-4 rounded-[1.5rem] border border-border-main bg-card-bg p-4"
      aria-label="Messages sécurisés Patient Companion"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-primary">
            <ShieldCheck size={16} />
            <p className="text-[10px] font-black uppercase tracking-[0.14em]">Messages sécurisés</p>
          </div>
          <h3 className="mt-1 text-lg font-black">Cabinet</h3>
          <p className="mt-1 text-[11px] font-bold leading-relaxed text-text-muted">
            Conversation asynchrone chiffrée avec votre cabinet. Ce canal n’est pas une messagerie d’urgence.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void syncLatest()}
          disabled={!transportReady || !enabled || busy}
          aria-label="Synchroniser les messages"
          className="grid min-h-11 min-w-11 shrink-0 place-items-center rounded-full border border-border-main bg-background text-primary disabled:opacity-40"
        >
          {busy ? <Loader2 className="animate-spin" size={18} /> : <RefreshCcw size={18} />}
        </button>
      </div>

      {!transportReady && (
        <p className="mt-3 rounded-xl bg-amber-50 px-3 py-2.5 text-[11px] font-black text-amber-800">
          Transport sécurisé non initialisé pour cet accès.
        </p>
      )}

      <button
        type="button"
        onClick={() => setThreadOpen(value => !value)}
        className="mt-3 flex min-h-[48px] w-full items-center justify-between rounded-2xl border border-border-main bg-background px-4 text-left"
      >
        <span>
          <span className="block text-sm font-black">{threadOpen ? 'Fermer la conversation' : 'Ouvrir la conversation'}</span>
          <span className="mt-0.5 block text-[10px] font-bold text-text-muted">
            {messages.length} message{messages.length === 1 ? '' : 's'} · {pending.length} en attente
          </span>
        </span>
        <ChevronDown size={18} className={threadOpen ? 'rotate-180 text-primary' : 'text-text-muted'} />
      </button>

      {threadOpen && (
        <div className="mt-3">
          {hasMore && beforeCursor && (
            <button
              type="button"
              onClick={() => void loadOlder()}
              disabled={!enabled || busy}
              className="mb-3 min-h-[44px] w-full rounded-xl border border-border-main bg-card-bg px-3 text-[11px] font-black text-primary disabled:opacity-50"
            >
              Charger les messages précédents
            </button>
          )}

          <div className="grid max-h-[420px] gap-2 overflow-y-auto pr-1" data-pc08-thread>
            {!messages.length && !pending.length && (
              <div className="rounded-2xl border border-border-main bg-background px-4 py-6 text-center">
                <MessageSquareText size={22} className="mx-auto text-primary" />
                <p className="mt-2 text-sm font-black">Aucun message sécurisé</p>
                <p className="mt-1 text-[11px] font-bold text-text-muted">
                  Vos échanges apparaîtront ici après synchronisation.
                </p>
              </div>
            )}

            {messages.map(item => {
              const outbound = item.senderKind === 'PATIENT';
              return (
                <article
                  key={item.messageId}
                  className={`min-w-0 max-w-[88%] rounded-2xl border px-3.5 py-3 ${outbound
                    ? 'ml-auto border-primary/15 bg-primary/5'
                    : 'mr-auto border-border-main bg-background'}`}
                >
                  <p className="whitespace-pre-wrap break-words [overflow-wrap:anywhere] text-sm font-semibold leading-relaxed text-main">
                    {item.body}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-[9px] font-black text-text-muted">
                    <span>{formatTime(item.createdAt)}</span>
                    <span>·</span>
                    <span>{canonicalStatus(item)}</span>
                  </div>
                </article>
              );
            })}

            {pending.map(item => (
              <article
                key={item.clientMessageId}
                className="ml-auto min-w-0 max-w-[88%] rounded-2xl border border-amber-200 bg-amber-50 px-3.5 py-3"
              >
                <p className="whitespace-pre-wrap break-words [overflow-wrap:anywhere] text-sm font-semibold leading-relaxed text-main">
                  {item.body}
                </p>
                <p className="mt-2 text-[9px] font-black text-amber-800">{pendingStatus(item)}</p>
                <div className="mt-2 flex gap-2">
                  <button
                    type="button"
                    onClick={() => void retryOne(item)}
                    disabled={!transportReady || busy}
                    className="min-h-[44px] rounded-xl border border-amber-300 bg-white px-3 text-[10px] font-black text-amber-900 disabled:opacity-50"
                  >
                    Réessayer
                  </button>
                  <button
                    type="button"
                    onClick={() => void discardOne(item)}
                    disabled={busy}
                    aria-label="Retirer localement"
                    className="grid min-h-[44px] min-w-[44px] place-items-center rounded-xl border border-border-main bg-white text-text-muted disabled:opacity-50"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </article>
            ))}
          </div>

          <div className="mt-3 rounded-2xl border border-border-main bg-background p-3">
            <label className="block">
              <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Votre message</span>
              <textarea
                value={draft}
                onChange={event => setDraft(event.target.value)}
                rows={3}
                placeholder="Écrire au cabinet…"
                className="mt-2 w-full resize-y rounded-xl border border-border-main bg-card-bg px-3 py-3 text-sm font-semibold outline-none focus:border-primary"
              />
            </label>
            <div className="mt-2 flex items-center justify-between gap-3">
              <span className={`text-[9px] font-black ${bytes > MAX_BODY_BYTES ? 'text-rose-700' : 'text-text-muted'}`}>
                {bytes}/{MAX_BODY_BYTES} octets
              </span>
              <button
                type="button"
                onClick={() => void sendDraft()}
                disabled={!canSend}
                className="inline-flex min-h-[48px] items-center justify-center gap-2 rounded-xl bg-primary px-4 text-xs font-black text-white disabled:opacity-40"
              >
                <Send size={15} /> Envoyer
              </button>
            </div>
            {!enabled && transportReady && (
              <p className="mt-2 text-[10px] font-bold text-text-muted">
                Hors connexion, le message reste chiffré sur cet appareil jusqu’à une prochaine synchronisation.
              </p>
            )}
          </div>
        </div>
      )}

      {message && (
        <p role="status" className="mt-3 rounded-xl bg-primary/5 px-3 py-2.5 text-[11px] font-black text-primary">
          {message}
        </p>
      )}
    </section>
  );
}
