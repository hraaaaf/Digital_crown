/**
 * LOT07 / 07.1.A+B — dormant declarative workspace primitives.
 * Never use this client-side catalogue to grant backend clinical permissions.
 */
export type Geometry = 'single' | 'two-columns' | 'two-rows' | 'three-columns' | 'hero-two' | 'grid-2x2' | 'focus-rail';
export type ModuleKey = 'dossier' | 'agenda' | 'imagerie' | 'galerie' | 'cephalo' | 'photos' | 'traitement' | 'suivi' | 'documents' | 'presentation';
export type Slot = Readonly<{ id: string; module: ModuleKey }>;
export type Layout = Readonly<{ id: string; label: string; geometry: Geometry; slots: readonly Slot[] }>;

export const GEOMETRIES: readonly Geometry[] = [
  'single', 'two-columns', 'two-rows', 'three-columns', 'hero-two', 'grid-2x2', 'focus-rail',
];

const MODULE_POLICY: Readonly<Record<ModuleKey, { patient: boolean; minWidth: number }>> = {
  dossier: { patient: true, minWidth: 440 }, agenda: { patient: false, minWidth: 390 },
  imagerie: { patient: true, minWidth: 450 }, galerie: { patient: true, minWidth: 320 },
  cephalo: { patient: true, minWidth: 560 }, photos: { patient: true, minWidth: 320 },
  traitement: { patient: true, minWidth: 500 }, suivi: { patient: true, minWidth: 440 },
  documents: { patient: true, minWidth: 400 }, presentation: { patient: true, minWidth: 680 },
};

/** Nine editable product starting points, NOT nine separately coded clinical UIs. */
export const PRESETS: readonly Layout[] = [
  { id: 'vue-ensemble', label: 'Vue d’ensemble', geometry: 'hero-two',
    slots: [{id:'dossier',module:'dossier'},{id:'agenda',module:'agenda'},{id:'imagerie',module:'imagerie'}] },
  { id: 'consultation', label: 'Consultation', geometry: 'two-columns',
    slots: [{id:'dossier',module:'dossier'},{id:'agenda',module:'agenda'}] },
  { id: 'agenda-cabinet', label: 'Agenda du cabinet', geometry: 'two-columns',
    slots: [{id:'agenda',module:'agenda'},{id:'dossier',module:'dossier'}] },
  { id: 'imagerie', label: 'Imagerie', geometry: 'two-columns',
    slots: [{id:'imagerie',module:'imagerie'},{id:'galerie',module:'galerie'}] },
  { id: 'comparaison-orthodontique', label: 'Comparaison orthodontique', geometry: 'three-columns',
    slots: [{id:'cephalo-t0',module:'cephalo'},{id:'cephalo-t1',module:'cephalo'},{id:'photos',module:'photos'}] },
  { id: 'planification-traitements', label: 'Planification des traitements', geometry: 'hero-two',
    slots: [{id:'traitement',module:'traitement'},{id:'dossier',module:'dossier'},{id:'imagerie',module:'imagerie'}] },
  { id: 'suivi-clinique', label: 'Suivi clinique', geometry: 'two-rows',
    slots: [{id:'suivi',module:'suivi'},{id:'photos',module:'photos'}] },
  { id: 'gestion-administrative', label: 'Gestion administrative', geometry: 'two-columns',
    slots: [{id:'agenda',module:'agenda'},{id:'documents',module:'documents'}] },
  { id: 'presentation-patient', label: 'Présentation au patient', geometry: 'single',
    slots: [{id:'presentation',module:'presentation'}] },
];

export function slotsRequired(geometry: Geometry): number {
  if (geometry === 'single') return 1;
  if (geometry === 'two-columns' || geometry === 'two-rows') return 2;
  if (geometry === 'grid-2x2') return 4;
  return 3;
}

export function validLayout(value: Layout): boolean {
  if (!GEOMETRIES.includes(value.geometry) || value.slots.length !== slotsRequired(value.geometry)) return false;
  if (!/^[a-z0-9-]{1,60}$/.test(value.id) || !value.label.trim() || value.label.length > 80) return false;
  const ids = new Set<string>();
  for (const slot of value.slots) {
    if (!/^[a-z0-9-]{1,60}$/.test(slot.id) || ids.has(slot.id) ||
        !Object.prototype.hasOwnProperty.call(MODULE_POLICY, slot.module)) return false;
    ids.add(slot.id);
  }
  return true;
}

