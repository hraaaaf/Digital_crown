export interface DocumentPreviewFingerprintInput {
  patientId?: string;
  activeTab: string;
  docDate: string;
  drugs: unknown;
  certifType: string;
  certifDays: number;
  certifStartDate: string;
  certifCustomMotif: string;
  items: unknown;
  paymentMode: string;
  paymentStatus?: string;
  isGlobalNote?: boolean;
  installments: unknown;
  libreTitle: string;
  libreContent: string;
  libreCustomPatient: string;
  libreCustomDate: string;
  libreHideHeader: boolean;
  librePageSize: 'A4' | 'A5';
  libreAlignment: 'left' | 'center' | 'right' | 'justify';
  showLegalAnnotations?: boolean;
  echeancierPayload: unknown;
}

export function documentPreviewFingerprint(input: DocumentPreviewFingerprintInput): string {
  return JSON.stringify({
    patientId: input.patientId ?? null,
    activeTab: input.activeTab,
    docDate: input.docDate,
    drugs: input.drugs,
    certifType: input.certifType,
    certifDays: input.certifDays,
    certifStartDate: input.certifStartDate,
    certifCustomMotif: input.certifCustomMotif,
    items: input.items,
    paymentMode: input.paymentMode,
    paymentStatus: input.paymentStatus ?? null,
    isGlobalNote: input.isGlobalNote ?? false,
    installments: input.installments,
    libreTitle: input.libreTitle,
    libreContent: input.libreContent,
    libreCustomPatient: input.libreCustomPatient,
    libreCustomDate: input.libreCustomDate,
    libreHideHeader: input.libreHideHeader,
    librePageSize: input.librePageSize,
    libreAlignment: input.libreAlignment,
    showLegalAnnotations: input.showLegalAnnotations ?? true,
    echeancierPayload: input.echeancierPayload,
  });
}
