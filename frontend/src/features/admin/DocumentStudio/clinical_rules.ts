// frontend/src/features/admin/DocumentStudio/clinical_rules.ts
//
// Référentiel clinique CURÉ (doses pédiatriques + contre-indications).
// ⚠️ Doses de RÉFÉRENCE standard à valider par le praticien selon le cas clinique.
// Couche distincte du dictionnaire national (existence/dosages, ~4200 médicaments)
// qui, lui, ne contient ni posologie pédiatrique ni contre-indications.

export type DrugCategory =
  | 'Antalgiques'
  | 'AINS'
  | 'Antibiotiques'
  | 'Corticoïdes'
  | 'Antiseptiques'
  | 'Antifongiques';

export interface ClinicalRule {
  molecule: string;
  category: DrugCategory;
  adult_dose: string;
  adult_posology: string;
  pediatric_calc: (weight: number) => { dosage: string, posology: string };
  contraindications: string[];
  /** Dosages oraux solides disponibles au Maroc (mg). Sert au contrôle d'existence. */
  available_strengths_mg?: number[];
  /** mg/kg/jour max indicatif (sécurité pédiatrique). */
  max_mg_per_kg_day?: number;
  /** Remarque de sécurité clé affichée dans le guide. */
  notes?: string;
}

export const MOROCCAN_CLINICAL_RULES: Record<string, ClinicalRule> = {
  'AMOXICILLINE': {
    molecule: 'AMOXICILLINE',
    category: 'Antibiotiques',
    adult_dose: '1G',
    adult_posology: '1 comprimé 2 à 3 fois par jour pendant 6 jours',
    pediatric_calc: (weight: number) => {
      // 50 mg/kg/jour en 2 ou 3 prises
      const totalMg = weight * 50;
      if (totalMg <= 500) return { dosage: '250MG', posology: '1 cuillère mesure 2 fois par jour' };
      if (totalMg <= 1000) return { dosage: '500MG', posology: '1 sachet/comprimé 2 fois par jour' };
      return { dosage: '500MG', posology: '1 sachet/comprimé 3 fois par jour' };
    },
    contraindications: ['ALLERGIE PENICILLINE', 'ALLERGIE BETA LACTAMINES'],
    available_strengths_mg: [250, 500, 1000],
    max_mg_per_kg_day: 50,
  },
  'AUGMENTIN': {
    molecule: 'AMOXICILLINE + ACIDE CLAVULANIQUE',
    category: 'Antibiotiques',
    adult_dose: '1G',
    adult_posology: '1 sachet 2 fois par jour pendant 7 jours',
    pediatric_calc: (weight: number) => {
      // 80 mg/kg/jour en 3 prises (Dose Amoxicilline)
      return { dosage: '100MG/ML', posology: `1 dose-poids (${weight}kg) 3 fois par jour` };
    },
    contraindications: ['ALLERGIE PENICILLINE', 'INSUFFISANCE HEPATIQUE'],
    available_strengths_mg: [500, 1000],
    max_mg_per_kg_day: 80,
  },
  'PARACETAMOL': {
    molecule: 'PARACETAMOL',
    category: 'Antalgiques',
    adult_dose: '1G',
    adult_posology: '1 comprimé toutes les 6 heures si douleur (max 4g/jour)',
    pediatric_calc: (weight: number) => {
      // 15 mg/kg toutes les 6 heures -> 60 mg/kg/jour
      return { dosage: '2.4%', posology: `1 dose-poids (${weight}kg) toutes les 6 heures si douleur` };
    },
    contraindications: ['INSUFFISANCE HEPATIQUE SEVERE'],
    available_strengths_mg: [100, 150, 200, 300, 500, 1000],
    max_mg_per_kg_day: 60,
  },
  'IBUPROFENE': {
    molecule: 'IBUPROFENE',
    category: 'AINS',
    adult_dose: '400MG',
    adult_posology: '1 comprimé toutes les 8 heures si douleur au milieu des repas',
    pediatric_calc: (weight: number) => {
      // 20 à 30 mg/kg/jour en 3 à 4 prises
      return { dosage: '2%', posology: `1 dose-poids (${weight}kg) 3 fois par jour au milieu des repas` };
    },
    contraindications: ['FEMME ENCEINTE', 'ULCERE', 'INFECTION SEVERE SANS ANTIBIOTIQUE', 'ALLERGIE AINS', 'ASTHME'],
    available_strengths_mg: [200, 400],
    max_mg_per_kg_day: 30,
  },
  'METRONIDAZOLE': {
    molecule: 'METRONIDAZOLE',
    category: 'Antibiotiques',
    adult_dose: '500MG',
    adult_posology: '1 comprimé 3 fois par jour pendant 7 jours',
    pediatric_calc: (weight: number) => {
      // 30 à 40 mg/kg/jour en 3 prises
      return { dosage: '125MG/5ML', posology: '1 cuillère mesure 3 fois par jour' };
    },
    contraindications: ['ALCOOL', 'FEMME ENCEINTE T1'],
    available_strengths_mg: [250, 500],
    max_mg_per_kg_day: 40,
  },
  'CORTICOIDES': {
    molecule: 'PREDNISOLONE',
    category: 'Corticoïdes',
    adult_dose: '20MG',
    adult_posology: '3 comprimés le matin pendant 3 jours (60mg/j)',
    pediatric_calc: (weight: number) => {
      // 1 à 2 mg/kg/jour le matin
      const dose = Math.round(weight * 1); // 1mg/kg
      return { dosage: '20MG', posology: `${Math.max(1, Math.round(dose/20))} comprimé(s) effervescent(s) le matin dans un verre d'eau pendant 3 jours` };
    },
    contraindications: ['INFECTION NON CONTROLEE', 'ULCERE EVOLUTIF'],
    available_strengths_mg: [5, 20],
    max_mg_per_kg_day: 2,
  },

  // ── Ajouts arsenal dentaire (juin 2026) ─────────────────────────────────────
  'RODOGYL': {
    molecule: 'SPIRAMYCINE + MÉTRONIDAZOLE',
    category: 'Antibiotiques',
    adult_dose: '-',
    adult_posology: '2 comprimés matin et soir pendant 6 à 10 jours',
    pediatric_calc: () => ({ dosage: '-', posology: 'Enfant > 6 ans : 1 cp 2 à 3 fois/jour selon le poids' }),
    contraindications: ['ALLERGIE MACROLIDES', 'ENFANT MOINS DE 6 ANS', 'GROSSESSE T1'],
    notes: 'Forme comprimé non adaptée avant 6 ans. Éviter l\'alcool (métronidazole).',
  },
  'CLINDAMYCINE': {
    molecule: 'CLINDAMYCINE',
    category: 'Antibiotiques',
    adult_dose: '300MG',
    adult_posology: '1 gélule (300 mg) 3 fois par jour pendant 7 jours',
    pediatric_calc: (weight: number) => {
      // 8 à 25 mg/kg/jour en 3 prises (cible ~15 mg/kg/j)
      const perDose = Math.max(75, Math.round((weight * 15) / 3));
      return { dosage: '75MG/5ML', posology: `~${perDose} mg 3 fois par jour (8 à 25 mg/kg/jour)` };
    },
    contraindications: ['ALLERGIE CLINDAMYCINE', 'ALLERGIE LINCOMYCINE', 'COLITE'],
    available_strengths_mg: [75, 150, 300],
    max_mg_per_kg_day: 25,
    notes: 'Alternative de choix en cas d\'allergie à la pénicilline.',
  },
  'AZITHROMYCINE': {
    molecule: 'AZITHROMYCINE',
    category: 'Antibiotiques',
    adult_dose: '500MG',
    adult_posology: '500 mg (1 cp) par jour pendant 3 jours',
    pediatric_calc: (weight: number) => {
      // 10 mg/kg/jour pendant 3 jours
      const perDay = Math.round(weight * 10);
      return { dosage: '200MG/5ML', posology: `~${perDay} mg/jour (10 mg/kg) pendant 3 jours` };
    },
    contraindications: ['ALLERGIE MACROLIDES', 'QT LONG', 'INSUFFISANCE HEPATIQUE SEVERE'],
    available_strengths_mg: [250, 500],
    max_mg_per_kg_day: 20,
  },
  'CHLORHEXIDINE': {
    molecule: 'CHLORHEXIDINE (bain de bouche)',
    category: 'Antiseptiques',
    adult_dose: '0.12%',
    adult_posology: '2 à 3 bains de bouche par jour pendant 7 jours (ne pas avaler)',
    pediatric_calc: () => ({ dosage: '0.12%', posology: 'Enfant > 6 ans : 1 bain de bouche dilué 2 fois/jour, sous surveillance' }),
    contraindications: ['ENFANT MOINS DE 6 ANS', 'ALLERGIE CHLORHEXIDINE'],
    notes: 'Ne pas avaler. Coloration dentaire réversible si usage prolongé.',
  },
  'MICONAZOLE': {
    molecule: 'MICONAZOLE (gel buccal)',
    category: 'Antifongiques',
    adult_dose: '2%',
    adult_posology: '2 cuillères-mesure 4 fois par jour, à garder en bouche après les repas',
    pediatric_calc: () => ({ dosage: '2%', posology: 'Enfant : 1.25 à 2.5 ml (¼ à ½ c-mesure) 4 fois/jour' }),
    contraindications: ['ALLERGIE IMIDAZOLES', 'ANTICOAGULANTS AVK', 'NOURRISSON MOINS DE 6 MOIS'],
    notes: 'Risque de fausse route chez le nourrisson. Interaction majeure avec les AVK.',
  },
  'CODEINE': {
    molecule: 'CODÉINE (antalgique palier 2)',
    category: 'Antalgiques',
    adult_dose: '-',
    adult_posology: 'Adulte : selon association (ex. paracétamol + codéine), max 6 prises/jour',
    pediatric_calc: () => ({ dosage: '-', posology: '⚠️ CONTRE-INDIQUÉ chez l\'enfant de moins de 12 ans' }),
    contraindications: ['ENFANT MOINS DE 12 ANS', 'INSUFFISANCE RESPIRATOIRE', 'ALLAITEMENT'],
    notes: '⚠️ Codéine interdite avant 12 ans (métaboliseurs rapides). Préférer paracétamol/ibuprofène.',
  },
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

// Marques commerciales fréquentes au Maroc → clé de règle clinique.
// Volontairement conservateur : on ne mappe que les correspondances sûres.
export const BRAND_TO_RULE: Record<string, string> = {
  DOLIPRANE: 'PARACETAMOL',
  EFFERALGAN: 'PARACETAMOL',
  DAFALGAN: 'PARACETAMOL',
  PARACETAMOL: 'PARACETAMOL',
  CLAMOXYL: 'AMOXICILLINE',
  AMOXICILLINE: 'AMOXICILLINE',
  AUGMENTIN: 'AUGMENTIN',
  FLAGYL: 'METRONIDAZOLE',
  METRONIDAZOLE: 'METRONIDAZOLE',
  BRUFEN: 'IBUPROFENE',
  IBUPROFENE: 'IBUPROFENE',
  SOLUPRED: 'CORTICOIDES',
  PREDNISOLONE: 'CORTICOIDES',
  // Ajouts arsenal dentaire
  RODOGYL: 'RODOGYL',
  BIRODOGYL: 'RODOGYL',
  SPIRAMYCINE: 'RODOGYL',
  DALACINE: 'CLINDAMYCINE',
  CLINDAMYCINE: 'CLINDAMYCINE',
  ZITHROMAX: 'AZITHROMYCINE',
  AZITHROMYCINE: 'AZITHROMYCINE',
  ELUDRIL: 'CHLORHEXIDINE',
  HEXTRIL: 'CHLORHEXIDINE',
  PAROEX: 'CHLORHEXIDINE',
  CHLORHEXIDINE: 'CHLORHEXIDINE',
  DAKTARIN: 'MICONAZOLE',
  MICONAZOLE: 'MICONAZOLE',
  CODOLIPRANE: 'CODEINE',
  CODEINE: 'CODEINE',
};

/** Résout la règle clinique d'un nom de médicament (molécule OU marque). */
export function resolveRule(name: string): ClinicalRule | null {
  const upper = (name || '').toUpperCase().trim();
  if (!upper) return null;
  let key = Object.keys(MOROCCAN_CLINICAL_RULES).find(k => upper.includes(k));
  if (!key) {
    const brand = Object.keys(BRAND_TO_RULE).find(b => upper.includes(b));
    if (brand) key = BRAND_TO_RULE[brand];
  }
  return key ? MOROCCAN_CLINICAL_RULES[key] : null;
}

/**
 * Estimation usuelle du poids pédiatrique à partir de l'âge (faute de poids saisi).
 * 1-10 ans : poids ≈ (âge × 2) + 8. Au-delà : approximation plafonnée.
 */
export function estimateWeightFromAge(age: number): number {
  if (age <= 0) return 3.5;
  if (age <= 10) return age * 2 + 8;
  return Math.min(age * 3, 60);
}

export type ValidationLevel = 'ok' | 'info' | 'warn' | 'danger' | 'unknown';

export interface DrugValidation {
  level: ValidationLevel;
  molecule: string | null;
  messages: string[];
}

/** Extrait une quantité en mg depuis un texte de dosage ("350 MG", "1G", "500mg"). */
export function parseDosageToMg(dosage: string): number | null {
  if (!dosage) return null;
  const m = dosage.toUpperCase().replace(/\s/g, '').match(/(\d+(?:[.,]\d+)?)(MG|G)\b/);
  if (!m) return null;
  const val = parseFloat(m[1].replace(',', '.'));
  return m[2] === 'G' ? val * 1000 : val;
}

/**
 * Validation Ghost Brain d'une ligne de prescription (référentiel curé) :
 *  - adéquation à l'âge de l'enfant (dose adulte chez un petit, dépassement mg/kg)
 *  - contre-indications selon les antécédents
 * L'EXISTENCE du dosage est vérifiée séparément par le dictionnaire national.
 * Retourne level 'unknown' si le médicament est hors référentiel curé.
 */
export function validatePrescriptionLine(
  name: string,
  dosage: string,
  age: number | null | undefined,
  antecedents?: string | null,
): DrugValidation {
  const rule = resolveRule(name);
  if (!rule) return { level: 'unknown', molecule: null, messages: [] };

  const messages: string[] = [];
  let level: ValidationLevel = 'ok';
  const bump = (l: ValidationLevel) => {
    const order: ValidationLevel[] = ['ok', 'info', 'warn', 'danger'];
    if (order.indexOf(l) > order.indexOf(level)) level = l;
  };

  const mg = parseDosageToMg(dosage);

  // 1. Adéquation à l'âge de l'enfant
  const isChild = typeof age === 'number' && age > 0 && age < 15;
  if (isChild && mg !== null) {
    const weight = estimateWeightFromAge(age as number);
    if (rule.max_mg_per_kg_day) {
      // Hypothèse prudente : 3 prises/jour pour estimer la dose journalière.
      const estDailyMg = mg * 3;
      const maxDailyMg = rule.max_mg_per_kg_day * weight;
      if (estDailyMg > maxDailyMg) {
        bump('danger');
        messages.push(
          `Dosage probablement trop élevé pour un enfant de ${age} ans (~${weight} kg) : ` +
          `max ≈ ${Math.round(maxDailyMg)} mg/j pour ${rule.molecule}.`
        );
      }
    }
    const adultMg = parseDosageToMg(rule.adult_dose);
    if (adultMg !== null && mg >= adultMg && level !== 'danger') {
      bump('warn');
      messages.push(`Dose adulte (${rule.adult_dose}) chez un enfant — adapter au poids.`);
    }
  }

  // 2. Contre-indications selon les antécédents
  const hist = (antecedents || '').toUpperCase();
  if (hist.trim()) {
    for (const ci of rule.contraindications) {
      const tokens = ci.split(/\s+/).filter(t => t.length > 3);
      const hit = tokens.length > 0 && tokens.every(t => hist.includes(t));
      if (hit) {
        bump('danger');
        messages.push(`Contre-indication possible : ${ci.toLowerCase()} (antécédents).`);
      }
    }
  }

  return { level, molecule: rule.molecule, messages };
}

/**
 * Retourne dosage + posologie ADAPTÉS À L'ÂGE pour un médicament connu.
 * - adulte (≥ 15 ans) : dose/posologie adulte de référence
 * - enfant (< 15 ans) : calcul pédiatrique (poids saisi, sinon estimé via l'âge)
 * Retourne null si le médicament n'est pas dans le référentiel.
 */
export function getAgeAwareDosing(
  name: string,
  age: number | null | undefined,
  weight?: number | null,
): { dosage: string; posology: string; pediatric: boolean; weight?: number } | null {
  const rule = resolveRule(name);
  if (!rule) return null;
  const isChild = typeof age === 'number' && age > 0 && age < 15;
  if (!isChild) {
    return { dosage: rule.adult_dose, posology: rule.adult_posology, pediatric: false };
  }
  const w = weight && weight > 0 ? weight : estimateWeightFromAge(age as number);
  const ped = rule.pediatric_calc(w);
  return { dosage: ped.dosage, posology: ped.posology, pediatric: true, weight: w };
}
