import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { createHash, webcrypto } from 'node:crypto';
import { api } from '../../services/api';
import {
  assertNonclinicalSceneEnvelope,
  readNonclinicalPremiumScene,
  readSceneOriginalChecked,
  saveNonclinicalPremiumScene,
  type NonclinicalSceneEnvelope,
} from './cephPremiumSceneFUEClient';

vi.mock('../../services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));

const SHA_IMAGE = 'a'.repeat(64);
const SHA_SCENE = 'b'.repeat(64);
const binary = new Uint8Array([80, 78, 71, 0, 1, 2]).buffer;
const realSha = createHash('sha256').update(new Uint8Array(binary)).digest('hex');

function envelope(imageSha = SHA_IMAGE): NonclinicalSceneEnvelope {
  return {
    scene_sha256: SHA_SCENE,
    scene_revision: 1,
    scientific_digest_source_certified: false,
    clinical_release: false,
    desktop_fue_verified: false,
    verified_original: {
      study_id: 33, patient_id: 22, asset_id: 44,
      image_sha256: imageSha, source_width: 640, source_height: 480,
      exif_orientation: 1, clinical_release: false,
      image_used_by_srpose38_inference_verified: false,
    },
    scene: {
      schema_version: 'CEPH_PREMIUM_SCENE_V1_DRAFT',
      identity: {
        employer_id: 11, patient_id: 22, study_id: 33,
        original_asset_id: 44, original_sha256: imageSha,
        original_width: 640, original_height: 480,
        scientific_revision: 1, scene_revision: 1,
        parent_scene_sha256: null,
        detector_mapping_authority: 'LEGACY_LOCAL_UNVERIFIED',
      },
      document_status: 'NONCLINICAL_DRAFT',
      clinical_release: false,
      landmarks: [{ id: 'S', x: 80, y: 90, origin: 'SRPOSE38_AUTO', score_status: 'NOT_EMITTED', confidence: null }],
      contours: [], constructions: [], measurements: [],
    },
  };
}

beforeEach(() => {
  vi.stubEnv('DEV', true);
  vi.stubEnv('VITE_CEPH_J21_SCENE_FUE', 'true');
  vi.stubGlobal('crypto', webcrypto);
  vi.clearAllMocks();
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe('J2.1 FUE-only frontend source-lock client (not mounted)', () => {
  it('refuses calls when explicit development flag is absent', async () => {
    vi.stubEnv('VITE_CEPH_J21_SCENE_FUE', 'false');
    await expect(readNonclinicalPremiumScene(22, 33)).rejects.toThrow(/Disabled/);
    expect(api.get).not.toHaveBeenCalled();
  });

  it('fails closed on patient, source, clinical authority and pixel bounds mismatches', () => {
    expect(assertNonclinicalSceneEnvelope(envelope(), { patientId: 22, studyId: 33 }).scene_revision).toBe(1);
    expect(() => assertNonclinicalSceneEnvelope(envelope(), { patientId: 23, studyId: 33 })).toThrow(/mismatch/);
    const changedClinical = structuredClone(envelope()) as unknown as Record<string, unknown>;
    changedClinical.clinical_release = true;
    expect(() => assertNonclinicalSceneEnvelope(changedClinical, { patientId: 22, studyId: 33 })).toThrow(/Unapproved/);
    const wrongSource = envelope();
    wrongSource.verified_original.image_sha256 = 'f'.repeat(64);
    expect(() => assertNonclinicalSceneEnvelope(wrongSource, { patientId: 22, studyId: 33 })).toThrow(/digest/);
    const overrun = envelope();
    overrun.scene.landmarks[0].x = 640;
    expect(() => assertNonclinicalSceneEnvelope(overrun, { patientId: 22, studyId: 33 })).toThrow(/geometry/);
  });

  it('GET and CAS POST keep the identity, and server response is revalidated', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: envelope() } as never);
    const got = await readNonclinicalPremiumScene(22, 33);
    expect(got.scene_sha256).toBe(SHA_SCENE);
    expect(api.get).toHaveBeenCalledWith('/ia/analyses/33/premium-scene-fue', { params: { patient_id: 22 } });
    vi.mocked(api.post).mockResolvedValue({ data: envelope() } as never);
    await saveNonclinicalPremiumScene(22, 33, got.scene, null);
    expect(api.post).toHaveBeenCalledWith('/ia/analyses/33/premium-scene-fue',
      { scene: got.scene, expected_parent_sha256: null });
    await expect(saveNonclinicalPremiumScene(23, 33, got.scene, null)).rejects.toThrow(/CAS identity/);
  });

  it('does not display EXIF rotated originals or SHA-altered bytes', async () => {
    const exif = envelope(realSha);
    exif.verified_original.exif_orientation = 6;
    await expect(readSceneOriginalChecked(exif)).rejects.toThrow(/EXIF/);
    expect(api.get).not.toHaveBeenCalled();

    const good = envelope(realSha);
    vi.mocked(api.get).mockResolvedValue({ data: binary } as never);
    const bytes = await readSceneOriginalChecked(good);
    expect(bytes).toBe(binary);
    expect(api.get).toHaveBeenCalledWith('/patients/22/assets/44/content', { responseType: 'arraybuffer' });
    const compromised = envelope('f'.repeat(64));
    await expect(readSceneOriginalChecked(compromised)).rejects.toThrow(/changed/);
  });
});
