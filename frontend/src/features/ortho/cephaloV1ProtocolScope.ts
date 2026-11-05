/** Display selection only; scientific measurement composition is source-versioned. */
export const V1_CEPHALO_PROTOCOLS = [
  { id: 'COM', mode: 'com', label: 'COM Digital Crown' },
  { id: 'STEINER', mode: 'steiner', label: 'Steiner complet (1953 + 1959)' },
] as const;
export type V1CephaloProtocol = (typeof V1_CEPHALO_PROTOCOLS)[number]['id'];
export type V1CephaloMode = (typeof V1_CEPHALO_PROTOCOLS)[number]['mode'];
export const asV1CephaloProtocol = (v: string | null | undefined): V1CephaloProtocol | null =>
  v === 'COM' || v === 'STEINER' ? v : null;
export const v1ModeForProtocol = (v: string | null | undefined): V1CephaloMode | null =>
  V1_CEPHALO_PROTOCOLS.find(p => p.id === v)?.mode ?? null;
export const v1ProtocolForMode = (v: string | null | undefined): V1CephaloProtocol | null =>
  V1_CEPHALO_PROTOCOLS.find(p => p.mode === v)?.id ?? null;
