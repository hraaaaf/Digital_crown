// Le mot 'export' est OBLIGATOIRE pour que les autres fichiers puissent l'utiliser
export type AssuranceType = 'CNOPS' | 'CNSS' | 'MUTUELLE_FAR' | 'PRIVEE' | 'AUCUNE';

export interface Patient {
  id?: number;
  numero_dossier?: string;
  nom: string;
  prenom: string;
  date_naissance: string;
  sexe: 'M' | 'F';
  telephone: string;
  email?: string;
  adresse?: string;
  assurance?: AssuranceType;
  antecedents_medicaux?: string;
}