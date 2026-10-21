/** LOT07 / 07-C — real Cabinet auth + read-only Dashboard parity, development opt-in only.
 * This is NOT the isolated synthetic Command target nor an experience selector.
 */
import { useMemo } from 'react';
import { CalendarDays, LockKeyhole, RefreshCw, ShieldCheck } from 'lucide-react';
import type { AppUser } from '../../types';
import { useAuthStore } from '../../stores/useAuthStore';
import { hasAccess } from '../../utils/accessControl';
import { useTodayAppointments } from '../dashboard/hooks/useTodayAppointments';
import type { DashboardAppointment, DataState } from '../dashboard/types';
import { projectReadOnlyAppointments } from './command-cabinet-readonly-policy';

type PreviewProps = {
  appointments: DashboardAppointment[] | null;
  appointmentsState: DataState;
  canReadPatients: boolean;
  onRefresh: () => void;
};

export function CommandCabinetReadOnlyView({
  appointments, appointmentsState, canReadPatients, onRefresh,
}: PreviewProps) {
  const projected = useMemo(
    () => projectReadOnlyAppointments(appointments, canReadPatients),
    [appointments, canReadPatients],
  );
  const ready = appointmentsState === 'ready' && projected !== null;
  const error = appointmentsState === 'error' || (appointmentsState === 'ready' && projected === null);

  return (
    <section
      data-testid="command-cabinet-readonly"
      data-experience="command-cabinet-07c-lab"
      className="min-w-0 space-y-4 text-text-main"
      aria-label="Command, aperçu Cabinet en lecture seule"
    >
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-border-main pb-4">
        <div className="space-y-1">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">Digital Crown / Command</p>
          <h1 className="text-2xl font-black tracking-tight">Cockpit Cabinet</h1>
          <p className="text-sm text-text-muted">
            <ShieldCheck size={15} className="mr-1 inline-block" aria-hidden="true" />
            Laboratoire 07-C · Lecture seule · Données depuis Cabinet
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={appointmentsState === 'loading'}
          aria-label="Actualiser les rendez-vous"
          className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-border-main bg-card-bg px-4 py-2 text-xs font-semibold text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50"
        >
          <RefreshCw size={16} aria-hidden="true" /> Actualiser
        </button>
      </header>
      <div className="grid min-w-0 gap-3 lg:grid-cols-[minmax(0,230px)_minmax(0,1fr)]">
        <aside className="rounded-xl border border-border-main bg-card-bg p-4" aria-label="Résumé en lecture seule">
          <CalendarDays size={20} className="text-primary" aria-hidden="true" />
          <p className="mt-3 text-xs uppercase tracking-wider text-text-muted">Rendez-vous du jour</p>
          <p className="mt-1 text-3xl font-black" data-testid="command-count">
            {ready ? projected.length : '—'}
          </p>
          <p className="mt-3 text-xs text-text-muted">Même source d'agenda que Signature. Aucune modification de statut possible ici.</p>
        </aside>
        <section className="min-w-0 overflow-hidden rounded-xl border border-border-main bg-card-bg" aria-label="Agenda compact">
          <div className="border-b border-border-main px-4 py-3">
            <h2 className="text-sm font-bold">Agenda compact · aujourd'hui</h2>
          </div>
          {appointmentsState === 'loading' || appointmentsState === 'idle' ? (
            <p role="status" className="p-5 text-sm text-text-muted">Vérification des rendez-vous en cours…</p>
          ) : error ? (
            <p role="alert" className="p-5 text-sm text-text-main">
              Données de l'agenda non vérifiables. Aucun état vide n'est supposé.
            </p>
          ) : ready && projected.length === 0 ? (
            <p role="status" className="p-5 text-sm text-text-muted">Aucun rendez-vous enregistré pour aujourd'hui.</p>
          ) : ready ? (
            <div className="max-h-[65vh] overflow-auto">
              <table className="w-full min-w-[330px] border-collapse text-left text-xs">
                <caption className="sr-only">Rendez-vous du jour, en lecture seule</caption>
                <thead className="sticky top-0 bg-card-bg text-text-muted">
                  <tr>
                    <th scope="col" className="px-4 py-3 font-semibold">Heure</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Rendez-vous</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Statut Cabinet</th>
                  </tr>
                </thead>
                <tbody>
                  {projected.map((appointment) => (
                    <tr key={appointment.id} className="border-t border-border-main">
                      <td className="whitespace-nowrap px-4 py-3 font-bold tabular-nums">{appointment.time}</td>
                      <td className="max-w-[280px] truncate px-4 py-3">{appointment.patientLabel}</td>
                      <td className="px-4 py-3">{appointment.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      </div>
      <p className="flex items-center gap-2 text-xs text-text-muted">
        <LockKeyhole size={14} aria-hidden="true" />
        Aucun accès au dossier clinique, imagerie, facturation ou écriture depuis cet aperçu.
      </p>
    </section>
  );
}

const noopStatsRefresh = async (): Promise<void> => {};
const noopCompleted = (): void => {};

function CommandCabinetReadOnlySession({ user }: { user: AppUser }) {
  const { appointments, appointmentsState, refreshAppointments } = useTodayAppointments({
    user, authLoading: false, onStatsRefresh: noopStatsRefresh, onCompleted: noopCompleted,
  });
  return <CommandCabinetReadOnlyView
    appointments={appointments}
    appointmentsState={appointmentsState}
    canReadPatients={hasAccess(user, 'patients')}
    onRefresh={() => { void refreshAppointments(); }}
  />;
}

export function CommandCabinetReadOnlyRoute() {
  const user = useAuthStore((state) => state.user);
  const authenticated = useAuthStore((state) => state.isAuthenticated);
  const loading = useAuthStore((state) => state.isLoading);

  // In addition to App's ProtectedRoute, WorkstationModeGate and PermissionRoute:
  // do not mount the data-fetching hook before identity and agenda permission.
  if (loading || !authenticated || !user || !hasAccess(user, 'agenda')) {
    return <p role="alert">Accès au cockpit Command non autorisé.</p>;
  }
  // No Command/Pocket surface. CSS viewport width is deliberately not used here:
  // Desktop zoom 200% must remain supported without being mistaken for a phone.
  if (typeof navigator !== 'undefined' && /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)) {
    return <p role="status">Prévisualisation Command réservée au Cabinet Desktop.</p>;
  }
  // Remount on account/tenant/role change to discard previous in-flight hook state.
  const identityKey = `${user.id}:${user.employer_id ?? 'owner'}:${user.role}`;
  return <CommandCabinetReadOnlySession key={identityKey} user={user} />;
}
