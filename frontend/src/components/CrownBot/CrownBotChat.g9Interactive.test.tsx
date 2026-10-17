import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
  API_BASE: 'http://127.0.0.1:8005',
  getRuntimeAuthToken: vi.fn(() => 'g9-token'),
}));

vi.mock('../../stores/useAuthStore', () => ({
  useAuthStore: () => ({
    user: { id: 9, employer_id: 42 },
  }),
}));

import { api } from '../../services/api';
import { CrownBotChat } from './CrownBotChat';

const getMock = vi.mocked(api.get);
const postMock = vi.mocked(api.post);

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  url: string;
  onopen: ((event?: unknown) => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: ((event?: unknown) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  close() {}

  emit(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }
}

function renderCrownBot(onUnreadChange = vi.fn()) {
  render(
    <MemoryRouter initialEntries={['/accounting']}>
      <CrownBotChat onUnreadChange={onUnreadChange} />
    </MemoryRouter>,
  );
  return onUnreadChange;
}

async function seedInsight() {
  await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0));
  act(() => {
    FakeWebSocket.instances.at(-1)?.emit({
      unread_count: 1,
      insights: [{
        id: 501,
        insight_type: 'finance',
        content: 'Impayé à vérifier',
        patient_id: 4,
        created_at: '2026-09-24T10:00:00Z',
      }],
    });
  });
  await screen.findByRole('button', { name: /^Marquer comme lu$/i });
}

