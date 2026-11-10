/** J2.1 FUE-only consumer. NOT imported by active clinical UI or release builds.
 * No clinical authority, inference validation or calibrated measurement enabled.
 */
import { api } from '../../services/api';

export type NonclinicalSceneLandmark = {
  id: string;
  x: number;
  y: number;
  origin: 'SRPOSE38_AUTO' | 'PRACTITIONER_EDIT' | 'CONSTRUCTED';
  score_status: 'AVAILABLE' | 'NOT_EMITTED';
  confidence: number | null;
};

export type NonclinicalPremiumScene = {
  schema_version: 'CEPH_PREMIUM_SCENE_V1_DRAFT';
  identity: {
    employer_id: number;
    patient_id: number;
    study_id: number;
    original_asset_id: number;
    original_sha256: string;
    original_width: number;
    original_height: number;
    scientific_revision: number;
    scene_revision: number;
    parent_scene_sha256: string | null;
    detector_mapping_authority: 'LEGACY_LOCAL_UNVERIFIED';
  };
  landmarks: NonclinicalSceneLandmark[];
  contours: unknown[];
  constructions: unknown[];
  measurements: Array<{ id: string; status: 'RAW_NONCLINICAL' | 'UNAVAILABLE'; value: number | null }>;
  clinical_release: false;
  document_status: 'NONCLINICAL_DRAFT';
  [key: string]: unknown;
};

export type NonclinicalSceneEnvelope = {
  scene: NonclinicalPremiumScene;
  scene_sha256: string;
  scene_revision: number;
  verified_original: {
    study_id: number;
    patient_id: number;
    asset_id: number;
    image_sha256: string;
    source_width: number;
    source_height: number;
    exif_orientation: number;
    clinical_release: false;
    image_used_by_srpose38_inference_verified: false;
  };
  scientific_digest_source_certified: false;
  clinical_release: false;
  desktop_fue_verified: false;
};

const SHA = /^[0-9a-f]{64}$/;

function fail(message: string): never {
  throw new Error(`CEPH J2.1 FUE: ${message}`);
}

export function assertSceneFUEDevGate(): void {
  if (import.meta.env.DEV !== true || import.meta.env.VITE_CEPH_J21_SCENE_FUE !== 'true') {
    fail('Disabled outside a deliberately isolated development session');
  }
}

function positiveInt(x: unknown): x is number {
  return Number.isSafeInteger(x) && (x as number) > 0;
}

function record(x: unknown): x is Record<string, unknown> {
  return typeof x === 'object' && x !== null && !Array.isArray(x);
}

export function assertNonclinicalSceneEnvelope(
  input: unknown, expected: { patientId: number; studyId: number },
): NonclinicalSceneEnvelope {
  if (!record(input) || !record(input.scene) || !record(input.verified_original)) fail('Missing scene or verified original');
  const scene = input.scene as Record<string, unknown>;
  const identity = scene.identity;
  const original = input.verified_original as Record<string, unknown>;
  if (!record(identity)) fail('Source identity missing');
  const i = identity as Record<string, unknown>;
  if (scene.schema_version !== 'CEPH_PREMIUM_SCENE_V1_DRAFT'
    || scene.clinical_release !== false || input.clinical_release !== false
    || input.desktop_fue_verified !== false || input.scientific_digest_source_certified !== false
    || scene.document_status !== 'NONCLINICAL_DRAFT') fail('Unapproved clinical state');
  if (!positiveInt(expected.patientId) || !positiveInt(expected.studyId)
    || i.patient_id !== expected.patientId || i.study_id !== expected.studyId
    || original.patient_id !== expected.patientId || original.study_id !== expected.studyId) {
    fail('Patient or study source mismatch');
  }
  if (!positiveInt(i.employer_id) || !positiveInt(i.original_asset_id)
    || original.asset_id !== i.original_asset_id
    || !positiveInt(i.original_width) || !positiveInt(i.original_height)
    || original.source_width !== i.original_width || original.source_height !== i.original_height
    || !positiveInt(i.scientific_revision) || !positiveInt(i.scene_revision)
    || i.scene_revision !== input.scene_revision
    || i.detector_mapping_authority !== 'LEGACY_LOCAL_UNVERIFIED') {
    fail('Invalid source/model metadata');
  }
  if (typeof i.original_sha256 !== 'string' || !SHA.test(i.original_sha256)
    || original.image_sha256 !== i.original_sha256
    || typeof input.scene_sha256 !== 'string' || !SHA.test(input.scene_sha256)
    || original.clinical_release !== false
    || original.image_used_by_srpose38_inference_verified !== false) {
    fail('Source or scene digest/authority failed');
  }
  if (!Array.isArray(scene.landmarks) || scene.landmarks.length < 1) fail('No landmarks to draw');
  const names = new Set<string>();
  for (const point of scene.landmarks) {
    if (!record(point) || typeof point.id !== 'string' || names.has(point.id)
      || typeof point.x !== 'number' || typeof point.y !== 'number'
      || !Number.isFinite(point.x) || !Number.isFinite(point.y)
      || point.x < 0 || point.y < 0 || point.x >= (i.original_width as number) || point.y >= (i.original_height as number)
      || !['SRPOSE38_AUTO', 'PRACTITIONER_EDIT', 'CONSTRUCTED'].includes(String(point.origin))) {
      fail('Invalid source-pixel landmark geometry');
    }
    names.add(point.id);
  }
  return input as NonclinicalSceneEnvelope;
}

export async function readNonclinicalPremiumScene(patientId: number, studyId: number) {
  assertSceneFUEDevGate();
  if (!positiveInt(patientId) || !positiveInt(studyId)) fail('Missing study identity');
  const response = await api.get(`/ia/analyses/${studyId}/premium-scene-fue`, {
    params: { patient_id: patientId },
  });
  return assertNonclinicalSceneEnvelope(response.data, { patientId, studyId });
}

export async function saveNonclinicalPremiumScene(
  patientId: number, studyId: number,
  scene: NonclinicalPremiumScene, expectedParentSha: string | null,
) {
  assertSceneFUEDevGate();
  if (!positiveInt(patientId) || !positiveInt(studyId)
    || scene.identity.patient_id !== patientId || scene.identity.study_id !== studyId
    || (expectedParentSha !== null && !SHA.test(expectedParentSha))) fail('Invalid CAS identity');
  const response = await api.post(`/ia/analyses/${studyId}/premium-scene-fue`, {
    scene, expected_parent_sha256: expectedParentSha,
  });
  return assertNonclinicalSceneEnvelope(response.data, { patientId, studyId });
}

export async function readSceneOriginalChecked(scene: NonclinicalSceneEnvelope): Promise<ArrayBuffer> {
  assertSceneFUEDevGate();
  const { patient_id: patientId, original_asset_id: assetId, original_sha256: sha } = scene.scene.identity;
  if (scene.verified_original.exif_orientation !== 1) fail('EXIF orientation not yet supported in FUE viewport');
  const response = await api.get(`/patients/${patientId}/assets/${assetId}/content`, {
    responseType: 'arraybuffer',
  });
  const bytes = response.data;
  if (!(bytes instanceof ArrayBuffer) || !globalThis.crypto?.subtle) fail('Original image bytes cannot be safely hashed');
  const hash = await globalThis.crypto.subtle.digest('SHA-256', bytes);
  const actual = Array.from(new Uint8Array(hash), b => b.toString(16).padStart(2, '0')).join('');
  if (actual !== sha) fail('Original radiograph changed after scene load');
  return bytes;
}
