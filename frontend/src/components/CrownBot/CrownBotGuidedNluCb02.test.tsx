import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../../services/api', () => ({
  api: { post: vi.fn(), get: vi.fn() },
}));
import { api } from '../../services/api';
import { CrownBotGuidedNluCb02 } from './CrownBotGuidedNluCb02';
const post = vi.mocked(api.post);

beforeEach(() => { vi.clearAllMocks(); });

describe('CB-02 read-only French guided preview, synthetic transport', () => {
  it('sends only utterance, renders field provenance, never an action', async () => {
    post.mockResolvedValueOnce({ data: {
      status: 'preview_only', intent: 'RDV_PREPARE',
      fields: { time: { value: '10:00', source: 'explicit', rule: 'STRICT_24H_TIME' } },
      message: 'Aperçu uniquement', proposal: null, executable: false,
    } } as never);
    render(<CrownBotGuidedNluCb02 />);
    fireEvent.change(screen.getByRole('textbox', { name: /Votre demande en français/i }), {
      target: { value: 'Prépare un RDV demain 10h pour Mme Benali contrôle' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Comprendre la demande/i }));
    expect(await screen.findByText('Aperçu uniquement')).toBeInTheDocument();
    expect(screen.getByText(/saisie explicitement/)).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith('/bot/guided/preview', {
      utterance: 'Prépare un RDV demain 10h pour Mme Benali contrôle',
    });
    expect(post).not.toHaveBeenCalledWith('/bot/execute', expect.anything());
    expect(screen.queryByRole('button', { name: /confirmer.*action|réserver|enregistrer/i })).not.toBeInTheDocument();
  });

  it('clears stale patient identity when a phrase is edited', async () => {
    post.mockResolvedValueOnce({ data: {
      status: 'read', intent: 'PATIENT_LOOKUP',
      fields: { patient: { value: 'id:3', source: 'server_verified', rule: 'LIVE_EMPLOYER_AND_DELETION_FILTER' } },
      message: 'Dossier identifié', proposal: null, executable: false,
      patient: { id: 3, prenom: 'Salma', nom: 'Benali', numero_dossier: 'BE-3' },
    } } as never);
    render(<CrownBotGuidedNluCb02 />);
    const box = screen.getByRole('textbox', { name: /Votre demande en français/i });
    fireEvent.change(box, { target: { value: 'Trouve Mme Benali' } });
    fireEvent.click(screen.getByRole('button', { name: /Comprendre la demande/i }));
    expect(await screen.findByText(/Identité vérifiée par le serveur/)).toHaveTextContent('Salma Benali');
    fireEvent.change(box, { target: { value: 'Trouve Mme Alaoui' } });
    expect(screen.queryByText(/Identité vérifiée par le serveur/)).not.toBeInTheDocument();
    expect(screen.queryByText('Dossier identifié')).not.toBeInTheDocument();
  });

  it('passes a chosen homonym only as an untrusted ID for live server recheck', async () => {
    post.mockResolvedValueOnce({ data: {
      status: 'disambiguation', intent: 'PATIENT_LOOKUP', fields: {},
      message: 'Choisissez un dossier', proposal: null, executable: false,
      candidates: [{ id: 3, prenom: 'Salma', nom: 'Benali', numero_dossier: 'BE-3' },
        { id: 4, prenom: 'Nadia', nom: 'Benali', numero_dossier: 'BE-4' }],
    } } as never).mockResolvedValueOnce({ data: {
      status: 'read', intent: 'PATIENT_LOOKUP',
      fields: { patient: { value: 'id:4', source: 'server_verified', rule: 'LIVE_EMPLOYER_AND_DELETION_FILTER' } },
      message: 'Dossier identifié', proposal: null, executable: false,
      patient: { id: 4, prenom: 'Nadia', nom: 'Benali', numero_dossier: 'BE-4' },
    } } as never);
    render(<CrownBotGuidedNluCb02 />);
    fireEvent.change(screen.getByRole('textbox', { name: /Votre demande en français/i }), {
      target: { value: 'Trouve Mme Benali' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Comprendre la demande/i }));
    const choice = await screen.findByRole('button', { name: /Nadia Benali/ });
    fireEvent.click(choice);
    await waitFor(() => expect(post).toHaveBeenLastCalledWith('/bot/guided/preview', {
      utterance: 'Trouve Mme Benali', chosen_patient_id: 4,
    }));
    expect(await screen.findByText(/Identité vérifiée par le serveur/)).toHaveTextContent('Nadia Benali');
  });

  it('refuses an executable or otherwise malformed backend result', async () => {
    post.mockResolvedValueOnce({ data: {
      status: 'preview_only', intent: 'RDV_PREPARE',
      fields: {}, message: 'OK', proposal: { type: 'CREATE_APPOINTMENT' }, executable: true,
    } } as never);
    render(<CrownBotGuidedNluCb02 />);
    fireEvent.change(screen.getByRole('textbox', { name: /Votre demande en français/i }), {
      target: { value: 'Prépare RDV demain' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Comprendre la demande/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Serveur indisponible/);
    expect(screen.queryByText('OK')).not.toBeInTheDocument();
  });

  it('does not show the previous patient after HTTP 403', async () => {
    post.mockRejectedValueOnce({ response: { status: 403 } });
    render(<CrownBotGuidedNluCb02 />);
    fireEvent.change(screen.getByRole('textbox', { name: /Votre demande en français/i }), {
      target: { value: 'Trouve Mme Benali' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Comprendre la demande/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Accès refusé/);
    expect(screen.queryByText(/Identité vérifiée par le serveur/)).not.toBeInTheDocument();
  });
});
