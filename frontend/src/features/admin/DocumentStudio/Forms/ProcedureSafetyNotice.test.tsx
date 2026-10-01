import React from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { api } from '../../../../services/api';
import {
  dispatchProcedureSafetyEvaluation,
  ProcedureSafetyNotice,
} from './ProcedureSafetyNotice';

vi.mock('../../../../services/api', () => ({
  api: {
    post: vi.fn(),
  },
}));

describe('ProcedureSafetyNotice', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing until explicit structured procedure context is dispatched', () => {
    render(<ProcedureSafetyNotice patientId="42" />);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('shows only the generic subtle clinical-review wording', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        status: 'CLINICAL_REVIEW_REQUIRED',
        alert_key: 'CLINICAL_REVIEW_RECOMMENDED',
        read_only: true,
      },
    } as any);

    render(<ProcedureSafetyNotice patientId="42" />);

    act(() => {
      dispatchProcedureSafetyEvaluation({
        patientId: 42,
        procedureDate: '2026-10-01',
        procedureBleedingRisk: 'HIGHER_POSTOP_BLEEDING_RISK',
        procedureOsseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
        procedureIsImplant: true,
      });
    });

    expect(await screen.findByText('Vérification clinique conseillée avant validation.')).toBeInTheDocument();
    expect(screen.queryByText(/MRONJ|endocard|anticoag|bisphosph|denosumab|CTX|drug holiday/i)).not.toBeInTheDocument();
  });

  it('maps every exposed key to short nontechnical wording only', async () => {
    const cases = [
      ['CONTEXT_REQUIRED', 'Contexte patient à compléter.'],
      ['PRESCRIBER_REVIEW_RECOMMENDED', 'Avis prescripteur recommandé.'],
      ['SPECIALIST_REVIEW_RECOMMENDED', 'Avis spécialisé recommandé.'],
    ] as const;

    const { rerender } = render(<ProcedureSafetyNotice patientId="42" />);

    for (const [key, message] of cases) {
      vi.mocked(api.post).mockResolvedValueOnce({
        data: { status: 'X', alert_key: key, read_only: true },
      } as any);

      act(() => {
        dispatchProcedureSafetyEvaluation({
          patientId: 42,
          procedureDate: '2026-10-01',
          procedureBleedingRisk: 'LOW_POSTOP_BLEEDING_RISK',
          procedureOsseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
        });
      });

      expect(await screen.findByText(message)).toBeInTheDocument();
      rerender(<ProcedureSafetyNotice patientId="42" />);
    }
  });

  it('stays silent on READY/null and wrong patient, but fails closed on unavailable/invalid responses', async () => {
    vi.mocked(api.post)
      .mockResolvedValueOnce({ data: { status: 'READY', alert_key: null, read_only: true } } as any)
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce({ data: { status: 'SPECIALIST_REVIEW_REQUIRED', alert_key: 'SPECIALIST_REVIEW_RECOMMENDED', read_only: false } } as any);

    render(<ProcedureSafetyNotice patientId="42" />);

    act(() => {
      dispatchProcedureSafetyEvaluation({
        patientId: 99,
        procedureDate: '2026-10-01',
        procedureBleedingRisk: 'LOW_POSTOP_BLEEDING_RISK',
        procedureOsseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
      });
    });
    expect(api.post).not.toHaveBeenCalled();

    act(() => {
      dispatchProcedureSafetyEvaluation({
        patientId: 42,
        procedureDate: '2026-10-01',
        procedureBleedingRisk: 'UNLIKELY_TO_CAUSE_BLEEDING',
        procedureOsseousRisk: 'NO_OSSEOUS_INJURY',
      });
    });
    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(1));
    expect(screen.queryByRole('status')).not.toBeInTheDocument();

    act(() => {
      dispatchProcedureSafetyEvaluation({
        patientId: 42,
        procedureDate: '2026-10-01',
        procedureBleedingRisk: 'LOW_POSTOP_BLEEDING_RISK',
        procedureOsseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
      });
    });
    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2));
    expect(await screen.findByText('Vérification clinique momentanément indisponible.')).toBeInTheDocument();

    act(() => {
      dispatchProcedureSafetyEvaluation({
        patientId: 42,
        procedureDate: '2026-10-01',
        procedureBleedingRisk: 'LOW_POSTOP_BLEEDING_RISK',
        procedureOsseousRisk: 'DENTOALVEOLAR_OSSEOUS_INJURY',
      });
    });
    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(3));
    expect(await screen.findByText('Vérification clinique momentanément indisponible.')).toBeInTheDocument();
  });
});
