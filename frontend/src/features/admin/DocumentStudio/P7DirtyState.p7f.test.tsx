import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import TreatmentPlanStudio from './TreatmentPlanStudio';
import { isP7Dirty, setP7Dirty } from './P7DirtyState';

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock('../../../services/api', () => ({
  api: { get: mocks.get },
}));

describe('P7-F dirty-state boundary', () => {
  beforeEach(() => {
    setP7Dirty(false);
    mocks.get.mockReset();
    mocks.get.mockResolvedValue({ data: { antecedents_medicaux: '' } });
    vi.restoreAllMocks();
  });

  it('tracks P7 proposal dirtiness independently from Documents navigation', () => {
    expect(isP7Dirty()).toBe(false);
    setP7Dirty(true);
    expect(isP7Dirty()).toBe(true);
    setP7Dirty(false);
    expect(isP7Dirty()).toBe(false);
  });

  it('marks P7 dirty after interaction and clears it on explicit reset', async () => {
    render(<TreatmentPlanStudio patientId={1} />);
    await waitFor(() => expect(mocks.get).toHaveBeenCalledWith('/patients/1'));

    expect(isP7Dirty()).toBe(false);
    fireEvent.click(screen.getByRole('button', { name: 'Contrôle de routine / Tartre' }));
    expect(isP7Dirty()).toBe(true);

    fireEvent.click(screen.getByRole('button', { name: 'Recommencer le compagnon diagnostique' }));
    expect(isP7Dirty()).toBe(false);
  });

  it('prevents unload while a P7 proposal is dirty', async () => {
    render(<TreatmentPlanStudio patientId={1} />);
    await waitFor(() => expect(mocks.get).toHaveBeenCalledWith('/patients/1'));

    setP7Dirty(true);
    const event = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(true);
  });
});
