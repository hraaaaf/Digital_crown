import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const dashboardPath = path.resolve(__dirname, '../../pages/Dashboard.tsx');
const dayOneTourPath = path.resolve(__dirname, '../../components/DayOneTour.tsx');
const retiredGuidedTourFiles = [
  path.resolve(__dirname, '../../components/GuidedTour/GuidedTour.tsx'),
  path.resolve(__dirname, '../../components/GuidedTour/TourLauncher.tsx'),
  path.resolve(__dirname, '../../components/GuidedTour/tourConfig.ts'),
];
const sourceRoot = path.resolve(__dirname, '../..');
const thisTestPath = path.resolve(__filename);
const dashboardSource = fs.readFileSync(dashboardPath, 'utf8');

const collectSourceFiles = (dir: string): string[] => fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
  const entryPath = path.join(dir, entry.name);
  if (entry.isDirectory()) return collectSourceFiles(entryPath);
  return /\.(ts|tsx)$/.test(entry.name) ? [entryPath] : [];
});

const retiredAutoTourMarkers = [
  'Tour' + 'Launcher',
  'digitalcrown_' + 'tour_completed',
  'TOUR_' + 'STORAGE_KEY',
];

describe('Dashboard tutorial cleanup', () => {
  it('keeps Dashboard free of the retired automatic DayOneTour integration', () => {
    expect(dashboardSource).not.toContain('../components/DayOneTour');
    expect(dashboardSource).not.toContain('<DayOneTour />');
    expect(fs.existsSync(dayOneTourPath)).toBe(false);
  });

  it('keeps frontend source free of the retired automatic guided-tour system', () => {
    for (const retiredFile of retiredGuidedTourFiles) {
      expect(fs.existsSync(retiredFile), `${path.relative(sourceRoot, retiredFile)} still exists`).toBe(false);
    }

    const sourceFiles = collectSourceFiles(sourceRoot).filter((file) => path.resolve(file) !== thisTestPath);
    for (const file of sourceFiles) {
      const source = fs.readFileSync(file, 'utf8');
      for (const marker of retiredAutoTourMarkers) {
        expect(source, `${marker} found in ${path.relative(sourceRoot, file)}`).not.toContain(marker);
      }
    }
  });
});
