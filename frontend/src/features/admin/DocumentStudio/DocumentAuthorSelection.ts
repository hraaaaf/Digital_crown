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
