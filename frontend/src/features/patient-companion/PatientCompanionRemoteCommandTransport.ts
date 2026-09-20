import { API_BASE } from '../../services/api';
import type { PatientPairing } from './PatientCompanionStorage';
import { PatientCompanionRemoteCrypto } from './PatientCompanionRemoteCrypto';

export type RemoteCommandResult = {
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

function parseAck(
  ack: Record<string, unknown>,
  pairing: PatientPairing,
  idempotencyKey: string,
  messageId: string,
  operation: string,
): RemoteCommandResult {
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

async function sendDirect(
  pairing: PatientPairing,
  blob: string,
  endpointPath: string,
  operation: string,
  idempotencyKey: string,
  messageId: string,
): Promise<RemoteCommandResult> {
  const binding = pairing.remoteTransport;
  if (!binding) throw new Error('Transport sécurisé Patient Companion non initialisé.');
  const accessId = encodeURIComponent(pairing.context.access_id);
  const response = await fetch(
    `${API_BASE}/api/patient-companion/contexts/${accessId}/${endpointPath}/remote-command`,
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
    const error = new Error(body.detail || 'Transmission Patient Companion impossible.');
    Object.assign(error, { status: response.status });
    throw error;
  }
  const ack = await PatientCompanionRemoteCrypto.decryptAndVerify(body.blob, binding);
  return parseAck(ack, pairing, idempotencyKey, messageId, operation);
}

const relayHeaders = (capability: string) => ({ Authorization: `RelayCap ${capability}` });
const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

async function sendViaRelay(
  pairing: PatientPairing,
  blob: string,
  operation: string,
  idempotencyKey: string,
  messageId: string,
): Promise<RemoteCommandResult> {
  const binding = pairing.remoteTransport;
  const relay = binding?.relay;
  if (!binding || !relay) throw new Error('Relay Patient Companion non initialisé.');

  const envelopeId = crypto.randomUUID();
  const push = await fetch(
    `${relay.relayUrl}/v1/mailboxes/${encodeURIComponent(relay.cabinetInboxId)}/envelopes`,
    {
      method: 'POST',
      headers: {
        ...relayHeaders(relay.cabinetWriteCapability),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ envelope_id: envelopeId, blob, ttl_seconds: 15 * 60 }),
    },
  );
  if (!push.ok) {
    const error = new Error('Relay Patient Companion indisponible.');
    Object.assign(error, { status: push.status });
    throw error;
  }

  for (let attempt = 0; attempt < 12; attempt += 1) {
    if (attempt > 0) await wait(1000);
    const pulled = await fetch(
      `${relay.relayUrl}/v1/mailboxes/${encodeURIComponent(relay.patientInboxId)}/envelopes?limit=100`,
      { headers: relayHeaders(relay.patientReadCapability), cache: 'no-store' },
    );
    if (!pulled.ok) continue;
    const payload = await pulled.json().catch(() => ({}));
    const items = Array.isArray(payload.items) ? payload.items : [];
    for (const item of items) {
      if (typeof item?.blob !== 'string' || typeof item?.envelope_id !== 'string') continue;
      let ack: Record<string, unknown>;
      try {
        ack = await PatientCompanionRemoteCrypto.decryptAndVerify(item.blob, binding);
      } catch {
        continue;
      }
      if (ack.access_id !== pairing.context.access_id || ack.idempotency_key !== idempotencyKey) continue;
      const result = parseAck(ack, pairing, idempotencyKey, messageId, operation);
      await fetch(
        `${relay.relayUrl}/v1/mailboxes/${encodeURIComponent(relay.patientInboxId)}/envelopes/${encodeURIComponent(item.envelope_id)}`,
        { method: 'DELETE', headers: relayHeaders(relay.patientReadCapability) },
      ).catch(() => undefined);
      return result;
    }
  }

  const pending = new Error('Commande relay transmise · ACK cabinet encore en attente.');
  Object.assign(pending, { remotePending: true });
  throw pending;
}

export async function sendRemoteCommand(
  pairing: PatientPairing,
  endpointPath: string,
  operation: string,
  payload: Record<string, unknown>,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<RemoteCommandResult> {
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
  return binding.relay
    ? sendViaRelay(pairing, blob, operation, idempotencyKey, messageId)
    : sendDirect(pairing, blob, endpointPath, operation, idempotencyKey, messageId);
}

export const PatientCompanionRemoteCommandTransport = { sendRemoteCommand };
