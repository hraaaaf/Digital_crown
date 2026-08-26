const PHONE_ALLOWED_RE = /^[+0-9\s().-]+$/;
const PHONE_VISUAL_SEPARATORS_RE = /[\s().-]/g;

function compactPhone(raw?: string | null): string | null {
  const value = raw?.trim();
  if (!value || !PHONE_ALLOWED_RE.test(value)) return null;
  const compact = value.replace(PHONE_VISUAL_SEPARATORS_RE, '');
  return compact || null;
}

function internationalDigits(compact: string): string | null {
  const digits = compact.startsWith('+')
    ? compact.slice(1)
    : compact.startsWith('00')
      ? compact.slice(2)
      : null;
  return digits && /^[1-9]\d+$/.test(digits) ? digits : null;
}

export function buildTelHref(raw?: string | null): string | null {
  const compact = compactPhone(raw);
  if (!compact) return null;
  const globalDigits = internationalDigits(compact);
  if (globalDigits) return `tel:+${globalDigits}`;
  if (compact.startsWith('+') || compact.startsWith('00')) return null;
  if (/^\d+$/.test(compact)) return `tel:${compact}`;
  return null;
}

export function buildWhatsAppHref(raw?: string | null): string | null {
  const compact = compactPhone(raw);
  if (!compact) return null;
  const globalDigits = internationalDigits(compact);
  return globalDigits ? `https://wa.me/${globalDigits}` : null;
}
