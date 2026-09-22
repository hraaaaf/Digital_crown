import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { PatientCompanionNotifications } from './PatientCompanionNotifications';
import { PatientCompanionNotificationTransport } from './PatientCompanionNotificationTransport';

vi.mock('./PatientCompanionNotificationTransport', () => ({
  PatientCompanionNotificationTransport: {
    sendNotificationCommand: vi.fn(),
  },
}));

const pairing = {
  accessToken: 'token',
  context: {
    access_id: 'pc05-access',
    relationship_type: 'SELF',
    patient: { display_name: 'Aya Test' },
  },
  pairedAt: '2026-09-20T20:00:00Z',
};

const item = {
  notification_id: 'n-1',
  category: 'consents',
  kind: 'CONSENT_PENDING',
  title: 'Signature en attente',
  message: 'Consentement traitement',
  created_at: '2026-09-20T19:00:00Z',
  priority: 'action',
};

const response = {
  items: [item],
  preferences: {
    appointments: true,
    documents: true,
    questionnaires: true,
    consents: true,
  },
};

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn());
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('PatientCompanionNotifications PC-05', () => {
  it('does not contact the cabinet until companion sync enables the surface', () => {
    render(<PatientCompanionNotifications pairing={pairing} enabled={false} />);
    expect(screen.getByText(/Synchronisez votre espace/i)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('removes a read item only after an authoritative ACCEPTED ACK and reload', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => response,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...response, items: [] }),
      } as Response);
    vi.mocked(PatientCompanionNotificationTransport.sendNotificationCommand).mockResolvedValue({
      status: 'ACCEPTED',
      result: { code: 'NOTIFICATION_READ' },
      messageId: 'm',
      idempotencyKey: 'i',
    });

    render(<PatientCompanionNotifications pairing={pairing} enabled />);
    expect(await screen.findByText('Signature en attente')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Lu'));

    await waitFor(() => expect(PatientCompanionNotificationTransport.sendNotificationCommand).toHaveBeenCalledWith(
      pairing,
      'notification.read',
      { notification_id: 'n-1' },
    ));
    expect(await screen.findByText(/Notification marquée comme lue par le cabinet/i)).toBeInTheDocument();
    expect(screen.queryByText('Signature en attente')).not.toBeInTheDocument();
  });

  it('keeps the item visible while a relay ACK is pending', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => response,
    } as Response);
    vi.mocked(PatientCompanionNotificationTransport.sendNotificationCommand)
      .mockRejectedValue(Object.assign(new Error('pending'), { remotePending: true }));

    render(<PatientCompanionNotifications pairing={pairing} enabled />);
    expect(await screen.findByText('Signature en attente')).toBeInTheDocument();
    fireEvent.click(screen.getByText('24 h'));

    expect(await screen.findByText(/confirmation cabinet encore en attente/i)).toBeInTheDocument();
    expect(screen.getByText('Signature en attente')).toBeInTheDocument();
  });

  it('does not claim preference changes before ACK', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => response,
    } as Response);
    vi.mocked(PatientCompanionNotificationTransport.sendNotificationCommand)
      .mockRejectedValue(Object.assign(new Error('pending'), { remotePending: true }));

    render(<PatientCompanionNotifications pairing={pairing} enabled />);
    expect(await screen.findByText('Signature en attente')).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('Régler les notifications'));
    const checkbox = screen.getByLabelText('Rendez-vous');
    fireEvent.click(checkbox);
    fireEvent.click(screen.getByText('Enregistrer les préférences'));

    expect(await screen.findByText(/Les réglages précédents restent actifs/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Rendez-vous')).toBeChecked();
  });
});
