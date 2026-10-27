/**
 * LOT07 R5 / 07-D — inert, fail-closed preference contract (DEV foundation).
 * Never persist this record to localStorage, Firebase, or an unauthenticated API.
 * Real storage MUST use an independently verified user + tenant + workstation
 * server scope, with fresh authorization on every restore and context change.
 */
import {
  authorizeLayout, projectLayoutPreference,
  type Geometry, type Layout, type LayoutPreference, type Slot, type WorkspaceContext,
} from './studioLayouts';

export type R5Signature = 'core' | 'iconic';
export type R5VerifiedScope = WorkspaceContext & Readonly<{ workstationVerified: boolean }>;
export type R5PreferenceRecord = Readonly<{
  version: 1;
  tenantId: string;
  userId: string;
  workstationId: string;
  signature: R5Signature;
  layout: LayoutPreference | null;
}>;
export type R5PreviewSession = Readonly<{
  applied: R5PreferenceRecord;
  preview: R5PreferenceRecord | null;
  previous: R5PreferenceRecord | null;
}>;

function safeScope(scope: R5VerifiedScope): boolean {
  return scope.authenticated === true && scope.workstationVerified === true &&
    typeof scope.tenantId === 'string' && scope.tenantId.trim().length > 0 &&
    typeof scope.userId === 'string' && scope.userId.trim().length > 0 &&
    typeof scope.workstationId === 'string' && scope.workstationId.trim().length > 0;
}

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value) &&
    (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null);
}

function onlyKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actual = Object.keys(value);
  return actual.length === keys.length && actual.every(key => keys.includes(key));
}

function isSignature(value: unknown): value is R5Signature {
  return value === 'core' || value === 'iconic';
}

/** Sanitized projection: no patient, clinical content, free-form labels, tokens or drafts. */
export function createR5Preference(
  scope: R5VerifiedScope, signature: R5Signature, layout: Layout | null, ratio = 50,
): R5PreferenceRecord | null {
  if (!safeScope(scope) || !isSignature(signature)) return null;
  let projected: LayoutPreference | null = null;
  if (layout !== null) {
    if (!Number.isFinite(ratio) || !authorizeLayout(layout,scope,ratio).ok) return null;
    projected = projectLayoutPreference(layout,scope.userId!,scope.workstationId!,ratio);
    if (!projected) return null;
  }
  return {
    version:1,tenantId:scope.tenantId!,userId:scope.userId!,
    workstationId:scope.workstationId!,signature,layout:projected,
  };
}

/** Reject untrusted persisted JSON instead of trusting TypeScript casts.
 * Replays the latest UI permission/desktop/patient checks, NOT server RBAC.
 */
export function readR5Preference(raw: unknown, scope: R5VerifiedScope): R5PreferenceRecord | null {
  if (!safeScope(scope) || !object(raw) ||
      !onlyKeys(raw,['version','tenantId','userId','workstationId','signature','layout']) ||
      raw.version !== 1 || raw.tenantId !== scope.tenantId ||
      raw.userId !== scope.userId || raw.workstationId !== scope.workstationId ||
      !isSignature(raw.signature)) return null;
  if (raw.layout === null) return createR5Preference(scope,raw.signature,null);

  const pref=raw.layout;
  if (!object(pref) || !onlyKeys(pref,['version','userId','workstationId','id','geometry','slots','ratio']) ||
      pref.version !== 1 || pref.userId !== scope.userId ||
      pref.workstationId !== scope.workstationId || typeof pref.id !== 'string' ||
      typeof pref.geometry !== 'string' || !Array.isArray(pref.slots) ||
      !Number.isInteger(pref.ratio) || (pref.ratio as number) < 37 || (pref.ratio as number) > 63) return null;
  if (!pref.slots.every(slot => object(slot) && onlyKeys(slot,['id','module']) &&
      typeof slot.id === 'string' && typeof slot.module === 'string')) return null;

  // The canonical registry validates module names, slot IDs, geometry and cardinality;
  // the reconstructed label is constant and cannot carry patient-identifying text.
  const layout: Layout={
    id:pref.id,label:'Préférence R5',geometry:pref.geometry as Geometry,
    slots:pref.slots as Slot[],
  };
  const clean=createR5Preference(scope,raw.signature,layout,pref.ratio as number);
  if (!clean?.layout || clean.layout.id !== pref.id || clean.layout.geometry !== pref.geometry ||
      clean.layout.ratio !== pref.ratio || clean.layout.slots.length !== pref.slots.length ||
      clean.layout.slots.some((slot,index) =>
        slot.id !== (pref.slots as Array<{id:string;module:string}>)[index].id ||
        slot.module !== (pref.slots as Array<{id:string;module:string}>)[index].module)) return null;
  return clean;
}

/** Volatile preview only. No I/O is performed by any of these transitions. */
export function beginR5Preview(
  applied: unknown, scope: R5VerifiedScope,
): R5PreviewSession | null {
  const clean=readR5Preference(applied,scope);
  return clean ? {applied:clean,preview:null,previous:null} : null;
}

export function previewR5Preference(
  session: R5PreviewSession, next: unknown, scope: R5VerifiedScope,
): R5PreviewSession | null {
  const applied=readR5Preference(session.applied,scope);
  const preview=readR5Preference(next,scope);
  return applied && preview ? {applied,preview,previous:session.previous} : null;
}

export function cancelR5Preview(
  session: R5PreviewSession, scope: R5VerifiedScope,
): R5PreviewSession | null {
  const applied=readR5Preference(session.applied,scope);
  return applied ? {applied,preview:null,previous:session.previous} : null;
}

export function applyR5Preview(
  session: R5PreviewSession, scope: R5VerifiedScope,
): R5PreviewSession | null {
  const current=readR5Preference(session.applied,scope);
  const next=readR5Preference(session.preview,scope);
  return current && next ? {applied:next,preview:null,previous:current} : null;
}

export function rollbackR5Preference(
  session: R5PreviewSession, scope: R5VerifiedScope,
): R5PreviewSession | null {
  const current=readR5Preference(session.applied,scope);
  const previous=readR5Preference(session.previous,scope);
  return current && previous ? {applied:previous,preview:null,previous:null} : null;
}
