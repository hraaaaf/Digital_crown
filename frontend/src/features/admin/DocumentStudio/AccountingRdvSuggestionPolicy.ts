import type { HubDocumentType } from '../DocumentHub';

/**
 * A quote is a proposal, not proof that treatment occurred.
 * Appointment follow-up suggestions may only be surfaced after clinical/financial
 * flows that represent performed care, never after merely archiving a Devis.
 */
export function shouldSurfaceRdvSuggestion(
  activeTab: HubDocumentType,
  isPreview: boolean,
  hasSuggestion: boolean,
): boolean {
  if (isPreview || !hasSuggestion) return false;
  return activeTab !== 'devis';
}
