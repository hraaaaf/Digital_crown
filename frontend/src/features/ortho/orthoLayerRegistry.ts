export type OrthoLayerId =
  | 'landmarks'
  | 'plans'
  | 'hard_tissue'
  | 'teeth'
  | 'soft_tissue'
  | 'measurements'
  | 't1'
  | 't2';

export type OrthoLayerAuthority =
  | 'measurement_authoritative'
  | 'derived_visualization'
  | 'display_template_only';

export interface OrthoLayerDefinition {
  id: OrthoLayerId;
  label: string;
  shortLabel: string;
  authority: OrthoLayerAuthority;
  defaultVisible: boolean;
  defaultOpacity: number;
  opacityAdjustable: boolean;
  availability: 'available' | 'planned';
  unavailableReason?: string;
}

export type OrthoLayerVisibility = Record<OrthoLayerId, boolean>;
export type OrthoLayerOpacity = Record<OrthoLayerId, number>;
export const ORTHO_LAYER_REGISTRY: readonly OrthoLayerDefinition[] = [
  { id: 'landmarks', label: 'Landmarks', shortLabel: 'Points', authority: 'derived_visualization', defaultVisible: true, defaultOpacity: 1, opacityAdjustable: true, availability: 'available' },
  { id: 'plans', label: 'Plans & constructions', shortLabel: 'Plans', authority: 'derived_visualization', defaultVisible: true, defaultOpacity: 1, opacityAdjustable: true, availability: 'available' },
  { id: 'hard_tissue', label: 'Tissus durs', shortLabel: 'Os', authority: 'display_template_only', defaultVisible: false, defaultOpacity: 0.85, opacityAdjustable: true, availability: 'planned', unavailableReason: 'Contours anatomiques versionnés non encore implémentés.' },
  { id: 'teeth', label: 'Dents', shortLabel: 'Dents', authority: 'display_template_only', defaultVisible: true, defaultOpacity: 1, opacityAdjustable: true, availability: 'available' },
  { id: 'soft_tissue', label: 'Tissus mous', shortLabel: 'Profil', authority: 'display_template_only', defaultVisible: true, defaultOpacity: 0.9, opacityAdjustable: true, availability: 'available' },
  { id: 'measurements', label: 'Annotations de mesure', shortLabel: 'Mesures', authority: 'derived_visualization', defaultVisible: true, defaultOpacity: 1, opacityAdjustable: true, availability: 'available' },
  { id: 't1', label: 'Projection T1', shortLabel: 'T1', authority: 'derived_visualization', defaultVisible: false, defaultOpacity: 0.5, opacityAdjustable: true, availability: 'available' },
  { id: 't2', label: 'Projection T2', shortLabel: 'T2', authority: 'derived_visualization', defaultVisible: false, defaultOpacity: 0.5, opacityAdjustable: true, availability: 'available' },
] as const;

export const clampLayerOpacity = (value: number): number =>
  Math.max(0.1, Math.min(1, Number.isFinite(value) ? value : 1));

export const createDefaultLayerVisibility = (): OrthoLayerVisibility =>
  Object.fromEntries(ORTHO_LAYER_REGISTRY.map(layer => [layer.id, layer.defaultVisible])) as OrthoLayerVisibility;

export const createDefaultLayerOpacity = (): OrthoLayerOpacity =>
  Object.fromEntries(ORTHO_LAYER_REGISTRY.map(layer => [layer.id, layer.defaultOpacity])) as OrthoLayerOpacity;
