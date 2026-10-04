import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const read = (relative: string) =>
  readFileSync(path.join(process.cwd(), 'src/features/ortho', relative), 'utf8');

describe('LOT08 Tweed-Merrifield authority audit', () => {
  it('uses the certified canonical Po bridge and refuses an unverified generic Po fallback', () => {
    const tracing = read('CephaloTracingLayerBase.tsx');
    expect(tracing).toContain("const poAnatomic = getPoint(finalPts, 'Po_anatomic') ?? (tweedPoAnatomicCertified ? po : undefined)");
    expect(tracing).toContain("showTweed ? seg(poAnatomic, or_, 'fh'");
    expect(tracing).not.toContain("showTweed || showMcNamara ? seg(po, or_, 'fh'");
    const step1 = read('components/Step1CephaloBase.tsx');
    expect(step1).toContain("scientific?.authority !== 'EVIDENCE_GRAPH_V1'");
    expect(step1).toContain("row?.availability_status === 'AVAILABLE'");
    expect(step1).toContain('tweedPoAnatomicCertified={tweedPoAnatomicCertified}');
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
