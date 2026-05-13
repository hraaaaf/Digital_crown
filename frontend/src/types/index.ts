export interface Patient {
  id: number;
  numero_dossier: string;
  nom: string;
  prenom: string;
  date_naissance: string;
  telephone: string;
  email?: string;
  adresse?: string;
  profession?: string;
  sexe?: 'M' | 'F';
  ville?: string;
  assurance: 'CNOPS' | 'CNSS' | 'MUTUELLE_FAR' | 'AUTRE' | 'AUCUNE';
  created_at: string;
  updated_at: string;
  
  // NOUVEAU : Score de fiabilité (calculé ou forcé)
  manual_grade?: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE' | null;
  grade_comment?: string | null;
}

export interface Document {
  id: number;
  patient_id: number;
  type: string;
  content: any;
  created_at: string;
  updated_at: string;
}

export interface AccountingRecord {
  id: number;
  patient_id: number;
  type: 'DEVIS' | 'NOTE_HONORAIRES';
  montant: number;
  status: 'PAID' | 'UNPAID' | 'PARTIAL';
  created_at: string;
}