describe('CrownBot G9 reachable interaction truth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // The CI synthetic preview opt-in is TRUE; explicitly test both ON/OFF
    // branches instead of inheriting a runner-wide flag by accident.
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'false');
    FakeWebSocket.instances = [];
    vi.stubGlobal('WebSocket', FakeWebSocket as any);
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      value: vi.fn(),
      configurable: true,
    });
    getMock.mockResolvedValue({ data: [] } as any);
    postMock.mockResolvedValue({ data: {} } as any);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('keeps an insight visible and unread when backend read-ack is refused', async () => {
    const onUnreadChange = renderCrownBot();
    await seedInsight();

    await waitFor(() => expect(onUnreadChange).toHaveBeenLastCalledWith(1));

    postMock.mockRejectedValueOnce(new Error('read refused'));
    fireEvent.click(screen.getByRole('button', { name: /^Marquer comme lu$/i }));

    await waitFor(() => {
      expect(postMock).toHaveBeenCalledWith('/ai/ghost-insights/501/read');
    });

    expect(screen.getByRole('button', { name: /^Marquer comme lu$/i })).toBeInTheDocument();
    expect(onUnreadChange).toHaveBeenLastCalledWith(1);
  });

  it('removes an insight and decrements unread only after backend read-ack succeeds', async () => {
    const onUnreadChange = renderCrownBot();
    await seedInsight();

    fireEvent.click(screen.getByRole('button', { name: /^Marquer comme lu$/i }));

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /^Marquer comme lu$/i })).not.toBeInTheDocument();
    });
    expect(postMock).toHaveBeenCalledWith('/ai/ghost-insights/501/read');
    await waitFor(() => {
      expect(onUnreadChange).toHaveBeenLastCalledWith(0);
    });
  });

  it('proves the conversation send/action branch is not reachable from the current Chat tab', async () => {
    renderCrownBot();
    await waitFor(() => expect(getMock).toHaveBeenCalledWith('/bot/sessions'));

    fireEvent.click(screen.getByRole('button', { name: 'Chat' }));

    expect(screen.getByText("Cette fonction n’est pas accessible depuis cet écran.")).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Confirmer' })).not.toBeInTheDocument();
  });

  it('discards stale patient identity and unsent dossier draft when navigating to another patient', async () => {
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'true');
    postMock
      .mockResolvedValueOnce({ data: {
        status: 'clarification', message: 'Patient : saisissez un identifiant',
        proposal: null,
      } } as any)
      .mockResolvedValueOnce({ data: {
        status: 'read', message: 'Patient identifié dans votre cabinet.',
        patient: { id: 42, nom: 'ANCIEN', prenom: 'DOSSIER', numero_dossier: 'T2-042' },
        proposal: null,
      } } as any);
    const NavigateSyntheticPatient = () => {
      const navigate=useNavigate();
      return <button onClick={() => navigate('/patients/43')}>Autre dossier synthétique</button>;
    };
    render(
      <MemoryRouter initialEntries={['/patients/42']}>
        <CrownBotChat />
        <NavigateSyntheticPatient />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Chat', exact: true }));
    const region=screen.getByRole('region', { name: 'Simulation ZERO-LLM Crown Bot' });
    fireEvent.click(screen.getByRole('button', { name: '/patient' }));
    await screen.findByText('Patient : saisissez un identifiant');
    fireEvent.change(screen.getByRole('textbox', { name: 'Votre réponse de simulation' }), {
      target: { value: 'dossier:T2-042' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    await screen.findByText(/Dossier T2-042/);
    expect(postMock).toHaveBeenLastCalledWith('/bot/workflows/preview', {
      messages: ['/patient', 'dossier:T2-042'],
    });
    // A changed patient route must never show a previous patient's result.
    fireEvent.click(screen.getByRole('button', { name: 'Autre dossier synthétique' }));
    const newRegion=screen.getByRole('region', { name: 'Simulation ZERO-LLM Crown Bot' });
    expect(newRegion).not.toBe(region);
    expect(screen.queryByText(/Dossier T2-042/)).not.toBeInTheDocument();
    expect(screen.queryByText('Patient identifié dans votre cabinet.')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '/patient' })).toBeInTheDocument();
    expect(screen.queryByRole('textbox', { name: 'Votre réponse de simulation' })).not.toBeInTheDocument();
    expect(postMock).toHaveBeenCalledTimes(2);
    expect(postMock).not.toHaveBeenCalledWith('/bot/execute', expect.anything());
  });

  it('S10 UX: failed new preview never keeps the previous successful patient response visible', async () => {
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'true');
    postMock
      .mockResolvedValueOnce({ data: {
        status: 'read',
        message: 'Patient identifié dans votre cabinet.',
        patient: { id: 42, nom: 'ANCIEN', prenom: 'DOSSIER', numero_dossier: 'T2-042' },
        proposal: null,
      } } as any)
      .mockRejectedValueOnce({ response: { status: 503 } });
    renderCrownBot();
    fireEvent.click(screen.getByRole('button', { name: 'Chat', exact: true }));
    fireEvent.click(screen.getByRole('button', { name: '/patient' }));
    await screen.findByText('Patient identifié dans votre cabinet.');
    expect(screen.getByText(/Dossier T2-042/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '/rdv' }));
    await screen.findByText('Vérification serveur impossible. Aucune action effectuée.');
    expect(screen.queryByText('Patient identifié dans votre cabinet.')).not.toBeInTheDocument();
    expect(screen.queryByText(/Dossier T2-042/)).not.toBeInTheDocument();
    expect(screen.queryByText('Étapes saisies : 1/8')).not.toBeInTheDocument();
    expect(postMock).toHaveBeenLastCalledWith('/bot/workflows/preview', { messages: ['/rdv'] });
    expect(postMock).not.toHaveBeenCalledWith('/bot/execute', expect.anything());
  });

  it('exposes safe ZERO-LLM preview inside existing mobile-responsive Chat only when frontend opt-in is explicit', async () => {
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'true');
    postMock.mockResolvedValue({ data: {
      status: 'clarification', message: 'Identifiant numérique du patient ?',
    } } as any);
    renderCrownBot();
    await waitFor(() => expect(getMock).toHaveBeenCalledWith('/bot/sessions'));
    fireEvent.click(screen.getByRole('button', { name: 'Chat' }));
    expect(screen.getByRole('region', { name: 'Simulation ZERO-LLM Crown Bot' })).toBeInTheDocument();
    expect(screen.getByText(/aucune écriture/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '/rdv' }));
    await screen.findByText('Identifiant numérique du patient ?');
    expect(postMock).toHaveBeenCalledWith('/bot/workflows/preview', {
      messages: ['/rdv'],
    });
    expect(postMock).not.toHaveBeenCalledWith('/bot/execute', expect.anything());
    expect(screen.queryByRole('button', { name: 'Confirmer' })).not.toBeInTheDocument();
  });

});
