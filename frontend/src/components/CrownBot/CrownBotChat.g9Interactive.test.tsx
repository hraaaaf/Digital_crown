import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
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
  await screen.findByRole('button', { name: /Marquer comme lu/i });
}

describe('CrownBot G9 reachable interaction truth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
  });

  it('keeps an insight visible and unread when backend read-ack is refused', async () => {
    const onUnreadChange = renderCrownBot();
    await seedInsight();

    await waitFor(() => expect(onUnreadChange).toHaveBeenLastCalledWith(1));

    postMock.mockRejectedValueOnce(new Error('read refused'));
    fireEvent.click(screen.getByRole('button', { name: /Marquer comme lu/i }));

    await waitFor(() => {
      expect(postMock).toHaveBeenCalledWith('/ai/ghost-insights/501/read');
    });

    expect(screen.getByRole('button', { name: /Marquer comme lu/i })).toBeInTheDocument();
    expect(onUnreadChange).toHaveBeenLastCalledWith(1);
  });

  it('removes an insight and decrements unread only after backend read-ack succeeds', async () => {
    const onUnreadChange = renderCrownBot();
    await seedInsight();

    fireEvent.click(screen.getByRole('button', { name: /Marquer comme lu/i }));

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /Marquer comme lu/i })).not.toBeInTheDocument();
    });
    expect(postMock).toHaveBeenCalledWith('/ai/ghost-insights/501/read');
    expect(onUnreadChange).toHaveBeenLastCalledWith(0);
  });

  it('proves the conversation send/action branch is not reachable from the current Chat tab', async () => {
    renderCrownBot();
    await waitFor(() => expect(getMock).toHaveBeenCalledWith('/bot/sessions'));

    fireEvent.click(screen.getByRole('button', { name: 'Chat' }));

    expect(screen.getByText("Cette fonction n’est pas accessible depuis cet écran.")).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Confirmer' })).not.toBeInTheDocument();
  });
});
