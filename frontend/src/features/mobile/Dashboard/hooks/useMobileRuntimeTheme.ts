import { useEffect } from 'react';
import { CryptoService } from '../../../../services/zka/CryptoService';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';

export interface MobileRuntimeTheme {
  selected_theme?: string | null;
  app_accent_color?: string | null;
  font_fr?: string | null;
  primary_color?: string | null;
  secondary_color?: string | null;
  accent_color?: string | null;
}

const FONT_STACKS: Record<string, string> = {
  inter: '"Inter", system-ui, sans-serif',
  outfit: '"Outfit", sans-serif',
  playfair: '"Playfair Display", serif',
  mono: '"JetBrains Mono", ui-monospace, monospace',
};

const MOBILE_THEME_CACHE_KEY = 'digitalcrown_mobile_theme';

function resolveApiBaseUrl(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return stored;
}

function setCssVariable(name: string, value?: string | null) {
  const targets = [document.documentElement, document.body];
  for (const target of targets) {
    if (value) target.style.setProperty(name, value);
    else target.style.removeProperty(name);
  }
}

export function textColorForHex(hexColor?: string | null): string | null {
  if (!hexColor || !/^#[0-9a-f]{6}$/i.test(hexColor)) return null;
  const hex = hexColor.slice(1);
  const rgb = [0, 2, 4].map(index => Number.parseInt(hex.slice(index, index + 2), 16));
  const luminance = (channels: number[]) => channels
    .map(channel => channel / 255)
    .map(value => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4)
    .reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
  const background = luminance(rgb);
  const dark = '#020617';
  const white = '#ffffff';
  const contrastDark = (Math.max(background, luminance([2, 6, 23])) + 0.05)
    / (Math.min(background, luminance([2, 6, 23])) + 0.05);
  const contrastWhite = (1.05) / (background + 0.05);
  return contrastDark >= contrastWhite ? dark : white;
}

/**
 * Compute a readable foreground ink from the actual cabinet-selected fill.
 * Keep --primary untouched for brand surfaces. Small labels must reach 4.5:1
 * against both the card and the Pocket canvas, including dark themes.
 */
export function accessiblePrimaryInk(
  primary: string | null | undefined,
  cardSurface: string,
  canvasSurface: string,
): string | null {
  const parse = (value: string | null | undefined): number[] | null => {
    if (!value) return null;
    const normalized = value.trim().toLowerCase();
    if (normalized === 'white') return [255, 255, 255];
    if (normalized === 'black') return [0, 0, 0];
    if (!/^#[0-9a-f]{6}$/.test(normalized)) return null;
    return [1, 3, 5].map(offset => Number.parseInt(normalized.slice(offset, offset + 2), 16));
  };
  const base = parse(primary);
  const card = parse(cardSurface);
  const canvas = parse(canvasSurface);
  if (!base || !card || !canvas) return null;
  const luminance = (rgb: number[]) => rgb
    .map(channel => channel / 255)
    .map(value => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4)
    .reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
  const ratio = (foreground: number[], background: number[]) => {
    const a = luminance(foreground);
    const b = luminance(background);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  };
  const target = luminance(card) < 0.179 ? [255, 255, 255] : [0, 0, 0];
  const encode = (rgb: number[]) => '#' + rgb.map(value => Math.round(value).toString(16).padStart(2, '0')).join('');
  for (let step = 0; step <= 100; step += 2) {
    const portion = step / 100;
    const foreground = base.map((value, index) => Math.round(value + (target[index] - value) * portion));
    if (ratio(foreground, card) >= 4.5 && ratio(foreground, canvas) >= 4.5) {
      return encode(foreground);
    }
  }
  return encode(target);
}

function enableMobileRuntimeFontRouting() {
  document.documentElement.dataset.mobileThemeRuntime = 'true';
}

export function applyMobileRuntimeTheme(theme: MobileRuntimeTheme) {
  enableMobileRuntimeFontRouting();

  const selectedTheme = theme.selected_theme || 'elite';
  const dataTheme = selectedTheme === 'elite' ? '' : selectedTheme;
  document.documentElement.dataset.theme = dataTheme;
  document.body.dataset.theme = dataTheme;

  setCssVariable('--primary', theme.primary_color);
  setCssVariable('--secondary', theme.secondary_color);
  setCssVariable('--accent', theme.accent_color);
  setCssVariable('--app-accent', theme.app_accent_color);
  setCssVariable('--text-on-primary', textColorForHex(theme.primary_color));
  const selectedPalette = getComputedStyle(document.documentElement);
  setCssVariable('--primary-ink', accessiblePrimaryInk(
    selectedPalette.getPropertyValue('--primary'),
    selectedPalette.getPropertyValue('--card-bg'),
    selectedPalette.getPropertyValue('--bg-medical-pearl'),
  ));

  const fontId = theme.font_fr || 'inter';
  const fontStack = FONT_STACKS[fontId] || FONT_STACKS.inter;
  setCssVariable('--app-font-family', fontStack);

  localStorage.setItem('digitalcrown_theme', selectedTheme);
  localStorage.setItem('digitalcrown_font_fr', fontId);
  localStorage.setItem(MOBILE_THEME_CACHE_KEY, JSON.stringify(theme));

  let metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (!metaThemeColor) {
    metaThemeColor = document.createElement('meta');
    metaThemeColor.setAttribute('name', 'theme-color');
    document.head.appendChild(metaThemeColor);
  }
  const background = getComputedStyle(document.documentElement)
    .getPropertyValue('--bg-medical-pearl')
    .trim();
  if (background) metaThemeColor.setAttribute('content', background);
}

function applyCachedTheme() {
  try {
    const cached = localStorage.getItem(MOBILE_THEME_CACHE_KEY);
    if (cached) applyMobileRuntimeTheme(JSON.parse(cached) as MobileRuntimeTheme);
  } catch {
    localStorage.removeItem(MOBILE_THEME_CACHE_KEY);
  }
}

export function bootstrapMobileRuntimeTheme() {
  enableMobileRuntimeFontRouting();
  setCssVariable('--app-font-family', FONT_STACKS.inter);
  applyCachedTheme();
}

export function useMobileRuntimeTheme(refreshKey?: string) {
  useEffect(() => {
    let cancelled = false;
    bootstrapMobileRuntimeTheme();

    const sync = async () => {
      const creds = await MobileStorage.getCredentials();
      if (!creds || cancelled) return;

      try {
        const response = await mobileFetch(
          `${resolveApiBaseUrl(creds.api_base_url)}/api/clinics/mobile-theme`,
          {
            headers: { Authorization: `Bearer ${creds.access_token}` },
            signal: AbortSignal.timeout(5000),
          },
        );
        if (!response.ok || cancelled) return;

        const raw = await response.json();
        const theme: MobileRuntimeTheme = raw.payload
          ? await CryptoService.decryptPayload(raw.payload, creds.masterKey)
          : raw;
        if (!cancelled) applyMobileRuntimeTheme(theme);
      } catch {
        // Offline or unavailable: keep the last verified local theme.
      }
    };

    void sync();
    return () => { cancelled = true; };
  }, [refreshKey]);
}
