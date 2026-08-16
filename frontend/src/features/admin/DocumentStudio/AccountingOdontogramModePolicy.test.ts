import { describe, expect, it } from 'vitest';
import {
  isToothCompatibleWithOdontogramType,
  odontogramGroupSelection,
  odontogramQuickGroupKeys,
} from './AccountingOdontogramModePolicy';

describe('P3-C2 odontogram mode policy', () => {
  it('keeps adult shortcuts on permanent FDI teeth only', () => {
    expect(odontogramGroupSelection('ADULT', 'Q1')).toEqual([11, 12, 13, 14, 15, 16, 17, 18]);
    expect(odontogramQuickGroupKeys('ADULT')).toContain('S6');
    expect(isToothCompatibleWithOdontogramType('ADULT', 55)).toBe(false);
  });

  it('uses primary FDI quadrants for pediatric mode', () => {
    expect(odontogramGroupSelection('PEDIATRIC', 'Q5')).toEqual([51, 52, 53, 54, 55]);
    expect(odontogramGroupSelection('PEDIATRIC', 'Q8')).toEqual([81, 82, 83, 84, 85]);
    expect(odontogramQuickGroupKeys('PEDIATRIC')).toEqual(['Q5', 'Q6', 'Q7', 'Q8']);
    expect(isToothCompatibleWithOdontogramType('PEDIATRIC', 16)).toBe(false);
  });

  it('returns an empty selection for reset and unknown groups', () => {
    expect(odontogramGroupSelection('PEDIATRIC', 'none')).toEqual([]);
    expect(odontogramGroupSelection('ADULT', 'Q9')).toEqual([]);
  });
});
