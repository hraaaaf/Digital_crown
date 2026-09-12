import { afterEach, describe, expect, it } from 'vitest';
import { PALETTE } from './cephaloTheme';

const setThemeTokens = (tokens: Record<string, string>) => {
  Object.entries(tokens).forEach(([name, value]) => document.body.style.setProperty(name, value));
};

afterEach(() => {
  document.body.removeAttribute('style');
  delete document.body.dataset.theme;
});

describe('cephaloTheme global token inheritance', () => {
  it('resolves the currently selected light-family theme instead of a local palette', () => {
    document.body.dataset.theme = 'emerald';
    setThemeTokens({
      '--bg-medical-pearl': '#f0fdf4',
      '--card-bg': '#fcfdfd',
      '--input-bg': '#f0fdf4',
      '--border-color': '#d1fae5',
      '--text-main': '#064e3b',
      '--text-muted': '#059669',
      '--primary': '#059669',
      '--shadow-elite': '0 10px 15px rgba(0,0,0,.05)',
      '--shadow-elite-hover': '0 20px 25px rgba(0,0,0,.08)',
    });

    const emerald = PALETTE.light;
    expect(emerald.bg).toBe('#f0fdf4');
    expect(emerald.bgPanel).toBe('#fcfdfd');
    expect(emerald.text).toBe('#064e3b');
    expect(emerald.accent).toBe('#059669');

    document.body.dataset.theme = 'rose';
    setThemeTokens({
      '--bg-medical-pearl': '#fff1f2',
      '--card-bg': '#fffbfb',
      '--input-bg': '#fff1f2',
      '--border-color': '#fecdd3',
      '--text-main': '#831843',
      '--text-muted': '#db2777',
      '--primary': '#db2777',
    });

    const rose = PALETTE.light;
    expect(rose.bg).toBe('#fff1f2');
    expect(rose.bgPanel).toBe('#fffbfb');
    expect(rose.text).toBe('#831843');
    expect(rose.accent).toBe('#db2777');
    expect(rose.accent).not.toBe(emerald.accent);
  });

  it('resolves prestige/dark from the same global semantic tokens', () => {
    document.body.dataset.theme = 'prestige';
    setThemeTokens({
      '--bg-medical-pearl': '#0f172a',
      '--card-bg': '#1e293b',
      '--input-bg': '#1e293b',
      '--border-color': '#334155',
      '--text-main': '#f8fafc',
      '--text-muted': '#94a3b8',
      '--primary': '#3b82f6',
    });

    const prestige = PALETTE.dark;
    expect(prestige.bg).toBe('#0f172a');
    expect(prestige.bgCard).toBe('#1e293b');
    expect(prestige.border).toBe('#334155');
    expect(prestige.text).toBe('#f8fafc');
    expect(prestige.accent).toBe('#3b82f6');
  });
});
