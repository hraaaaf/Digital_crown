import React from 'react';

/**
 * P2 Patient Journey: l'ancien FlashSummary mélangeait des heuristiques de risque,
 * des alertes et une synthèse algorithmique sans provenance visible. La Vue
 * d'ensemble s'appuie désormais exclusivement sur PatientJourney et ses sources
 * factuelles. Le composant reste exporté temporairement pour compatibilité des
 * imports existants, mais n'effectue plus aucun appel backend ni rendu.
 */
export const FlashSummary: React.FC<{ patientId: number; patientName: string }> = () => null;
