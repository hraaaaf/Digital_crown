import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { PatientCompanionQuestionnaires } from './PatientCompanionQuestionnaires';

const pairing = {
  accessToken: 'token',
  context: {
    access_id: 'opaque-access',
    relationship_type: 'SELF',
    patient: { display_name: 'Aya Test' },
  },
  pairedAt: '2026-09-20T18:00:00Z',
};

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn());
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('PatientCompanionQuestionnaires PC-03', () => {
  it('does not contact the cabinet until the parent explicitly enables online sync', () => {
    render(<PatientCompanionQuestionnaires pairing={pairing} enabled={false} />);
    expect(screen.getByText(/Synchronisez votre espace/i)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('renders an assigned questionnaire and marks it sent only after cabinet ACK', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [{
            assignment_id: 'assignment-1',
            questionnaire_id: 'questionnaire-1',
            title: 'Questionnaire cabinet',
            version: 1,
            state: 'ASSIGNED',
            assigned_at: '2026-09-20T18:00:00Z',
            questions: [{ id: 'q1', label: 'Question test', type: 'yes_no', required: true, options: [] }],
          }],
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          submission_id: 'submission-1',
          status: 'PENDING_REVIEW',
          clinical_record_updated: false,
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [{
            assignment_id: 'assignment-1',
            questionnaire_id: 'questionnaire-1',
            title: 'Questionnaire cabinet',
            version: 1,
            state: 'PENDING_REVIEW',
            assigned_at: '2026-09-20T18:00:00Z',
            submitted_at: '2026-09-20T18:10:00Z',
            questions: [{ id: 'q1', label: 'Question test', type: 'yes_no', required: true, options: [] }],
          }],
        }),
      } as Response);

    render(<PatientCompanionQuestionnaires pairing={pairing} enabled />);

    expect(await screen.findByText('Questionnaire cabinet')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Remplir'));
    fireEvent.click(screen.getByText('Oui'));
    fireEvent.click(screen.getByText('Envoyer'));

    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
    expect(await screen.findByText(/Envoyé au cabinet · en attente de revue/i)).toBeInTheDocument();
    expect(screen.getByText('Envoyé · en attente de revue')).toBeInTheDocument();
  });

  it('never claims success when submission transport fails', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [{
            assignment_id: 'assignment-2',
            questionnaire_id: 'questionnaire-2',
            title: 'Questionnaire cabinet',
            version: 1,
            state: 'ASSIGNED',
            assigned_at: '2026-09-20T18:00:00Z',
            questions: [{ id: 'q1', label: 'Question test', type: 'yes_no', required: true, options: [] }],
          }],
        }),
      } as Response)
      .mockRejectedValueOnce(new Error('offline'));

    render(<PatientCompanionQuestionnaires pairing={pairing} enabled />);
    expect(await screen.findByText('Questionnaire cabinet')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Remplir'));
    fireEvent.click(screen.getByText('Non'));
    fireEvent.click(screen.getByText('Envoyer'));

    expect(await screen.findByText(/offline/i)).toBeInTheDocument();
    expect(screen.queryByText('Envoyé · en attente de revue')).not.toBeInTheDocument();
  });
});
