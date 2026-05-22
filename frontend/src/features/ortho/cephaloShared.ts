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
  // Skeletal / Hard Tissue
  'S', 'N', 'Or', 'Po', 'A', 'B', 'Pog', 'Me', 'Gn', 'Go', 
  // Dental
  'L1_incisal', 'U1_incisal', 'U1_apex', 'L1_apex', 'U6', 'L6',
  // Soft Tissue
  'Ls_soft', 'Li_soft', 'Sn_soft', 'Pog_soft',
  'Ls2', 'Li2', 'Gn_soft', 'Me_soft', 'G_soft', 'N_soft', 'Cm', 'Prn',
  // Other Skeletal
  'PNS', 'ANS', 'Ar', 'D_point', 'Ptm', 'Co', 'Ba', 'PT_point', 'Bo', 'C_point'
] as const;
