import { useEffect, useMemo, useState } from 'react';
import { Bell, Check, Clock3, Loader2, Settings2 } from 'lucide-react';

import { API_BASE } from '../../services/api';
import type { PatientPairing } from './PatientCompanionStorage';
import { PatientCompanionNotificationTransport } from './PatientCompanionNotificationTransport';

export type PatientNotification = {
  notification_id: string;
  category: 'appointments' | 'documents' | 'questionnaires' | 'consents';
  kind: string;
  title: string;
  message: string;
  created_at?: string | null;
  due_at?: string | null;
  priority: 'action' | 'reminder' | 'info';
};

export type PatientNotificationPreferences = {
  appointments: boolean;
  documents: boolean;
  questionnaires: boolean;
  consents: boolean;
};

type NotificationResponse = {
  items: PatientNotification[];
  preferences: PatientNotificationPreferences;
};

const defaultPreferences: PatientNotificationPreferences = {
  appointments: true,
  documents: true,
  questionnaires: true,
  consents: true,
};

const categoryLabel: Record<keyof PatientNotificationPreferences, string> = {
  appointments: 'Rendez-vous',
  documents: 'Documents',
  questionnaires: 'Questionnaires',
  consents: 'Consentements',
};

const priorityLabel = (value: PatientNotification['priority']) => {
  if (value === 'action') return 'Action requise';
  if (value === 'reminder') return 'Rappel';
  return 'Information';
};

