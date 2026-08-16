export const DOCUMENT_STUDIO_LABELS = {
  ordonnance: 'Ordonnance',
  certificat: 'Certificat',
  devis: 'Devis',
  honoraires: 'Note Honoraires',
  echeancier: 'Suivi Paiement',
  libre: 'Document Libre',
  plan: 'Compagnon Diagnostique',
} as const;

export type CertifiableDocumentStudioTab = keyof typeof DOCUMENT_STUDIO_LABELS;

export const DOCUMENT_STUDIO_TABS = Object.keys(DOCUMENT_STUDIO_LABELS) as CertifiableDocumentStudioTab[];

export const isCertifiableDocumentStudioTab = (value: string | null): value is CertifiableDocumentStudioTab =>
  Boolean(value && DOCUMENT_STUDIO_TABS.includes(value as CertifiableDocumentStudioTab));

export const DOCUMENT_STUDIO_PREVIEW_TITLES: Record<CertifiableDocumentStudioTab, string> = {
  ordonnance: 'Ordonnance',
  certificat: 'Certificat',
  devis: 'Devis',
  honoraires: "Note d'Honoraires",
  echeancier: 'Suivi Paiement',
  libre: 'Document Libre',
  plan: 'Compagnon Diagnostique',
};
