import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import {
  assertSceneFUEDevGate,
  readNonclinicalPremiumScene,
  readSceneOriginalChecked,
  saveNonclinicalPremiumScene,
  type NonclinicalSceneEnvelope,
} from '../cephPremiumSceneFUEClient';
import { CephPremiumSceneFUEViewer } from './CephPremiumSceneFUEViewer';

vi.mock('../cephPremiumSceneFUEClient', () => ({
  assertSceneFUEDevGate: vi.fn(),
  readNonclinicalPremiumScene: vi.fn(),
  readSceneOriginalChecked: vi.fn(),
  saveNonclinicalPremiumScene: vi.fn(),
}));

const hashA = 'a'.repeat(64);
const hashB = 'b'.repeat(64);
const hashC = 'c'.repeat(64);
const fakePNG = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10, 2, 3]).buffer;

function sample(sha=hashB, revision=1): NonclinicalSceneEnvelope {
  return {
    scene_sha256: sha,
    scene_revision: revision,
    clinical_release: false,
    desktop_fue_verified: false,
    scientific_digest_source_certified: false,
    verified_original: {
      patient_id: 22, study_id: 33, asset_id: 44,
      image_sha256: hashA, source_width: 640, source_height: 480,
      exif_orientation: 1, clinical_release: false,
      image_used_by_srpose38_inference_verified: false,
    },
    scene: {
      schema_version: 'CEPH_PREMIUM_SCENE_V1_DRAFT',
      identity: {
        employer_id: 11, patient_id: 22, study_id: 33, original_asset_id: 44,
        original_sha256: hashA, original_width: 640, original_height: 480,
        scientific_revision: 1, scene_revision: revision,
        parent_scene_sha256: revision === 1 ? null : hashB,
        detector_mapping_authority: 'LEGACY_LOCAL_UNVERIFIED',
      },
      landmarks: [
        { id: 'S', x: revision === 1 ? 100 : 101, y: 80, origin: revision === 1 ? 'SRPOSE38_AUTO' : 'PRACTITIONER_EDIT',
          confidence: null, score_status: 'NOT_EMITTED' },
      ],
      contours: [], constructions: [],
      measurements: [{ id: 'SNA', status: revision === 1 ? 'RAW_NONCLINICAL' : 'UNAVAILABLE',
        value: revision === 1 ? 80.4 : null }],
      document_status: 'NONCLINICAL_DRAFT',
      clinical_release: false,
    },
  };
}

beforeEach(() => {
  vi.stubGlobal('URL', { createObjectURL: vi.fn(() => 'blob:synthetic-only'), revokeObjectURL: vi.fn() });
  vi.mocked(readNonclinicalPremiumScene).mockResolvedValue(sample());
  vi.mocked(readSceneOriginalChecked).mockResolvedValue(fakePNG);
  vi.mocked(saveNonclinicalPremiumScene).mockResolvedValue(sample(hashC, 2));
});

afterEach(() => {
  cleanup(); // Unmount while the synthetic object URL methods are still available.
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('CephPremiumSceneFUEViewer (unmounted synthetic UI only)', () => {
  it('shows verified native source-pixel SVG and replays a keyboard correction through CAS', async () => {
    vi.mocked(readNonclinicalPremiumScene)
      .mockResolvedValueOnce(sample(hashB, 1))
      .mockResolvedValueOnce(sample(hashC, 2));
    render(<CephPremiumSceneFUEViewer patientId={22} studyId={33} />);
    const svg = await screen.findByRole('img', { name: /Radiographie originale vérifiée/ });
    expect(svg.getAttribute('viewBox')).toBe('0 0 640 480');
    const marker = svg.querySelector('[data-ceph-point="S"]')!;
    fireEvent.pointerDown(marker, { pointerId: 1 });
    fireEvent.keyDown(svg, { key: 'ArrowRight' });
    fireEvent.click(screen.getByRole('button', { name: /Sauvegarder puis relire/ }));
    await waitFor(() => expect(saveNonclinicalPremiumScene).toHaveBeenCalledTimes(1));
    const [, , savedDraft, parent] = vi.mocked(saveNonclinicalPremiumScene).mock.calls[0];
    expect(parent).toBe(hashB);
    expect(savedDraft.identity.scene_revision).toBe(2);
    expect(savedDraft.landmarks[0].x).toBe(101);
    expect(savedDraft.landmarks[0].origin).toBe('PRACTITIONER_EDIT');
    expect(savedDraft.measurements[0]).toMatchObject({ status: 'UNAVAILABLE', value: null });
    await waitFor(() => expect(screen.getByText(/Révision 2/)).toBeInTheDocument());
    expect(assertSceneFUEDevGate).toHaveBeenCalled();
  });

  it('keeps the real image hidden on source verification error', async () => {
    vi.mocked(readSceneOriginalChecked).mockRejectedValue(new Error('Source SHA mismatch'));
    render(<CephPremiumSceneFUEViewer patientId={22} studyId={33} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Source SHA mismatch');
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });
});
