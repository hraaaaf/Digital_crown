export function isSamePatientDocumentTabNavigation(
  currentHref: string,
  nextUrl: string | URL | null | undefined,
  patientId: string,
): boolean {
  if (nextUrl == null || !patientId) return false;

  const current = new URL(currentHref);
  const next = new URL(String(nextUrl), current);
  const patientPath = `/patients/${patientId}`;

  if (current.pathname !== patientPath || next.pathname !== patientPath) return false;

  return current.searchParams.get('documentTab') !== next.searchParams.get('documentTab');
}
