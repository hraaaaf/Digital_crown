import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const dayOneTourSource = fs.readFileSync(
  path.resolve(__dirname, '../../components/DayOneTour.tsx'),
  'utf8',
);

describe('Dashboard tutorial T1 neutralization', () => {
  it('keeps DayOneTour free of automatic runtime side effects', () => {
    expect(dayOneTourSource).toContain('export const DayOneTour: React.FC = () => null');
    expect(dayOneTourSource).not.toContain('setTimeout');
    expect(dayOneTourSource).not.toContain('localStorage');
    expect(dayOneTourSource).not.toContain('react-joyride');
  });
});
