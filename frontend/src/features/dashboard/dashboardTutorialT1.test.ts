import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const dashboardPath = path.resolve(__dirname, '../../pages/Dashboard.tsx');
const dayOneTourPath = path.resolve(__dirname, '../../components/DayOneTour.tsx');
const dashboardSource = fs.readFileSync(dashboardPath, 'utf8');

describe('Dashboard tutorial cleanup', () => {
  it('keeps Dashboard free of the retired automatic DayOneTour integration', () => {
    expect(dashboardSource).not.toContain("../components/DayOneTour");
    expect(dashboardSource).not.toContain('<DayOneTour />');
    expect(fs.existsSync(dayOneTourPath)).toBe(false);
  });
});
