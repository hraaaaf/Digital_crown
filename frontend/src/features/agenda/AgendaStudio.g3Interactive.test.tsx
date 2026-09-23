import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AgendaStudio } from './AgendaStudio';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));

vi.mock('../clinic/practitionerContext', () => ({
  usePractitionerContextStore: () => 11,
}));

vi.mock('./DailyView', () => ({ DailyView: () => <div>Day view</div> }));
vi.mock('./WeeklyView', () => ({ WeeklyView: () => <div>Week view</div> }));
vi.mock('./MonthlyView', () => ({ MonthlyView: () => <div>Month view</div> }));
vi.mock('./MultiPractitionerTimelineView', () => ({
  MultiPractitionerTimelineView: ({ loading, data }: { loading: boolean; data: unknown }) =>
    <div>{loading ? 'Multi loading' : data ? 'Multi view' : 'Multi empty'}</div>,
}));
vi.mock('./GoogleImportModal', () => ({
  GoogleImportModal: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) =>
    isOpen ? <div><span>Google import modal</span><button onClick={onClose}>Close import</button></div> : null,
}));
vi.mock('./FrontdeskModal', () => ({
  FrontdeskModal: ({ open, onClose }: { open: boolean; onClose: () => void }) =>
    open ? <div><span>Frontdesk modal</span><button onClick={onClose}>Close frontdesk</button></div> : null,
}));
vi.mock('./AgendaModal', () => ({
  AgendaModal: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) =>
    isOpen ? <div><span>Prefill agenda modal</span><button onClick={onClose}>Close prefill</button></div> : null,
}));
vi.mock('./PendingRequestCard', () => ({
  PendingRequestCard: ({ request }: { request: { id: number } }) => <div>Pending request {request.id}</div>,
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/upcoming-holidays') return { data: [{ name: 'Test Holiday', date: '2026-09-21' }] } as never;
    if (url === '/agenda/settings') return { data: {} } as never;
    if (url === '/agenda/exceptions') return { data: [] } as never;
    if (url === '/appointments/pending') return { data: [{ id: 5 }] } as never;
    if (url === '/appointments/multi-practitioner') return { data: { dentists: [] } } as never;
    throw new Error('unexpected GET ' + url);
  });
  vi.mocked(api.post).mockResolvedValue({ data: {} } as never);
});

afterEach(() => cleanup());

describe('AgendaStudio G3 interactive shell matrix', () => {
  it('switches day/week/month/multi views and loads multi-practitioner data', async () => {
    render(<MemoryRouter><AgendaStudio /></MemoryRouter>);
    expect(await screen.findByText('Week view')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /Jour$/i }));
    expect(await screen.findByText('Day view')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /Mois$/i }));
    expect(await screen.findByText('Month view')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /Multi$/i }));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith(
      '/appointments/multi-practitioner',
      expect.objectContaining({ params: expect.objectContaining({ start_date: expect.any(String), end_date: expect.any(String) }) }),
    ));
    expect(await screen.findByText('Multi view')).toBeTruthy();
  });

  it('opens and closes frontdesk and Google import modals', async () => {
    render(<MemoryRouter><AgendaStudio /></MemoryRouter>);

    fireEvent.click(await screen.findByTitle('Nouvelle demande de rendez-vous'));
    expect(screen.getByText('Frontdesk modal')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Close frontdesk' }));
    expect(screen.queryByText('Frontdesk modal')).toBeNull();

    fireEvent.click(screen.getByTitle('Importer depuis Google Agenda'));
    expect(screen.getByText('Google import modal')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Close import' }));
    expect(screen.queryByText('Google import modal')).toBeNull();
  });

  it('shows pending requests and toggles the pending-only control', async () => {
    render(<MemoryRouter><AgendaStudio /></MemoryRouter>);

    expect(await screen.findByText('Demandes en attente (1)')).toBeTruthy();
    expect(screen.getByText('Pending request 5')).toBeTruthy();

    expect(screen.getByText('Week view')).toBeTruthy();
    const toggle = screen.getByRole('button', { name: 'Afficher seulement' });
    fireEvent.click(toggle);
    expect(screen.getByRole('button', { name: 'Afficher tout' })).toBeTruthy();
    expect(screen.queryByText('Week view')).toBeNull();
    expect(screen.getByText('Pending request 5')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Afficher tout' }));
    expect(screen.getByText('Week view')).toBeTruthy();
  });

  it('blocks the next holiday only after backend ACK', async () => {
    render(<MemoryRouter><AgendaStudio /></MemoryRouter>);

    expect(await screen.findByText(/Test Holiday/)).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: "Bloquer l'agenda" }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/agenda/exceptions', {
      start_date: '2026-09-21',
      end_date: '2026-09-21',
      reason: 'Test Holiday',
      is_recurring: false,
    }));
    await waitFor(() => expect(screen.queryByText(/Test Holiday/)).toBeNull());
  });

  it('opens the dedicated appointment modal from patient prefill navigation state', async () => {
    render(
      <MemoryRouter initialEntries={[{ pathname: '/agenda', state: { prefillPatientId: 7, prefillPatientNom: 'BENALI', prefillPatientPrenom: 'Sara' } }]}>
        <AgendaStudio />
      </MemoryRouter>,
    );

    expect(await screen.findByText('Prefill agenda modal')).toBeTruthy();
  });
});
