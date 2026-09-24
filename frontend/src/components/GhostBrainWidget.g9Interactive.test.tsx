import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../services/api', () => ({
  api: {
    post: vi.fn(),
  },
  API_BASE: 'http://127.0.0.1:8005',
}));

vi.mock('../stores/useAuthStore', () => ({
  useAuthStore: () => ({
    user: { id: 9, employer_id: 42 },
  }),
}));

import { api } from '../services/api';
import { GhostBrainWidget } from './GhostBrainWidget';

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

async function renderSeededWidget() {
  render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <GhostBrainWidget />
    </MemoryRouter>,
  );

  await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0));
  act(() => {
    FakeWebSocket.instances.at(-1)?.emit({
      unread_count: 1,
      insights: [{
        id: 601,
        insight_type: 'FINANCE',
        content: 'Impayé à vérifier',
        patient_id: 4,
        created_at: '2026-09-24T10:00:00Z',
      }],
    });
  });

  fireEvent.click(screen.getByTitle('Synthèse contextuelle'));
  await screen.findByRole('button', { name: /Marquer comme lu/i });
}

describe('GhostBrainWidget G9 read-ack truth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    FakeWebSocket.instances = [];
    localStorage.setItem('token', 'g9-token');
    vi.stubGlobal('WebSocket', FakeWebSocket as any);
    postMock.mockResolvedValue({ data: {} } as any);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it('keeps the insight visible when read persistence is refused', async () => {
    await renderSeededWidget();

    postMock.mockRejectedValueOnce(new Error('read refused'));
    fireEvent.click(screen.getByRole('button', { name: /Marquer comme lu/i }));

    await waitFor(() => {
      expect(postMock).toHaveBeenCalledWith('/ai/ghost-insights/601/read');
    });

    expect(screen.getByRole('button', { name: /Marquer comme lu/i })).toBeInTheDocument();
  });

  it('removes the insight only after backend ACK', async () => {
    await renderSeededWidget();

    fireEvent.click(screen.getByRole('button', { name: /Marquer comme lu/i }));

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /Marquer comme lu/i })).not.toBeInTheDocument();
    });
    expect(postMock).toHaveBeenCalledWith('/ai/ghost-insights/601/read');
    expect(screen.getByText('Aucune nouvelle déduction.')).toBeInTheDocument();
  });
});
