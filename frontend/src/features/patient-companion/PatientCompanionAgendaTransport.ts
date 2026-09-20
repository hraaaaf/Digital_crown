import { API_BASE } from '../../services/api';
import type { PatientPairing } from './PatientCompanionStorage';
import { PatientCompanionRemoteCrypto } from './PatientCompanionRemoteCrypto';

export type AgendaOperation = 'agenda.create' | 'agenda.reschedule' | 'agenda.cancel';

export type AgendaCommandResult = {
  status: 'ACCEPTED' | 'REJECTED';
  result: Record<string, unknown>;
  messageId: string;
  idempotencyKey: string;
};

function assertUuid(value: string): void {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value)) {
    throw new Error('Identifiant de commande Patient Companion invalide.');
  }
}

function assertFreshAck(payload: Record<string, unknown>): void {
  const sentAt = new Date(String(payload.sent_at || ''));
  const expiresAt = new Date(String(payload.expires_at || ''));
  const now = Date.now();
  if (!Number.isFinite(sentAt.getTime()) || !Number.isFinite(expiresAt.getTime())) {
    throw new Error('Horodatage ACK Patient Companion invalide.');
  }
  if (expiresAt.getTime() <= now || expiresAt.getTime() <= sentAt.getTime()) {
    throw new Error('ACK Patient Companion expiré.');
  }
  if (expiresAt.getTime() - sentAt.getTime() > 15 * 60 * 1000) {
    throw new Error('Durée ACK Patient Companion invalide.');
  }
}

export async function sendAgendaCommand(
  pairing: PatientPairing,
  operation: AgendaOperation,
  payload: Record<string, unknown>,
  idempotencyKey = crypto.randomUUID(),
): Promise<AgendaCommandResult> {
  const binding = pairing.remoteTransport;
  if (!binding) throw new Error('Transport sécurisé Patient Companion non initialisé.');
  const messageId = crypto.randomUUID();
  assertUuid(messageId);
  assertUuid(idempotencyKey);

  const sentAt = new Date();
  const expiresAt = new Date(sentAt.getTime() + 10 * 60 * 1000);
  const inner = {
    protocol_version: 'dc-pc-remote-v1',
    message_id: messageId,
    access_id: pairing.context.access_id,
    sent_at: sentAt.toISOString(),
    expires_at: expiresAt.toISOString(),
    idempotency_key: idempotencyKey,
    operation,
    payload,
  };

  const blob = await PatientCompanionRemoteCrypto.signAndEncrypt(inner, binding);
  const accessId = encodeURIComponent(pairing.context.access_id);
  const response = await fetch(
    `${API_BASE}/api/patient-companion/contexts/${accessId}/agenda/remote-command`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${pairing.accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ blob }),
    },
  );
  const body = await response.json().catch(() => ({}));
  if (!response.ok || typeof body.blob !== 'string') {
    const error = new Error(body.detail || 'Transmission agenda Patient Companion impossible.');
    Object.assign(error, { status: response.status });
    throw error;
  }

  const ack = await PatientCompanionRemoteCrypto.decryptAndVerify(body.blob, binding);
  assertFreshAck(ack);
  if (
    ack.protocol_version !== 'dc-pc-remote-v1'
    || ack.operation !== 'command.result'
    || ack.access_id !== pairing.context.access_id
    || ack.idempotency_key !== idempotencyKey
  ) {
    throw new Error('ACK Patient Companion ne correspond pas à la commande.');
  }
  const ackPayload = ack.payload;
  if (typeof ackPayload !== 'object' || ackPayload === null || Array.isArray(ackPayload)) {
    throw new Error('Payload ACK Patient Companion invalide.');
  }
  const resultPayload = ackPayload as Record<string, unknown>;
  if (
    resultPayload.request_message_id !== messageId
    || resultPayload.request_operation !== operation
    || (resultPayload.status !== 'ACCEPTED' && resultPayload.status !== 'REJECTED')
    || typeof resultPayload.result !== 'object'
    || resultPayload.result === null
    || Array.isArray(resultPayload.result)
  ) {
    throw new Error('Résultat ACK Patient Companion invalide.');
  }

  return {
    status: resultPayload.status,
    result: resultPayload.result as Record<string, unknown>,
    messageId,
    idempotencyKey,
  };
}

export const PatientCompanionAgendaTransport = { sendAgendaCommand };
