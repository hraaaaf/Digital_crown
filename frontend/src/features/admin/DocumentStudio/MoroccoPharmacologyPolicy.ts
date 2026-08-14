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
  MOROCCO_DMP: {
    id: 'MOROCCO_DMP',
    tier: 'MOROCCO_OFFICIAL',
    authority: 'Ministère de la Santé / DMP – Maroc',
    title: 'Direction du Médicament et de la Pharmacie — missions et référentiel réglementaire',
    url: 'https://www.sante.gov.ma/Pages/ADM_Centrale/DMP.aspx',
    reviewedAt: '2026-08-14',
    scope: 'FORMULARY',
  },
  MOROCCO_AMM: {
    id: 'MOROCCO_AMM',
    tier: 'MOROCCO_OFFICIAL',
    authority: 'Ministère de la Santé / AMMPS – Maroc',
    title: 'Médicaments autorisés — recherche AMM Maroc',
    url: 'https://www.sante.gov.ma/medicaments/amm/default.aspx',
    reviewedAt: '2026-08-14',
    scope: 'AMM',
    note: 'Required before Digital Crown may claim Moroccan market availability or auto-propose a marketed presentation.',
  },
  MOROCCO_ANTIBIOTIC_STEWARDSHIP: {
    id: 'MOROCCO_ANTIBIOTIC_STEWARDSHIP',
    tier: 'MOROCCO_OFFICIAL',
    authority: 'Ministère de la Santé – Maroc',
    title: 'Bon usage des antibiotiques / antibiorésistance',
    url: 'https://www.sante.gov.ma/Pages/Communiques.aspx?IDCom=307',
    reviewedAt: '2026-08-14',
    scope: 'STEWARDSHIP',
    note: 'Antibiotics require appropriate indication, dose and duration; inappropriate and unnecessary use must be avoided.',
  },
  MOROCCO_PARACETAMOL: {
    id: 'MOROCCO_PARACETAMOL',
    tier: 'MOROCCO_OFFICIAL',
    authority: 'Sehati / Ministère de la Santé – Maroc',
    title: 'Recommandations pour le bon usage du paracétamol',
    url: 'https://sehati.gov.ma/article/recommandations_pour_le_bon_usage_du_paracetamol',
    reviewedAt: '2026-08-14',
    scope: 'DOSING',
    note: 'Official Moroccan good-use rules; exact product dosing still depends on locally authorised product information.',
  },
  MOROCCO_PRACTITIONER_ANTIBIOTICS_2020: {
    id: 'MOROCCO_PRACTITIONER_ANTIBIOTICS_2020',
    tier: 'MOROCCO_PROFESSIONAL',
    authority: 'Pr Lahcen Belyamani & Dr Said Jidane / Moroccan academic reference',
    title: 'Antibiotiques — Antibio-choix du praticien marocain',
    url: 'https://biblio.um6ss.ma/antibiotiques-antibio-choix-du-praticien-marocain/',
    reviewedAt: '2026-08-14',
    scope: 'FORMULARY',
    note: 'Moroccan professional reference, useful for arbitration but lower authority than current official Moroccan regulator/guidance.',
  },
};

/**
 * Morocco-first gate.
 *
 * Automatic regimen proposal requires BOTH:
 * 1. Moroccan AMM/market verification for the molecule/presentation context, and
 * 2. Moroccan regimen-level evidence.
 *
 * If Morocco has no current dental regimen guidance for that molecule, an
 * international guideline may be displayed as SUPPORT ONLY, never silently
 * promoted to a Moroccan recommendation.
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
      messages: [`Statut AMM Maroc non vérifié pour ${evidence.molecule}; proposition automatique interdite.`],
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
