import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  isPrescriptionDirty,
  setPrescriptionDirty,
  subscribePrescriptionDirty,
} from './PrescriptionDirtyState';

afterEach(() => {
  setPrescriptionDirty(false);
});

describe('PrescriptionDirtyState', () => {
  it('tracks dirty state deterministically', () => {
    expect(isPrescriptionDirty()).toBe(false);
    setPrescriptionDirty(true);
    expect(isPrescriptionDirty()).toBe(true);
    setPrescriptionDirty(false);
    expect(isPrescriptionDirty()).toBe(false);
  });

  it('notifies subscribers only when the value changes', () => {
    const listener = vi.fn();
    const unsubscribe = subscribePrescriptionDirty(listener);

    setPrescriptionDirty(true);
    setPrescriptionDirty(true);
    setPrescriptionDirty(false);

    expect(listener).toHaveBeenCalledTimes(2);
    expect(listener).toHaveBeenNthCalledWith(1, true);
    expect(listener).toHaveBeenNthCalledWith(2, false);

    unsubscribe();
  });
});
