/* Visual fixture ONLY; never mount on a clinical route or ship patient data. */
import React from 'react';
import { createRoot } from 'react-dom/client';
import { api } from '../src/services/api';
import { BlockedPrintJobsReadOnly } from '../src/features/admin/Settings/tabs/BlockedPrintJobsReadOnly';
import '../src/index.css';

const fake = {
  status: 'review_only',
  printingAvailable: false,
  retrySupported: false,
  total: 2,
  jobs: [
    { reference: 'e7c389ab23de', status: 'uncertain', updatedAt: '2026-10-13T11:00:00Z', investigations: 2 },
    { reference: '194aadd510bd', status: 'uncertain', updatedAt: '2026-10-13T10:00:00Z', investigations: 0 },
  ],
} as const;

// Explicit test fixture, no session token or PHI. This test does not claim
// live API authentication or an actual Cabinet workflow.
api.get = (async () => ({ data: fake })) as typeof api.get;

const host = document.getElementById('root');
if (!host) throw new Error('VISUAL_FIXTURE_ROOT_MISSING');
createRoot(host).render(
  <main className="mx-auto w-full max-w-6xl p-3 sm:p-8">
    <h1 className="mb-4 text-2xl font-bold">Sécurité du cabinet — LAB</h1>
    <BlockedPrintJobsReadOnly ownerVerified />
  </main>,
);
