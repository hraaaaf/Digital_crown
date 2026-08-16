type DirtyListener = (dirty: boolean) => void;

interface ArchiveResponseLike {
  config?: {
    url?: string;
    method?: string;
    data?: unknown;
  };
  data?: {
    pdf_url?: unknown;
  };
}

let libreDirty = false;
const listeners = new Set<DirtyListener>();

export function isLibreDirty(): boolean {
  return libreDirty;
}

export function setLibreDirty(dirty: boolean): void {
  if (libreDirty === dirty) return;
  libreDirty = dirty;
  listeners.forEach(listener => listener(dirty));
}

export function subscribeLibreDirty(listener: DirtyListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function isSuccessfulLibreArchiveResponse(response: ArchiveResponseLike): boolean {
  const url = String(response?.config?.url || '');
  const method = String(response?.config?.method || '').toLowerCase();
  if (method !== 'post' || !url.includes('/documents/generate') || !url.includes('archive=true')) {
    return false;
  }

  let payload = response?.config?.data;
  if (typeof payload === 'string') {
    try {
      payload = JSON.parse(payload);
    } catch {
      return false;
    }
  }

  if (!payload || typeof payload !== 'object' || !('type' in payload)) {
    return false;
  }

  return (payload as { type?: unknown }).type === 'libre'
    && typeof response?.data?.pdf_url === 'string'
    && response.data.pdf_url.trim().length > 0;
}
