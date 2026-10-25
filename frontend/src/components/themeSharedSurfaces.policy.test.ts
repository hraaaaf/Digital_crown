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
  it('primary action foreground meets WCAG AA in all eight canonical themes', () => {
    const css = readFileSync(resolve(process.cwd(), 'src/index.css'), 'utf8');
    const root = css.match(/^:root\s*\{([\s\S]*?)^\}/m)?.[1] ?? '';
    expect(root).not.toBe('');
    const value = (block: string, name: string) =>
      block.match(new RegExp('--' + name + '\\s*:\\s*([^;]+);'))?.[1].trim();
    const luminance = (hex: string) => {
      expect(hex).toMatch(/^#[0-9a-f]{6}$/i);
      const c = hex.slice(1).match(/../g)!.map(v => parseInt(v, 16) / 255)
        .map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
      return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
    };
    for (const theme of ['default', 'emerald', 'rose', 'ocean', 'graphite',
                         'prestige', 'dark', 'high-contrast']) {
      const match = theme === 'default'
        ? null
        : css.match(new RegExp("^\\[data-theme='" + theme + "'\\]\\s*\\{([\\s\\S]*?)^\\}", 'm'));
      const block = match?.[1] ?? root;
      const primary = value(block, 'primary') ?? value(root, 'primary')!;
      const foreground = value(block, 'text-on-primary') ?? value(root, 'text-on-primary')!;
      const a = luminance(primary);
      const b = luminance(foreground);
      const contrast = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
      expect(contrast, 'Insufficient AA brand-button contrast for ' + theme)
        .toBeGreaterThanOrEqual(4.5);
    }
  });

});
