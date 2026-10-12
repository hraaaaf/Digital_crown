import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { CephaloTracingLayer } from './CephaloTracingLayer';
import { createDefaultLayerOpacity, createDefaultLayerVisibility } from './orthoLayerRegistry';
import type { Landmark } from './cephaloShared';
import './../../index.css';

// Synthetic deterministic geometry only. Not radiographic or patient data.
const initial: Landmark[] = [
  { id: 'Po', x: 30, y: 40 }, { id: 'Or', x: 100, y: 42 },
  { id: 'N', x: 130, y: 70 }, { id: 'Pog', x: 170, y: 175 },
  { id: 'S', x: 75, y: 65 }, { id: 'A', x: 140, y: 100 },
  { id: 'B', x: 155, y: 135 }, { id: 'Go', x: 35, y: 160 },
  { id: 'Me', x: 100, y: 200 },
  { id: 'U1_apex', x: 128, y: 117 }, { id: 'U1_incisal', x: 147, y: 151 },
  { id: 'L1_apex', x: 114, y: 195 }, { id: 'L1_incisal', x: 139, y: 153 },
];
const mode = new URLSearchParams(window.location.search).get('mode') === 'com' ? 'com' : 'all';

const Fixture: React.FC = () => {
  const [landmarks, setLandmarks] = useState<Landmark[]>(initial);
  const [commitCount, setCommitCount] = useState(0);
  const [showPlans, setShowPlans] = useState(true);
  return (
    <main style={{ width: '100vw', height: '100vh', padding: 22, boxSizing: 'border-box', background: '#f1f5f9', color: '#0f172a', fontFamily: 'system-ui' }}>
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20, height: 50 }}>
        <div>
          <strong>DC-CEPH-03B — Contrôle graphique desktop</strong>
          <small style={{ display: 'block' }}>Géométrie synthétique, sans donnée patient</small>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <span data-commit-count={commitCount}>Corrections validées : {commitCount}</span>
          <button data-toggle-plans type="button" onClick={() => setShowPlans(v => !v)}>Plans : {showPlans ? 'visibles' : 'masqués'}</button>
        </div>
      </header>
      <section data-ceph03b-browser-fixture={mode} style={{ position: 'relative', height: 'calc(100vh - 115px)', maxWidth: 1240, margin: '10px auto 0', borderRadius: 16, overflow: 'hidden', background: 'radial-gradient(ellipse at 53% 38%, #334155, #020617 80%)' }}>
        <CephaloTracingLayer
          imageWidth={240} imageHeight={240} landmarks={landmarks}
          ghosts={[{ layerId: 't1', opacity: 0.35, color: '#94a3b8', landmarks: initial.map(p => ({ ...p, x: p.x + 5 })) }]}
          onUpdateLandmarks={next => { setLandmarks(next); setCommitCount(n => n + 1); }}
          activeAnalysis={mode}
          magnifierEnabled={false}
          vto={{ enabled: false, showGhostFace: false, showSoftTissue: false }}
          layerPresentation={{
            visibility: { ...createDefaultLayerVisibility(), landmarks: true, plans: showPlans, measurements: true, t1: true },
            opacity: createDefaultLayerOpacity(),
          }}
        />
      </section>
    </main>
  );
};

createRoot(document.getElementById('root')!).render(<Fixture />);
