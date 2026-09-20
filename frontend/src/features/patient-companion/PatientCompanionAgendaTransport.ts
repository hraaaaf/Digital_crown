import type { PatientPairing } from './PatientCompanionStorage';
import { sendRemoteCommand, type RemoteCommandResult } from './PatientCompanionRemoteCommandTransport';

export type AgendaOperation =
  | 'agenda.create'
  | 'agenda.reschedule'
  | 'agenda.cancel'
  | 'agenda.list'
  | 'agenda.practitioners'
  | 'agenda.slots';

export type AgendaCommandResult = RemoteCommandResult;

export async function sendAgendaCommand(
  pairing: PatientPairing,
  operation: AgendaOperation,
  payload: Record<string, unknown>,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<AgendaCommandResult> {
  return sendRemoteCommand(pairing, 'agenda', operation, payload, idempotencyKey);
}

export const PatientCompanionAgendaTransport = { sendAgendaCommand };
