const MIME_EXTENSION: Record<string, string> = {
  'application/pdf': 'pdf',
  'image/jpeg': 'jpg',
  'image/png': 'png',
  'image/webp': 'webp',
  'image/gif': 'gif',
  'text/plain': 'txt',
};

export interface DocumentShareNavigator {
  share?: (data: ShareData) => Promise<void>;
  canShare?: (data?: ShareData) => boolean;
}

export function buildDocumentShareFile(blob: Blob, mimeHint?: string | null): File {
  const type = (blob.type || mimeHint || 'application/octet-stream').toLowerCase();
  const extension = MIME_EXTENSION[type];
  const name = extension ? `document-digital-crown.${extension}` : 'document-digital-crown';
  return new File([blob], name, { type });
}

export function buildDocumentShareData(blob: Blob, mimeHint?: string | null): ShareData {
  return { files: [buildDocumentShareFile(blob, mimeHint)] };
}

export function canNativeShareDocument(navigatorLike: DocumentShareNavigator, data: ShareData): boolean {
  if (typeof navigatorLike.share !== 'function' || typeof navigatorLike.canShare !== 'function' || !data.files?.length) return false;
  try {
    return navigatorLike.canShare({ files: data.files });
  } catch {
    return false;
  }
}

export function isShareAbortError(error: unknown): boolean {
  return !!error && typeof error === 'object' && 'name' in error && (error as { name?: unknown }).name === 'AbortError';
}
