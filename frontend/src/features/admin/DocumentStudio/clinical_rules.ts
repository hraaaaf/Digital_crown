// frontend/src/features/admin/DocumentStudio/clinical_rules.ts

export interface ClinicalRule {
  molecule: string;
  adult_dose: string;
  adult_posology: string;
  pediatric_calc: (weight: number) => { dosage: string, posology: string };
  contraindications: string[];
}

export const MOROCCAN_CLINICAL_RULES: Record<string, ClinicalRule> = {
  'AMOXICILLINE': {
    molecule: 'AMOXICILLINE',
    adult_dose: '1G',
    adult_posology: '1 comprimé 2 à 3 fois par jour pendant 6 jours',
    pediatric_calc: (weight: number) => {
      // 50 mg/kg/jour en 2 ou 3 prises
      const totalMg = weight * 50;
      if (totalMg <= 500) return { dosage: '250MG', posology: '1 cuillère mesure 2 fois par jour' };
      if (totalMg <= 1000) return { dosage: '500MG', posology: '1 sachet/comprimé 2 fois par jour' };
      return { dosage: '500MG', posology: '1 sachet/comprimé 3 fois par jour' };
    },
    contraindications: ['ALLERGIE PENICILLINE', 'ALLERGIE BETA LACTAMINES']
  },
  'AUGMENTIN': {
    molecule: 'AMOXICILLINE + ACIDE CLAVULANIQUE',
    adult_dose: '1G',
    adult_posology: '1 sachet 2 fois par jour pendant 7 jours',
    pediatric_calc: (weight: number) => {
      // 80 mg/kg/jour en 3 prises (Dose Amoxicilline)
      const totalMg = weight * 80;
      return { dosage: '100MG/ML', posology: `1 dose-poids (${weight}kg) 3 fois par jour` };
    },
    contraindications: ['ALLERGIE PENICILLINE', 'INSUFFISANCE HEPATIQUE']
  },
  'PARACETAMOL': {
    molecule: 'PARACETAMOL',
    adult_dose: '1G',
    adult_posology: '1 comprimé toutes les 6 heures si douleur (max 4g/jour)',
    pediatric_calc: (weight: number) => {
      // 15 mg/kg toutes les 6 heures -> 60 mg/kg/jour
      return { dosage: '2.4%', posology: `1 dose-poids (${weight}kg) toutes les 6 heures si douleur` };
    },
    contraindications: ['INSUFFISANCE HEPATIQUE SEVERE']
  },
  'IBUPROFENE': {
    molecule: 'IBUPROFENE',
    adult_dose: '400MG',
    adult_posology: '1 comprimé toutes les 8 heures si douleur au milieu des repas',
    pediatric_calc: (weight: number) => {
      // 20 à 30 mg/kg/jour en 3 à 4 prises
      return { dosage: '2%', posology: `1 dose-poids (${weight}kg) 3 fois par jour au milieu des repas` };
    },
    contraindications: ['FEMME ENCEINTE', 'ULCERE', 'INFECTION SEVERE SANS ANTIBIOTIQUE', 'ALLERGIE AINS', 'ASTHME']
  },
  'METRONIDAZOLE': {
    molecule: 'METRONIDAZOLE',
    adult_dose: '500MG',
    adult_posology: '1 comprimé 3 fois par jour pendant 7 jours',
    pediatric_calc: (weight: number) => {
      // 30 à 40 mg/kg/jour en 3 prises
      return { dosage: '125MG/5ML', posology: '1 cuillère mesure 3 fois par jour' };
    },
    contraindications: ['ALCOOL', 'FEMME ENCEINTE T1']
  },
  'CORTICOIDES': {
    molecule: 'PREDNISOLONE',
    adult_dose: '20MG',
    adult_posology: '3 comprimés le matin pendant 3 jours (60mg/j)',
    pediatric_calc: (weight: number) => {
      // 1 à 2 mg/kg/jour le matin
      const dose = Math.round(weight * 1); // 1mg/kg
      return { dosage: '20MG', posology: `${Math.max(1, Math.round(dose/20))} comprimé(s) effervescent(s) le matin dans un verre d'eau pendant 3 jours` };
    },
    contraindications: ['INFECTION NON CONTROLEE', 'ULCERE EVOLUTIF']
  }
};

export function getPediatricGuide(moleculeName: string, weight: number) {
  const name = moleculeName.toUpperCase();
  for (const [key, rule] of Object.entries(MOROCCAN_CLINICAL_RULES)) {
    if (name.includes(key) || rule.molecule.includes(name)) {
      return rule.pediatric_calc(weight);
    }
  }
  return null;
}
