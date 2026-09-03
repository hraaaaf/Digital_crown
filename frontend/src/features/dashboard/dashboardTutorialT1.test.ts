import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const dashboardPath = path.resolve(__dirname, '../../pages/Dashboard.tsx');
const dayOneTourPath = path.resolve(__dirname, '../../components/DayOneTour.tsx');
const guidedTourPath = path.resolve(__dirname, '../../components/GuidedTour');
const sourceRoot = path.resolve(__dirname, '../..');
const dashboardSource = fs.readFileSync(dashboardPath, 'utf8');

const collectSourceFiles = (dir: string): string[] => fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
  const entryPath = path.join(dir, entry.name);
  if (entry.isDirectory()) return collectSourceFiles(entryPath);
  return /\.(ts|tsx)$/.test(entry.name) ? [entryPath] : [];
});

const retiredMarkers = [
  'Tour' + 'Launcher',
  'Guided' + 'Tour',
  'digitalcrown_' + 'tour_completed',
  'TOUR_' + 'STORAGE_KEY',
];

describe('Dashboard tutorial cleanup', () => {
  it('keeps Dashboard free of the retired automatic DayOneTour integration', () => {
    expect(dashboardSource).not.toContain('../components/DayOneTour');
    expect(dashboardSource).not.toContain('<DayOneTour />');
    expect(fs.existsSync(dayOneTourPath)).toBe(false);
  });

  it('keeps frontend source free of the retired guided-tour auto-launch system', () => {
    expect(fs.existsSync(guidedTourPath)).toBe(false);

    const sourceFiles = collectSourceFiles(sourceRoot);
    for (const file of sourceFiles) {
      const source = fs.readFileSync(file, 'utf8');
      for (const marker of retiredMarkers) {
        expect(source, `${marker} found in ${path.relative(sourceRoot, file)}`).not.toContain(marker);
      }
    }
  });
});
