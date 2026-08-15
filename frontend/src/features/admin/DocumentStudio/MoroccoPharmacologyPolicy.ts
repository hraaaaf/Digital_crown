// Morocco-first pharmacology governance for Digital Crown.
//
// This module does not prescribe. It decides whether a medication rule may be
// auto-proposed for the Moroccan market, must stay advisory, or must fail closed.

export type MoroccoEvidenceTier =
  | 'MOROCCO_OFFICIAL'
  | 'MOROCCO_PROFESSIONAL'
  | 'INTERNATIONAL_SUPPORT';

export type MoroccoMarketStatus =
  | 'morocco_verified'
  | 'morocco_guideline_gap'
  | 'morocco_amm_unverified'
  | 'morocco_conflict'
  | 'manual_review_required';

export interface MoroccoEvidenceRef {
  id: string;
  tier: MoroccoEvidenceTier;
  authority: string;
  title: string;
  url: string;
  reviewedAt: string;
  scope: 'AMM' | 'PHARMACOVIGILANCE' | 'STEWARDSHIP' | 'DOSING' | 'DENTAL_GUIDANCE' | 'FORMULARY';
  note?: string;
}

export interface MoroccoMedicationEvidence {
  molecule: string;
  ammVerified: boolean;
  ammEvidenceId?: string;
  moroccoRegimenEvidenceIds: string[];
  internationalSupportEvidenceIds: string[];
  conflict?: string | null;
}

export interface MoroccoPolicyDecision {
  status: MoroccoMarketStatus;
  mayAutoProposeRegimen: boolean;
  messages: string[];
  evidenceIds: string[];
}

export const MOROCCO_PHARMACOLOGY_EVIDENCE: Record<string, MoroccoEvidenceRef> = {
  MOROCCO_AMMPS_MEDICINES: {
    id: 'MOROCCO_AMMPS_MEDICINES',
    tier: 'MOROCCO_OFFICIAL',
    authority: 'Agence Marocaine du Médicament et des Produits de Santé (AMMPS)',
    title: 'Base de données des médicaments — Maroc',
    url: 'https://www.ammps.gov.ma/recherche-medicaments',
    reviewedAt: '2026-08-15',
    scope: 'AMM',
    note: 'Référentiel officiel courant. Vérifier par présentation la substance active, le dosage, la forme, le RCP et le statut de commercialisation. La présence dans la base ne signifie pas nécessairement « commercialisé ».',
  },
  MOROCCO_AMMPS_GENERICS_2026: {
    id: 'MOROCCO_AMMPS_GENERICS_2026',
    tier: 'MOROCCO_OFFICIAL',
    authority: 'Agence Marocaine du Médicament et des Produits de Santé (AMMPS)',
    title: 'Répertoire Marocain des Médicaments Génériques — édition projet janvier 2026',
    url: 'https://www.ammps.gov.ma/repertoire-medicaments-generiques',
    reviewedAt: '2026-08-15',
    scope: 'FORMULARY',
    note: 'Répertoire pilote des génériques autorisés. Complément de gouvernance, pas substitut au RCP ni au statut de commercialisation par présentation.',
  },
  MOROCCO_ANTIBIOTIC_STEWARDSHIP: {
    id: 'MOROCCO_ANTIBIOTIC_STEWARDSHIP',
    tier: 'MOROCCO_OFFICIAL',
    authority: 'Autorités sanitaires marocaines',
    title: 'Bon usage des antibiotiques / antibiorésistance',
    url: 'https://www.sante.gov.ma/Pages/Communiques.aspx?IDCom=307',
    reviewedAt: '2026-08-15',
    scope: 'STEWARDSHIP',
    note: 'Support de bon usage. Une recommandation dentaire de schéma doit rester sourcée séparément.',
  },
  MOROCCO_PARACETAMOL: {
    id: 'MOROCCO_PARACETAMOL',
    tier: 'MOROCCO_OFFICIAL',
    authority: 'Sehati / Ministère de la Santé – Maroc',
    title: 'Recommandations pour le bon usage du paracétamol',
    url: 'https://sehati.gov.ma/article/recommandations_pour_le_bon_usage_du_paracetamol',
    reviewedAt: '2026-08-15',
    scope: 'DOSING',
    note: 'Bon usage marocain. Le dosage exact d’une présentation reste à vérifier dans son RCP/AMM.',
  },
  MOROCCO_PRACTITIONER_ANTIBIOTICS_2020: {
    id: 'MOROCCO_PRACTITIONER_ANTIBIOTICS_2020',
    tier: 'MOROCCO_PROFESSIONAL',
    authority: 'Pr Lahcen Belyamani & Dr Said Jidane / référence académique marocaine',
    title: 'Antibiotiques — Antibio-choix du praticien marocain',
    url: 'https://biblio.um6ss.ma/antibiotiques-antibio-choix-du-praticien-marocain/',
    reviewedAt: '2026-08-15',
    scope: 'FORMULARY',
    note: 'Référence professionnelle marocaine, autorité inférieure à une recommandation officielle actuelle ou au RCP.',
  },
};

/**
 * Morocco-first gate.
 *
 * Automatic regimen proposal requires BOTH:
 * 1. Moroccan AMM/market verification for the actual molecule/presentation, and
 * 2. Moroccan regimen-level evidence.
 *
 * A local dictionary match is identity assistance only and never proves current
 * AMM/commercialisation. If Morocco has no current dental regimen guidance for a
 * molecule, an international guideline may be displayed as SUPPORT ONLY, never
 * silently promoted to a Moroccan recommendation.
 */
export function arbitrateForMorocco(
  evidence: MoroccoMedicationEvidence,
): MoroccoPolicyDecision {
  if (evidence.conflict) {
    return {
      status: 'morocco_conflict',
      mayAutoProposeRegimen: false,
      messages: [`Conflit de références pour ${evidence.molecule}: ${evidence.conflict}`],
      evidenceIds: [
        ...(evidence.ammEvidenceId ? [evidence.ammEvidenceId] : []),
        ...evidence.moroccoRegimenEvidenceIds,
        ...evidence.internationalSupportEvidenceIds,
      ],
    };
  }

  if (!evidence.ammVerified) {
    return {
      status: 'morocco_amm_unverified',
      mayAutoProposeRegimen: false,
      messages: [`Statut AMM/commercialisation Maroc non vérifié pour ${evidence.molecule}; proposition automatique interdite.`],
      evidenceIds: evidence.internationalSupportEvidenceIds,
    };
  }

  if (evidence.moroccoRegimenEvidenceIds.length === 0) {
    return {
      status: 'morocco_guideline_gap',
      mayAutoProposeRegimen: false,
      messages: [
        `Aucune recommandation marocaine actuelle de schéma dentaire n'est enregistrée pour ${evidence.molecule}.`,
        evidence.internationalSupportEvidenceIds.length > 0
          ? 'Une référence internationale peut être montrée comme support, avec validation explicite du praticien.'
          : 'Validation pharmacologique manuelle requise.',
      ],
      evidenceIds: [
        ...(evidence.ammEvidenceId ? [evidence.ammEvidenceId] : []),
        ...evidence.internationalSupportEvidenceIds,
      ],
    };
  }

  return {
    status: 'morocco_verified',
    mayAutoProposeRegimen: true,
    messages: [],
    evidenceIds: [
      ...(evidence.ammEvidenceId ? [evidence.ammEvidenceId] : []),
      ...evidence.moroccoRegimenEvidenceIds,
    ],
  };
}
