import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const ROOT = path.resolve(process.cwd(), 'src/features/ortho');
const read = (relative: string) => fs.readFileSync(path.join(ROOT, relative), 'utf8');

const LEGACY_SCIENTIFIC_HEX = [
  '#00f5ff', '#8b5cf6', '#eab308', '#32cd32', '#ff8a65',
  '#67e8f9', '#f472b6', '#2dd4bf', '#c084fc', '#fb7185',
  '#facc15', '#fb923c', '#60a5fa', '#ec4899', '#ff00ff',
  '#ff0000', '#00ff00', '#ff6b6b', '#fca5a5',
];

const CONTRACT_OWNERS = [
  'cephaloVisualSemantics.ts',
  'CephaloTracingLayer.tsx',
  'CephaloTracingLayerBase.tsx',
  'components/CephaloAnalysisWorkbenchPanel.tsx',
  'components/CephaloLandmarkReticles.tsx',
  'components/CephaloSvgDefs.tsx',
  'components/CephaloCalibrationOverlay.tsx',
];

describe('Céphalo semantic color ownership audit', () => {
  it('keeps legacy scientific hex colors out of the migrated rendering path', () => {
    for (const file of CONTRACT_OWNERS) {
      const source = read(file).toLowerCase();
      for (const legacyHex of LEGACY_SCIENTIFIC_HEX) {
        expect(source, `${file} still contains ${legacyHex}`).not.toContain(legacyHex.toLowerCase());
      }
    }
  });

  it('keeps the table and tracing layers connected to the shared contract', () => {
    expect(read('components/CephaloAnalysisWorkbenchPanel.tsx')).toContain('cephaloMetricColor');
    expect(read('CephaloTracingLayer.tsx')).toContain('cephaloGeometryColor');
    expect(read('CephaloTracingLayerBase.tsx')).toContain('CEPHALO_SCIENTIFIC_COLORS');
  });
});
