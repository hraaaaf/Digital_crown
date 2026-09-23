import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ClinicPractitionerBar } from './ClinicPractitionerBar';
import { api } from '../../services/api';

const s = vi.hoisted(() => ({
  user: { id: 7, role: 'ADMIN', employer_id: null, nom_complet: 'Dr Owner' } as any,
  practitioners: [{ id: 7, name: 'Dr Owner', appointmentCount: 2 }, { id: 8, name: 'Dr Associate', appointmentCount: 1 }] as any[],
  selectedPractitionerId: 7 as number | null,
  setPractitioners: vi.fn(),
  selectPractitioner: vi.fn(),
}));

vi.mock('../../services/api', () => ({ api: { get: vi.fn() } }));
vi.mock('../../stores/useAuthStore', () => ({ useAuthStore: (selector: any) => selector({ user: s.user }) }));
vi.mock('./practitionerContext', () => ({
  usePractitionerContextStore: (selector: any) => selector({
    practitioners: s.practitioners,
    selectedPractitionerId: s.selectedPractitionerId,
    setPractitioners: s.setPractitioners,
    selectPractitioner: s.selectPractitioner,
  }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  s.user = { id: 7, role: 'ADMIN', employer_id: null, nom_complet: 'Dr Owner' };
  vi.mocked(api.get).mockResolvedValue({ data: { dentists: [
    { dentist_id: 7, dentist_name: 'Dr Owner', appointments: [{}, {}] },
    { dentist_id: 8, dentist_name: 'Dr Associate', appointments: [{}] },
  ] } } as never);
});
afterEach(() => cleanup());

describe('ClinicPractitionerBar G5', () => {
  it('loads practitioner truth and selects an explicit practitioner', async () => {
    render(<MemoryRouter initialEntries={['/agenda']}><ClinicPractitionerBar /></MemoryRouter>);
    await waitFor(() => expect(s.setPractitioners).toHaveBeenCalledWith([
      { id: 7, name: 'Dr Owner', appointmentCount: 2 },
      { id: 8, name: 'Dr Associate', appointmentCount: 1 },
    ]));
    fireEvent.click(screen.getByRole('button', { name: /Dr Associate/i }));
    expect(s.selectPractitioner).toHaveBeenCalledWith({ id: 8, name: 'Dr Associate', appointmentCount: 1 });
  });

  it('falls back to owner identity when multi-practitioner read fails', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('unavailable'));
    render(<MemoryRouter initialEntries={['/agenda']}><ClinicPractitionerBar /></MemoryRouter>);
    await waitFor(() => expect(s.setPractitioners).toHaveBeenCalledWith([
      expect.objectContaining({ id: 7, name: 'Dr Owner', isFallback: true }),
    ]));
  });

  it('falls back to employer practitioner for a secretary', async () => {
    s.user = { id: 99, role: 'SECRETAIRE', employer_id: 7, nom_complet: 'Assistante' };
    vi.mocked(api.get).mockRejectedValueOnce(new Error('unavailable'));
    render(<MemoryRouter initialEntries={['/agenda']}><ClinicPractitionerBar /></MemoryRouter>);
    await waitFor(() => expect(s.setPractitioners).toHaveBeenCalledWith([
      expect.objectContaining({ id: 7, name: 'Praticien principal', isFallback: true }),
    ]));
  });
});
