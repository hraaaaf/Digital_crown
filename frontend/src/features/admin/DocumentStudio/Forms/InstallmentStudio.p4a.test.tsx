import { render, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { InstallmentStudio } from './InstallmentStudio';
import { api } from '../../../../services/api';
import { PriceBrain } from '../../../../components/odontogram/PriceBrain';

vi.mock('../../../../services/api', () => ({
  api: { get: vi.fn() },
}));

vi.mock('../../../../components/odontogram/PriceBrain', () => ({
  PriceBrain: {
    suggestInstallmentPlan: vi.fn(() => ({ advance: 500, months: 6, monthly: 400 })),
    recordInstallmentPlan: vi.fn(),
  },
}));

describe('InstallmentStudio P4-A financial inference boundary', () => {
  it('n’applique ni ne consulte automatiquement une suggestion financière PriceBrain', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => ({
      data: url.startsWith('/patients/') ? { telephone: '' } : [],
    }) as never);

    render(<InstallmentStudio patientId="42" onPayloadChange={vi.fn()} />);

    await waitFor(() => expect(api.get).toHaveBeenCalled());
    expect(PriceBrain.suggestInstallmentPlan).not.toHaveBeenCalled();
    expect(PriceBrain.recordInstallmentPlan).not.toHaveBeenCalled();
  });
});
