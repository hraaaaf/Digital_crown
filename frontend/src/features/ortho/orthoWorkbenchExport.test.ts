import { describe, expect, it } from 'vitest';
import {
  createDefaultLayerOpacity,
  createDefaultLayerVisibility,
} from './orthoLayerRegistry';
import { buildOrthoWorkbenchExportPresentationState } from './orthoWorkbenchExport';

describe('LOT07-G workbench export presentation serializer', () => {
  it('serializes presentation state without accepting scientific calculation inputs', () => {
    const state = buildOrthoWorkbenchExportPresentationState({
      timepoint: 'T0',
      layerVisibility: createDefaultLayerVisibility(),
      layerOpacity: createDefaultLayerOpacity(),
      sessionEditAudit: [{
        sequence: 1,
        action: 'EDIT',
        transactionId: 'landmark-edit-1',
        changedLandmarkIds: ['A'],
      }],
    });

    expect(state.timepoint).toBe('T0');
    expect(state.layer_visibility.hard_tissue).toBe(false);
    expect(state.traced_structures).toEqual([]);
    expect(state.session_edit_audit[0].changedLandmarkIds).toEqual(['A']);
    expect(state).not.toHaveProperty('landmarks');
    expect(state).not.toHaveProperty('measurements');
    expect(state).not.toHaveProperty('constructions');
    expect(state).not.toHaveProperty('calibration');
  });

  it('keeps traced structures explicitly display-only or derived', () => {
    const now = '2026-10-03T10:00:00Z';
    const state = buildOrthoWorkbenchExportPresentationState({
      timepoint: 'T1',
      layerVisibility: createDefaultLayerVisibility(),
      layerOpacity: createDefaultLayerOpacity(),
      tracedStructures: [{
        structure_id: 'soft_tissue_profile',
        structure_class: 'SOFT_TISSUE_PROFILE',
        authority_state: 'DISPLAY_TEMPLATE_ONLY',
        coordinate_space: 'IMAGE_PIXEL',
        version: 'LOT07-DISPLAY-V1',
        source_record_id: 'analysis:7',
        created_at: now,
        updated_at: now,
        provenance: { renderer: 'CephaloTracingLayerBase' },
        edit_history: [],
      }],
    });

    expect(state.traced_structures[0].authority_state).toBe('DISPLAY_TEMPLATE_ONLY');
  });
});
