import { describe, expect, it } from 'vitest';

import { moveAccountingLine } from './AccountingLineOrderPolicy';

const lines = [
  { id: 1, description: 'A' },
  { id: 2, description: 'B' },
  { id: 3, description: 'C' },
];

describe('AccountingLineOrderPolicy', () => {
  it('moves a line up without mutating the source array', () => {
    const moved = moveAccountingLine(lines, 2, 'UP');
    expect(moved.map(item => item.id)).toEqual([2, 1, 3]);
    expect(lines.map(item => item.id)).toEqual([1, 2, 3]);
  });

  it('moves a line down', () => {
    expect(moveAccountingLine(lines, 2, 'DOWN').map(item => item.id)).toEqual([1, 3, 2]);
  });

  it('keeps boundary lines stable', () => {
    expect(moveAccountingLine(lines, 1, 'UP')).toBe(lines);
    expect(moveAccountingLine(lines, 3, 'DOWN')).toBe(lines);
  });

  it('keeps unknown ids stable', () => {
    expect(moveAccountingLine(lines, 999, 'DOWN')).toBe(lines);
  });
});
