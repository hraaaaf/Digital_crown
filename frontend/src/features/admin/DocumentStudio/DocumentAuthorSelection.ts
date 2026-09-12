export interface DocumentPractitionerOption {
  id: number;
  name: string;
  role: string;
}

let selectedAuthorPractitionerId: number | null = null;

export function setDocumentAuthorPractitionerId(practitionerId: number | null): void {
  selectedAuthorPractitionerId = practitionerId;
}

export function getDocumentAuthorPractitionerId(): number | null {
  return selectedAuthorPractitionerId;
}

export function clearDocumentAuthorPractitionerId(): void {
  selectedAuthorPractitionerId = null;
}

export function resolveDocumentAuthorPreselection(
  practitioners: DocumentPractitionerOption[],
  currentUserId: number | null,
  referentPractitionerId: number | null,
): number | null {
  if (currentUserId !== null && practitioners.some(item => item.id === currentUserId)) {
    return currentUserId;
  }
  if (
    referentPractitionerId !== null &&
    practitioners.some(item => item.id === referentPractitionerId)
  ) {
    return referentPractitionerId;
  }
  return practitioners.length === 1 ? practitioners[0].id : null;
}

export interface RequestInterceptorClient {
  interceptors: {
    request: {
      use: (handler: (config: any) => any) => number;
      eject: (id: number) => void;
    };
  };
}

export function installDocumentAuthorRequestGuard(client: RequestInterceptorClient): () => void {
  const interceptorId = client.interceptors.request.use((config: any) => {
    const method = String(config?.method || 'get').toLowerCase();
    const url = String(config?.url || '');
    if (method !== 'post' || !url.includes('/documents/generate')) return config;

    const authorId = getDocumentAuthorPractitionerId();
    if (authorId === null) return config;

    const data = config?.data && typeof config.data === 'object'
      ? { ...config.data, author_practitioner_id: authorId }
      : config?.data;

    return { ...config, data };
  });

  return () => client.interceptors.request.eject(interceptorId);
}