const dueLabel = (value?: string | null) => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString([], {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export function PatientCompanionNotifications({
  pairing,
  enabled,
}: {
  pairing: PatientPairing;
  enabled: boolean;
}) {
  const [items, setItems] = useState<PatientNotification[]>([]);
  const [preferences, setPreferences] = useState<PatientNotificationPreferences>(defaultPreferences);
  const [draftPreferences, setDraftPreferences] = useState<PatientNotificationPreferences>(defaultPreferences);
  const [loading, setLoading] = useState(false);
  const [mutatingId, setMutatingId] = useState<string | null>(null);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [message, setMessage] = useState('');

  const unreadCount = items.length;
  const hasPreferenceChanges = useMemo(
    () => Object.keys(defaultPreferences).some(
      key => draftPreferences[key as keyof PatientNotificationPreferences]
        !== preferences[key as keyof PatientNotificationPreferences],
    ),
    [draftPreferences, preferences],
  );

  const load = async () => {
    if (!enabled) return;
    setLoading(true);
    setMessage('');
    try {
      const accessId = encodeURIComponent(pairing.context.access_id);
      const response = await fetch(
        `${API_BASE}/api/patient-companion/contexts/${accessId}/notifications`,
        {
          headers: { Authorization: `Bearer ${pairing.accessToken}` },
          cache: 'no-store',
        },
      );
      const body = await response.json().catch(() => ({}));
      if (!response.ok || !Array.isArray(body.items) || typeof body.preferences !== 'object') {
        throw new Error(body.detail || 'Notifications indisponibles.');
      }
      const nextPreferences = {
        appointments: body.preferences.appointments !== false,
        documents: body.preferences.documents !== false,
        questionnaires: body.preferences.questionnaires !== false,
        consents: body.preferences.consents !== false,
      };
      setItems(body.items);
      setPreferences(nextPreferences);
      setDraftPreferences(nextPreferences);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Notifications indisponibles.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!enabled) return;
    void load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, pairing.context.access_id, pairing.accessToken]);

  const mutate = async (item: PatientNotification, operation: 'notification.read' | 'notification.snooze') => {
    setMutatingId(item.notification_id);
    setMessage('');
    try {
      const result = await PatientCompanionNotificationTransport.sendNotificationCommand(
        pairing,
        operation,
        { notification_id: item.notification_id },
      );
      const expectedCode = operation === 'notification.read'
        ? 'NOTIFICATION_READ'
        : 'NOTIFICATION_SNOOZED';
      if (result.status !== 'ACCEPTED' || result.result.code !== expectedCode) {
        throw new Error(String(result.result.code || 'Action refusée par le cabinet.'));
      }
      await load();
      setMessage(
        operation === 'notification.read'
          ? 'Notification marquée comme lue par le cabinet.'
          : 'Rappel reporté de 24 h par le cabinet.',
      );
    } catch (error) {
      const pending = Boolean((error as { remotePending?: boolean } | null)?.remotePending);
      setMessage(
        pending
          ? 'Action transmise · confirmation cabinet encore en attente. L’état n’a pas été modifié.'
          : error instanceof Error
            ? error.message
            : 'Action non enregistrée.',
      );
    } finally {
      setMutatingId(null);
    }
  };

  const savePreferences = async () => {
    setSavingPreferences(true);
    setMessage('');
    try {
      const result = await PatientCompanionNotificationTransport.sendNotificationCommand(
        pairing,
        'notification.preferences',
        draftPreferences,
      );
      if (
        result.status !== 'ACCEPTED'
        || result.result.code !== 'NOTIFICATION_PREFERENCES_UPDATED'
        || typeof result.result.preferences !== 'object'
      ) {
        throw new Error(String(result.result.code || 'Préférences refusées par le cabinet.'));
      }
      await load();
      setSettingsOpen(false);
      setMessage('Préférences enregistrées par le cabinet.');
    } catch (error) {
      const pending = Boolean((error as { remotePending?: boolean } | null)?.remotePending);
      setDraftPreferences(preferences);
      setMessage(
        pending
          ? 'Préférences transmises · confirmation cabinet encore en attente. Les réglages précédents restent actifs.'
          : error instanceof Error
            ? error.message
            : 'Préférences non enregistrées.',
      );
    } finally {
      setSavingPreferences(false);
    }
  };

  return (
    <section
      data-pc05-notifications
      className="mt-4 rounded-[1.5rem] border border-border-main bg-card-bg p-4"
      aria-label="Notifications Patient Companion"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-black uppercase tracking-[0.14em] text-primary">À ne pas manquer</p>
          <h3 className="mt-0.5 text-lg font-black">Notifications</h3>
          <p className="mt-1 text-[11px] font-bold text-text-muted">
            {enabled ? `${unreadCount} à traiter` : 'Synchronisation requise'}
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <span className="grid min-h-11 min-w-11 place-items-center rounded-full bg-primary/5 text-primary" aria-hidden="true">
            <Bell size={20} />
          </span>
          <button
            type="button"
            aria-label="Régler les notifications"
            onClick={() => {
              setDraftPreferences(preferences);
              setSettingsOpen(current => !current);
            }}
            disabled={!enabled}
            className="grid min-h-11 min-w-11 place-items-center rounded-full border border-border-main bg-background text-text-muted disabled:opacity-50"
          >
            <Settings2 size={18} />
          </button>
        </div>
      </div>

      {!enabled && (
        <p className="mt-3 text-xs font-bold text-text-muted">
          Synchronisez votre espace pour consulter les rappels et actions en attente.
        </p>
      )}

      {enabled && loading && (
        <div className="mt-3 flex min-h-[48px] items-center gap-2 text-xs font-black text-text-muted">
          <Loader2 className="animate-spin" size={16} /> Chargement…
        </div>
      )}

      {enabled && settingsOpen && (
        <div data-pc05-settings className="mt-3 rounded-2xl border border-primary/15 bg-primary/5 p-3">
          <p className="text-xs font-black">Choisir mes catégories</p>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {(Object.keys(categoryLabel) as Array<keyof PatientNotificationPreferences>).map(key => (
              <label
                key={key}
                className="flex min-h-[48px] items-center gap-2 rounded-xl border border-border-main bg-card-bg px-3 text-[11px] font-black"
              >
                <input
                  type="checkbox"
                  checked={draftPreferences[key]}
                  onChange={event => setDraftPreferences(current => ({ ...current, [key]: event.target.checked }))}
                  className="h-4 w-4"
                />
                <span>{categoryLabel[key]}</span>
              </label>
            ))}
          </div>
          <button
            type="button"
            disabled={!hasPreferenceChanges || savingPreferences}
            onClick={() => void savePreferences()}
            className="mt-3 min-h-[48px] w-full rounded-xl bg-primary px-3 text-xs font-black text-white disabled:opacity-50"
          >
            {savingPreferences ? 'Enregistrement…' : 'Enregistrer les préférences'}
          </button>
          <p className="mt-2 text-[10px] font-bold text-text-muted">
            Les réglages restent inchangés tant que le cabinet n’a pas accusé réception.
          </p>
        </div>
      )}

      {enabled && !loading && items.length === 0 && (
        <div className="mt-3 rounded-2xl border border-border-main bg-background px-4 py-5 text-center">
          <Check size={20} className="mx-auto text-primary" />
          <p className="mt-2 text-sm font-black">Tout est à jour</p>
          <p className="mt-1 text-[11px] font-bold text-text-muted">Aucune action ou rappel actif.</p>
        </div>
      )}

      <div className="mt-3 grid gap-2">
        {items.map(item => {
          const busy = mutatingId === item.notification_id;
          const due = dueLabel(item.due_at);
          return (
            <article
              key={item.notification_id}
              className="rounded-2xl border border-border-main bg-background p-3.5"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <span className="inline-flex rounded-full bg-primary/5 px-2 py-1 text-[9px] font-black text-primary">
                    {priorityLabel(item.priority)}
                  </span>
                  <p className="mt-2 text-sm font-black">{item.title}</p>
                  <p className="mt-1 text-[11px] font-semibold leading-relaxed text-text-muted">{item.message}</p>
                  {due && <p className="mt-1 text-[10px] font-black text-text-muted">{due}</p>}
                </div>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void mutate(item, 'notification.read')}
                  className="flex min-h-[48px] items-center justify-center gap-1.5 rounded-xl bg-primary px-2 text-[11px] font-black text-white disabled:opacity-50"
                >
                  <Check size={14} /> Lu
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void mutate(item, 'notification.snooze')}
                  className="flex min-h-[48px] items-center justify-center gap-1.5 rounded-xl border border-border-main bg-card-bg px-2 text-[11px] font-black disabled:opacity-50"
                >
                  <Clock3 size={14} /> 24 h
                </button>
              </div>
            </article>
          );
        })}
      </div>

      {message && (
        <p role="status" className="mt-3 rounded-xl bg-amber-50 px-3 py-2.5 text-[11px] font-black text-amber-800">
          {message}
        </p>
      )}
    </section>
  );
}
