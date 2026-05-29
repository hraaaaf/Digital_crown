import type { Preset } from './types';
import { BRAND_IDENTITIES } from '../../../constants';

export const PRESETS: Preset[] = [
  { id:'swiss_minimal', name:'Swiss Clinic (Ligne Claire)', vibe:'Moderne', palette:'noir-elite', font:'inter', template:'swiss', appTheme:'graphite', density:'compact' },
  { id:'royal_prestige', name:'Royal Elite (Classique)', vibe:'Luxe', palette:'elite-royal', font:'playfair', template:'royal', appTheme:'elite', density:'etendu' },
];

export const DENSITY_DEFAULTS = {
  compact: { margin_top: 2.6, margin_bottom: 2.4, header_logo_scale: 0.8,  header_font_scale: 0.9, footer_font_scale: 0.9, header_line_height: 0.95, footer_line_height: 0.95 },
  confort: { margin_top: 3.6, margin_bottom: 3.2, header_logo_scale: 1.0,  header_font_scale: 1.0, footer_font_scale: 1.0, header_line_height: 1.0,  footer_line_height: 1.0  },
  etendu:  { margin_top: 4.4, margin_bottom: 3.8, header_logo_scale: 1.15, header_font_scale: 1.1, footer_font_scale: 1.05, header_line_height: 1.1, footer_line_height: 1.1  },
};

export function presetToProfilePatch(preset: Preset) {
  const pal = BRAND_IDENTITIES.find(p => p.id === preset.palette);
  if (!pal) return {};
  return {
    primary_color: pal.primary,
    secondary_color: pal.secondary,
    accent_color: pal.accent,
    font_fr: preset.font,
    selected_template: preset.template,
    selected_theme: preset.appTheme,
    ...DENSITY_DEFAULTS[preset.density],
  };
}

export function detectPreset(profile: any): Preset | null {
  return PRESETS.find(p => {
    const pal = BRAND_IDENTITIES.find(b => b.id === p.palette);
    const primaryMatch = !pal || pal.primary === profile.primary_color;
    return (
      p.font === profile.font_fr &&
      p.template === profile.selected_template &&
      p.appTheme === profile.selected_theme &&
      primaryMatch
    );
  }) ?? null;
}
