import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const read = (relative: string) =>
  readFileSync(path.join(process.cwd(), 'src/features/ortho', relative), 'utf8');

describe('LOT08 Tweed-Merrifield authority audit', () => {
  it('requires explicit Po_anatomic and never aliases generic Po', () => {
    const tracing = read('CephaloTracingLayerBase.tsx');
    expect(tracing).toContain("const poAnatomic = getPoint(finalPts, 'Po_anatomic')");
    expect(tracing).not.toContain("tweedPoAnatomicCertified ? po");
    expect(tracing).toContain("showTweed || showMcNamara ? seg(poAnatomic, or_, 'fh'");
    expect(tracing).not.toContain("showTweed || showMcNamara ? seg(po, or_, 'fh'");
    expect(tracing).toContain("const activeFrankfortPo = ['all', 'tweed', 'mcnamara'].includes(activeAnalysisKey) ? poAnatomic : po");
    expect(tracing).toContain('if (activeFrankfortPo && or_)');
    expect(tracing).toContain('const wPo = (u1Dragged || frkDragged) ? activeFrankfortPo : null');
  });

  it('renders the lower-incisor axis used by the canonical Tweed triangle', () => {
    const tracing = read('CephaloTracingLayerBase.tsx');
    expect(tracing).toContain("showTweed ? seg(l1a, l1i, 'l1'");
  });

  it('contains no frontend historical norm delta for Tweed-Merrifield', () => {
    const panel = read('components/CephaloAnalysisWorkbenchPanel.tsx');
    expect(panel).toContain("analysis === 'tweed' ? 'Contexte'");
    expect(panel).toContain("analysis === 'tweed' ? 'brute'");
    expect(panel).toContain("sans classification automatique");
    expect(panel).not.toMatch(/analysis === 'tweed'[\s\S]{0,180}reference_delta/);
  });
});
