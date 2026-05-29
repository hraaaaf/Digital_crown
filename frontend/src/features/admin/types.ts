export interface IdentityState { 
  nomCabinet: string; 
  nomPraticien: string; 
  nomPraticienAR: string; 
  adresse: string; 
  ice: string;
  if: string;
  inpe: string;
}

export type HeaderOption = 'auto' | 'letterhead';
export type TemplateOption = 'swiss' | 'royal';
export type ContactType = 'fixe' | 'mobile' | 'whatsapp' | 'instagram';

export interface ContactConfig {
  fixe: { enabled: boolean; value: string };
  mobile: { enabled: boolean; value: string };
  whatsapp: { enabled: boolean; value: string };
  instagram: { enabled: boolean; value: string };
}

export interface WizardStep {
  id: number;
  title: string;
  icon: any;
}
