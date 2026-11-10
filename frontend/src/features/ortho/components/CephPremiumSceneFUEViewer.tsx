/** J2.1 disposable visual consumer of verified scene pixels. NOT mounted in clinical app.
 * Never enable via production routes. No diagnostics or millimeter measurements.
 */
import React from 'react';
import {
  assertSceneFUEDevGate,
  readNonclinicalPremiumScene,
  readSceneOriginalChecked,
  saveNonclinicalPremiumScene,
  type NonclinicalSceneEnvelope,
  type NonclinicalPremiumScene,
} from '../cephPremiumSceneFUEClient';

interface Props {
  patientId: number;
  studyId: number;
}

function editedPoint(scene: NonclinicalPremiumScene, name: string, x: number, y: number): NonclinicalPremiumScene {
  const width = scene.identity.original_width;
  const height = scene.identity.original_height;
  if (!Number.isFinite(x) || !Number.isFinite(y) || x < 0 || y < 0 || x >= width || y >= height) {
    return scene; // Explicitly do not save invalid source-pixel coordinates.
  }
  return {
    ...scene,
    landmarks: scene.landmarks.map(p => p.id === name ? {
      ...p, x, y, origin: 'PRACTITIONER_EDIT' as const,
      confidence: null, score_status: 'NOT_EMITTED' as const,
    } : p),
    measurements: scene.measurements.map(m => ({ ...m, status: 'UNAVAILABLE' as const, value: null })),
  };
}

function byteMime(bytes: ArrayBuffer): string {
  const view = new Uint8Array(bytes);
  if (view.length > 8 && view[0] === 137 && view[1] === 80 && view[2] === 78 && view[3] === 71) return 'image/png';
  if (view.length > 3 && view[0] === 255 && view[1] === 216 && view[2] === 255) return 'image/jpeg';
  throw new Error('CEPH J2.1 FUE: Original image format is not JPEG/PNG');
}

