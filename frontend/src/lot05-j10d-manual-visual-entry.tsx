import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { Step1Cephalo } from './features/ortho/components/Step1Cephalo';
import { getCephaloPalette } from './features/ortho/cephaloTheme';
import { useOrthoStore } from './features/ortho/stores/useOrthoStore';
import './index.css';

// Synthetic UI evidence only. No personal data, no clinical assertion.
useOrthoStore.setState({
  patientId: 901,
  patientName: 'Patient synthétique LOT05',
  analysisId: undefined,
  imageSrc: undefined,
  local: { landmarks: [], version: 0 },
  anglesData: {},
  visionMetadata: {},
  isCalibrated: false,
  mmPerPixel: null,
  step: 1,
  completedSteps: new Set(),
  uploadError: null,
  isUploading: false,
});

const App = () => {
  const fileRef = React.useRef<HTMLInputElement>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const P = getCephaloPalette();
  return (
    <MemoryRouter>
      <main style={{ minHeight: '100vh', padding: '8px', background: P.bg }}>
        <Step1Cephalo P={P} fileRef={fileRef} step1ContainerRef={containerRef} />
      </main>
    </MemoryRouter>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
