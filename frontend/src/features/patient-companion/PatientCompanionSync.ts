import { API_BASE } from '../../services/api';
import {
  PatientCompanionStorage,
  type PatientPairing,
  type PatientWalletSnapshot,
} from './PatientCompanionStorage';

async function getJson<T>(path: string, accessToken: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: 'no-store',
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.detail || 'Synchronisation Patient Companion impossible.');
    Object.assign(error, { status: response.status });
    throw error;
  }
  return payload as T;
}

export const PatientCompanionSync = {
  async sync(pairing: PatientPairing): Promise<PatientWalletSnapshot> {
    const accessId = encodeURIComponent(pairing.context.access_id);
    const [appointments, shares] = await Promise.all([
      getJson<{ items: PatientWalletSnapshot['appointments'] }>(
        `/api/patient-companion/contexts/${accessId}/appointments`,
        pairing.accessToken,
      ),
      getJson<{ items: PatientWalletSnapshot['shares'] }>(
        `/api/patient-companion/contexts/${accessId}/shares`,
        pairing.accessToken,
      ),
    ]);

    const snapshot: PatientWalletSnapshot = {
      version: 1,
      accessId: pairing.context.access_id,
      syncedAt: new Date().toISOString(),
      appointments: appointments.items,
      shares: shares.items,
    };
    await PatientCompanionStorage.saveWallet(snapshot);
    return snapshot;
  },
};
