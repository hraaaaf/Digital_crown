import type { CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';

export interface DocumentPreviewFingerprintInput {
  activeTab: CertifiableDocumentStudioTab;
  patientId?: string;
  docDate: string;
  drugs?: Array<Record<string, unknown>>;
  certificate?: {
    type: string;
    days: number;
    startDate: string;
    customReason: string;
  };
  accounting?: {
    items: Array<Record<string, unknown>>;
    paymentMode: string;
    paymentStatus: string;
    installments: Array<Record<string, unknown>>;
    isGlobalNote: boolean;
    selectedTeeth: Array<Record<string, unknown>>;
  };
  libre?: {
    title: string;
    content: string;
    customPatient: string;
    customDate: string;
    hideHeader: boolean;
    pageSize: 'A4' | 'A5';
    alignment: 'left' | 'center' | 'right' | 'justify';
  };
  isAccounted?: boolean;
  showLegalAnnotations?: boolean;
  installmentPayload?: unknown;
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([key, nested]) => [key, canonicalize(nested)]),
    );
  }
  return value;
}

export function documentPreviewFingerprint(input: DocumentPreviewFingerprintInput): string {
  return JSON.stringify(canonicalize(input));
}
