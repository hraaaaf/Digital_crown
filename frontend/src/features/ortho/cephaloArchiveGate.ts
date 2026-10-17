/** Strict wire contract returned by /patients/:id/cephalo-validation. */
export interface CephaloArchiveValidation {
  valid: boolean;
  fatals: string[];
  warnings: string[];
}

export function canArchiveCephaloValidation(value: CephaloArchiveValidation | null): boolean {
  return value?.valid === true && Array.isArray(value.fatals) && value.fatals.length === 0;
}

/** PDF transport is a Blob: preserve structured 409/422 refusals instead of a generic toast. */
export async function cephaloArchiveErrorMessage(error: unknown): Promise<string> {
  const response = (error as { response?: { data?: unknown; status?: number } })?.response;
  let body: unknown = response?.data;
  if (typeof Blob !== 'undefined' && body instanceof Blob) {
    try { body = JSON.parse(await body.text()); } catch { body = null; }
  }
  const detail = body && typeof body === 'object' && 'detail' in body
    ? (body as { detail: unknown }).detail : null;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (detail && typeof detail === 'object') {
    const structured = detail as { message?: unknown; fatals?: unknown };
    if (Array.isArray(structured.fatals) && typeof structured.fatals[0] === 'string')
      return 'Archivage refusé : ' + structured.fatals[0];
    if (typeof structured.message === 'string') return structured.message;
  }
  if (response?.status === 409) return "L'étude a changé : rechargez-la avant l'archivage.";
  if (response?.status === 403) return "Archivage refusé : autorisation insuffisante.";
  if (response?.status === 422) return "Archivage refusé : vérifiez les incohérences signalées.";
  return "Erreur lors de l'archivage.";
}
