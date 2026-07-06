// ==============================================================================
// TYPES MULTI-TENANT (Phase SaaS)
// ==============================================================================

export type DocumentType = 'ordonnance' | 'certificat' | 'devis' | 'note_honoraires' | 'libre' | 'bilan';
export type StyleKey = 'classique' | 'moderne' | 'minimaliste' | 'medical' | 'premium' | 'saninova';
export type PageSize = 'A4' | 'A5';

// --- Design Config ---

export interface FontConfig {
  fr: string;
  ar: string;
  fallback: string;
}

export interface ColorConfig {
  primary: string;
  secondary: string;
  background: string;
  accent: string;
}

export interface MarginConfig {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export interface LayoutConfig {
  page_size: PageSize;
  margins: MarginConfig;
  header_height: number;
  footer_height: number;
}

export interface WatermarkConfig {
  enabled: boolean;
  size_cm: number;
  opacity: number;
  position: 'center' | 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

export interface HeaderConfig {
  bilingual: boolean;
  logo_in_header: boolean;
  logo_header_size_cm: number;
  show_lines: boolean;
}

export interface BorderConfig {
  header_line: boolean;
  header_line_style: 'single' | 'double' | 'none';
  header_line_color: string;
  content_border: boolean;
  content_border_radius: number;
}

export interface TypographyConfig {
  title_size: number;
  title_bold: boolean;
  title_underline: boolean;
  title_align: 'left' | 'center' | 'right';
  body_size: number;
  body_line_height: number;
}

export interface SpacingConfig {
  paragraph_gap_cm: number;
  section_gap_cm: number;
}

export interface DesignConfig {
  fonts: FontConfig;
  colors: ColorConfig;
  layout: LayoutConfig;
  watermark: WatermarkConfig;
  header: HeaderConfig;
  borders: BorderConfig;
  typography: TypographyConfig;
  spacing: SpacingConfig;
}

// --- Cabinet Config ---

export interface CabinetConfig {
  id: string;
  public_id: string;
  owner_id: number;
  nom_cabinet: string;
  logo_url?: string;
  header_lines_fr: string[];
  header_lines_ar: string[];
  footer_address: string;
  footer_phones: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_fr: string;
  font_ar: string;
  watermark_enabled: boolean;
  watermark_opacity: number;
  selected_theme: string;
  is_initialized: boolean;
  created_at: string;
  updated_at: string;
}

export interface CabinetConfigCreate {
  nom_cabinet: string;
  nom_praticien?: string;
  nom_praticien_ar?: string;
  header_lines_fr: string[];
  header_lines_ar: string[];
  footer_address: string;
  footer_phones: string;
  ice?: string;
  if_?: string;
  inpe?: string;
  cabinet_type?: 'PRIVE' | 'CLINIQUE';
  specialty_ids?: string[];
  custom_specialty_fr?: string;
  custom_specialty_ar?: string;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  font_fr?: string;
  font_ar?: string;
  watermark_enabled?: boolean;
  watermark_opacity?: number;
  selected_theme?: string;
  selected_template?: string;
  margin_top?: number;
  margin_bottom?: number;
  header_scale?: number;
  header_font_scale?: number;
  header_logo_scale?: number;
  header_line_height?: number;
  footer_font_scale?: number;
  footer_qr_scale?: number;
  footer_line_height?: number;
  contacts_json?: Record<string, { enabled: boolean; value: string }>;
  qr_code_enabled?: boolean;
  qr_code_type?: string;
  qr_code_value?: string;
  qr_code_color?: string;
  qr_code_label?: string;
  qr_code_style?: string;
  use_letterhead?: boolean;
  hide_header?: boolean;
  hide_footer?: boolean;
}

export interface CabinetInitStatus {
  is_initialized: boolean;
  needs_setup: boolean;
}

// --- Document Templates ---

export interface DocumentTemplate {
  id: string;
  type: DocumentType;
  style_key: StyleKey;
  name: string;
  description?: string;
  user_id?: number;
  is_system: boolean;
  is_default: boolean;
  design_config: DesignConfig;
  body_html?: string; // Uniquement pour templates perso
  created_at: string;
  updated_at: string;
}

export interface DocumentTemplateList {
  id: string;
  type: DocumentType;
  style_key: StyleKey;
  name: string;
  is_default: boolean;
  description?: string;
}

export interface DocumentTemplateCreate {
  type: DocumentType;
  style_key: StyleKey;
  name: string;
  description?: string;
  body_html: string;
  design_config: DesignConfig;
  is_system?: boolean;
  is_default?: boolean;
}

export interface DocumentTemplateUpdate {
  name?: string;
  design_config?: DesignConfig;
  is_default?: boolean;
}

// --- Preview ---

export interface TemplatePreviewRequest {
  template_id: string;
  sample_data?: {
    patient?: { nom: string; prenom: string; age: number };
    date?: string;
    titre?: string;
  };
}
export interface LetterheadUploadResponse {
  letterhead_url: string;
  use_letterhead?: boolean;
  hide_default_header: boolean;
  hide_default_footer: boolean;
  detected_colors?: {
    primary_color: string;
    secondary_color: string;
    accent_color: string;
  } | null;
  message: string;
}

export interface CardExtractionResult {
  nom_cabinet: string | null;
  nom_praticien: string | null;
  nom_praticien_ar: string | null;
  adresse: string | null;
  specialites: string[] | null;
  telephone_fixe: string | null;
  telephone_mobile: string | null;
  email: string | null;
  error?: string;
}
