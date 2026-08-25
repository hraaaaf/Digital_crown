import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const creds = {
  publicId: '0123456789abcdef',
  masterKey: 'a'.repeat(64),
  access_token: 'audit-token',
  refresh_token: 'audit-refresh',
  device_id: '11111111-1111-4111-8111-111111111111',
  api_base_url: 'http://127.0.0.1:8005',
};

const initialAlerts = [
  { id: 71, patient_id: 12, patient_name: 'Patient Test', type: 'OVERDUE_PAYMENT', title: 'Paiement à surveiller', message: 'Action administrative.', priority: 1 },
  { id: 72, patient_id: null, patient_name: null, type: 'STOCK_GANTS', title: 'Stock à anticiper', message: 'Seuil de vigilance.', priority: 2 },
];

let getCount = 0;
let resolveStaleGet: ((response: Response) => void) | null = null;
const mobileFetchMock = vi.fn();

vi.mock('../services/zka/MobileStorage', () => ({
  MobileStorage: {
    getCredentials: vi.fn(async () => creds),
  },
}));

vi.mock('../services/zka/mobileFetch', () => ({
  mobileFetch: (...args: unknown[]) => mobileFetchMock(...args),
}));

import { MobileNotificationCenter } from '../features/mobile/Dashboard/components/MobileNotificationCenter';

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

beforeEach(() => {
  getCount = 0;
  resolveStaleGet = null;
  mobileFetchMock.mockReset();
  mobileFetchMock.mockImplementation((input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = String(input);
    const method = init.method ?? 'GET';
    if (method === 'GET' && url.endsWith('/api/mobile/notifications')) {
      getCount += 1;
      if (getCount === 1) {
        return Promise.resolve(jsonResponse({ total: 2, alerts: initialAlerts }));
      }
      if (getCount === 2) {
        return new Promise<Response>(resolve => { resolveStaleGet = resolve; });
      }
      return Promise.resolve(jsonResponse({ total: 1, alerts: [initialAlerts[1]] }));
    }
    if (method === 'PATCH' && url.endsWith('/api/mobile/notifications/71/read')) {
      return Promise.resolve(jsonResponse({ status: 'ok' }));
    }
    if (method === 'PATCH' && url.endsWith('/api/mobile/notifications/72/snooze')) {
      return Promise.resolve(jsonResponse({ status: 'ok', snoozed_until: '2026-08-26T20:20:00' }));
    }
    return Promise.resolve(new Response(JSON.stringify({ detail: 'unexpected' }), { status: 404 }));
  });
});

describe('M6-D1 notification center diagnostic', () => {
  it('keeps the read mutation when an older open-triggered GET resolves afterwards', async () => {
    const user = userEvent.setup();
    render(<MobileNotificationCenter />);

    const bell = await screen.findByRole('button', { name: 'Notifications, 2 non lues' });
    await user.click(bell);
    expect(resolveStaleGet).not.toBeNull();

    await user.click((await screen.findAllByRole('button', { name: 'Lu' }))[0]);
    await screen.findByText('1 non lue');

    resolveStaleGet?.(jsonResponse({ total: 2, alerts: initialAlerts }));
    await waitFor(() => {
      expect(screen.getByText('1 non lue')).toBeInTheDocument();
      expect(screen.queryByText('2 non lues')).not.toBeInTheDocument();
    });

    expect(mobileFetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/mobile/notifications/71/read'),
      expect.objectContaining({ method: 'PATCH' }),
    );
  });

  it('confirms the current dialog is trapped inside its rendering ancestor', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <div data-testid="header-stacking-context">
        <MobileNotificationCenter />
      </div>,
    );
    await user.click(await screen.findByRole('button', { name: 'Notifications, 2 non lues' }));
    const dialog = await screen.findByRole('dialog', { name: 'Notifications' });
    expect(container.contains(dialog)).toBe(true);
  });
});
