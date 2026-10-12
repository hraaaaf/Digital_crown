import React from 'react';
import { createRoot } from 'react-dom/client';
import '../../index.css';
import { CephaloWorkspace } from './CephaloWorkspace';
import { Toaster } from 'react-hot-toast';

// Harness-only entry: render the real Step1/Workspace + Zustand store + Axios
// repository. No prediction JSON, endpoint mocking, fake data in frontend or
// interception of HTTP responses; all data comes from live FastAPI/SQLite.
const params = new URLSearchParams(window.location.search);
const patientId = Number(params.get('patient'));
if (!Number.isSafeInteger(patientId) || patientId <= 0) {
  throw Error('Explicit isolated test patient id is required');
}
document.body.dataset.theme = 'light';
createRoot(document.getElementById('root')!).render(
  <div data-ceph03b3f-live-http-step1 style={{ height: '100vh', minHeight: 900 }}>
    <CephaloWorkspace patientId={patientId} patientName="PUBLIC RADIO — TEST SYNTHÉTIQUE" />
    <Toaster />
  </div>,
);
