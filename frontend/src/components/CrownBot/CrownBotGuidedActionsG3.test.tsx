import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../../services/api', () => ({ api: { post: vi.fn(), get: vi.fn() } }));
import { api } from '../../services/api';
import { CrownBotGuidedActionsG3 } from './CrownBotGuidedActionsG3';
import { CrownBotWorkflowPreview } from './CrownBotWorkflowPreview';

const post = vi.mocked(api.post);
const get = vi.mocked(api.get);
const ID = 'd4a97731-cdcb-4b9c-94d3-f1d21c242a21';
const PATIENT = { id: 21, nom: 'Benali', prenom: 'Salma', numero_dossier: 'S-21' };
const BOOKING = {
  status: 'prepared', executable: false, preparation_id: ID, expires_at: '2026-11-01T12:30:00',
  summary: { patient: PATIENT, praticien_id: 9, resource_id: null,
    datetime_start: '2026-11-07T10:00:00', duration_minutes: 30, motif: 'CONTROLE' },
};
const STATUS = {
  status: 'prepared', executable: false, preparation_id: ID, expires_at: '2026-11-01T12:30:00',
  summary: { patient: PATIENT, appointment_id: 32, datetime_start: '2026-11-07T10:00:00',
    expected_status: 'PREVU', expected_revision: 4,
    new_status: 'EN_SALLE_ATTENTE', new_status_label: "En salle d'attente" },
};
const reconciliation = (status: string, result: unknown = null) => ({
  preparation_id: ID, action_type: 'CREATE_APPOINTMENT', status, result,
  safe_to_retry_automatically: false, manual_reconciliation_required: false,
});
function requestBooking() {
  fireEvent.change(screen.getByRole('textbox', { name: 'Votre demande en français' }), {
    target: { value: 'Prépare un RDV demain 10h pour Mme Benali contrôle' },
  });
  fireEvent.click(screen.getByRole('button', { name: /Vérifier et préparer/i }));
}
async function preparedBooking() {
  post.mockResolvedValueOnce({ data: BOOKING } as never);
  requestBooking();
  await screen.findByText('Salma Benali · Dossier S-21');
}
const acknowledge = () => fireEvent.click(screen.getByRole('checkbox', { name: /J’ai vérifié le patient/i }));
const confirmButton = () => screen.getByRole('button', { name: 'Confirmer explicitement cette action' });
const checkButton = () => screen.getByRole('button', { name: /Vérifier l’état par identifiant/i });

beforeEach(() => { vi.clearAllMocks(); });
afterEach(() => { vi.unstubAllEnvs(); });

