import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../../services/api', () => ({
  api: { post: vi.fn() },
}));

import { api } from '../../services/api';
import { CrownBotWorkflowPreview } from './CrownBotWorkflowPreview';

const post = vi.mocked(api.post);

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
    fireEvent.click(screen.getByRole('button', { name: '/patient' }));
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
    fireEvent.click(screen.getByRole('button', { name: '/rdv' }));
    await screen.findByText(/Proposition CREATE_APPOINTMENT : simulation uniquement/i);
    expect(screen.queryByRole('button', { name: 'Confirmer' })).not.toBeInTheDocument();
    expect(post).toHaveBeenCalledTimes(1);
  });

  it('handles a stale 409 without automatic replay or accidentally clearing the previous step', async () => {
    post.mockResolvedValueOnce({
      data: { status: 'clarification', message: 'Identifiant numérique du patient ?' },
    } as never).mockRejectedValueOnce({ response: { status: 409 } });
    render(<CrownBotWorkflowPreview />);
    fireEvent.click(screen.getByRole('button', { name: '/rdv' }));
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
    fireEvent.click(screen.getByRole('button', { name: '/devis' }));
    await screen.findByRole('alert');
    expect(screen.getByRole('alert')).toHaveTextContent(/indisponible sur ce serveur/i);
    expect(post).toHaveBeenCalledTimes(1);
  });
});
