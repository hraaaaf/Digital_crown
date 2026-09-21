import type { PatientPairing } from './PatientCompanionStorage';
import { sendRemoteCommand } from './PatientCompanionRemoteCommandTransport';

export const PC07_CHUNK_BYTES = 96 * 1024;

export type EmergencyPhotoUploadProgress = {
  uploadId: string;
  sentChunks: number;
  totalChunks: number;
};

const bytesToBase64 = (bytes: Uint8Array) => {
  let binary = '';
  for (let index = 0; index < bytes.length; index += 1) {
    binary += String.fromCharCode(bytes[index]);
  }
  return btoa(binary);
};

const sha256Hex = async (bytes: Uint8Array) => {
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), value => value.toString(16).padStart(2, '0')).join('');
};

export async function uploadEmergencyPhoto(
  pairing: PatientPairing,
  uploadId: string,
  bytes: Uint8Array<ArrayBuffer>,
  capturedAt: string,
  onProgress?: (progress: EmergencyPhotoUploadProgress) => void,
) {
  if (!bytes.byteLength) throw new Error('Photo locale vide.');
  const totalChunks = Math.ceil(bytes.byteLength / PC07_CHUNK_BYTES);
  const objectSha256 = await sha256Hex(bytes);

  const begin = await sendRemoteCommand(
    pairing,
    'emergency-photo',
    'emergency_photo.begin',
    {
      upload_id: uploadId,
      object_sha256: objectSha256,
      byte_size: bytes.byteLength,
      chunk_count: totalChunks,
      captured_at: capturedAt,
    },
  );

  if (begin.status !== 'ACCEPTED') {
    throw new Error('Le cabinet a refusé la préparation de la photo.');
  }
  if (begin.result.state === 'received') {
    return begin;
  }

  const receivedChunks = Number(begin.result.received_chunks ?? 0);
  const startIndex = Number.isInteger(receivedChunks)
    ? Math.max(0, Math.min(totalChunks, receivedChunks))
    : 0;

  onProgress?.({ uploadId, sentChunks: startIndex, totalChunks });

  for (let index = startIndex; index < totalChunks; index += 1) {
    const start = index * PC07_CHUNK_BYTES;
    const end = Math.min(bytes.byteLength, start + PC07_CHUNK_BYTES);
    const chunk = bytes.slice(start, end);
    const result = await sendRemoteCommand(
      pairing,
      'emergency-photo',
      'emergency_photo.chunk',
      {
        upload_id: uploadId,
        chunk_index: index,
        chunk_sha256: await sha256Hex(chunk),
        chunk_b64: bytesToBase64(chunk),
      },
    );
    if (result.status !== 'ACCEPTED') {
      throw new Error('Le cabinet a refusé un fragment de la photo.');
    }
    onProgress?.({ uploadId, sentChunks: index + 1, totalChunks });
  }

  const finalized = await sendRemoteCommand(
    pairing,
    'emergency-photo',
    'emergency_photo.finalize',
    { upload_id: uploadId },
  );
  if (finalized.status !== 'ACCEPTED' || finalized.result.state !== 'received') {
    throw new Error('Le cabinet n’a pas confirmé la réception de la photo.');
  }
  return finalized;
}
