export interface PocketReadAccess {
  agenda: boolean;
  patients: boolean;
  clinical: boolean;
  finance: boolean;
}

export const DENY_POCKET_READ: PocketReadAccess = {
  agenda: false, patients: false, clinical: false, finance: false,
};

/** Only destinations covered by the read contract; other guards remain intact. */
export function canOpenPocketReadTab(tab: string, access: PocketReadAccess): boolean {
  if (['today', 'agenda', 'waiting-room', 'frontdesk'].includes(tab)) return access.agenda;
  if (['patients', 'notifications', 'stock', 'lab', 'marketplace'].includes(tab)) return access.patients;
  if (tab === 'finance') return access.finance;
  return ['securite', 'bot', 'dentists', 'library'].includes(tab);
}

const ACTIONS = {
  agenda: 'agenda.read',
  patients: 'cabinet.patients.read',
  clinical: 'cabinet.clinical.read',
  finance: 'cabinet.finance.read',
} as const;

/** A patient contract or an unknown schema must never authorize staff UI. */
export function parsePocketReadAccess(value: unknown): PocketReadAccess {
  if (!value || typeof value !== 'object') throw new Error('Contrat de droits indisponible.');
  const payload = value as Record<string, unknown>;
  if (payload.version !== 1 || payload.principal_kind !== 'staff'
    || !payload.capabilities || typeof payload.capabilities !== 'object') {
    throw new Error('Contrat de droits incompatible.');
  }
  const capabilities = payload.capabilities as Record<string, unknown>;
  const access = { ...DENY_POCKET_READ };
  for (const [key, action] of Object.entries(ACTIONS)) {
    const entry = capabilities[action];
    if (!entry || typeof entry !== 'object') throw new Error('Droits incomplets.');
    const grant = entry as Record<string, unknown>;
    if (typeof grant.allowed !== 'boolean'
      || (grant.allowed ? grant.scope !== 'cabinet' : grant.scope !== null)) {
      throw new Error('Périmètre de droits invalide.');
    }
    access[key as keyof PocketReadAccess] = grant.allowed;
  }
  // Opening a clinical patient context also requires access to patient records.
  access.clinical = access.clinical && access.patients;
  return access;
}
