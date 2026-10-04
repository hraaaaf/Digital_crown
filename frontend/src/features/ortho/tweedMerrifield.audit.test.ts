import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const read = (relative: string) =>
  readFileSync(path.join(process.cwd(), 'src/features/ortho', relative), 'utf8');

describe('LOT08 Tweed-Merrifield authority audit', () => {
  it('uses generic Po for Tweed only when the verified canonical read-path certifies Po_anatomic', () => {
    const tracing = read('CephaloTracingLayerBase.tsx');
    expect(tracing).toContain("const poAnatomic = getPoint(finalPts, 'Po_anatomic') ?? (tweedPoAnatomicCertified ? po : undefined)");
    expect(tracing).toContain("showTweed ? seg(poAnatomic, or_, 'fh'");
    expect(tracing).toContain("showMcNamara ? seg(po, or_, 'fh'");
    expect(tracing).not.toContain("showTweed || showMcNamara ? seg(poAnatomic, or_, 'fh'");
    expect(tracing).toContain("const activeFrankfortPo = activeAnalysisKey === 'tweed' ? poAnatomic : po");
    expect(tracing).toContain('const wPo = (u1Dragged || frkDragged) ? activeFrankfortPo : null');
    const step1 = read('components/Step1CephaloBase.tsx');
    expect(step1).toContain('hasCertifiedTweedPoAnatomic(anglesData)');
    expect(step1).toContain('tweedPoAnatomicCertified={tweedPoAnatomicCertified}');
    const wrapper = read('CephaloTracingLayer.tsx');
    expect(wrapper).toContain("'po', 'po_anatomic', 'or', 'go', 'me'");
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
