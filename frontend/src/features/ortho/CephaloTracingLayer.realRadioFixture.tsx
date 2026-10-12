import React from 'react';
import { createRoot } from 'react-dom/client';
import './../../index.css';
import { CephaloTracingLayer } from './CephaloTracingLayer';
import { createDefaultLayerOpacity, createDefaultLayerVisibility } from './orthoLayerRegistry';
import { createLandmarkEditTimeline } from './orthoLandmarkEditHistory';
import { useOrthoStore } from './stores/useOrthoStore';
import type { Landmark } from './cephaloShared';

const params = new URLSearchParams(window.location.search);
const film = params.get('film') === 'B' ? 'B' : 'A';
const mode = params.get('mode') === 'com' ? 'com' : 'all';
const info = film === 'B'
  ? { name: 'Challiyan (CC BY-SA 4.0)', width: 1000, height: 1255, file: '/dc-ceph03b3c/cephalo-B.jpg' }
  : { name: 'ANUG (CC BY-SA 4.0)', width: 2272, height: 1818, file: '/dc-ceph03b3c/cephalo-A.jpg' };
const w = info.width;
const h = info.height;

// Synthetic test-only coordinates. These are NOT measured or expertly traced
// anatomical landmarks for either public film; never use for diagnosis.
const initial: Landmark[] = [
  { id: 'Po', x: w * 0.35, y: h * 0.48 },
  { id: 'Or', x: w * 0.63, y: h * 0.40 },
  { id: 'N', x: w * 0.73, y: h * 0.22 },
  { id: 'Pog', x: w * 0.81, y: h * 0.73 },
  { id: 'S', x: w * 0.51, y: h * 0.30 },
  { id: 'A', x: w * 0.76, y: h * 0.59 },
  { id: 'B', x: w * 0.78, y: h * 0.69 },
  { id: 'Go', x: w * 0.53, y: h * 0.78 },
  { id: 'Me', x: w * 0.72, y: h * 0.82 },
  { id: 'U1_apex', x: w * 0.75, y: h * 0.59 },
  { id: 'U1_incisal', x: w * 0.81, y: h * 0.67 },
  { id: 'L1_apex', x: w * 0.71, y: h * 0.79 },
  { id: 'L1_incisal', x: w * 0.79, y: h * 0.68 },
];
const layers = { ...createDefaultLayerVisibility(), t1: true, t2: true };
useOrthoStore.setState({
  patientId: null,
  analysisId: null,
  local: { landmarks: initial, version: 1 },
  landmarkEditTimeline: createLandmarkEditTimeline(initial),
  layerVisibility: layers,
  layerOpacity: createDefaultLayerOpacity(),
  activeMorphing: 'none',
});

function TestWorkspace() {
  const landmarks = useOrthoStore(state => state.local.landmarks);
  const editTimeline = useOrthoStore(state => state.landmarkEditTimeline);
  const visibility = useOrthoStore(state => state.layerVisibility);
  const opacity = useOrthoStore(state => state.layerOpacity);
  const undo = useOrthoStore(state => state.undoLandmarkEdit);
  const redo = useOrthoStore(state => state.redoLandmarkEdit);
  const toggle = useOrthoStore(state => state.setLayerVisible);
  const keyboardNudge = useOrthoStore(state => state.nudgeLandmarkFromKeyboard);
  const updateLandmarks = useOrthoStore(state => state.updateLandmarksOptimistic);

  // Independent synthetic visual ghost layers, not a longitudinal prediction.
  const ghosts = (['t1', 't2'] as const).map((id, i) => ({
    layerId: id,
    color: i === 0 ? '#93c5fd' : '#f0abfc',
    opacity: 1,
    landmarks: initial.map(p => ({ ...p, x: p.x + (i + 1) * 8, y: p.y - (i + 1) * 5 })),
  }));

  const po = landmarks.find(p => p.id === 'Po');
  return (
    <main style={{ margin: 0, height: '100vh', width: '100vw', padding: 16,
      boxSizing: 'border-box', background: '#0b1322', color: '#e2e8f0',
      fontFamily: 'system-ui,sans-serif', display: 'flex', flexDirection: 'column' }}>
      <header style={{ display:'flex', alignItems:'center', justifyContent:'space-between',
        gap:12, minHeight:66, flexWrap:'wrap' }}>
        <div>
          <strong>DC-CEPH-03B.3c — radio réelle {film}, vérification technique</strong>
          <div style={{fontSize:12, opacity:.78}}>
            {info.name} · {w}×{h} · {mode.toUpperCase()} · points fictifs, aucune mesure clinique
          </div>
        </div>
        <div style={{display:'flex',gap:8,alignItems:'center'}}>
          <button type="button" onClick={undo} disabled={!editTimeline.undoStack.length}>Annuler</button>
          <button type="button" onClick={redo} disabled={!editTimeline.redoStack.length}>Rétablir</button>
          <button type="button" data-t1 onClick={() => toggle('t1', !visibility.t1)}>T1 {visibility.t1 ? 'visible' : 'masqué'}</button>
          <button type="button" data-t2 onClick={() => toggle('t2', !visibility.t2)}>T2 {visibility.t2 ? 'visible' : 'masqué'}</button>
        </div>
      </header>
      <div data-film={film} data-mode={mode}
        data-po-x={po?.x ?? -1}
        data-undo={editTimeline.undoStack.length}
        data-redo={editTimeline.redoStack.length}
        data-audit={editTimeline.auditTrail.length}
        data-ghost-t1={visibility.t1}
        data-ghost-t2={visibility.t2}
        style={{flex:1,minHeight:0,position:'relative',border:'1px solid #475569',
          borderRadius:12,overflow:'hidden',background:'#070d18'}}>
        <CephaloTracingLayer
          imageSrc={info.file}
          landmarks={landmarks}
          ghosts={ghosts}
          imageWidth={w}
          imageHeight={h}
          onUpdateLandmarks={updateLandmarks}
          onKeyboardNudgeLandmark={keyboardNudge}
          activeAnalysis={mode}
          uiMode="pro"
          performanceMode
          magnifierEnabled={false}
          layerPresentation={{visibility,opacity}}
        />
      </div>
      <footer style={{fontSize:10,opacity:.75,paddingTop:5}}>
        Image publique sous CC BY-SA 4.0 — auteur : {info.name}. Les traces et
        projections sont purement techniques et ne constituent pas un diagnostic.
      </footer>
    </main>
  );
}
createRoot(document.getElementById('root')!).render(<TestWorkspace />);
