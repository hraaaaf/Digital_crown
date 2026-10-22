import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { CephaloAnalysisWorkbenchPanel } from './CephaloAnalysisWorkbenchPanel';
import { deriveCephaloMetricProvenance, rawCephaloMetricStatus } from '../cephaloMetricProvenance';

const state = vi.hoisted(() => ({
  analysisId: 27 as number | undefined,
  anglesData: {} as Record<string, any>,
  local: {landmarks: [] as any[]},
  activePointId: null as string | null,
  setActivePointId: vi.fn(),
}));

vi.mock('../stores/useOrthoStore', () => ({
  useOrthoStore: (selector: (value: typeof state) => unknown) => selector(state),
}));

const P: any = {
  bg: '#ffffff', bgPanel: '#ffffff', bgCard: '#ffffff', bgInput: '#f8fafc',
  border: '#dddddd', borderFocus: '#003380', text: '#111111',
  textMuted: '#666666', textDim: '#999999', accent: '#003380',
  accentSuccess: '#008800', accentWarning: '#aa6600', accentError: '#dd0000',
  shadow: 'none', shadowLg: 'none',
};

const automated = () => ({
  vision_metadata: {mode_inference: 'SOTA_ONNX_38'},
  metrics: {
    analyse_osseuse: {
      SNA: {value: 82.3, status: 'Normal', norm_mean: 82, availability_status: 'AVAILABLE'},
      SNB: {value: 80.1, status: 'Normal'},
    },
    analyse_dentaire: {},
    analyse_esthetique: {},
  },
});

beforeEach(() => {
  state.analysisId = 27;
  state.anglesData = automated();
  state.local = {landmarks: []};
  state.activePointId = null;
  vi.clearAllMocks();
});
afterEach(() => cleanup());

describe('R23-J clinical-authority guard — pure provenance', () => {
  it('identifies only real signed mode ID from study metadata as automatic, never as clinician approved', () => {
    const p = deriveCephaloMetricProvenance(automated(), 27);
    expect(p.origin).toBe('AUTOMATIC_SRPOSE38_UNREVIEWED');
    expect(p.methodLabel).toContain('SRPose38');
    expect(p.studyLabel).toBe('Étude #27');
    expect(p.clinicianValidated).toBe(false);
    expect(p.classificationAuthorized).toBe(false);
  });

  it('refuses fabricated clinician-validation fields and source-less records', () => {
    for (const x of [
      {vision_metadata: {mode_inference: 'SOTA_ONNX_38'}, validated_by: 'user', validated_at: '2026-10-22'},
      {vision_metadata: {mode_inference: 'T2_SEEDED_CERTIFIED_SRPOSE38'}, clinician_reviewed: true},
      {vision_metadata: {mode_inference: '<script>trust model</script>'}, clinical_release: true},
      {calibration_status: 'clinician_confirmed', verified: true},
    ]) {
      const p = deriveCephaloMetricProvenance(x, undefined);
      expect(p.clinicianValidated).toBe(false);
      expect(p.classificationAuthorized).toBe(false);
      expect(p.studyLabel).toBe('Étude non identifiée');
    }
  });

  it('keeps 0 and missing raw metrics NOT_COMPUTABLE; real angles remain raw', () => {
    expect(rawCephaloMetricStatus(true)).toBe('Mesure brute · non validée cliniquement');
    expect(rawCephaloMetricStatus(false)).toBe('Non calculable');
  });
});

describe('R23-J actual legacy All panel render — no fabricated clinical success', () => {
  it('keeps computed SNA/SNB in degrees while showing neutral count and explicit automatic provenance', () => {
    render(<CephaloAnalysisWorkbenchPanel P={P} analysis="all" />);
    const origin = document.querySelector('[data-r23j-provenance]');
    expect(origin?.getAttribute('data-r23j-provenance')).toBe('AUTOMATIC_SRPOSE38_UNREVIEWED');
    expect(origin?.textContent).toContain('SRPose38');
    expect(origin?.textContent).toContain('revue par un praticien non attestée');
    const count = document.querySelector('[data-r23j-raw-metric-count]') as HTMLElement;
    expect(count.textContent).toContain('2/15 mesures brutes calculées');
    expect(count.style.color).toBe('rgb(102, 102, 102)');
    const row = document.querySelector('[data-r19-metric="SNA"]');
    expect(row?.textContent).toContain('82,3 °');
    expect(row?.textContent).toContain('Réf.');
    const detail = document.querySelector('[data-r23j-metric-authority]');
    expect(detail?.getAttribute('data-r23j-metric-authority')).toBe('UNREVIEWED');
    expect(detail?.textContent).toContain('Mesure brute · non validée cliniquement');
    expect(detail?.querySelector('svg.lucide-circle-check-big,svg.lucide-check-circle-2')).toBeNull();
  });

  it('remains neutral even if server passes status Normal and availability AVAILABLE', () => {
    render(<CephaloAnalysisWorkbenchPanel P={P} analysis="all" />);
    expect(screen.queryByText('Normal')).toBeNull();
    expect(screen.queryByText('Validée')).toBeNull();
    expect(document.querySelector('[data-r23j-provenance]')?.textContent).toContain('valeurs non validées cliniquement');
  });

  it('never claims unknown method or reviewer status after switching to another study', () => {
    const first = render(<CephaloAnalysisWorkbenchPanel P={P} analysis="all" />);
    first.unmount();
    state.analysisId = 88;
    state.anglesData = {metrics: {analyse_osseuse: {SNA: {value: null}}}};
    render(<CephaloAnalysisWorkbenchPanel P={P} analysis="all" />);
    const banner = document.querySelector('[data-r23j-provenance]');
    expect(banner?.textContent).toContain('Origine des repères non attestée');
    expect(banner?.textContent).toContain('Étude #88');
    expect(banner?.textContent).not.toContain('SRPose38');
    expect(document.querySelector('[data-r23j-raw-metric-count]')?.textContent).toContain('0/15');
    expect(document.querySelector('[data-r23j-metric-authority]')?.textContent).toContain('Non calculable');
  });
});
