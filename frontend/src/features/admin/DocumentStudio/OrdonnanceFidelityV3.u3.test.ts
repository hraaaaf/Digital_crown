import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio/Forms/QuickEntryBar.tsx'),
  'utf8',
);

describe('Ordonnance Fidelity V3 U3 premium glass inheritance', () => {
  it('marks the premium layer and covers the main Ordonnance surfaces', () => {
    expect(source).toContain('data-ordonnance-premium="u3"');
    expect(source).toContain('[data-ordonnance-hierarchy-header="primary"]');
    expect(source).toContain('[data-ordonnance-density-context]');
    expect(source).toContain('[data-ordonnance-protocol-chips]');
    expect(source).toContain('[data-ordonnance-quick-entry]');
    expect(source).toContain('[data-ordonnance-drug-card]');
  });

  it('inherits the active app theme instead of creating an Ordonnance palette', () => {
    for (const token of [
      '--glass-bg',
      '--glass-border',
      '--card-bg',
      '--text-main',
      '--input-bg',
      '--border-color',
      '--primary',
      '--accent',
    ]) {
      expect(source).toContain(`var(${token})`);
    }
    expect(source).toContain('color-mix(in srgb');
    expect(source).not.toContain('data-theme=');
  });

  it('uses optical depth without hard-coded hexadecimal colors', () => {
    expect(source).toContain('backdrop-filter: blur(24px) saturate(145%)');
    expect(source).toContain('inset 0 1px 0');
    expect(source).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
  });
});
