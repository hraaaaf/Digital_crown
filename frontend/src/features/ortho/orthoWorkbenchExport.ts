import type { LandmarkEditAuditEvent } from './orthoLandmarkEditHistory';
import type { OrthoLayerOpacity, OrthoLayerVisibility } from './orthoLayerRegistry';

export type WorkbenchDisplayAuthority = 'DISPLAY_TEMPLATE_ONLY' | 'DERIVED_VISUALIZATION';
// Longitudinal registration is explicitly outside LOT07 authority.
export type WorkbenchCoordinateSpace = 'IMAGE_PIXEL' | 'CALIBRATED_MM';

export interface OrthoWorkbenchTracedStructure {
  structure_id: string;
  structure_class: string;
  authority_state: WorkbenchDisplayAuthority;
  coordinate_space: WorkbenchCoordinateSpace;
  version: string;
  source_record_id: string;
  created_at: string;
  updated_at: string;
  provenance: Record<string, unknown>;
  edit_history: Array<Record<string, unknown>>;
  geometry?: Record<string, unknown> | null;
}

export interface OrthoWorkbenchExportPresentationState {
  timepoint: 'T0' | 'T1' | 'T2' | 'T3' | 'OTHER';
  layer_visibility: OrthoLayerVisibility;
  layer_opacity: OrthoLayerOpacity;
  traced_structures: OrthoWorkbenchTracedStructure[];
  session_edit_audit: LandmarkEditAuditEvent[];
}

/**
 * Serialize presentation-only LOT07 state.
 *
 * Scientific landmarks, constructions, measurements and calibration are
 * intentionally absent. The backend resolves those from LOT06 typed evidence.
 */
export const buildOrthoWorkbenchExportPresentationState = ({
  timepoint,
  layerVisibility,
  layerOpacity,
  tracedStructures = [],
  sessionEditAudit = [],
}: {
  timepoint: OrthoWorkbenchExportPresentationState['timepoint'];
  layerVisibility: OrthoLayerVisibility;
  layerOpacity: OrthoLayerOpacity;
  tracedStructures?: OrthoWorkbenchTracedStructure[];
  sessionEditAudit?: LandmarkEditAuditEvent[];
}): OrthoWorkbenchExportPresentationState => ({
  timepoint,
  layer_visibility: { ...layerVisibility },
  layer_opacity: { ...layerOpacity },
  traced_structures: tracedStructures.map(item => ({
    ...item,
    provenance: { ...item.provenance },
    edit_history: item.edit_history.map(event => ({ ...event })),
    geometry: item.geometry ? { ...item.geometry } : item.geometry,
  })),
  session_edit_audit: sessionEditAudit.map(event => ({
    ...event,
    changedLandmarkIds: [...event.changedLandmarkIds],
  })),
});
