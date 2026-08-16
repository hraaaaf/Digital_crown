import { describe, expect, it } from 'vitest';

import { resolveDocumentNavigation } from './DocumentNavigationPolicy';

const clean = {
  accountingDirty: false,
  prescriptionDirty: false,
  certificateDirty: false,
  libreDirty: false,
  diagnosticDirty: false,
};

describe('DocumentNavigationPolicy', () => {
  it('does nothing on the current tab', () => {
    expect(resolveDocumentNavigation('ordonnance', 'ordonnance', clean)).toEqual({
      allow: false,
      requiresTransitionConfirmation: false,
      discardSource: null,
    });
  });

  it('allows a clean ordinary transition', () => {
    expect(resolveDocumentNavigation('ordonnance', 'certificat', clean)).toMatchObject({
      allow: true,
      discardSource: null,
    });
  });

  it('guards a dirty prescription', () => {
    expect(resolveDocumentNavigation('ordonnance', 'certificat', { ...clean, prescriptionDirty: true }).discardSource)
      .toBe('prescription');
  });

  it('guards a dirty certificate', () => {
    expect(resolveDocumentNavigation('certificat', 'libre', { ...clean, certificateDirty: true }).discardSource)
      .toBe('certificate');
  });

  it('guards a dirty free document', () => {
    expect(resolveDocumentNavigation('libre', 'ordonnance', { ...clean, libreDirty: true }).discardSource)
      .toBe('libre');
  });

  it('guards practitioner work in the diagnostic companion', () => {
    expect(resolveDocumentNavigation('plan', 'devis', { ...clean, diagnosticDirty: true }).discardSource)
      .toBe('diagnostic');
  });

  it('guards leaving a dirty accounting document', () => {
    expect(resolveDocumentNavigation('devis', 'ordonnance', { ...clean, accountingDirty: true }).discardSource)
      .toBe('accounting');
  });

  it('requires explicit confirmation for Devis to Honoraires', () => {
    const decision = resolveDocumentNavigation('devis', 'honoraires', clean);
    expect(decision.requiresTransitionConfirmation).toBe(true);
    expect(decision.allow).toBe(true);
  });

  it('does not treat Devis to Honoraires as discard even when accounting is dirty', () => {
    const decision = resolveDocumentNavigation('devis', 'honoraires', { ...clean, accountingDirty: true });
    expect(decision.discardSource).toBeNull();
    expect(decision.requiresTransitionConfirmation).toBe(true);
  });

  it('allows Honoraires to Devis without discard confirmation', () => {
    const decision = resolveDocumentNavigation('honoraires', 'devis', { ...clean, accountingDirty: true });
    expect(decision.allow).toBe(true);
    expect(decision.discardSource).toBeNull();
  });
});
