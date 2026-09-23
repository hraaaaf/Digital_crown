import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { FrontdeskModal } from './FrontdeskModal';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: { post: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } } as never);
});
afterEach(() => cleanup());

function renderModal() {
  const onClose = vi.fn();
  const onSuccess = vi.fn();
  render(
    <FrontdeskModal
      open
      onClose={onClose}
      onSuccess={onSuccess}
      selectedDate={new Date('2026-09-21T00:00:00')}
    />,
  );
  return { onClose, onSuccess };
}

function fillForm() {
  fireEvent.change(screen.getByPlaceholderText('Prénom'), { target: { value: 'Sara' } });
  fireEvent.change(screen.getByPlaceholderText('Nom'), { target: { value: 'BENALI' } });
  fireEvent.change(screen.getByPlaceholderText('Téléphone (optionnel)'), { target: { value: '0612345678' } });
  fireEvent.change(screen.getByPlaceholderText('Motif de la visite'), { target: { value: 'Contrôle' } });
  fireEvent.change(screen.getByPlaceholderText('Notes (optionnel)'), { target: { value: 'Appeler avant' } });
  fireEvent.change(screen.getByRole('combobox'), { target: { value: '45' } });
}

describe('FrontdeskModal G3 mutation matrix', () => {
  it('creates a pending frontdesk request with the exact business payload', async () => {
    const { onClose, onSuccess } = renderModal();
    fillForm();

    fireEvent.click(screen.getByRole('button', { name: /Créer demande/i }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      '/frontdesk/appointment-request',
      expect.objectContaining({
        first_name: 'Sara',
        last_name: 'BENALI',
        phone: '0612345678',
        appointment_reason: 'Contrôle',
        duration_minutes: 45,
        source: 'frontdesk',
        notes: 'Appeler avant',
        requested_start: expect.any(String),
      }),
    ));
    expect(onSuccess).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('shows backend refusal and does not close or report success', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({ response: { data: { detail: 'Créneau indisponible' } } });
    const { onClose, onSuccess } = renderModal();
    fillForm();

    fireEvent.click(screen.getByRole('button', { name: /Créer demande/i }));

    expect(await screen.findByText('Créneau indisponible')).toBeTruthy();
    expect(onSuccess).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('cancels without any mutation', () => {
    const { onClose, onSuccess } = renderModal();
    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onSuccess).not.toHaveBeenCalled();
    expect(api.post).not.toHaveBeenCalled();
  });
});
