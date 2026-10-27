/**
 * Browser-only isolated E2E bootstrap.
 * Loads the unchanged StaffReviewLab UI and its REAL axios→FastAPI adapter.
 * No patient IDs, JWTs, credentials or media are checked into source.
 * This fixture is NEVER mounted from App.tsx or a production HTML entry.
 */
import React from 'react';
import { createRoot } from 'react-dom/client';
import { StaffReviewLab } from '../StaffReviewLab';
import { labStaffHttpClient } from '../StaffReviewLabApi';
import type { LabCapturePreview, LabStaffTarget } from '../StaffReviewLab';
import '../../../index.css';

declare global {
  interface Window {
    __DC06B_HTTP_TEST__?: {
      workstationId: string;
      capture: LabCapturePreview;
      targets: LabStaffTarget[];
    };
  }
}

if (!import.meta.env.DEV || window.location.hostname !== '127.0.0.1') {
  throw new Error('ISOLATED_HTTP_HARNESS_DISABLED');
}
const fixture = window.__DC06B_HTTP_TEST__;
if (!fixture || !fixture.workstationId || fixture.targets.length === 0) {
  throw new Error('ISOLATED_HTTP_FIXTURE_REQUIRED');
}
createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <StaffReviewLab
      capture={fixture.capture}
      targets={fixture.targets}
      workstationId={fixture.workstationId}
      client={labStaffHttpClient}
    />
  </React.StrictMode>,
);
