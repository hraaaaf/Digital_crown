/**
 * Bounded static token contrast regression, WCAG 2.2 SC 1.4.3 AA benchmark.
 * This proves specified opaque role combinations, not all rendered UI,
 * alpha-blended layers, status/brand charts, or human visual acceptance.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const css = readFileSync(resolve(process.cwd(), 'src/index.css'), 'utf8');
const themes = ['default', 'emerald', 'rose', 'ocean', 'graphite', 'prestige', 'dark', 'high-contrast'] as const;

function declarations(selector: string): Record<string, string> {
  const marker = selector + ' {';
  const pos = css.indexOf(marker);
  if (pos < 0 || css.indexOf(marker, pos + marker.length) !== -1) {
    throw new Error('Missing or ambiguous CSS block: ' + selector);
  }
  const start = css.indexOf('{', pos) + 1;
  let level = 1;
  let end = start;
  for (; end < css.length && level; end++) {
    if (css[end] === '{') level++;
    if (css[end] === '}') level--;
  }
  if (level) throw new Error('Unclosed CSS block: ' + selector);
  const output: Record<string, string> = {};
  for (const match of css.slice(start, end - 1).matchAll(/(--[a-z-]+):\s*([^;]+);/g)) {
    output[match[1]] = match[2].trim();
  }
  return output;
}

function resolveColor(name: string, values: Record<string, string>, seen = new Set<string>()): string {
  if (seen.has(name)) throw new Error('Circular theme token: ' + name);
  const raw = values[name];
  if (!raw) throw new Error('Missing theme token: ' + name);
  const value = raw.trim().toLowerCase();
  if (value === 'white') return '#ffffff';
  if (value === 'black') return '#000000';
  if (/^#[0-9a-f]{6}$/.test(value)) return value;
  const reference = /^var\((--[a-z-]+)\)$/.exec(value);
  if (reference) return resolveColor(reference[1], values, new Set([...seen, name]));
  throw new Error('Cannot evaluate theme token ' + name + ' = ' + raw);
}

function luminance(hex: string): number {
  const channels = [1, 3, 5].map(offset => parseInt(hex.slice(offset, offset + 2), 16) / 255);
  const linear = channels.map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722;
}

function contrast(fg: string, bg: string): number {
  const a = luminance(fg);
  const b = luminance(bg);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

const base = declarations(':root');

describe('All eight themes: opaque semantic text contrast, WCAG AA benchmark', () => {
  it.each(themes)('%s supports 4.5:1 for regular text on card, input and background', theme => {
    const vars = theme === 'default' ? base : { ...base, ...declarations("[data-theme='" + theme + "']") };
    for (const background of ['--card-bg', '--input-bg', '--bg-medical-pearl']) {
      for (const foreground of ['--text-muted', '--text-main']) {
        const value = contrast(resolveColor(foreground, vars), resolveColor(background, vars));
        expect(value, theme + ' ' + foreground + ' / ' + background + ' ratio: ' + value.toFixed(3)).toBeGreaterThanOrEqual(4.5);
      }
    }
    const primaryText = contrast(resolveColor('--text-on-primary', vars), resolveColor('--primary', vars));
    expect(primaryText, theme + ' on-primary ratio: ' + primaryText.toFixed(3)).toBeGreaterThanOrEqual(4.5);
  });
});
