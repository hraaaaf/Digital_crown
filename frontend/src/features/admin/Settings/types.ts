export interface ContactInfo {
  enabled: boolean;
  value: string;
}

export interface ContactsJson {
  fixe: ContactInfo;
  mobile: ContactInfo;
  whatsapp: ContactInfo;
  instagram: ContactInfo;
  [key: string]: ContactInfo;
}

export interface CabinetProfile {
  nom: string;
  adresse: string;
  telephone: string;
  inpe: string;
  nom_cabinet?: string;
  letterhead_path?: string;
  use_letterhead?: boolean;
  margin_top?: number;
  margin_bottom?: number;
  header_scale?: number;
  watermark_enabled?: boolean;
  ice?: string;
  if?: string;
  contacts_json?: ContactsJson;
  selected_theme?: string;
  app_accent_color?: string;
  font_fr?: string;
  selected_template?: string;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  qr_code_enabled?: boolean;
  qr_code_type?: 'VCARD' | 'WEBSITE' | 'INSTAGRAM' | 'WHATSAPP' | 'LOCATION' | 'VALIDATION' | 'PAYMENT';
  qr_code_value?: string;
  qr_code_color?: string;
  qr_code_label?: string;
  show_patient_badges?: boolean;
  performance_mode?: boolean;
  clinical_tips_enabled?: boolean;
  hide_header?: boolean;
  hide_footer?: boolean;
  cabinet_type?: 'PRIVE' | 'CLINIQUE';
  nom_praticien_ar?: string;
  specialty_ids?: string[];
  custom_specialty_fr?: string;
  custom_specialty_ar?: string;
  logo_path?: string;
  header_lines_fr?: string[];
  header_lines_ar?: string[];
  header_customized?: boolean;
  qr_code_style?: string;
  qr_code_offset_x?: number;
  qr_code_offset_y?: number;
  header_font_scale?: number;
  header_logo_scale?: number;
  header_logo_offset_x?: number;
  header_logo_offset_y?: number;
  header_line_height?: number;
  footer_font_scale?: number;
  footer_qr_scale?: number;
  footer_line_height?: number;
}

export type Tab = 'profil' | 'branding' | 'ia' | 'securite' | 'equipe' | 'catalogue' | 'agenda';
