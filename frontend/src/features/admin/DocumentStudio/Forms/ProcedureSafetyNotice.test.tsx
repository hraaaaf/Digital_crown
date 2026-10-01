import React from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { api } from '../../../../services/api';
import { ProcedureSafetyNotice } from './ProcedureSafetyNotice';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

describe('ProcedureSafetyNotice', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('stays absent for an invalid/no-patient context', () => {
    render(<ProcedureSafetyNotice patientId="0" />);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(api.get).not.toHaveBeenCalled();
  });

  it('renders only the generic subtle clinical-review wording', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        status: 'CLINICAL_REVIEW_REQUIRED',
        alert_key: 'CLINICAL_REVIEW_RECOMMENDED',
        read_only: true,
      },
    } as any);

    render(<ProcedureSafetyNotice patientId="42" />);

    expect(await screen.findByText('Vérification clinique conseillée avant validation.')).toBeInTheDocument();
    expect(screen.queryByText(/MRONJ|endocard|anticoag|bisphosph|denosumab|CTX|drug holiday/i)).not.toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith(
      '/prescriptions/clinical-rules/procedure-safety/alert/42',
      { params: {} },
    );
  });

  it('passes only exact presentation identity when supplied', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { status: 'READY', alert_key: null, read_only: true },
    } as any);

    render(<ProcedureSafetyNotice patientId="42" presentationId="rx-123" />);

    await waitFor(() => expect(api.get).toHaveBeenCalledWith(
      '/prescriptions/clinical-rules/procedure-safety/alert/42',
      { params: { presentation_id: 'rx-123' } },
    ));
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('maps exposed keys to short nontechnical wording only', async () => {
    const cases = [
      ['CONTEXT_REQUIRED', 'Contexte patient à compléter.'],
      ['PRESCRIBER_REVIEW_RECOMMENDED', 'Avis prescripteur recommandé.'],
      ['SPECIALIST_REVIEW_RECOMMENDED', 'Avis spécialisé recommandé.'],
    ] as const;

    const { rerender } = render(<ProcedureSafetyNotice patientId="42" />);
    for (const [key, message] of cases) {
      vi.mocked(api.get).mockResolvedValueOnce({
        data: { status: 'X', alert_key: key, read_only: true },
      } as any);
      rerender(<ProcedureSafetyNotice patientId={String(Math.random())} />);
      expect(await screen.findByText(message)).toBeInTheDocument();
    }
  });

  it('fails closed on backend failure or non-read-only response', async () => {
    vi.mocked(api.get)
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce({
        data: {
          status: 'SPECIALIST_REVIEW_REQUIRED',
          alert_key: 'SPECIALIST_REVIEW_RECOMMENDED',
          read_only: false,
        },
      } as any);

    const { rerender } = render(<ProcedureSafetyNotice patientId="42" />);
    expect(await screen.findByText('Vérification clinique momentanément indisponible.')).toBeInTheDocument();

    rerender(<ProcedureSafetyNotice patientId="43" />);
    expect(await screen.findByText('Vérification clinique momentanément indisponible.')).toBeInTheDocument();
  });

  it('refreshes after structured backoffice context update events', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { status: 'READY', alert_key: null, read_only: true } } as any)
      .mockResolvedValueOnce({
        data: {
          status: 'SPECIALIST_REVIEW_REQUIRED',
          alert_key: 'SPECIALIST_REVIEW_RECOMMENDED',
          read_only: true,
        },
      } as any);

    render(<ProcedureSafetyNotice patientId="42" />);
    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(1));

    act(() => {
      window.dispatchEvent(new CustomEvent('digitalcrown:procedure-safety-context-updated', {
        detail: { patientId: 42 },
      }));
    });

    expect(await screen.findByText('Avis spécialisé recommandé.')).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledTimes(2);
  });
});
