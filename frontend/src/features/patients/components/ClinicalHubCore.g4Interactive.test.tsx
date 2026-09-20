import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ClinicalHub } from './ClinicalHubCore';
import { api } from '../../../services/api';
import { patientClinicalPersistence } from '../../../services/patientClinicalPersistence';

vi.mock('../../../services/api', () => ({
  api: { get: vi.fn(), put: vi.fn() },
}));

vi.mock('../../../services/patientClinicalPersistence', () => ({
  patientClinicalPersistence: {
    getOdontogram: vi.fn(),
    saveOdontogram: vi.fn(),
    listConclusions: vi.fn(),
    createConclusion: vi.fn(),
    listMasterPlanRevisions: vi.fn(),
  },
}));

vi.mock('../../../components/odontogram/Odontogram', () => ({
  Odontogram: ({ onStatusChange }: { onStatusChange: (state: Record<number, unknown>) => void }) => (
    <button
      type="button"
      onClick={() => {
        onStatusChange({ 11: { status: 'SOUND' } });
        onStatusChange({ 11: { status: 'CARIES' } });
      }}
    >
      Modifier odontogramme
    </button>
  ),
}));

vi.mock('./wizards/AssistantParo', () => ({ AssistantParo: () => <div>Wizard paro</div> }));
vi.mock('./wizards/AssistantEndo', () => ({ AssistantEndo: () => <div>Wizard endo</div> }));
vi.mock('./wizards/AssistantChirurgie', () => ({ AssistantChirurgie: () => <div>Wizard chirurgie</div> }));
vi.mock('./wizards/AssistantProthese', () => ({ AssistantProthese: () => <div>Wizard prothese</div> }));
vi.mock('./wizards/AssistantPedo', () => ({ AssistantPedo: () => <div>Wizard pedo</div> }));
vi.mock('./wizards/AssistantOrtho', () => ({ AssistantOrtho: () => <div>Wizard ortho</div> }));
vi.mock('./wizards/AssistantExamenComplet', () => ({ AssistantExamenComplet: () => <div>Wizard complet</div> }));
vi.mock('./wizards/AssistantATM', () => ({ AssistantATM: () => <div>Wizard ATM</div> }));
vi.mock('./wizards/AssistantPatho', () => ({ AssistantPatho: () => <div>Wizard patho</div> }));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

const persistedOdontogram = {
  patient_id: 7,
  dentition_type: 'ADULT',
  state: { 11: { status: 'SOUND' } },
  revision: 3,
  updated_at: '2026-09-19T10:00:00Z',
};

const plan = {
  steps: [
    { id: 10, title: 'Endodontie 11', assistant: 'Endodontie', status: 'pending', date_str: '' },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/patients/7') return { data: { antecedents_medicaux: 'Allergie pénicilline' } } as never;
    if (url === '/patients/7/master-plan') return { data: plan } as never;
    throw new Error('unexpected GET ' + url);
  });
  vi.mocked(api.put).mockResolvedValue({ data: plan } as never);

  vi.mocked(patientClinicalPersistence.getOdontogram).mockResolvedValue(persistedOdontogram as never);
  vi.mocked(patientClinicalPersistence.saveOdontogram).mockResolvedValue({
    ...persistedOdontogram,
    state: { 11: { status: 'CARIES' } },
    revision: 4,
  } as never);
  vi.mocked(patientClinicalPersistence.listConclusions).mockResolvedValue([] as never);
  vi.mocked(patientClinicalPersistence.createConclusion).mockResolvedValue({} as never);
  vi.mocked(patientClinicalPersistence.listMasterPlanRevisions).mockResolvedValue([] as never);
});

afterEach(() => cleanup());

