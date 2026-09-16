import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  CEPHALO_SCIENTIFIC_BASE_HUES,
  CEPHALO_SCIENTIFIC_COLORS,
  cephaloGeometryColor,
  cephaloGeometryFamily,
  cephaloMetricColor,
  cephaloMetricFamily,
} from './cephaloVisualSemantics';

type Rgb = readonly [number, number, number];

const SCIENTIFIC_BASE_WEIGHT = 0.42;
const RADIOGRAPH_ANCHOR = '#f8fafc';
const RADIOGRAPH_BACKGROUND = '#020617';

const parseColor = (value: string): Rgb => {
  const normalized = value.trim().toLowerCase();
  if (normalized === 'white') return [255, 255, 255];
  if (normalized === 'black') return [0, 0, 0];
  const match = normalized.match(/^#([0-9a-f]{6})$/);
  if (!match) throw new Error(`Unsupported theme color: ${value}`);
  return [
    Number.parseInt(match[1].slice(0, 2), 16),
    Number.parseInt(match[1].slice(2, 4), 16),
    Number.parseInt(match[1].slice(4, 6), 16),
  ];
};

const mixSrgb = (base: Rgb, anchor: Rgb, baseWeight = SCIENTIFIC_BASE_WEIGHT): Rgb => [
  Math.round(base[0] * baseWeight + anchor[0] * (1 - baseWeight)),
  Math.round(base[1] * baseWeight + anchor[1] * (1 - baseWeight)),
  Math.round(base[2] * baseWeight + anchor[2] * (1 - baseWeight)),
];

const relativeLuminance = (rgb: Rgb): number => {
  const linear = rgb.map(channel => {
    const srgb = channel / 255;
    return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
};

const contrastRatio = (a: Rgb, b: Rgb): number => {
  const l1 = relativeLuminance(a);
  const l2 = relativeLuminance(b);
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
};

const css = fs.readFileSync(path.resolve(process.cwd(), 'src/index.css'), 'utf8');
const themeSelectors = [
  [':root', 'default'],
  ["[data-theme='emerald']", 'emerald'],
  ["[data-theme='rose']", 'rose'],
  ["[data-theme='prestige']", 'prestige'],
  ["[data-theme='ocean']", 'ocean'],
  ["[data-theme='graphite']", 'graphite'],
  ["[data-theme='dark']", 'dark'],
  ["[data-theme='high-contrast']", 'high-contrast'],
] as const;

const themeBlock = (selector: string): string => {
  const marker = `${selector} {`;
  const start = css.indexOf(marker);
  if (start < 0) throw new Error(`Missing Digital Crown theme block: ${selector}`);
  const end = css.indexOf('}', start);
  if (end < 0) throw new Error(`Unclosed Digital Crown theme block: ${selector}`);
  return css.slice(start, end + 1);
};

const themeToken = (block: string, token: string): Rgb => {
  const match = block.match(new RegExp(`--${token}:\\s*([^;]+);`));
  if (!match) throw new Error(`Missing Digital Crown token --${token}`);
  return parseColor(match[1]);
};

describe('Céphalo scientific color semantics', () => {
  it('keeps the five scientific families distinct', () => {
    expect(new Set(Object.values(CEPHALO_SCIENTIFIC_BASE_HUES)).size).toBe(5);
    expect(new Set(Object.values(CEPHALO_SCIENTIFIC_COLORS)).size).toBe(5);
  });

  it('uses a context anchor with Digital Crown text fallback', () => {
    for (const family of Object.keys(CEPHALO_SCIENTIFIC_BASE_HUES) as Array<keyof typeof CEPHALO_SCIENTIFIC_BASE_HUES>) {
      const rendered = CEPHALO_SCIENTIFIC_COLORS[family];
      expect(rendered).toContain(CEPHALO_SCIENTIFIC_BASE_HUES[family]);
      expect(rendered).toContain('42%');
      expect(rendered).toContain('58%');
      expect(rendered).toContain('var(--cephalo-scientific-anchor');
      expect(rendered).toContain('var(--text-main)');
      expect(rendered).toContain('color-mix(in srgb');
    }
  });

  it('keeps every scientific family at or above 4.5:1 on Digital Crown card and input surfaces', () => {
    for (const [selector, themeName] of themeSelectors) {
      const block = themeBlock(selector);
      const text = themeToken(block, 'text-main');
      const surfaces = [themeToken(block, 'card-bg'), themeToken(block, 'input-bg')];

      for (const [family, baseHue] of Object.entries(CEPHALO_SCIENTIFIC_BASE_HUES)) {
        const rendered = mixSrgb(parseColor(baseHue), text);
        for (const surface of surfaces) {
          expect(
            contrastRatio(rendered, surface),
            `${family} contrast is insufficient in ${themeName}`,
          ).toBeGreaterThanOrEqual(4.5);
        }
      }
    }
  });

  it('keeps on-radiograph family variants strongly visible on the cinematic viewer', () => {
    const anchor = parseColor(RADIOGRAPH_ANCHOR);
    const background = parseColor(RADIOGRAPH_BACKGROUND);
    for (const [family, baseHue] of Object.entries(CEPHALO_SCIENTIFIC_BASE_HUES)) {
      const rendered = mixSrgb(parseColor(baseHue), anchor);
      expect(
        contrastRatio(rendered, background),
        `${family} is too dark on the radiographic viewer`,
      ).toBeGreaterThanOrEqual(7);
    }
  });

  it('maps skeletal metrics to the skeletal family', () => {
    for (const key of ['SNA', 'SNB', 'ANB', 'Angle_de_Tweed', 'Situation_A', 'Situation_B', 'Profondeur_Faciale', 'Co_A', 'Co_Gn', 'ANS_Me']) {
      expect(cephaloMetricFamily(key)).toBe('skeletal');
      expect(cephaloMetricColor(key)).toBe(CEPHALO_SCIENTIFIC_COLORS.skeletal);
    }
  });

  it('maps dental metrics to the dental family', () => {
    for (const key of ['IMPA', 'I_Francfort', 'Inter_Incisif', 'Surplomb', 'Recouvrement']) {
      expect(cephaloMetricFamily(key)).toBe('dental');
      expect(cephaloMetricColor(key)).toBe(CEPHALO_SCIENTIFIC_COLORS.dental);
    }
  });

  it('maps soft-tissue metrics to the soft-tissue family', () => {
    for (const key of ['Ligne_E_Ls', 'Ligne_E_Li']) {
      expect(cephaloMetricFamily(key)).toBe('soft_tissue');
      expect(cephaloMetricColor(key)).toBe(CEPHALO_SCIENTIFIC_COLORS.soft_tissue);
    }
  });

  it('keeps reference planes distinct from measured structures', () => {
    for (const key of ['fh', 'mp', 'sn', 'occ', 'mcnamara_perp']) {
      expect(cephaloGeometryFamily(key)).toBe('reference');
      expect(cephaloGeometryColor(key)).toBe(CEPHALO_SCIENTIFIC_COLORS.reference);
    }
  });

  it('maps geometry to the same vocabulary used by the table', () => {
    expect(cephaloGeometryFamily('na')).toBe('skeletal');
    expect(cephaloGeometryFamily('nb')).toBe('skeletal');
    expect(cephaloGeometryFamily('u1')).toBe('dental');
    expect(cephaloGeometryFamily('l1')).toBe('dental');
    expect(cephaloGeometryFamily('eline')).toBe('soft_tissue');
  });

  it('fails safely to auxiliary for unknown presentation-only keys', () => {
    expect(cephaloMetricFamily('UNKNOWN_METRIC')).toBe('auxiliary');
    expect(cephaloGeometryFamily('unknown_geometry')).toBe('auxiliary');
  });
});
