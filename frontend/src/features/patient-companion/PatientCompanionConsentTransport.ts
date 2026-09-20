import type { PatientPairing } from './PatientCompanionStorage';
import { sendRemoteCommand, type RemoteCommandResult } from './PatientCompanionRemoteCommandTransport';

export type ConsentOperation = 'consent.sign';
export type ConsentCommandResult = RemoteCommandResult;

export async function sendConsentCommand(
  pairing: PatientPairing,
  payload: Record<string, unknown>,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<ConsentCommandResult> {
  return sendRemoteCommand(pairing, 'consents', 'consent.sign', payload, idempotencyKey);
}

export const PatientCompanionConsentTransport = { sendConsentCommand };
