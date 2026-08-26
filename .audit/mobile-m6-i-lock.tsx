import React from 'react';
import ReactDOM from 'react-dom/client';
import { MobileBiometricGate } from './features/mobile/Security/MobileBiometricGate';
import './index.css';
import './styles/mobileGlassSystem.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MobileBiometricGate>
      <div data-protected-secret>PROTECTED CONTENT MUST NOT BE VISIBLE</div>
    </MobileBiometricGate>
  </React.StrictMode>,
);
