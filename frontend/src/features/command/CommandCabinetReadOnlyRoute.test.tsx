import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import type { AppUser } from '../../types';
import { useAuthStore } from '../../stores/useAuthStore';
import type { DashboardAppointment } from '../dashboard/types';
import { isCommandCabinetLabEnabled, projectReadOnlyAppointments } from './command-cabinet-readonly-policy';

const mockToday = vi.hoisted(() => vi.fn());
vi.mock('../dashboard/hooks/useTodayAppointments', () => ({ useTodayAppointments: mockToday }));

import { CommandCabinetReadOnlyRoute, CommandCabinetReadOnlyView } from './CommandCabinetReadOnlyRoute';

const appointment: DashboardAppointment = {
  id: 13, start_time: '2026-10-20T09:15:00', status: 'EN_S_ATTENTE',
  patient_id: 991, patient: { id: 991, nom: 'TEST-NOM', prenom: 'TEST-PRÉNOM' },
};
const userWith = (permissions: Record<string, boolean>) =>
  ({ id: '101', role: 'SECRETAIRE', employer_id: 10, permissions } as unknown as AppUser);

beforeEach(() => {
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false });
  mockToday.mockReset();
  mockToday.mockReturnValue({
    appointments: [appointment], appointmentsState: 'ready', refreshAppointments: vi.fn(),
  });
});
afterEach(() => {
  cleanup();
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false });
});