export function getPreset(id: string): Layout | undefined {
  return PRESETS.find(preset => preset.id === id);
}

export type WorkspaceContext = Readonly<{
  authenticated: boolean;
  userId: string | null;
  workstationId: string | null;
  tenantId: string | null;
  patientId: number | null;
  cssViewportWidth: number;
  /** Input from actual server-verified permissions, NOT a client-side permission grant. */
  allowedModules: readonly ModuleKey[];
  /** May be supplied ONLY when independent per-slot state is proven, e.g. for two Céphalo views. */
  independentlyMountable?: readonly ModuleKey[];
}>;

export type Denial = 'INVALID_LAYOUT' | 'SESSION_NOT_VERIFIED' | 'DESKTOP_ONLY' |
  'PATIENT_MISSING' | 'MODULE_DENIED' | 'INSTANCE_ISOLATION_MISSING' | 'UNREADABLE_LAYOUT';
export type LayoutGate = { ok: false; reason: Denial } | { ok: true; layout: Layout };

function minimumWidth(layout: Layout): number {
  const width = (index: number) => MODULE_POLICY[layout.slots[index].module].minWidth;
  if (layout.geometry === 'single') return width(0);
  if (layout.geometry === 'two-rows') return Math.max(width(0), width(1));
  if (layout.geometry === 'two-columns') return width(0) + width(1) + 12;
  if (layout.geometry === 'three-columns') return width(0) + width(1) + width(2) + 24;
  if (layout.geometry === 'grid-2x2') return Math.max(width(0),width(2)) + Math.max(width(1),width(3)) + 12;
  return width(0) + Math.max(width(1),width(2)) + 12;
}

/** Defence-in-depth UI precondition. Real adapter MUST authorize per slot on server. */
export function authorizeLayout(layout: Layout | undefined, context: WorkspaceContext): LayoutGate {
  if (!layout || !validLayout(layout)) return {ok:false,reason:'INVALID_LAYOUT'};
  if (!context.authenticated || !context.userId?.trim() ||
      !context.workstationId?.trim() || !context.tenantId?.trim()) {
    return {ok:false,reason:'SESSION_NOT_VERIFIED'};
  }
  if (!Number.isFinite(context.cssViewportWidth) || context.cssViewportWidth < 1280) {
    return {ok:false,reason:'DESKTOP_ONLY'};
  }
  if (layout.slots.some(slot => MODULE_POLICY[slot.module].patient) &&
      (!Number.isSafeInteger(context.patientId) || Number(context.patientId) <= 0)) {
    return {ok:false,reason:'PATIENT_MISSING'};
  }
  if (layout.slots.some(slot => !context.allowedModules.includes(slot.module))) {
    return {ok:false,reason:'MODULE_DENIED'};
  }
  const seen = new Set<ModuleKey>();
  for (const slot of layout.slots) {
    if (seen.has(slot.module) && !context.independentlyMountable?.includes(slot.module)) {
      return {ok:false,reason:'INSTANCE_ISOLATION_MISSING'};
    }
    seen.add(slot.module);
  }
  if (context.cssViewportWidth < Math.max(1280, minimumWidth(layout))) {
    return {ok:false,reason:'UNREADABLE_LAYOUT'};
  }
  return {ok:true,layout};
}

export type LayoutPreference = Readonly<{
  version: 1; userId: string; workstationId: string; id: string; geometry: Geometry;
  slots: readonly Readonly<{id: string; module: ModuleKey}>[]; ratio: number;
}>;

/** Allowlist projection only. NO patient IDs, clinical subviews, media, tokens or drafts. */
export function projectLayoutPreference(layout: Layout, userId: string, workstationId: string, ratio = 50): LayoutPreference | null {
  if (!validLayout(layout) || !userId.trim() || !workstationId.trim() || !Number.isFinite(ratio)) return null;
  return {version:1,userId,workstationId,id:layout.id,geometry:layout.geometry,
    slots:layout.slots.map(slot => ({id:slot.id,module:slot.module})),
    ratio:Math.max(37,Math.min(63,Math.round(ratio)))};
}
