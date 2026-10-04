import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  CEPHALO_LOT06_FOCUS_REGISTRY,
} from './cephaloLot06FocusRegistry.generated';
import {
  resolveCanonicalMeasurementId,
  resolveCanonicalMetricFocus,
} from './cephaloCanonicalFocusAdapter';

describe('LOT07 canonical measure-to-geometry adapter', () => {
  it('is an exact generated projection of the LOT06 executable measurement contract', () => {
    const sourcePath = path.resolve(process.cwd(), '..', 'docs', 'audits', 'schemas', 'cephalo_vnext_lot06_executable_measurement_contract_v1.json');
    const source = JSON.parse(fs.readFileSync(sourcePath, 'utf8'));
    expect(Object.keys(CEPHALO_LOT06_FOCUS_REGISTRY).sort()).toEqual(
      source.measurements.map((item: any) => item.measurement_id).sort(),
    );
    for (const item of source.measurements) {
      expect(CEPHALO_LOT06_FOCUS_REGISTRY[item.measurement_id as keyof typeof CEPHALO_LOT06_FOCUS_REGISTRY]).toEqual({
        measurementId: item.measurement_id,
        unit: item.unit,
        requiredLandmarks: item.required_landmarks,
        requiredConstructions: item.required_constructions,
        sourceContracts: item.source_contracts,
        availabilityGate: item.availability_gate,
        requiresCalibration: Boolean(item.requires_calibration),
      });
    }
  });

  it('resolves direct canonical ids and uses LOT06 dependencies rather than frontend point fallbacks', () => {
    const metric = {
      canonical_measurement_id: 'M_SNA_DEG_V1',
      involved_points: ['WRONG_FRONTEND_POINT'],
      involved_lines: ['sn'],
    };
    const focus = resolveCanonicalMetricFocus('SNA', metric, { scientific_read_path: { authority: 'EVIDENCE_GRAPH_V1' } });
    expect(focus?.canonicalMeasurementId).toBe('M_SNA_DEG_V1');
    expect(focus?.points).toEqual(['S', 'N', 'A']);
    expect(focus?.points).not.toContain('WRONG_FRONTEND_POINT');
    expect(focus?.lines).toEqual(['sn']);
    expect(focus?.authority).toBe('LOT06_EXECUTABLE_MEASUREMENT_CONTRACT');
  });

  it('resolves canonical ids through scientific_read_path measurement refs', () => {
    const metric = { measurement_id: 'measurement:case:Situation_A' };
    const anglesData = {
      scientific_read_path: {
        authority: 'EVIDENCE_GRAPH_V1',
        canonical_measurements: [{
          canonical_measurement_id: 'M_A_NPERP_MM_V1',
          measurement_refs: ['measurement:case:Situation_A'],
        }],
      },
    };
    expect(resolveCanonicalMeasurementId(metric, anglesData)).toBe('M_A_NPERP_MM_V1');
    const focus = resolveCanonicalMetricFocus('Situation_A', metric, anglesData);
    expect(focus?.points).toEqual(['A', 'N', 'Po_anatomic', 'Or']);
    expect(focus?.constructionIds).toEqual(['FH_PO_OR_V1', 'NASION_VERTICAL_FH_V1']);
  });

  it('fails closed when runtime evidence cannot bind the displayed metric to a canonical LOT06 id', () => {
    expect(resolveCanonicalMeasurementId({ measurement_id: 'unknown' }, { scientific_read_path: { authority: 'EVIDENCE_GRAPH_V1', canonical_measurements: [] } })).toBeNull();
    expect(resolveCanonicalMetricFocus('SNA', { canonical_measurement_id: 'M_SNA_DEG_V1' }, {})).toBeNull();
    expect(resolveCanonicalMetricFocus('SNA', { involved_points: ['S', 'N', 'A'] }, { scientific_read_path: { authority: 'EVIDENCE_GRAPH_V1' } })).toBeNull();
  });

  it('drives COM focus styling from canonical construction ids rather than metric-name lists', () => {
    const tracingPath = path.resolve(process.cwd(), 'src', 'features', 'ortho', 'CephaloTracingLayer.tsx');
    const tracing = fs.readFileSync(tracingPath, 'utf8');
    expect(tracing).not.toContain("comStyle(['");
    expect(tracing).toContain('FH_PO_OR_V1');
    expect(tracing).toContain('NASION_VERTICAL_FH_V1');
    expect(tracing).toContain('CRANIOM_AB_PRIME_V1');
    expect(tracing).toContain('LOT06_EXECUTABLE_MEASUREMENT_CONTRACT');
  });

  it('removes frontend scientific geometry fallbacks from the analysis panel', () => {
    const panelPath = path.resolve(process.cwd(), 'src', 'features', 'ortho', 'components', 'CephaloAnalysisWorkbenchPanel.tsx');
    const panel = fs.readFileSync(panelPath, 'utf8');
    expect(panel).not.toContain('definition.points');
    expect(panel).not.toContain('definition.lines');
    expect(panel).not.toContain('activeDefinition.construction');
    expect(panel).toContain('resolveCanonicalMetricFocus');
  });
});
