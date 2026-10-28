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
import type { LabCapturePreview, LabStaffTarget, LabReviewClient } from '../StaffReviewLab';
import '../../../index.css';

declare global {
  interface Window {
    __DC06B_HTTP_TEST__?: {
      workstationId: string;
      capture: LabCapturePreview;
      targets: LabStaffTarget[];
    };
    // Synthetic e2e debugging only; no patient identifiers, secrets or codes.
    __DC06B_HTTP_TRACE__?: string;
    __DC06B_HTTP_API_ORIGIN__?: string;
  }
}

if (!import.meta.env.DEV || window.location.hostname !== '127.0.0.1') {
  throw new Error('ISOLATED_HTTP_HARNESS_DISABLED');
}
window.__DC06B_HTTP_API_ORIGIN__ = import.meta.env.VITE_API_URL;
const fixture = window.__DC06B_HTTP_TEST__;
if (!fixture || !fixture.workstationId || fixture.targets.length === 0) {
  throw new Error('ISOLATED_HTTP_FIXTURE_REQUIRED');
}
// TEST-ONLY adapter. The existing UI's reason input is not part of the
// production backend contract yet. Require an exact provisional LAB code
// typed by the tester; attach it to BOTH real Axios calls, never translate
// arbitrary clinical free text or auto-approve a patient association.
const codes = new Set(['LAB_WALK_IN', 'LAB_UNSCHEDULED', 'LAB_URGENT']);
let reviewedReason: string | null = null;
function enteredReason(): string | null {
  const raw = document.querySelector<HTMLInputElement>('#lab-reason')?.value.trim();
  return raw || null;
}
const e2eHttpClient: LabReviewClient = {
  async review(input) {
    window.__DC06B_HTTP_TRACE__ = 'review-called';
    const reason = input.appointment_id === null ? enteredReason() : null;
    if (input.appointment_id === null && !codes.has(reason ?? '')) {
      window.__DC06B_HTTP_TRACE__ = 'reason-code-not-visible';
      throw new Error('ISOLATED_LAB_REASON_CODE_REQUIRED');
    }
    reviewedReason = null;
    const payload = { ...input, patient_only_reason: reason };
    window.__DC06B_HTTP_TRACE__ = 'sending-fastapi-review';
    try {
      const response = await labStaffHttpClient.review(payload);
      window.__DC06B_HTTP_TRACE__ = 'received-fastapi-review';
      const verified = response as typeof response & { patient_only_reason?: string | null };
      if (verified.patient_only_reason !== reason) {
        window.__DC06B_HTTP_TRACE__ = 'reason-binding-invalid';
        throw new Error('ISOLATED_LAB_REASON_NOT_BOUND');
      }
      reviewedReason = reason;
      return response;
    } catch (error) {
      if (window.__DC06B_HTTP_TRACE__ === 'sending-fastapi-review') {
        window.__DC06B_HTTP_TRACE__ = 'fastapi-review-http-rejected';
      }
      throw error;
    }
  },
  async approve(input) {
    const reason = input.appointment_id === null ? enteredReason() : null;
    if (reason !== reviewedReason ||
        (input.appointment_id === null && !codes.has(reason ?? ''))) {
      throw new Error('ISOLATED_LAB_REASON_CHANGED_AFTER_REVIEW');
    }
    try {
      const payload = { ...input, patient_only_reason: reason };
      return await labStaffHttpClient.approve(payload);
    } finally {
      // The challenge is one-use. Never reuse cached review context.
      reviewedReason = null;
    }
  },
};

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <StaffReviewLab
      capture={fixture.capture}
      targets={fixture.targets}
      workstationId={fixture.workstationId}
      client={e2eHttpClient}
    />
  </React.StrictMode>,
);
