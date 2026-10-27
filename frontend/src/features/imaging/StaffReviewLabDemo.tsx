import React from 'react';
import { createRoot } from 'react-dom/client';
import { StaffReviewLab } from './StaffReviewLab';
import type { LabReviewClient, LabReviewInput } from './StaffReviewLab';
import '../../index.css';

// Accessible only as a separate Vite dev HTML entry. NOT mounted in App.tsx,
// NOT bundled by the normal single-entry production build, no clinic traffic.
if (!import.meta.env.DEV) {
  throw new Error('LAB_DESKTOP_PREVIEW_DISABLED');
}

let activeReview: { input: LabReviewInput; token: string } | null = null;
const previewClient: LabReviewClient = {
  async review(input) {
    const token = 'synthetic-review-' + crypto.randomUUID();
    activeReview = { input: { ...input }, token };
    return {
      status: 'STAFF_REVIEW_REQUIRED',
      review_challenge: token,
      expires_at: Math.floor(Date.now() / 1000) + 300,
      patient_id: input.patient_id,
      appointment_id: input.appointment_id,
      server_confirmed: false,
    };
  },
  async approve(input) {
    if (!activeReview || input.review_challenge !== activeReview.token ||
        input.patient_id !== activeReview.input.patient_id ||
        input.appointment_id !== activeReview.input.appointment_id ||
        input.capture !== activeReview.input.capture ||
        input.device !== activeReview.input.device ||
        input.workstation_id !== activeReview.input.workstation_id) {
      throw new Error('SYNTHETIC_REVIEW_DENIED');
    }
    activeReview = null;
    return { status: 'APPROVED', server_confirmed: false };
  },
};

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <StaffReviewLab
      workstationId="fixture-desktop-06b"
      capture={{
        device: 'CONNECTEUR-LAB-01',
        capture: 'capture-fixture-20261027-0001',
        modality: 'Photographie intra-orale (simulation)',
        receivedAtLabel: 'Donnée fictive · 27 octobre 2026',
        claimedSha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      }}
      targets={[
        {
          patientId: 101,
          label: 'PATIENT FICTIF A · dossier 101',
          appointments: [{ id: 301, label: 'RDV fictif · bilan dentaire 09:30' }],
        },
        {
          patientId: 102,
          label: 'PATIENT FICTIF B · dossier 102',
          appointments: [{ id: 302, label: 'RDV fictif · consultation 11:00' }],
        },
      ]}
      client={previewClient}
    />
  </React.StrictMode>,
);
