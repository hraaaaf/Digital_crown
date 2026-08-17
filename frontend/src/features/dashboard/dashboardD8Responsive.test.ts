import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = readFileSync(
  resolve(process.cwd(), 'src/features/dashboard/components/WaitingRoom.tsx'),
  'utf8',
);

describe('Dashboard D8 — responsive waiting room', () => {
  it('empile les rendez-vous et leurs actions sur mobile', () => {
    expect(source).toContain('flex flex-col sm:flex-row sm:items-center sm:justify-between');
    expect(source).toContain('w-full sm:w-auto min-h-11');
    expect(source).toContain('min-h-[410px] sm:h-[410px]');
  });

  it('ne réintroduit pas la ligne desktop-only qui débordait à 390 px', () => {
    expect(source).not.toContain('className="flex items-center justify-between p-4 bg-white/40');
  });
});
