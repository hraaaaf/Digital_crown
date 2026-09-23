import type { PatientPairing } from './PatientCompanionStorage';
import { sendRemoteCommand } from './PatientCompanionRemoteCommandTransport';

export type TeleconsultSession = {
  session_id: string;
  state: 'CREATED' | 'WAITING_PATIENT' | 'WAITING_STAFF' | 'NEGOTIATING' | 'CONNECTED' | 'ENDED' | 'REJECTED' | 'EXPIRED' | 'FAILED';
  created_at: string;
  expires_at: string;
  patient_joined_at?: string | null;
  staff_joined_at?: string | null;
  connected_at?: string | null;
  ended_at?: string | null;
  ended_by?: string | null;
  failure_code?: string | null;
};

export type TeleconsultSignal = {
  signal_id: string;
  client_signal_id: string;
  sender_kind: 'PATIENT' | 'STAFF';
  signal_type: 'offer' | 'answer' | 'ice';
  payload: Record<string, unknown>;
  created_at: string;
};

async function command(
  pairing: PatientPairing,
  operation: string,
  payload: Record<string, unknown>,
) {
  return sendRemoteCommand(pairing, 'teleconsultation', operation, payload);
}

export const PatientCompanionTeleconsultTransport = {
  async list(pairing: PatientPairing): Promise<TeleconsultSession[]> {
    const result = await command(pairing, 'teleconsult.list', {});
    if (result.status !== 'ACCEPTED' || result.result.code !== 'SESSION_LIST') {
      throw new Error(String(result.result.code || 'Téléconsultation indisponible.'));
    }
    return Array.isArray(result.result.items) ? result.result.items as TeleconsultSession[] : [];
  },

  async iceConfig(pairing: PatientPairing, sessionId: string): Promise<RTCIceServer[]> {
    const result = await command(pairing, 'teleconsult.ice-config', { session_id: sessionId });
    if (result.status !== 'ACCEPTED' || result.result.code !== 'ICE_CONFIG') {
      throw new Error(String(result.result.code || 'Configuration réseau indisponible.'));
    }
    return Array.isArray(result.result.ice_servers) ? result.result.ice_servers as RTCIceServer[] : [];
  },

  async join(pairing: PatientPairing, sessionId: string): Promise<TeleconsultSession> {
    const result = await command(pairing, 'teleconsult.join', { session_id: sessionId });
    if (result.status !== 'ACCEPTED') throw new Error(String(result.result.code || 'Impossible de rejoindre.'));
    return result.result.session as TeleconsultSession;
  },

  async signal(
    pairing: PatientPairing,
    sessionId: string,
    signalType: TeleconsultSignal['signal_type'],
    payload: Record<string, unknown>,
  ): Promise<void> {
    const result = await command(pairing, 'teleconsult.signal', {
      session_id: sessionId,
      client_signal_id: crypto.randomUUID(),
      signal_type: signalType,
      payload,
    });
    if (result.status !== 'ACCEPTED') throw new Error(String(result.result.code || 'Signal refusé.'));
  },

  async sync(
    pairing: PatientPairing,
    sessionId: string,
    afterSignalId?: string | null,
  ): Promise<{ session: TeleconsultSession; signals: TeleconsultSignal[] }> {
    const payload: Record<string, unknown> = { session_id: sessionId };
    if (afterSignalId) payload.after_signal_id = afterSignalId;
    const result = await command(pairing, 'teleconsult.sync', payload);
    if (result.status !== 'ACCEPTED') throw new Error(String(result.result.code || 'Synchronisation impossible.'));
    return {
      session: result.result.session as TeleconsultSession,
      signals: Array.isArray(result.result.signals) ? result.result.signals as TeleconsultSignal[] : [],
    };
  },

  async connected(pairing: PatientPairing, sessionId: string): Promise<TeleconsultSession> {
    const result = await command(pairing, 'teleconsult.connected', { session_id: sessionId });
    if (result.status !== 'ACCEPTED') throw new Error(String(result.result.code || 'Connexion non confirmée.'));
    return result.result.session as TeleconsultSession;
  },

  async failed(pairing: PatientPairing, sessionId: string, failureCode: 'PEER_CONNECTION_FAILED'): Promise<TeleconsultSession> {
    const result = await command(pairing, 'teleconsult.failed', {
      session_id: sessionId,
      failure_code: failureCode,
    });
    if (result.status !== 'ACCEPTED') throw new Error(String(result.result.code || 'Échec de connexion non confirmé.'));
    return result.result.session as TeleconsultSession;
  },

  async reject(pairing: PatientPairing, sessionId: string): Promise<TeleconsultSession> {
    const result = await command(pairing, 'teleconsult.reject', { session_id: sessionId });
    if (result.status !== 'ACCEPTED') throw new Error(String(result.result.code || 'Refus non confirmé.'));
    return result.result.session as TeleconsultSession;
  },

  async end(pairing: PatientPairing, sessionId: string): Promise<TeleconsultSession> {
    const result = await command(pairing, 'teleconsult.end', { session_id: sessionId });
    if (result.status !== 'ACCEPTED') throw new Error(String(result.result.code || 'Fin de consultation non confirmée.'));
    return result.result.session as TeleconsultSession;
  },
};