export const CephPremiumSceneFUEViewer: React.FC<Props> = ({ patientId, studyId }) => {
  const [saved, setSaved] = React.useState<NonclinicalSceneEnvelope | null>(null);
  const [draft, setDraft] = React.useState<NonclinicalPremiumScene | null>(null);
  const [imageUrl, setImageUrl] = React.useState<string | null>(null);
  const [selectedPoint, setSelectedPoint] = React.useState<string | null>(null);
  const [dragging, setDragging] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const currentImage = React.useRef<string | null>(null);
  const mounted = React.useRef(true);

  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      if (currentImage.current) URL.revokeObjectURL(currentImage.current);
    };
  }, []);

  const load = React.useCallback(async () => {
    assertSceneFUEDevGate();
    setBusy(true);
    setError(null);
    try {
      const envelope = await readNonclinicalPremiumScene(patientId, studyId);
      const bytes = await readSceneOriginalChecked(envelope);
      const objectUrl = URL.createObjectURL(new Blob([bytes], { type: byteMime(bytes) }));
      if (!mounted.current) {
        URL.revokeObjectURL(objectUrl);
        return;
      }
      if (currentImage.current) URL.revokeObjectURL(currentImage.current);
      currentImage.current = objectUrl;
      setImageUrl(objectUrl);
      setSaved(envelope);
      setDraft(envelope.scene);
      setSelectedPoint(null);
    } catch (e) {
      if (mounted.current) setError(e instanceof Error ? e.message : 'Source non disponible');
    } finally {
      if (mounted.current) setBusy(false);
    }
  }, [patientId, studyId]);

  React.useEffect(() => {
    void load();
  }, [load]);

  const moveToPointer = (event: React.PointerEvent<SVGSVGElement>, pointId: string) => {
    if (!draft) return;
    const transform = event.currentTarget.getScreenCTM();
    if (!transform) {
      setError('Transformation écran/source non disponible');
      return;
    }
    try {
      const p = new DOMPoint(event.clientX, event.clientY).matrixTransform(transform.inverse());
      setDraft(before => before ? editedPoint(before, pointId, p.x, p.y) : null);
    } catch {
      setError('Impossible de projeter en pixels sources');
    }
  };

  const commit = async () => {
    if (!draft || !saved) return;
    assertSceneFUEDevGate();
    setBusy(true);
    setError(null);
    try {
      const scene: NonclinicalPremiumScene = {
        ...draft,
        identity: {
          ...draft.identity,
          scene_revision: saved.scene_revision + 1,
          parent_scene_sha256: saved.scene_sha256,
        },
      };
      const candidate = await saveNonclinicalPremiumScene(patientId, studyId, scene, saved.scene_sha256);
      const reopened = await readNonclinicalPremiumScene(patientId, studyId);
      if (reopened.scene_sha256 !== candidate.scene_sha256) {
        throw new Error('La scène sauvegardée ne correspond pas à la relecture');
      }
      if (mounted.current) {
        setSaved(reopened);
        setDraft(reopened.scene);
      }
    } catch (e) {
      if (mounted.current) setError(e instanceof Error ? e.message : 'Échec de sauvegarde');
    } finally {
      if (mounted.current) setBusy(false);
    }
  };

  if (!draft || !saved || !imageUrl) {
    return (
      <section aria-label="Laboratoire J2.1" data-ceph-j21-fue-only>
        <p>LAB synthétique uniquement — aucun usage clinique.</p>
        {busy && <p role="status">Lecture du média et de la scène vérifiés…</p>}
        {error && <p role="alert">{error}</p>}
        <button type="button" onClick={() => void load()} disabled={busy}>Réessayer</button>
      </section>
    );
  }
  const { original_width: width, original_height: height } = draft.identity;
  return (
    <section aria-label="Laboratoire de tracé J2.1" data-ceph-j21-fue-only className="space-y-2">
      <p role="status">LAB non clinique · référentiel anatomique NON VALIDÉ · calibration mm INDISPONIBLE</p>
      <svg
        role="img" aria-label="Radiographie originale vérifiée et points de la scène brouillon"
        data-ceph-j21-svg viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet" tabIndex={0}
        style={{ width: '100%', maxHeight: '75vh', touchAction: 'none' }}
        onPointerDown={event => {
          const target = event.target as Element;
          const name = target.getAttribute('data-ceph-point');
          if (!name) return;
          setSelectedPoint(name);
          setDragging(true);
          event.currentTarget.setPointerCapture?.(event.pointerId);
        }}
        onPointerMove={event => {
          if (dragging && selectedPoint) moveToPointer(event, selectedPoint);
        }}
        onPointerUp={event => {
          setDragging(false);
          event.currentTarget.releasePointerCapture?.(event.pointerId);
        }}
        onKeyDown={event => {
          if (!selectedPoint) return;
          const point = draft.landmarks.find(p => p.id === selectedPoint);
          if (!point) return;
          const d: Record<string, [number, number]> = {
            ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1],
          };
          if (!d[event.key]) return;
          event.preventDefault();
          setDraft(before => before ? editedPoint(before, selectedPoint, point.x + d[event.key][0], point.y + d[event.key][1]) : null);
        }}
      >
        <image href={imageUrl} x="0" y="0" width={width} height={height} />
        {draft.landmarks.map(p => (
          <g key={p.id}>
            <circle data-ceph-point={p.id} cx={p.x} cy={p.y} r={selectedPoint === p.id ? 6 : 4}
              fill="none" stroke={p.origin === 'PRACTITIONER_EDIT' ? '#ffd43b' : '#55ddff'} strokeWidth="2" />
            <text x={p.x + 6} y={p.y - 4} fill="#55ddff" stroke="black" strokeWidth="0.5" fontSize="12">{p.id}</text>
          </g>
        ))}
      </svg>
      <p>Source SHA : {draft.identity.original_sha256.slice(0, 12)}… · Révision {saved.scene_revision}</p>
      <button type="button" disabled={busy} onClick={() => void commit()}>Sauvegarder puis relire la scène de test</button>
      <button type="button" disabled={busy} onClick={() => void load()}>Rouvrir depuis l'API de test</button>
      {error && <p role="alert">{error}</p>}
    </section>
  );
};
