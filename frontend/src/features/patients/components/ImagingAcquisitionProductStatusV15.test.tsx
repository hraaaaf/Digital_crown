import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ImagingAcquisitionProductStatusV15 } from './ImagingAcquisitionProductStatusV15';
import { api } from '../../../services/api';

vi.mock('../../../services/api', () => ({ api: { get: vi.fn() } }));
const get = vi.mocked(api.get);
const closed = {
  schema_version: 'dc06-product-status-v1',
  state: 'NATIVE_IPC_NOT_CONNECTED', read_only: true, acquisition_enabled: false,
  clinical_receipt_authorized: false, pending_captures: null,
  reason: 'WINDOWS_IPC_AND_TPM_PRODUCT_GATE_NOT_VERIFIED',
};

describe('LOT06 Phase2 product status — fail closed', () => {
  beforeEach(() => vi.resetAllMocks());

  it('reads real patient route without submitting capture or creating review authority', async () => {
    get.mockResolvedValue({ data: closed });
    render(<ImagingAcquisitionProductStatusV15 patientId={42} />);
    expect(screen.getByRole('status')).toHaveTextContent('Vérification');
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('non activée'));
    expect(get).toHaveBeenCalledWith('/patients/42/acquisition/status');
    expect(get).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('button')).toBeNull();
    expect(screen.queryByRole('checkbox')).toBeNull();
    expect(screen.queryByRole('img')).toBeNull();
  });

  it('does not trust a contradictory server response advertising acquisition enabled', async () => {
    get.mockResolvedValue({ data: { ...closed, acquisition_enabled: true, pending_captures: 1 } });
    render(<ImagingAcquisitionProductStatusV15 patientId={42} />);
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('indisponible'));
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('treats network/authorization failure as unavailable, never an empty queue', async () => {
    get.mockRejectedValue(new Error('private patient data must not surface'));
    render(<ImagingAcquisitionProductStatusV15 patientId={42} />);
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Aucune capture'));
    expect(screen.queryByText(/private patient data/)).toBeNull();
  });

  it('ignores a stale response from an earlier patient route', async () => {
    let finishOld!: (value: { data: unknown }) => void;
    get.mockImplementationOnce(() => new Promise(resolve => {
      finishOld = resolve as typeof finishOld;
    }) as ReturnType<typeof api.get>).mockResolvedValueOnce({ data: closed });
    const view = render(<ImagingAcquisitionProductStatusV15 patientId={42} />);
    view.rerender(<ImagingAcquisitionProductStatusV15 patientId={43} />);
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('non activée'));
    finishOld({ data: { ...closed, acquisition_enabled: true } });
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('non activée'));
    expect(get).toHaveBeenLastCalledWith('/patients/43/acquisition/status');
  });
});
