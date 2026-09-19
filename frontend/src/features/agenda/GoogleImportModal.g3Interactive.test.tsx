import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { GoogleImportModal } from './GoogleImportModal';
import { api } from '../../services/api';
import { parseIcsContent } from '../../utils/icsParser';

vi.mock('../../services/api', () => ({
  api: { post: vi.fn() },
}));

vi.mock('../../utils/icsParser', () => ({
  parseIcsContent: vi.fn(),
}));

const events = [
  {
    patient_name: 'Sara BENALI',
    datetime_start: '2026-09-21T10:00:00.000Z',
    duration_minutes: 30,
    notes: 'Contrôle',
  },
  {
    patient_name: 'Omar ALAMI',
    datetime_start: '2026-09-21T11:00:00.000Z',
    duration_minutes: 45,
    notes: '',
  },
];

function renderModal() {
  const onClose = vi.fn();
  const onSuccess = vi.fn();
  const view = render(<GoogleImportModal isOpen onClose={onClose} onSuccess={onSuccess} />);
  return { ...view, onClose, onSuccess };
}

async function chooseFile(container: HTMLElement) {
  const input = container.querySelector('input[type="file"]') as HTMLInputElement;
  const file = new File(['BEGIN:VCALENDAR'], 'agenda.ics', { type: 'text/calendar' });
  Object.defineProperty(file, 'text', { value: vi.fn().mockResolvedValue('BEGIN:VCALENDAR') });
  fireEvent.change(input, { target: { files: [file] } });
  await screen.findByText('2/2 rendez-vous sélectionnés');
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(parseIcsContent).mockReturnValue(events as never);
  vi.mocked(api.post).mockResolvedValue({ data: {} } as never);
});
afterEach(() => cleanup());

describe('GoogleImportModal G3 interactive matrix', () => {
  it('parses the ICS, selects all events by default and imports exact selected payload', async () => {
    const { container, onClose, onSuccess } = renderModal();
    await chooseFile(container);

    fireEvent.click(screen.getByRole('button', { name: /Confirmer l'import/i }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/appointments/bulk', {
      appointments: [
        {
          patient_name: 'Sara BENALI',
          datetime_start: '2026-09-21T10:00:00.000Z',
          duration_minutes: 30,
          notes: 'Contrôle',
          status: 'PRÉVU',
        },
        {
          patient_name: 'Omar ALAMI',
          datetime_start: '2026-09-21T11:00:00.000Z',
          duration_minutes: 45,
          notes: 'Importé depuis Google Agenda',
          status: 'PRÉVU',
        },
      ],
    }));
    expect(onSuccess).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('imports only checked events and disables confirmation when none are selected', async () => {
    const { container } = renderModal();
    await chooseFile(container);

    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]);
    expect(screen.getByText('1/2 rendez-vous sélectionnés')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /Confirmer l'import/i }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/appointments/bulk', {
      appointments: [expect.objectContaining({ patient_name: 'Omar ALAMI' })],
    }));

    cleanup();
    vi.clearAllMocks();
    vi.mocked(parseIcsContent).mockReturnValue(events as never);
    const second = renderModal();
    await chooseFile(second.container);
    const allCheckbox = screen.getAllByRole('checkbox')[0];
    fireEvent.click(allCheckbox);
    expect(screen.getByText('0/2 rendez-vous sélectionnés')).toBeTruthy();
    expect((screen.getByRole('button', { name: /Confirmer l'import/i }) as HTMLButtonElement).disabled).toBe(true);
  });

  it('rejects an ICS with no valid appointments before any backend mutation', async () => {
    vi.mocked(parseIcsContent).mockReturnValueOnce([]);
    const { container } = renderModal();
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['invalid'], 'empty.ics', { type: 'text/calendar' });
    Object.defineProperty(file, 'text', { value: vi.fn().mockResolvedValue('invalid') });

    fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText('Aucun rendez-vous valide trouvé dans ce fichier.')).toBeTruthy();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('keeps the import preview open and reports no false success on backend refusal', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('bulk refused'));
    const { container, onClose, onSuccess } = renderModal();
    await chooseFile(container);

    fireEvent.click(screen.getByRole('button', { name: /Confirmer l'import/i }));

    expect(await screen.findByText("Erreur lors de l'importation des rendez-vous.")).toBeTruthy();
    expect(onSuccess).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByText('2/2 rendez-vous sélectionnés')).toBeTruthy();
  });

  it('changes file or cancels without backend mutation', async () => {
    const first = renderModal();
    await chooseFile(first.container);
    fireEvent.click(screen.getByRole('button', { name: 'Changer de fichier' }));
    expect(screen.getByText('Sélectionnez un fichier .ics')).toBeTruthy();
    expect(api.post).not.toHaveBeenCalled();

    cleanup();
    const second = renderModal();
    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(second.onClose).toHaveBeenCalledTimes(1);
    expect(api.post).not.toHaveBeenCalled();
  });
});
