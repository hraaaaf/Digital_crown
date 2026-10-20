/** LOT07/07-C Windows browser-zoom visual harness.
 * Synthetic data only; explicitly NOT the authenticated Cabinet/T2 FUE.
 * Served by Vite dev server as an extra HTML entry, never shipped by Vite
 * production's single index.html build.
 */
import React from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MainLayout } from '../../components/Layout/MainLayout';
import { CommandCabinetReadOnlyView } from './CommandCabinetReadOnlyRoute';
import type { DashboardAppointment } from '../dashboard/types';
import '../../index.css';

const today = new Date();
const localDay = [today.getFullYear(), String(today.getMonth() + 1).padStart(2, '0'),
  String(today.getDate()).padStart(2, '0')].join('-');

const appointments: DashboardAppointment[] = [
  { id: 1001, start_time: localDay + 'T09:15:00', datetime_start: localDay + 'T09:15:00',
    patient_name: 'T2 WINDOWS SYNTHETIC', status: 'EN_S_ATTENTE', patient_id: null },
  { id: 1002, start_time: localDay + 'T10:30:00', datetime_start: localDay + 'T10:30:00',
    patient_name: 'T2 WINDOWS SYNTHETIC 2', status: 'PRÉVU', patient_id: null },
];

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
document.body.dataset.syntheticWindowsZoom = 'true';
// Keep the actual URL on this dev-only HTML entry. Windows Chromium may reload
// the document when zoom changes, and rewriting history to /command-cabinet-lab
// would reload the authenticated production SPA instead of this synthetic lab.
// MemoryRouter gives MainLayout the real Command pathname without changing URL.

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/command-cabinet-lab']}>
        <MainLayout>
          <CommandCabinetReadOnlyView appointments={appointments} appointmentsState="ready"
            canReadPatients onRefresh={() => {}} />
        </MainLayout>
      </MemoryRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
