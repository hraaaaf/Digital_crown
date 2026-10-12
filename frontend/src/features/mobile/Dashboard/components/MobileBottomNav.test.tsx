import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MobileBottomNav } from './MobileBottomNav';
import type { Snapshot } from '../types';

const SNAPSHOT: Snapshot = {
  generated_at: new Date().toISOString(),
  role: 'DENTISTE',
  is_superadmin: false,
  appointments: [],
  finance: {
    today_revenue: 0,
    month_revenue: 0,
    month_variation: null,
    appointments_count: 0,
    weekly_revenue: [],
    total_patients: 0,
    total_debt: 0,
  },
  debtors: [],
};

afterEach(() => cleanup());

describe('Digital Crown Pocket canonical navigation', () => {
  it('uses granted finance for secretary and withdraws denied read destinations without moving the five buttons', () => {
    const setActiveTab = vi.fn();
    const props = { activeTab: 'today' as const, setActiveTab, totalCount: 3, termineCount: 1, snapshot: { ...SNAPSHOT, role: 'SECRETAIRE' }, quickActionsAvailable: false, quickActionsOpen: false, onToggleQuickActions: vi.fn() };
    const { rerender } = render(<MobileBottomNav {...props} readAccess={{ agenda: true, patients: true, clinical: false, finance: true }} />);
    fireEvent.click(screen.getByText('Plus'));
    fireEvent.click(screen.getByText('Trésorerie'));
    expect(setActiveTab).toHaveBeenCalledWith('finance');
    rerender(<MobileBottomNav {...props} snapshot={SNAPSHOT} readAccess={{ agenda: false, patients: false, clinical: false, finance: false }} />);
    expect(screen.getByRole('button', { name: 'Patients' }).hasAttribute('disabled')).toBe(true);
    expect(screen.getByRole('button', { name: 'Agenda' }).hasAttribute('disabled')).toBe(true);
    expect(document.querySelectorAll('[data-mobile-nav-item]')).toHaveLength(5);
    fireEvent.click(screen.getByText('Plus'));
    for (const label of ['Trésorerie', 'Stock', 'Notifications', 'Salle d’attente', 'Envois Labo']) expect(screen.queryByText(label)).toBeNull();
    expect(screen.getByText('Sécurité')).toBeTruthy();
  });
  it('renders the five-entry Pocket navigation and opens Patients directly', () => {
    const setActiveTab = vi.fn();
    const onToggleQuickActions = vi.fn();

    render(
      <MobileBottomNav readAccess={{ agenda: true, patients: true, clinical: true, finance: true }} activeTab="today" setActiveTab={setActiveTab} totalCount={4} termineCount={1} snapshot={SNAPSHOT} quickActionsAvailable quickActionsOpen={false} onToggleQuickActions={onToggleQuickActions} />,
    );

    expect(screen.getByText('Aujourd’hui')).toBeTruthy();
    expect(screen.getByText('Agenda')).toBeTruthy();
    expect(screen.getByText('Patients')).toBeTruthy();
    expect(screen.queryByText('Assistant')).toBeNull();
    expect(screen.getByText('Plus')).toBeTruthy();
    expect(screen.queryByText('Alertes')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }));
    expect(onToggleQuickActions).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText('Patients'));
    expect(setActiveTab).toHaveBeenCalledWith('patients');

    fireEvent.click(screen.getByText('Agenda'));
    expect(setActiveTab).toHaveBeenCalledWith('agenda');
  });

  it('renders one aligned WhatsApp-inspired glass row and slides the selection between tabs', () => {
    const props = {
      setActiveTab: vi.fn(), totalCount: 1, termineCount: 0, snapshot: SNAPSHOT,
      quickActionsAvailable: true, onToggleQuickActions: vi.fn(),
    };
    const { rerender } = render(<MobileBottomNav readAccess={{ agenda: true, patients: true, clinical: true, finance: true }} {...props} activeTab="today" quickActionsOpen={false} />);
    const nav = document.querySelector('[data-mobile-bottom-nav]') as HTMLElement;
    const targets = [...nav.querySelectorAll<HTMLButtonElement>('[data-mobile-nav-item]')];
    const indicator = nav.querySelector<HTMLElement>('[data-mobile-nav-indicator]');

    expect(nav.hasAttribute('data-pocket-glass-nav')).toBe(true);
    expect(nav.getAttribute('style')).toContain('var(--card-bg)');
    expect(targets.map(target => target.dataset.mobileNavItem)).toEqual([
      'today', 'agenda', 'actions', 'patients', 'more',
    ]);
    expect(targets.every(target => target.className.includes('min-h-[54px]'))).toBe(true);
    expect(targets[2].className).not.toContain('absolute');
    expect(targets[2].className).not.toContain('-top-2.5');
    expect(targets[2].textContent).toContain('Actions');
    expect(indicator?.style.transform).toBe('translate(0%, -50%)');

    rerender(<MobileBottomNav readAccess={{ agenda: true, patients: true, clinical: true, finance: true }} {...props} activeTab="patients" quickActionsOpen={false} />);
    expect(indicator?.style.transform).toBe('translate(300%, -50%)');

    rerender(<MobileBottomNav readAccess={{ agenda: true, patients: true, clinical: true, finance: true }} {...props} activeTab="patients" quickActionsOpen />);
    expect(indicator?.style.transform).toBe('translate(200%, -50%)');
    expect(screen.getByRole('button', { name: 'Fermer les actions rapides' })).toBeTruthy();
  });

  it('restores merged Pocket V1 secondary destinations for practitioners', () => {
    const setActiveTab = vi.fn();
    render(
      <MobileBottomNav readAccess={{ agenda: true, patients: true, clinical: true, finance: true }} activeTab="today" setActiveTab={setActiveTab} totalCount={0} termineCount={0} snapshot={SNAPSHOT} quickActionsAvailable quickActionsOpen={false} onToggleQuickActions={() => undefined} />,
    );

    fireEvent.click(screen.getByText('Plus'));
    expect(screen.getByText('Salle d’attente')).toBeTruthy();
    expect(screen.getByText('Notifications')).toBeTruthy();
    expect(screen.getByText('Accueil')).toBeTruthy();
    expect(screen.getByText('Sécurité')).toBeTruthy();
    expect(screen.getByText('Stock')).toBeTruthy();
    expect(screen.getByText('Bibliothèque')).toBeTruthy();
    expect(screen.getByText('Approvisionnement')).toBeTruthy();
    expect(screen.getByText('Trésorerie')).toBeTruthy();
    expect(screen.getByText('Envois Labo')).toBeTruthy();
    expect(screen.getByText('Équipe')).toBeTruthy();
    expect(screen.getByText('Assistant · En cours de construction')).toBeTruthy();

    // The Safari sheet must be solid, readable and touch-friendly over clinical content.
    const dialog = screen.getByRole('dialog', { name: 'Plus' });
    expect(dialog.getAttribute('style')).toContain('var(--card-bg)');
    expect(dialog.className).toContain('bg-card');
    const stockItem = screen.getByRole('button', { name: 'Stock' });
    expect(stockItem.className).toContain('min-h-[54px]');
    expect(stockItem.querySelector('span.flex-1')?.className).toContain('text-[14px]');
    const nav = document.querySelector('[data-mobile-bottom-nav]') as HTMLElement;
    expect(nav.getAttribute('style')).toContain('var(--card-bg)');

    fireEvent.click(screen.getByText('Salle d’attente'));
    expect(setActiveTab).toHaveBeenCalledWith('waiting-room');
    expect(screen.queryByText('Accès secondaires')).toBeNull();
  });

  it('traps focus inside Plus and restores it to the trigger on Escape', () => {
    render(
      <MobileBottomNav readAccess={{ agenda: true, patients: true, clinical: true, finance: true }} activeTab="today" setActiveTab={() => undefined} totalCount={0} termineCount={0} snapshot={SNAPSHOT} quickActionsAvailable quickActionsOpen={false} onToggleQuickActions={() => undefined} />,
    );

    const trigger = screen.getByText('Plus').closest('button') as HTMLButtonElement;
    const nav = document.querySelector('[data-mobile-bottom-nav]') as HTMLElement;
    expect(nav.hasAttribute('inert')).toBe(false);
    fireEvent.click(trigger);
    // A modal cannot leave the higher z-index bottom bar pointer/keyboard active.
    expect(nav.hasAttribute('inert')).toBe(true);

    const close = screen.getByRole('button', { name: 'Fermer Plus' });
    expect(document.activeElement).toBe(close);

    const firstItem = screen.getByRole('button', { name: 'Salle d’attente' });
    const lastItem = screen.getByRole('button', { name: 'Sécurité' });
    lastItem.focus();
    fireEvent.keyDown(window, { key: 'Tab' });
    expect(document.activeElement).toBe(close);

    close.focus();
    fireEvent.keyDown(window, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(lastItem);

    firstItem.focus();
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(screen.queryByText('Accès secondaires')).toBeNull();
    expect(nav.hasAttribute('inert')).toBe(false);
    expect(document.activeElement).toBe(trigger);
  });

  it('gives secretary the same bounded Pocket secondary shell', () => {
    render(
      <MobileBottomNav activeTab="today" setActiveTab={() => undefined} totalCount={0} termineCount={0} snapshot={{ ...SNAPSHOT, role: 'SECRETAIRE' }} readAccess={{ agenda: true, patients: true, clinical: false, finance: false }} quickActionsAvailable={false} quickActionsOpen={false} onToggleQuickActions={() => undefined} />,
    );

    expect(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }).hasAttribute('disabled')).toBe(true);
    fireEvent.click(screen.…8237 tokens truncated… Bell, CalendarDays, CheckCircle2, ChevronRight, Clock3, UsersRound } from 'lucide-react';
import type { Appointment, Snapshot } from '../types';

function localDateKey(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function timeMinutes(value: string): number {
  const [hour, minute] = value.split(':').map(Number);
  if (!Number.isFinite(hour) || !Number.isFinite(minute)) return Number.POSITIVE_INFINITY;
  return hour * 60 + minute;
}

export function nextOperationalAppointment(
  appointments: Appointment[],
  selectedDate: string,
  now = new Date(),
): Appointment | null {
  const today = localDateKey(now);
  if (selectedDate < today) return null;

  const actionable = appointments.filter((appointment) => (
    Boolean(appointment.patient_id)
    && appointment.status !== 'TERMINE'
    && appointment.status !== 'ANNULE'
  ));

  if (selectedDate > today) {
    return actionable
      .slice()
      .sort((a, b) => timeMinutes(a.time) - timeMinutes(b.time) || a.id - b.id)[0] ?? null;
  }

  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const rank = (appointment: Appointment): number => {
    if (appointment.status === 'EN_COURS') return 0;
    if (appointment.status === 'EN_ATTENTE') return 1;
    if (appointment.status === 'PLANIFIE' && timeMinutes(appointment.time) >= currentMinutes) return 2;
    return 99;
  };

  return actionable
    .filter((appointment) => rank(appointment) < 99)
    .slice()
    .sort((a, b) => rank(a) - rank(b) || timeMinutes(a.time) - timeMinutes(b.time) || a.id - b.id)[0] ?? null;
}

export function PocketTodayOverview({
  snapshot,
  selectedDate,
  onOpenPatient,
  onOpenWaitingRoom,
  onOpenFrontdesk,
  onOpenAlerts,
  canOpenPatient = true,
}: {
  snapshot: Snapshot | null;
  selectedDate: string;
  onOpenPatient: (patientId: number) => void;
  onOpenWaitingRoom: () => void;
  onOpenFrontdesk: () => void;
  onOpenAlerts: () => void;
  canOpenPatient?: boolean;
}) {
  const appointments = snapshot?.appointments ?? [];
  const role = snapshot?.role ?? 'DENTISTE';
  const isAssistant = role === 'SECRETAIRE';
  const waitingCount = appointments.filter((appointment) => appointment.status === 'EN_ATTENTE').length;
  const completedCount = appointments.filter((appointment) => appointment.status === 'TERMINE').length;
  const nextAppointment = nextOperationalAppointment(appointments, selectedDate);
  const remainingCount = appointments.filter(
    (appointment) => appointment.status !== 'TERMINE' && appointment.status !== 'ANNULE',
  ).length;
  const localToday = localDateKey();
  const isToday = selectedDate === localToday;
  const selectedDateLabel = (() => {
    const parsed = new Date(`${selectedDate}T12:00:00`);
    if (Number.isNaN(parsed.getTime())) return 'Journée sélectionnée';
    return `Journée du ${parsed.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}`;
  })();
  const compactAgenda = appointments
    .filter((appointment) => appointment.status !== 'ANNULE')
    .slice()
    .sort((a, b) => timeMinutes(a.time) - timeMinutes(b.time) || a.id - b.id);

  return (
    <section
      data-dc-pocket-today
      data-dc-pocket-role={isAssistant ? 'assistant' : 'practitioner'}
      className="mb-5 space-y-3.5"
    >
      <div className="rounded-[24px] border border-border-main bg-card p-4 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.11em] text-primary">Digital Crown Pocket</p>
            <h1 className="mt-1 text-[24px] font-bold tracking-tight text-text-main">
              {isToday ? 'Aujourd’hui' : selectedDateLabel}
            </h1>
            <p className="mt-1 text-[13px] font-medium text-text-muted">
              {isAssistant ? 'Vue assistante · flux cabinet' : 'Vue praticien · priorité clinique'}
            </p>
          </div>
          <div className="grid h-12 w-12 shrink-0 place-items-center rounded-[17px] border border-primary/10 bg-primary/5 text-primary">
            {isAssistant ? <UsersRound size={21} /> : <Clock3 size={21} />}
          </div>
        </div>

        <div className="mt-3 grid grid-cols-3 gap-2">
          <div className="rounded-[17px] border border-border-main bg-background px-3 py-3">
            <CalendarDays size={14} className="text-primary" />
            <p className="mt-2 text-[20px] font-bold text-text-main">{appointments.length}</p>
            <p className="text-[12px] font-bold uppercase tracking-wide text-text-muted">RDV</p>
          </div>
          <button
            type="button"
            onClick={onOpenWaitingRoom}
            data-dc-pocket-waiting-count={waitingCount}
            className="rounded-[17px] border border-warning-border bg-warning-surface px-3 py-3 text-left active:scale-[0.98]"
          >
            <UsersRound size={14} className="text-warning" />
            <p className="mt-2 text-[20px] font-bold text-text-main">{waitingCount}</p>
            <p className="text-[12px] font-bold uppercase tracking-wide text-text-muted">Attente</p>
          </button>
          <div
            data-dc-pocket-progress-count={isAssistant ? remainingCount : completedCount}
            className="rounded-[17px] border border-success-border bg-success-surface px-3 py-3"
          >
            <CheckCircle2 size={14} className="text-success" />
            <p className="mt-2 text-[20px] font-bold text-text-main">{isAssistant ? remainingCount : completedCount}</p>
            <p className="text-[12px] font-bold uppercase tracking-wide text-text-muted">
              {isAssistant ? 'À gérer' : 'Terminés'}
            </p>
          </div>
        </div>
      </div>

      {!isAssistant && nextAppointment && (
        <article className="rounded-[24px] border border-primary/15 bg-card p-4 shadow-sm" style={{ backgroundColor: 'var(--card-bg)' }}>
          <div className="flex items-start gap-3">
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-[16px] bg-primary/10 text-primary">
              <span className="text-[12px] font-black">{nextAppointment.time}</span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[12px] font-bold uppercase tracking-[0.09em] text-primary">
                {selectedDate > localToday
                  ? 'Premier patient'
                  : nextAppointment.status === 'EN_COURS'
                    ? 'Patient en cours'
                    : nextAppointment.status === 'EN_ATTENTE'
                      ? 'Patient en attente'
                      : 'Prochain patient'}
              </p>
              <h2 className="mt-1 truncate text-[17px] font-bold text-text-main">{nextAppointment.patient_name}</h2>
              <p className="mt-0.5 truncate text-[12px] font-medium text-text-muted">
                {nextAppointment.motif} · {nextAppointment.duration_minutes} min
              </p>
            </div>
          </div>
          <button
            type="button"
            disabled={!canOpenPatient || !nextAppointment.patient_id}
            onClick={() => nextAppointment.patient_id && onOpenPatient(nextAppointment.patient_id)}
            className="mt-4 flex min-h-[52px] w-full items-center justify-center gap-2 rounded-[16px] bg-primary px-4 text-[14px] font-semibold text-on-primary disabled:cursor-not-allowed disabled:opacity-40"
          >
            Ouvrir le dossier <ChevronRight size={15} />
          </button>
        </article>
      )}

      <div className={`grid gap-2 ${isAssistant ? 'grid-cols-3' : 'grid-cols-2'}`}>
        <button
          type="button"
          onClick={onOpenWaitingRoom}
          className="min-h-[52px] rounded-[16px] border border-glass-border bg-card px-3 text-[13px] font-semibold text-text-main shadow-sm active:scale-[0.98]"
        >
          Salle d’attente
        </button>
        {isAssistant && (
          <button
            type="button"
            onClick={onOpenFrontdesk}
            className="min-h-[52px] rounded-[16px] border border-glass-border bg-card px-3 text-[13px] font-semibold text-text-main shadow-sm active:scale-[0.98]"
          >
            Accueil
          </button>
        )}
        <button
          type="button"
          onClick={onOpenAlerts}
          disabled={!canOpenPatient}
          className="flex min-h-[52px] items-center justify-center gap-1.5 rounded-[16px] border border-glass-border bg-card px-3 text-[13px] font-semibold text-text-main shadow-sm active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Bell size={13} /> Alertes
        </button>
      </div>

      <div
        data-dc-pocket-compact-agenda
        className="overflow-hidden rounded-[24px] border border-glass-border bg-card shadow-sm"
        style={{ backgroundColor: 'var(--card-bg)' }}
      >
        <div className="flex items-center justify-between gap-3 border-b border-border-main px-4 py-3">
          <div>
            <p className="text-[12px] font-bold uppercase tracking-[0.09em] text-primary">
              {isToday ? 'Agenda du jour' : 'Agenda sélectionné'}
            </p>
            <p className="mt-0.5 text-[12px] font-medium text-text-muted">
              {isAssistant ? 'Vue opérationnelle' : 'Lecture rapide avant le fauteuil'}
            </p>
          </div>
          <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">
            {compactAgenda.length} RDV
          </span>
        </div>

        {compactAgenda.length === 0 ? (
          <p className="px-4 py-6 text-center text-[12px] font-medium text-text-muted">
            Aucun rendez-vous pour cette journée.
          </p>
        ) : (
          <div className="divide-y divide-border-main">
            {compactAgenda.map((appointment) => {
              const content = (
                <>
                  <div className="w-12 shrink-0 text-[12px] font-semibold text-primary">{appointment.time}</div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[14px] font-semibold text-text-main">{appointment.patient_name}</p>
                    <p className="mt-0.5 truncate text-[12px] font-medium text-text-muted">
                      {appointment.motif || 'Rendez-vous'} · {(appointment.status || 'PLANIFIE').replace('_', ' ')}
                    </p>
                  </div>
                  {canOpenPatient && !isAssistant && appointment.patient_id && <ChevronRight size={15} className="shrink-0 text-text-muted" />}
                </>
              );

              return canOpenPatient && !isAssistant && appointment.patient_id ? (
                <button
                  key={appointment.id}
                  type="button"
                  aria-label={`Ouvrir ${appointment.patient_name}`}
                  onClick={() => onOpenPatient(appointment.patient_id as number)}
                  className="flex min-h-[64px] w-full items-center gap-3 px-4 py-2.5 text-left active:bg-primary/5"
                >
                  {content}
                </button>
              ) : (
                <div key={appointment.id} className="flex min-h-[64px] items-center gap-3 px-4 py-2.5">
                  {content}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
