import type { CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';

type PermissionMap = Record<string, boolean | undefined> | undefined;

export function allowedDocumentStudioTabs(
  employerId: number | null | undefined,
  permissions: PermissionMap,
): CertifiableDocumentStudioTab[] {
  const isOwner = !employerId;
  const has = (permission: string) => isOwner || Boolean(permissions?.[permission]);
  const tabs: CertifiableDocumentStudioTab[] = [];

  if (has('prescriptions')) tabs.push('ordonnance');
  if (has('patients')) tabs.push('certificat');
  if (has('accounting')) tabs.push('devis', 'honoraires', 'echeancier');
  if (has('clinical')) tabs.push('libre');

  return tabs;
}