describe('CB-03 G3 synthetic explicit-confirmation UX', () => {
  it('does not mount without independent G3 opt-in, even when CB02 is shown', () => {
    vi.stubEnv('VITE_CROWN_BOT_GUIDED_NLU_ENABLED', 'true');
    vi.stubEnv('VITE_CROWN_BOT_CB03_G3_ENABLED', 'false');
    render(<CrownBotWorkflowPreview />);
    expect(screen.getByRole('region', { name: /Français guidé Crown Bot CB-02/i })).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: /CB-03 G3/i })).not.toBeInTheDocument();
    expect(post).not.toHaveBeenCalled();
  });
  it('G3 cannot bypass CB02 opt-in', () => {
    vi.stubEnv('VITE_CROWN_BOT_GUIDED_NLU_ENABLED', 'false');
    vi.stubEnv('VITE_CROWN_BOT_CB03_G3_ENABLED', 'true');
    render(<CrownBotWorkflowPreview />);
    expect(screen.queryByRole('region', { name: /CB-03 G3/i })).not.toBeInTheDocument();
  });
  it('mounts only in opted-in CB01 preview with chosen practitioner', () => {
    vi.stubEnv('VITE_CROWN_BOT_GUIDED_NLU_ENABLED', 'true');
    vi.stubEnv('VITE_CROWN_BOT_CB03_G3_ENABLED', 'true');
    render(<CrownBotWorkflowPreview practitionerId={9} />);
    expect(screen.getByRole('region', { name: /CB-03 G3/i })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /Praticien ID/i })).toHaveValue('9');
    expect(post).not.toHaveBeenCalled();
  });
  it('server-only prepared summary is shown, checkbox prevents implicit execution', async () => {
    render(<CrownBotGuidedActionsG3 practitionerId={9} />);
    await preparedBooking();
    expect(post).toHaveBeenCalledWith('/bot/guided/prepare-appointment', {
      utterance: 'Prépare un RDV demain 10h pour Mme Benali contrôle',
      duration_minutes: 30, praticien_id: 9,
    });
    expect(screen.getByText(/Préparation prête · non exécutée/i)).toBeInTheDocument();
    expect(screen.getByText('2026-11-07 à 10:00')).toBeInTheDocument();
    expect(confirmButton()).toBeDisabled();
    acknowledge();
    expect(confirmButton()).toBeEnabled();
    fireEvent.click(screen.getByRole('button', { name: /Nouvelle préparation/i }));
    expect(screen.queryByRole('button', { name: /Confirmer explicitement/i })).not.toBeInTheDocument();
    expect(post).toHaveBeenCalledTimes(1);
  });
  it('confirms strictly by ID+true once, and read-only GET verifies durable receipt', async () => {
    render(<CrownBotGuidedActionsG3 practitionerId={9} />);
    await preparedBooking();
    post.mockResolvedValueOnce({ data: {
      status: 'executed', preparation_id: ID,
      result: { appointment_id: 81, status: 'CREATED' },
    } } as never);
    acknowledge();
    fireEvent.click(confirmButton());
    expect(await screen.findByText(/Action exécutée et vérifiée/i)).toHaveTextContent('RDV #81');
    expect(post).toHaveBeenCalledWith('/bot/guided/confirm', {
      preparation_id: ID, confirm: true,
    });
    expect(screen.queryByRole('button', { name: /Confirmer explicitement/i })).not.toBeInTheDocument();
    get.mockResolvedValueOnce({ data: reconciliation('executed', {
      appointment_id: 81, status: 'CREATED',
    }) } as never);
    fireEvent.click(checkButton());
    await waitFor(() => expect(get).toHaveBeenCalledWith('/bot/guided/actions/' + ID));
    expect(post).toHaveBeenCalledTimes(2);
    expect(screen.getByText(/Action exécutée et vérifiée/i)).toBeInTheDocument();
  });
  it('lost ACK never enables replay; even GET prepared is not a new confirmation authorization', async () => {
    render(<CrownBotGuidedActionsG3 />);
    await preparedBooking();
    post.mockRejectedValueOnce(new Error('network lost'));
    acknowledge();
    fireEvent.click(confirmButton());
    expect(await screen.findByText(/Résultat à réconcilier/i)).toBeInTheDocument();
    expect(await screen.findByRole('alert')).toHaveTextContent(/incertaine/i);
    get.mockResolvedValueOnce({ data: reconciliation('prepared') } as never);
    fireEvent.click(checkButton());
    expect(await screen.findByText(/Aucune exécution prouvée/i)).toBeInTheDocument();
    expect(post).toHaveBeenCalledTimes(2);
    expect(get).toHaveBeenCalledWith('/bot/guided/actions/' + ID);
    expect(screen.queryByRole('button', { name: /Confirmer explicitement/i })).not.toBeInTheDocument();
  });
  it('lost ACK with executed receipt is confirmed by GET only', async () => {
    render(<CrownBotGuidedActionsG3 />);
    await preparedBooking();
    post.mockRejectedValueOnce(new Error('lost ACK'));
    acknowledge();
    fireEvent.click(confirmButton());
    await screen.findByText(/Résultat à réconcilier/i);
    get.mockResolvedValueOnce({ data: reconciliation('executed', {
      appointment_id: 81, status: 'CREATED',
    }) } as never);
    fireEvent.click(checkButton());
    expect(await screen.findByText(/Action exécutée et vérifiée/i)).toHaveTextContent('RDV #81');
    expect(post).toHaveBeenCalledTimes(2);
  });
  it('status preparation sends selected appointment only; initial revision comes from SQL response', async () => {
    render(<CrownBotGuidedActionsG3 />);
    fireEvent.click(screen.getByRole('button', { name: 'Changer le statut d’un RDV' }));
    fireEvent.change(screen.getByRole('textbox', { name: /Identifiant du RDV sélectionné/i }), {
      target: { value: '32' },
    });
    post.mockResolvedValueOnce({ data: STATUS } as never);
    fireEvent.click(screen.getByRole('button', { name: /Vérifier et préparer/i }));
    expect(await screen.findByText('PREVU')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith('/bot/guided/prepare-status', {
      selected_appointment_id: 32, utterance: "Prépare le statut du RDV en salle d'attente",
    });
    expect(JSON.stringify(post.mock.calls[0])).not.toContain('expected_revision');
    expect(confirmButton()).toBeDisabled();
    post.mockResolvedValueOnce({ data: {
      status: 'executed', preparation_id: ID,
      result: { appointment_id: 32, status: 'EN_SALLE_ATTENTE' },
    } } as never);
    acknowledge();
    fireEvent.click(confirmButton());
    expect(await screen.findByText(/Action exécutée et vérifiée/i)).toHaveTextContent('EN_SALLE_ATTENTE');
    expect(post).toHaveBeenCalledTimes(2);
  });
  it('requires explicit server homonym choice and rechecks selected patient ID', async () => {
    render(<CrownBotGuidedActionsG3 practitionerId={9} />);
    post.mockResolvedValueOnce({ data: {
      status: 'disambiguation', message: 'Sélectionnez le dossier',
      candidates: [PATIENT, { id: 22, prenom: 'Nadia', nom: 'Benali', numero_dossier: 'S-22' }],
    } } as never).mockResolvedValueOnce({ data: BOOKING } as never);
    requestBooking();
    expect(await screen.findByText('Sélectionnez le dossier')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Salma Benali/i }));
    expect(await screen.findByText(/Préparation prête · non exécutée/i)).toBeInTheDocument();
    expect(post).toHaveBeenLastCalledWith('/bot/guided/prepare-appointment', {
      utterance: 'Prépare un RDV demain 10h pour Mme Benali contrôle',
      duration_minutes: 30, praticien_id: 9, chosen_patient_id: 21,
    });
    expect(confirmButton()).toBeDisabled();
  });
  it('rejects malformed or executable draft; no action button', async () => {
    render(<CrownBotGuidedActionsG3 />);
    post.mockResolvedValueOnce({ data: { ...BOOKING, executable: true } } as never);
    requestBooking();
    expect(await screen.findByRole('alert')).toHaveTextContent(/indisponible/i);
    expect(screen.queryByRole('button', { name: /Confirmer explicitement/i })).not.toBeInTheDocument();
  });
  it('403 during confirm scrubs patient identity and action state', async () => {
    render(<CrownBotGuidedActionsG3 />);
    await preparedBooking();
    post.mockRejectedValueOnce({ response: { status: 403 } });
    acknowledge();
    fireEvent.click(confirmButton());
    expect(await screen.findByRole('alert')).toHaveTextContent(/Accès refusé/i);
    expect(screen.queryByText(/Salma Benali/)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Vérifier l’état/i })).not.toBeInTheDocument();
  });
  it('rejects forged reconciliation encouraging automatic retry', async () => {
    render(<CrownBotGuidedActionsG3 />);
    await preparedBooking();
    post.mockRejectedValueOnce(new Error('lost ACK'));
    acknowledge();
    fireEvent.click(confirmButton());
    await screen.findByText(/Résultat à réconcilier/i);
    get.mockResolvedValueOnce({ data: {
      ...reconciliation('executed', { appointment_id: 81, status: 'CREATED' }),
      safe_to_retry_automatically: true,
    } } as never);
    fireEvent.click(checkButton());
    expect(await screen.findByRole('alert')).toHaveTextContent(/incertaine/i);
    expect(screen.queryByText(/Action exécutée et vérifiée/i)).not.toBeInTheDocument();
    expect(post).toHaveBeenCalledTimes(2);
  });
  it('invalid appointment ID is rejected locally without POST', () => {
    render(<CrownBotGuidedActionsG3 />);
    fireEvent.click(screen.getByRole('button', { name: 'Changer le statut d’un RDV' }));
    fireEvent.change(screen.getByRole('textbox', { name: /Identifiant du RDV sélectionné/i }), {
      target: { value: '-7' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Vérifier et préparer/i }));
    expect(screen.getByRole('alert')).toHaveTextContent(/Identifiant de rendez-vous valide/i);
    expect(post).not.toHaveBeenCalled();
  });
  it('never persists patient identifiers in browser local storage', async () => {
    const spy = vi.spyOn(Storage.prototype, 'setItem');
    try {
      render(<CrownBotGuidedActionsG3 />);
      await preparedBooking();
      expect(spy).not.toHaveBeenCalled();
    } finally { spy.mockRestore(); }
  });
});
