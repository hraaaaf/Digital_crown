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

function textColorForHex(hexColor?: string | null): string | null {
  if (!hexColor || !/^#[0-9a-f]{6}$/i.test(hexColor)) return null;
  const hex = hexColor.slice(1);
  const r = Number.parseInt(hex.slice(0, 2), 16);
  const g = Number.parseInt(hex.slice(2, 4), 16);
  const b = Number.parseInt(hex.slice(4, 6), 16);
  const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
  return yiq >= 128 ? '#0f172a' : '#ffffff';
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