describe('ClinicalHubCore G4 deep clinical matrix', () => {
  it('keeps odontogram save disabled until a real edit, then persists with expected revision', async () => {
    render(<ClinicalHub patientId={7} />);

    const save = await screen.findByRole('button', { name: 'Enregistrer' });
    expect((save as HTMLButtonElement).disabled).toBe(true);

    fireEvent.click(screen.getByRole('button', { name: 'Modifier odontogramme' }));
    expect(screen.getByText('Modifications non enregistrées.')).toBeTruthy();
    expect((screen.getByRole('button', { name: 'Enregistrer' }) as HTMLButtonElement).disabled).toBe(false);

    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    await waitFor(() => expect(patientClinicalPersistence.saveOdontogram).toHaveBeenCalledWith(
      7,
      expect.objectContaining({
        dentition_type: 'ADULT',
        expected_revision: 3,
        state: expect.any(Object),
      }),
    ));
    await waitFor(() => expect(screen.queryByText('Modifications non enregistrées.')).toBeNull());
  });

  it('surfaces optimistic-concurrency conflict and does not pretend the odontogram was saved', async () => {
    vi.mocked(patientClinicalPersistence.saveOdontogram).mockRejectedValueOnce({ response: { status: 409 } });
    render(<ClinicalHub patientId={7} />);

    await screen.findByRole('button', { name: 'Modifier odontogramme' });
    fireEvent.click(screen.getByRole('button', { name: 'Modifier odontogramme' }));
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    expect(await screen.findByText(/modifié ailleurs/i)).toBeTruthy();
    expect(screen.getByText('Modifications non enregistrées.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Recharger' })).toBeTruthy();
  });

  it('records a practitioner conclusion only after explicit validation', async () => {
    render(<ClinicalHub patientId={7} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Examens' }));

    const input = screen.getByPlaceholderText(/Saisir la conclusion/i);
    const save = screen.getByRole('button', { name: 'Enregistrer la conclusion' });
    expect((save as HTMLButtonElement).disabled).toBe(true);

    fireEvent.change(input, { target: { value: 'Conclusion validée par le praticien' } });
    fireEvent.click(save);

    await waitFor(() => expect(patientClinicalPersistence.createConclusion).toHaveBeenCalledWith(
      7,
      expect.objectContaining({
        conclusion_text: 'Conclusion validée par le praticien',
        proposal_text: null,
        proposal_source: null,
      }),
    ));
  });

  it('surfaces a 403 conclusion refusal and keeps the draft for correction/retry', async () => {
    vi.mocked(patientClinicalPersistence.createConclusion).mockRejectedValueOnce({ response: { status: 403 } });
    render(<ClinicalHub patientId={7} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Examens' }));

    const input = screen.getByPlaceholderText(/Saisir la conclusion/i);
    fireEvent.change(input, { target: { value: 'Conclusion non autorisée' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer la conclusion' }));

    expect(await screen.findByText(/pas autorisé à retenir une conclusion clinique/i)).toBeTruthy();
    expect((screen.getByPlaceholderText(/Saisir la conclusion/i) as HTMLTextAreaElement).value).toBe('Conclusion non autorisée');
  });

  it('updates and deletes treatment-plan steps only through persisted backend PUTs', async () => {
    render(<ClinicalHub patientId={7} />);

    expect(await screen.findByText('Endodontie 11')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Fait' }));
    await waitFor(() => expect(api.put).toHaveBeenCalledWith(
      '/patients/7/master-plan',
      [expect.objectContaining({ title: 'Endodontie 11', status: 'done' })],
    ));

    vi.mocked(api.put).mockClear();
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer l’étape' }));
    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/patients/7/master-plan', []));
  });

  it('keeps the displayed plan and surfaces refusal when plan persistence fails', async () => {
    vi.mocked(api.put).mockRejectedValueOnce(new Error('save failed'));
    render(<ClinicalHub patientId={7} />);

    expect(await screen.findByText('Endodontie 11')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Fait' }));

    expect(await screen.findByText(/modification n'a pas été enregistrée/i)).toBeTruthy();
    expect(screen.getByText('Endodontie 11')).toBeTruthy();
  });
});
