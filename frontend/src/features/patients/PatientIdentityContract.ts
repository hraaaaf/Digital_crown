export type DossierStatus = {
  status: 'idle' | 'checking' | 'available' | 'taken' | 'error';
  owner?: string;
};

export type PatientIdentityFormData = {
  numero_dossier: string;
  nom: string;
  prenom: string;
  date_naissance: string;
  sexe: '' | 'M' | 'F';
  telephone: string;
  telephone_2: string;
  telephone_3: string;
  email: string;
  adresse: string;
  assurance: string;
  assurance_privee_nom: string;
  assurance_complementaire: boolean;
  assurance_complementaire_nom: string;
  antecedents_medicaux: string;
  motif_consultation: string[];
};

export type PatientIdentityErrors = Record<string, string>;

const EMPTY_IDENTITY: PatientIdentityFormData = {
  numero_dossier: '',
  nom: '',
  prenom: '',
  date_naissance: '',
  sexe: '',
  telephone: '',
  telephone_2: '',
  telephone_3: '',
  email: '',
  adresse: '',
  assurance: 'AUCUNE',
  assurance_privee_nom: '',
  assurance_complementaire: false,
  assurance_complementaire_nom: '',
  antecedents_medicaux: '',
  motif_consultation: [],
};

export const createPatientIdentityFormData = (
  overrides: Partial<PatientIdentityFormData> = {},
): PatientIdentityFormData => ({ ...EMPTY_IDENTITY, ...overrides });

const parseMotifConsultation = (value: unknown): string[] => {
  if (Array.isArray(value)) return value.filter((item): item is string => typeof item === 'string');
  if (typeof value !== 'string' || !value.trim()) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed)
      ? parsed.filter((item): item is string => typeof item === 'string')
      : [value];
  } catch {
    return [value];
  }
};

const toDateInputValue = (value: unknown): string => {
  if (!value) return '';
  const date = new Date(String(value));
  return Number.isNaN(date.getTime()) ? '' : date.toISOString().split('T')[0];
};

export const patientIdentityFromApi = (patient: Record<string, any>): PatientIdentityFormData =>
  createPatientIdentityFormData({
    numero_dossier: patient.numero_dossier || '',
    nom: patient.nom || '',
    prenom: patient.prenom || '',
    date_naissance: toDateInputValue(patient.date_naissance),
    sexe: patient.sexe === 'M' || patient.sexe === 'F' ? patient.sexe : '',
    telephone: patient.telephone || '',
    telephone_2: patient.telephone_2 || '',
    telephone_3: patient.telephone_3 || '',
    email: patient.email || '',
    adresse: patient.adresse || '',
    assurance: patient.assurance || 'AUCUNE',
    assurance_privee_nom: patient.assurance_privee_nom || '',
    assurance_complementaire: Boolean(patient.assurance_complementaire),
    assurance_complementaire_nom: patient.assurance_complementaire_nom || '',
    antecedents_medicaux: patient.antecedents_medicaux || '',
    motif_consultation: parseMotifConsultation(patient.motif_consultation),
  });

export const validatePatientIdentity = (
  data: PatientIdentityFormData,
  now: Date = new Date(),
): PatientIdentityErrors => {
  const errors: PatientIdentityErrors = {};
  if (!data.nom.trim()) errors.nom = 'Le nom est requis.';
  if (!data.prenom.trim()) errors.prenom = 'Le prénom est requis.';

  if (!data.date_naissance) {
    errors.date_naissance = 'La date de naissance est obligatoire.';
  } else {
    const birthDate = new Date(data.date_naissance);
    const minDate = new Date('1900-01-01T00:00:00');
    if (Number.isNaN(birthDate.getTime()) || birthDate < minDate || birthDate > now) {
      errors.date_naissance = "Date invalide (doit être entre 1900 et aujourd'hui).";
    }
  }

  if (data.sexe !== 'M' && data.sexe !== 'F') {
    errors.sexe = 'Le sexe doit être renseigné explicitement.';
  }
  if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    errors.email = "Format d'email invalide.";
  }
  return errors;
};

export const patientIdentityToApiPayload = (data: PatientIdentityFormData) => ({
  ...data,
  numero_dossier: data.numero_dossier || null,
  email: data.email || null,
  adresse: data.adresse || null,
  telephone: data.telephone || null,
  telephone_2: data.telephone_2 || null,
  telephone_3: data.telephone_3 || null,
  assurance_privee_nom: data.assurance_privee_nom || null,
  assurance_complementaire_nom: data.assurance_complementaire_nom || null,
  antecedents_medicaux: data.antecedents_medicaux || null,
  motif_consultation: data.motif_consultation.length > 0
    ? JSON.stringify(data.motif_consultation)
    : null,
});
