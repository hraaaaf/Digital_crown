import { describe, expect, it } from 'vitest';
import { shouldGuardDocumentTabTransition, type DocumentDirtySnapshot, type DocumentTab } from './DocumentTabNavigationPolicy';

const clean: DocumentDirtySnapshot = {
  prescription: false,
  certificate: false,
  accounting: false,
  installment: false,
  libre: false,
};

describe('shouldGuardDocumentTabTransition', () => {
  it.each([
    ['ordonnance', 'prescription'],
    ['certificat', 'certificate'],
    ['devis', 'accounting'],
    ['honoraires', 'accounting'],
    ['echeancier', 'installment'],
    ['libre', 'libre'],
  ] as const)('guards dirty %s transitions', (activeTab, dirtyKey) => {
    const nextTab: DocumentTab = activeTab === 'ordonnance' ? 'certificat' : 'ordonnance';
    expect(shouldGuardDocumentTabTransition(activeTab, nextTab, { ...clean, [dirtyKey]: true })).toBe(true);
  });

  it('does not guard a clean transition or a transition to the same tab', () => {
    expect(shouldGuardDocumentTabTransition('libre', 'ordonnance', clean)).toBe(false);
    expect(shouldGuardDocumentTabTransition('libre', 'libre', { ...clean, libre: true })).toBe(false);
  });

  it('keeps devis/honoraires as one shared accounting workspace', () => {
    const dirty = { ...clean, accounting: true };
    expect(shouldGuardDocumentTabTransition('devis', 'honoraires', dirty)).toBe(false);
    expect(shouldGuardDocumentTabTransition('honoraires', 'devis', dirty)).toBe(false);
  });
});