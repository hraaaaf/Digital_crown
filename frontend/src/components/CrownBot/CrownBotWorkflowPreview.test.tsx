import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../../services/api', () => ({
  api: { post: vi.fn(), get: vi.fn() },
}));

import { api } from '../../services/api';
import { CrownBotWorkflowPreview } from './CrownBotWorkflowPreview';

const post = vi.mocked(api.post);
const get = vi.mocked(api.get);

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('ZERO-LLM simulation — guarded, non-executable mobile/desktop contract', () => {
  it('collects a bounded deterministic transcript without executing or booking', async () => {
    post
      .mockResolvedValueOnce({ data: { status: 'clarification', message: 'Identifiant numérique du patient ?' } } as never)
      .mockResolvedValueOnce({ data: {
        status: 'read', message: 'Patient identifié dans votre cabinet.',
        patient: { id: 7, nom: 'Synthetic', prenom: 'Test' },
      } } as never);
    render(<CrownBotWorkflowPreview />);
    expect(screen.getByText(/aucune écriture/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Trouver un patient' }));
    await screen.findByText('Identifiant numérique du patient ?');
    expect(post).toHaveBeenCalledWith('/bot/workflows/preview', { messages: ['/patient'] });
    fireEvent.change(screen.getByRole('textbox', { name: 'Votre réponse de simulation' }), {
      target: { value: '7' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    await screen.findByText('Patient identifié dans votre cabinet.');
    expect(post).toHaveBeenCalledWith('/bot/workflows/preview', { messages: ['/patient', '7'] });
    expect(post).not.toHaveBeenCalledWith('/bot/execute', expect.anything());
    expect(screen.queryByRole('button', { name: /confirmer cette action/i })).not.toBeInTheDocument();
  });

  it('shows proposals explicitly as NON executable, without a confirm action', async () => {
    post.mockResolvedValueOnce({ data: {
      status: 'proposal_only',
      message: 'Simulation uniquement, non exécutée.',
      proposal: { type: 'CREATE_APPOINTMENT', params: { patient_id: 7 } },
    } } as never);
    render(<CrownBotWorkflowPreview />);
    fireEvent.click(screen.getByRole('button', { name: 'Préparer un RDV' }));
    await screen.findByText(/Proposition CREATE_APPOINTMENT : simulation uniquement/i);
    expect(screen.queryByRole('button', { name: 'Confirmer' })).not.toBeInTheDocument();
    expect(post).toHaveBeenCalledTimes(1);
  });

  it('handles a stale 409 without automatic replay or accidentally clearing the previous step', async () => {
    post.mockResolvedValueOnce({
      data: { status: 'clarification', message: 'Identifiant numérique du patient ?' },
    } as never).mockRejectedValueOnce({ response: { status: 409 } });
    render(<CrownBotWorkflowPreview />);
    fireEvent.click(screen.getByRole('button', { name: 'Préparer un RDV' }));
    await screen.findByText('Identifiant numérique du patient ?');
    fireEvent.change(screen.getByRole('textbox', { name: 'Votre réponse de simulation' }), {
      target: { value: '7' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    await screen.findByRole('alert');
    expect(screen.getByRole('alert')).toHaveTextContent(/réinitialisez/i);
    expect(screen.getByText(/Étapes saisies : 1\/8/)).toBeInTheDocument();
    await waitFor(() => expect(post).toHaveBeenCalledTimes(2));
    expect(post).not.toHaveBeenCalledWith('/bot/execute', expect.anything());
  });

  it('fails closed when the backend flag is OFF (404)', async () => {
    post.mockRejectedValueOnce({ response: { status: 404 } });
    render(<CrownBotWorkflowPreview />);
    fireEvent.click(screen.getByRole('button', { name: 'Préparer un RDV' }));
    await screen.findByRole('alert');
    expect(screen.getByRole('alert')).toHaveTextContent(/indisponible sur ce serveur/i);
    expect(post).toHaveBeenCalledTimes(1);
  });
});


describe('CB-01 FIRST_VALUE_UI — programme métier source vérifiée, lecture seule', () => {
  it('filters a clinician programme to their authenticated practitioner and never submits an appointment', async () => {
    get.mockResolvedValueOnce({ data: [] } as never);
    render(<CrownBotWorkflowPreview practitionerId={19} />);
    fireEvent.click(screen.getByRole('button', { name: 'Mon programme' }));
    await screen.findByRole('status', { name: 'Programme du jour' });
    expect(get).toHaveBeenCalledWith('/appointments/', {
      params: {
        start_date: expect.any(String),
        end_date: expect.any(String),
        praticien_id: 19,
      },
    });
    expect(post).not.toHaveBeenCalled();
  });

  it('reads the canonical authorized Agenda endpoint with bounded local-day dates and a truthful source', async () => {
    get.mockResolvedValueOnce({ data: [
      { id: 72, datetime_start: '2026-10-17T10:00:00', patient_name: 'BENALI TEST', motif: 'Consultation', status: 'PRÉVU' },
    ] } as never);
    render(<CrownBotWorkflowPreview />);
    expect(screen.getByRole('button', { name: 'Mon programme' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Trouver un patient' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Préparer un RDV' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '/devis' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Mon programme' }));
    const programme = await screen.findByRole('status', { name: 'Programme du jour' });
    expect(programme).toHaveTextContent('BENALI TEST');
    expect(programme).toHaveTextContent(/Source : Agenda du cabinet · Lecture serveur à/);
    expect(get).toHaveBeenCalledWith('/appointments/', {
      params: {
        start_date: expect.any(String),
        end_date: expect.any(String),
      },
    });
    const arg = get.mock.calls[0][1]?.params as { start_date: string; end_date: string };
    expect(new Date(arg.start_date).getTime()).toBeLessThan(new Date(arg.end_date).getTime());
    expect(post).not.toHaveBeenCalled();
  });

  it('fails closed and discards an old program when authorization is revoked', async () => {
    get.mockResolvedValueOnce({ data: [
      { id: 8, datetime_start: '2026-10-17T08:30:00', patient_name: 'Dossier confidentiel' },
    ] } as never).mockRejectedValueOnce({ response: { status: 403 } });
    render(<CrownBotWorkflowPreview />);
    fireEvent.click(screen.getByRole('button', { name: 'Mon programme' }));
    await screen.findByText(/Dossier confidentiel/);
    fireEvent.click(screen.getByRole('button', { name: 'Mon programme' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Accès Agenda refusé/);
    expect(screen.queryByText(/Dossier confidentiel/)).not.toBeInTheDocument();
    expect(post).not.toHaveBeenCalled();
  });

  it('does not confuse stale programme or patient result with a new preparation', async () => {
    get.mockResolvedValueOnce({ data: [] } as never);
    post.mockResolvedValueOnce({ data: { status: 'clarification', message: 'Patient ?' } } as never);
    render(<CrownBotWorkflowPreview />);
    fireEvent.click(screen.getByRole('button', { name: 'Mon programme' }));
    expect(await screen.findByRole('status', { name: 'Programme du jour' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Préparer un RDV' }));
    await screen.findByText('Patient ?');
    expect(screen.queryByRole('status', { name: 'Programme du jour' })).not.toBeInTheDocument();
    expect(post).toHaveBeenCalledWith('/bot/workflows/preview', { messages: ['/rdv'] });
  });
});

describe('CB-00 scoped patient selectors', () => {
  it('shows dossier matches and explicitly selects a homonym by internal ID', async () => {
    post
      .mockResolvedValueOnce({ data: { status: 'clarification', message: 'Nom ou dossier ?' } } as never)
      .mockResolvedValueOnce({ data: {
        status: 'disambiguation', message: 'Plusieurs patients correspondent. Choisissez le bon dossier.',
        proposal: null, candidates: [
          { id: 5, nom: 'Benali', prenom: 'Amina', numero_dossier: 'B-001' },
          { id: 8, nom: 'Benali', prenom: 'Salma', numero_dossier: 'B-002' },
        ],
      } } as never)
      .mockResolvedValueOnce({ data: {
        status: 'read', message: 'Patient identifié dans votre cabinet.',
        proposal: null, patient: { id: 8, nom: 'Benali', prenom: 'Salma', numero_dossier: 'B-002' },
      } } as never);
    render(<CrownBotWorkflowPreview />);
    fireEvent.click(screen.getByRole('button', { name: 'Trouver un patient' }));
    await screen.findByText('Nom ou dossier ?');
    fireEvent.change(screen.getByRole('textbox', { name: 'Votre réponse de simulation' }), {
      target: { value: 'Mme Benali' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    await screen.findByText(/Plusieurs patients correspondent/);
    const candidate = screen.getByRole('button', { name: /Salma Benali.*B-002/ });
    fireEvent.click(candidate);
    await screen.findByText(/Dossier B-002/);
    expect(post).toHaveBeenLastCalledWith('/bot/workflows/preview', {
      messages: ['/patient', 'id:8'],
    });
    expect(post).not.toHaveBeenCalledWith('/bot/execute', expect.anything());
  });

  it('renders missing dossier error without implying a disabled feature', async () => {
    post.mockResolvedValueOnce({ data: {
      status: 'clarification', message: 'Patient ?',
    } } as never).mockRejectedValueOnce({
      response: { status: 404, data: { detail: 'Patient introuvable.' } },
    });
    render(<CrownBotWorkflowPreview />);
    fireEvent.click(screen.getByRole('button', { name: 'Trouver un patient' }));
    await screen.findByText('Patient ?');
    fireEvent.change(screen.getByRole('textbox', { name: 'Votre réponse de simulation' }), {
      target: { value: 'dossier:INCONNU-102' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/aucun dossier correspondant/i);
  });
});
