type CephaloPalette = {
  bg: string;
  bgPanel: string;
  bgCard: string;
  bgInput: string;
  border: string;
  borderFocus: string;
  text: string;
  textMuted: string;
  textDim: string;
  accent: string;
  accentSuccess: string;
  accentWarning: string;
  accentError: string;
  shadow: string;
  shadowLg: string;
};

const FALLBACK = {
  dark: {
    bg: '#020617',
    bgPanel: '#0a0f1e',
    bgCard: '#0f172a',
    bgInput: '#020617',
    border: '#1e293b',
    borderFocus: '#6366f1',
    text: '#ffffff',
    textMuted: '#94a3b8',
    textDim: '#64748b',
    accent: '#4f46e5',
    accentSuccess: '#10b981',
    accentWarning: '#f59e0b',
    accentError: '#fb7185',
    shadow: '0 8px 32px rgba(0,0,0,0.5)',
    shadowLg: '0 20px 60px rgba(0,0,0,0.6)',
  },
  light: {
    bg: '#f8fafb',
    bgPanel: '#ffffff',
    bgCard: '#f3f7fb',
    bgInput: '#ffffff',
    border: '#dde5f0',
    borderFocus: '#2563eb',
    text: '#0f172a',
    textMuted: '#64748b',
    textDim: '#94a3b8',
    accent: '#2563eb',
    accentSuccess: '#059669',
    accentWarning: '#d97706',
    accentError: '#dc2626',
    shadow: '0 4px 16px rgba(0,0,0,0.06)',
    shadowLg: '0 12px 40px rgba(0,0,0,0.08)',
  },
} satisfies Record<'dark' | 'light', CephaloPalette>;

const cssToken = (name: string, fallback: string) => {
  if (typeof document === 'undefined' || typeof getComputedStyle === 'undefined') return fallback;
  const value = getComputedStyle(document.body).getPropertyValue(name).trim();
  return value || fallback;
};

const fromGlobalTheme = (fallback: CephaloPalette): CephaloPalette => ({
  bg: cssToken('--bg-medical-pearl', fallback.bg),
  bgPanel: cssToken('--card-bg', fallback.bgPanel),
  bgCard: cssToken('--card-bg', fallback.bgCard),
  bgInput: cssToken('--input-bg', fallback.bgInput),
  border: cssToken('--border-color', fallback.border),
  borderFocus: cssToken('--primary', fallback.borderFocus),
  text: cssToken('--text-main', fallback.text),
  textMuted: cssToken('--text-muted', fallback.textMuted),
  textDim: cssToken('--text-muted', fallback.textDim),
  accent: cssToken('--primary', fallback.accent),
  accentSuccess: fallback.accentSuccess,
  accentWarning: fallback.accentWarning,
  accentError: fallback.accentError,
  shadow: cssToken('--shadow-elite', fallback.shadow),
  shadowLg: cssToken('--shadow-elite-hover', fallback.shadowLg),
});

/**
 * Céphalo consumes the application's semantic CSS tokens instead of owning a
 * parallel theme. The light/dark keys remain only for the legacy UIMode API;
 * every read resolves the currently selected Digital Crown theme (emerald,
 * rose, prestige, ocean, graphite, dark, high-contrast, or default).
 */
export const PALETTE = {
  get dark(): CephaloPalette {
    return fromGlobalTheme(FALLBACK.dark);
  },
  get light(): CephaloPalette {
    return fromGlobalTheme(FALLBACK.light);
  },
};
