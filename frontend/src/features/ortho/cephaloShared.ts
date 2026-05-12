export interface Landmark {
  id: string;
  x: number;
  y: number;
  isAdjusted?: boolean;
  version?: number;
}

export type CVMStage = 'CS1' | 'CS2' | 'CS3' | 'CS4' | 'CS5' | 'CS6';
export type UIMode = 'light' | 'dark';
export type StepId = 1 | 2 | 3 | 4;
export type SyncState = 'idle' | 'syncing' | 'success' | 'error';

export interface ImageFilters {
  brightness: number;
  contrast: number;
  invert: boolean;
}

export interface VTOSettings {
  enabled: boolean;
  showGhostFace: boolean;
  showSoftTissue: boolean;
  u1_offset: { x: number; y: number };
  l1_offset: { x: number; y: number };
  mand_offset: { x: number; y: number };
}

export const REQUIRED_LANDMARKS = [
  'Po', 'Or', 'N', 'S', 'A', 'B', 'Go', 'Me',
  'U1_incisal', 'U1_apex', 'L1_incisal', 'L1_apex',
] as const;