describe('07-C / real Cabinet read-only boundary', () => {
  it('never enables the Command lab in production or without explicit opt-in', () => {
    expect(isCommandCabinetLabEnabled(false, 'true')).toBe(false);
    expect(isCommandCabinetLabEnabled(false, undefined)).toBe(false);
    expect(isCommandCabinetLabEnabled(true, undefined)).toBe(false);
    expect(isCommandCabinetLabEnabled(true, 'TRUE')).toBe(false);
    expect(isCommandCabinetLabEnabled(true, 'false')).toBe(false);
    expect(isCommandCabinetLabEnabled(true, 'true')).toBe(true);
    const app = fs.readFileSync(path.resolve(__dirname, '../../App.tsx'), 'utf8');
    expect(app).toContain("isCommandCabinetLabEnabled(import.meta.env.DEV, import.meta.env.VITE_COMMAND_CABINET_LAB)");
    expect(app).toMatch(/path="\/command-cabinet-lab" element=\{<PermissionRoute permission="agenda">/);
    expect(app).toContain('<WorkstationModeGate target="protected"><ProtectedRoutes /></WorkstationModeGate>');
  });

  it('denies mounting the API-reading hook without an authenticated user', () => {
    render(<CommandCabinetReadOnlyRoute />);
    expect(screen.getByRole('alert')).toHaveTextContent('non autorisé');
    expect(mockToday).not.toHaveBeenCalled();
  });

  it('denies mounting the API-reading hook when the actor lacks agenda permission', () => {
    useAuthStore.setState({ user: userWith({ agenda: false, patients: true }), isAuthenticated: true, isLoading: false });
    render(<CommandCabinetReadOnlyRoute />);
    expect(screen.getByRole('alert')).toHaveTextContent('non autorisé');
    expect(mockToday).not.toHaveBeenCalled();
  });

  it('keeps appointment time and status from the Dashboard contract without exposing patient details to agenda-only actor', () => {
    useAuthStore.setState({ user: userWith({ agenda: true, patients: false }), isAuthenticated: true, isLoading: false });
    const { container } = render(<CommandCabinetReadOnlyRoute />);
    expect(mockToday).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('command-count')).toHaveTextContent('1');
    expect(within(screen.getByRole('table')).getByText('09:15')).toBeInTheDocument();
    expect(within(screen.getByRole('table')).getByText('EN_S_ATTENTE')).toBeInTheDocument();
    expect(container.textContent).not.toContain('TEST-NOM');
    expect(container.textContent).not.toContain('TEST-PRÉNOM');
    expect(container.textContent).not.toContain('991');
    expect(container.querySelector('input')).toBeNull();
  });

  it('permits patient display only with patients permission, without any mutation controls', () => {
    useAuthStore.setState({ user: userWith({ agenda: true, patients: true }), isAuthenticated: true, isLoading: false });
    render(<CommandCabinetReadOnlyRoute />);
    expect(screen.getByText('TEST-PRÉNOM TEST-NOM')).toBeInTheDocument();
    expect(screen.queryByText(/modifier|terminer le rendez-vous|encaisser/i)).not.toBeInTheDocument();
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(1);
    expect(buttons[0]).toHaveAccessibleName('Actualiser les rendez-vous');
  });

  it('refuses to turn an API failure or malformed response into a false empty agenda', () => {
    const refresh = vi.fn();
    const { rerender } = render(<CommandCabinetReadOnlyView
      appointments={null} appointmentsState="error" canReadPatients onRefresh={refresh}
    />);
    expect(screen.getByRole('alert')).toHaveTextContent('non vérifiables');
    expect(screen.getByTestId('command-count')).toHaveTextContent('—');
    rerender(<CommandCabinetReadOnlyView
      appointments={[{ ...appointment, start_time: 'garbage' }]}
      appointmentsState="ready" canReadPatients onRefresh={refresh}
    />);
    expect(screen.getByRole('alert')).toHaveTextContent('non vérifiables');
    expect(screen.getByTestId('command-count')).toHaveTextContent('—');
    rerender(<CommandCabinetReadOnlyView appointments={[]} appointmentsState="ready" canReadPatients onRefresh={refresh} />);
    expect(screen.getByText("Aucun rendez-vous enregistré pour aujourd'hui.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Actualiser les rendez-vous/i }));
    expect(refresh).toHaveBeenCalledOnce();
  });

  it('hides stale appointments during a subsequent loading state', () => {
    render(<CommandCabinetReadOnlyView
      appointments={[appointment]} appointmentsState="loading" canReadPatients onRefresh={vi.fn()}
    />);
    expect(screen.getByRole('status')).toHaveTextContent('Vérification');
    expect(screen.queryByText('TEST-PRÉNOM TEST-NOM')).not.toBeInTheDocument();
    expect(screen.getByTestId('command-count')).toHaveTextContent('—');
    expect(screen.getByRole('button', { name: /Actualiser les rendez-vous/i })).toBeDisabled();
  });

  it('clears prior patient rows when the signed-in account or cabinet changes', () => {
    mockToday.mockImplementation(({ user }: { user: AppUser }) => {
      const firstActor = user.id === '101';
      return {
        appointments: firstActor ? [appointment] : null,
        appointmentsState: firstActor ? 'ready' : 'loading',
        refreshAppointments: vi.fn(),
      };
    });
    useAuthStore.setState({ user: userWith({ agenda: true, patients: true }), isAuthenticated: true, isLoading: false });
    const { container } = render(<CommandCabinetReadOnlyRoute />);
    expect(screen.getByText('TEST-PRÉNOM TEST-NOM')).toBeInTheDocument();
    const nextActor = { ...userWith({ agenda: true, patients: true }), id: '202', employer_id: 20 } as AppUser;
    act(() => {
      useAuthStore.setState({ user: nextActor, isAuthenticated: true, isLoading: false });
    });
    expect(container.textContent).not.toContain('TEST-NOM');
    expect(screen.getByTestId('command-count')).toHaveTextContent('—');
    expect(mockToday).toHaveBeenCalledWith(expect.objectContaining({ user: nextActor }));
  });

  it('redacts patient names immediately if the patients permission is revoked', () => {
    useAuthStore.setState({ user: userWith({ agenda: true, patients: true }), isAuthenticated: true, isLoading: false });
    const { container } = render(<CommandCabinetReadOnlyRoute />);
    expect(screen.getByText('TEST-PRÉNOM TEST-NOM')).toBeInTheDocument();
    act(() => {
      useAuthStore.setState({ user: userWith({ agenda: true, patients: false }), isAuthenticated: true, isLoading: false });
    });
    expect(container.textContent).not.toContain('TEST-NOM');
    expect(screen.getAllByRole('cell').map((cell) => cell.textContent)).toContain('Rendez-vous');
  });

  it('projects actual FastAPI AppointmentOut schema and does not leak patient_name to agenda-only staff', () => {
    const wire = {
      id: 57, datetime_start: '2026-10-20T09:15:00', status: 'EN_S_ATTENTE',
      patient_name: 'T2-NOM-FICTIF', patient_id: 991, duration_minutes: 30,
    } as unknown as DashboardAppointment;
    expect(projectReadOnlyAppointments([wire], true)).toEqual([{
      id: 57, time: '09:15', status: 'EN_S_ATTENTE', patientLabel: 'T2-NOM-FICTIF',
    }]);
    expect(projectReadOnlyAppointments([wire], false)).toEqual([{
      id: 57, time: '09:15', status: 'EN_S_ATTENTE', patientLabel: 'Rendez-vous',
    }]);
    expect(projectReadOnlyAppointments([{ ...wire, datetime_start: 'fakeT09:15:00' } as DashboardAppointment], true)).toBeNull();
  });

  it('rejects mixed-validity API data and preserves local cabinet clock without UTC shifting', () => {
    expect(projectReadOnlyAppointments([appointment], false)).toEqual([{
      id: 13, time: '09:15', status: 'EN_S_ATTENTE', patientLabel: 'Rendez-vous',
    }]);
    expect(projectReadOnlyAppointments([{ ...appointment, id: -1 }], true)).toBeNull();
    expect(projectReadOnlyAppointments([appointment, { ...appointment, start_time: '2026-10-20T25:90:00' }], true)).toBeNull();
    expect(projectReadOnlyAppointments(null, true)).toBeNull();
  });
});
