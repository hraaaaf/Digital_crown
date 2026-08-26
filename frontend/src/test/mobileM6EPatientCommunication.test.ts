import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { buildTelHref, buildWhatsAppHref } from '../features/mobile/Context/mobilePatientContact';

const contextSource = readFileSync(resolve(process.cwd(), 'src/features/mobile/Context/MobileContext.tsx'), 'utf8');

describe('M6-E patient mobile communication', () => {
  it('builds a safe tel URI for international and local phone numbers', () => {
    expect(buildTelHref('+212 612-345-678')).toBe('tel:+212612345678');
    expect(buildTelHref('00212 612 345 678')).toBe('tel:+212612345678');
    expect(buildTelHref('0612345678')).toBe('tel:0612345678');
    expect(buildTelHref('000')).toBeNull();
    expect(buildTelHref('  ')).toBeNull();
    expect(buildTelHref('0612;DROP')).toBeNull();
  });

  it('opens WhatsApp only for an explicitly international number', () => {
    expect(buildWhatsAppHref('+212 612-345-678')).toBe('https://wa.me/212612345678');
    expect(buildWhatsAppHref('00212 612 345 678')).toBe('https://wa.me/212612345678');
    expect(buildWhatsAppHref('0612345678')).toBeNull();
    expect(buildWhatsAppHref('000')).toBeNull();
    expect(buildWhatsAppHref(null)).toBeNull();
  });

  it('never adds patient content or prefilled text to the WhatsApp URL', () => {
    const href = buildWhatsAppHref('+212 612 345 678');
    expect(href).toBe('https://wa.me/212612345678');
    expect(href).not.toContain('?');
    expect(href).not.toContain('text=');
    expect(href).not.toContain('BENNANI');
  });

  it('keeps explicit disabled states and preserves the existing quick actions', () => {
    expect(contextSource).toContain('data-m6e-whatsapp');
    expect(contextSource).toContain('data-m6e-call');
    expect(contextSource).toContain('WhatsApp : indicatif international requis.');
    expect(contextSource).toContain('WhatsApp indisponible : aucun numéro patient.');
    expect(contextSource).toContain('Photo clinique');
    expect(contextSource).toContain('Scanner un document');
    expect(contextSource).toContain("navigate('/mobile/dashboard?tab=agenda')");
  });
});
