import type { User } from '@supabase/supabase-js';

/**
 * Supabase User étendu avec les champs métier injectés par le backend `/auth/me`.
 * Toutes les propriétés métier sont optionnelles car getFullProfile() peut
 * retourner uniquement le User Supabase brut en cas d'échec de la sync backend.
 */
export interface AppUser extends User {
  role?: string;
  is_licensed?: boolean;
  license_expires_at?: string | null;
  full_name?: string;
  cabinet_name?: string;
}

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