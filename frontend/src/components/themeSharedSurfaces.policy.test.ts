/** Shared UI must inherit Digital Crown's semantic theme; no fixed palette. */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = (file: string) =>
  readFileSync(resolve(process.cwd(), 'src/components', file), 'utf8');
// Include fixed named colors, opacity variants and Tailwind arbitrary hex classes.
const fixed = /\b(?:[\w-]+:)*(?:bg|text|border|from|via|to|ring|outline|fill|stroke|shadow)-(?:slate|gray|zinc|neutral|stone|blue|indigo|emerald|green|amber|orange|rose|red|cyan|teal|purple|pink|yellow|sky|violet|fuchsia|lime|white|black)(?:-\d{2,3})?(?:\/\d+)?\b|(?:bg|text|border)-\[#[0-9a-f]{3,8}\]/gi;
const files = [
  'AppLoader.tsx',
  'ComingSoon.tsx',
  'EliteGhostLoader.tsx',
  'ErrorBoundary.tsx',
  'PWAInstallPrompt.tsx',
  'CrownBot/ChatMessage.tsx',
  'CrownBot/CrownBotGuidedNluCb02.tsx',
  'CrownBot/CrownBotWorkflowPreview.tsx',
] as const;

describe('Digital Crown shared UI semantic theme contract', () => {
  it.each(files)('%s has no fixed Tailwind palette, including white and black', file => {
    const content = source(file);
    expect(content.match(fixed) ?? []).toEqual([]);
    expect(content).toMatch(/(?:bg|text|border)-(?:background|card|primary|text-main|text-muted|danger|warning|info|success|border-main|input-field|on-primary)/);
  });

  it('branded buttons always use the canonical on-primary foreground', () => {
    for (const file of ['ErrorBoundary.tsx', 'PWAInstallPrompt.tsx',
                        'CrownBot/ChatMessage.tsx', 'CrownBot/CrownBotGuidedNluCb02.tsx',
                        'CrownBot/CrownBotWorkflowPreview.tsx']) {
      const content = source(file);
      expect(content).toContain('bg-primary');
      expect(content).toContain('text-on-primary');
    }
  });

  it('the error and offline surfaces use semantic role colors', () => {
    expect(source('ErrorBoundary.tsx')).toContain('bg-danger-surface text-danger');
    expect(source('CrownBot/CrownBotWorkflowPreview.tsx')).toContain('bg-danger-surface');
    expect(source('CrownBot/ChatMessage.tsx')).toContain('bg-card text-text-main');
    expect(source('PWAInstallPrompt.tsx')).toContain('bg-input-field');
    expect(source('AppLoader.tsx')).toContain('bg-primary');
  });

  it('all eight application themes define a canonical dynamic palette', () => {
    const css = readFileSync(resolve(process.cwd(), 'src/index.css'), 'utf8');
    for (const alias of ['--color-card:', '--color-background:', '--color-primary:',
                        '--color-on-primary:', '--color-danger-surface:',
                        '--color-warning-surface:', '--color-info-surface:']) {
      expect(css).toContain(alias);
    }
    for (const name of ['emerald', 'rose', 'ocean', 'graphite', 'prestige', 'dark', 'high-contrast']) {
      expect(css).toContain("[data-theme='" + name + "']");
    }
  });
});
