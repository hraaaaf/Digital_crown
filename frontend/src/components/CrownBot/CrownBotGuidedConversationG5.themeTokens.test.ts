/** CB2 G5 — semantic visual roles, no fixed theme palette in real workflow UI.
 * This static regression is intentionally separate from live browser/NVDA proof.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const component = readFileSync(
  resolve(process.cwd(), 'src/components/CrownBot/CrownBotGuidedConversationG5.tsx'),
  'utf8',
);
const css = readFileSync(resolve(process.cwd(), 'src/index.css'), 'utf8');

describe('CB2 G5: theme semantic role contract', () => {
  it('uses role-driven colours across conversation, confirmation and reconciliation', () => {
    for (const token of [
      'bg-background', 'text-text-main', 'bg-card', 'border-border-main',
      'bg-primary', 'text-on-primary', 'bg-warning-surface',
      'border-warning-border', 'bg-danger-surface', 'text-danger',
      'bg-info-surface', 'border-info-border', 'text-info',
      'bg-input-field', 'text-text-muted',
    ]) {
      expect(component).toContain(token);
    }
  });

  it('does not override theme roles with any fixed branded or neutral Tailwind palette', () => {
    const fixed = /\b(?:bg|text|border|ring|from|to|hover:bg|hover:text)-(?:white|black|slate|gray|blue|indigo|amber|emerald|green|orange|red|rose)(?:-\d+)?(?:\/\d+)?\b/g;
    expect(component.match(fixed) ?? []).toEqual([]);
    expect(component).not.toMatch(/(?:backgroundColor|color)\s*:\s*['"]?#(?:[0-9a-f]{3}|[0-9a-f]{6})\b/i);
  });

  it('all supported themes define semantic surfaces and accessible on-primary colours', () => {
    for (const role of [
      '--color-primary:', '--color-on-primary:', '--color-card:',
      '--color-text-main:', '--color-border-main:',
      '--color-warning-surface:', '--color-danger-surface:',
      '--color-info-surface:',
    ]) {
      expect(css).toContain(role);
    }
    for (const name of ['emerald', 'rose', 'ocean', 'graphite', 'prestige', 'dark', 'high-contrast']) {
      expect(css).toContain("[data-theme='" + name + "']");
    }
    expect(component).not.toContain('text-white');
  });
});
