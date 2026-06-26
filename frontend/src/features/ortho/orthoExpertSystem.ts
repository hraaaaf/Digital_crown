import type { DonneesEtape3, DivisionClasseII } from './cephaloTypes';

export function deriveDentureFromAge(ageStr: string | number): 'TEMPORAIRE' | 'MIXTE' | 'PERMANENTE' | '' {
  if (ageStr === '') return '';
  const age = Number(ageStr);
  if (isNaN(age)) return '';
  if (age > 12) return 'PERMANENTE';
  if (age >= 6) return 'MIXTE';
  return 'TEMPORAIRE';
}

export function deriveDivision(classeSquelettique: string, surplombStr: string | number): DivisionClasseII {
  if (!classeSquelettique.toLowerCase().includes('classe ii')) return null;
  const surplomb = Number(surplombStr);
  if (isNaN(surplomb)) return null;
  // Si le surplomb est > 3mm, on est généralement sur une proalvéolie incisive (Division 1)
  // Sinon, (incisives droites ou palato-versées), c'est une Division 2
  return surplomb > 3 ? '1' : '2';
}

export interface OrthoExpertReport {
  extraction: {
    recommandee: boolean;
    raison: string;
    dents?: string;
  };
  damon: {
    maxillaire: 'Low Torque (Vert)' | 'Standard Torque (Bleu)' | 'High Torque (Rouge)';
    mandibulaire: 'Low Torque (Vert)' | 'Standard Torque (Bleu)' | 'High Torque (Rouge)';
    raison: string;
  };
  mecanique: string[];
  rapportMarkdown: string;
}

export function evaluateCase(data: DonneesEtape3, ddmTotale: number | null): OrthoExpertReport {
  const impa = data.dentaire.impa === '' ? 90 : Number(data.dentaire.impa);
  const ifranc = data.dentaire.i_francfort === '' ? 107 : Number(data.dentaire.i_francfort);
  const pattern = data.pattern_vertical || 'normodivergent';
  const classe = data.classe_squelettique || 'Classe I';
  const profil = data.profil || 'droit';
  const surplomb = data.dentaire.surplomb === '' ? 2.2 : Number(data.dentaire.surplomb);
  const recouv = data.dentaire.recouvrement === '' ? 2.2 : Number(data.dentaire.recouvrement);
  
  // 1. DÉCISION EXTRACTION (INTÉGRATION PANORAMIQUE & WITS)
  let extrRecommandee = false;
  let extrRaison = "Profil plat et DDM légère/modérée permettant une résolution sans extraction.";
  let extrDents = "";

  const ddmDeficit = ddmTotale !== null ? ddmTotale : 0; // Negative means deficit
  const isSevereCrowding = ddmDeficit < -7;
  const isModerateCrowding = ddmDeficit >= -7 && ddmDeficit <= -4;

  const ddsIncluses = data.panoramique?.dds_incluses ?? false;
  const perteOsseuse = data.panoramique?.perte_osseuse ?? false;
  const wits = typeof data.wits_mcnamara?.wits_appraisal === 'number' ? data.wits_mcnamara.wits_appraisal : 0;

  if (isSevereCrowding && impa >= 95 && profil !== 'concave') {
    extrRecommandee = true;
    extrRaison = `DDM Sévère (${Math.abs(ddmDeficit).toFixed(1)}mm) couplée à une biprotrusion (IMPA ${impa}°) et un profil ${profil}.`;
    extrDents = classe.includes('Classe II') || wits > 2 ? "14, 24, 35, 45 (Ou 14, 24, 34, 44 selon le type de mécanique)" : "14, 24, 34, 44";
  } else if (impa >= 100 && ifranc >= 120) {
    extrRecommandee = true;
    extrRaison = `Biprotrusion alvéolo-dentaire critique (IMPA ${impa}°, I/F ${ifranc}°). Nécessité de recul labial.`;
    extrDents = "14, 24, 34, 44";
  } else if ((isModerateCrowding && impa > 95 && pattern === 'hyperdivergent') || (perteOsseuse && isModerateCrowding)) {
    extrRecommandee = true;
    extrRaison = perteOsseuse 
      ? `Parodonte affaibli (perte osseuse). Expansion transversale et vestibulo-version proscrites.`
      : `Tendance hyperdivergente (risque d'ouverture de l'axe charnière en cas d'expansion) avec IMPA fort (${impa}°).`;
    extrDents = "14, 24, 34, 44";
  } else if (classe.includes('Classe II') && ddsIncluses && !extrRecommandee) {
    extrRaison = "Classe II Squelettique/Dentaire : Traitement sans extraction pré-molaire, MAIS nécessité absolue d'avulser les Dents de Sagesse pour permettre la distalisation molaire (Recul).";
  }

  // 2. PRESCRIPTION DAMON
  const denture_type = data.denture_type || '';
  const isMixteOrPediatric = denture_type === 'MIXTE' || denture_type === 'TEMPORAIRE';

  let torqueMax: 'Low Torque (Vert)' | 'Standard Torque (Bleu)' | 'High Torque (Rouge)' = 'Standard Torque (Bleu)';
  let torqueMand: 'Low Torque (Vert)' | 'Standard Torque (Bleu)' | 'High Torque (Rouge)' = 'Standard Torque (Bleu)';
  let raisonTorque = "Inclinaisons initiales physiologiques, maintien des torques standard.";

  if (!isMixteOrPediatric) {
    // Maxillaire
    if (extrRecommandee || classe.includes('Classe II')) {
      torqueMax = 'High Torque (Rouge)';
      raisonTorque = "Maxillaire: High Torque pour contrôler le torque radiculaire lors de la rétraction incisive ou éviter l'effet 'rabbiting'. ";
    } else if (ifranc > 120 && !extrRecommandee) {
      torqueMax = 'Low Torque (Vert)';
      raisonTorque = "Maxillaire: Low Torque pour limiter la vestibulo-version lors de la levée d'encombrement. ";
    }

    // Mandibulaire
    if (impa > 95 || (isModerateCrowding && !extrRecommandee)) {
      torqueMand = 'Low Torque (Vert)';
      raisonTorque += "Mandibule: Low Torque pour empêcher la vestibulo-version excessive lors de l'alignement/expansion.";
    } else if (impa < 85) {
      torqueMand = 'High Torque (Rouge)';
      raisonTorque += "Mandibule: High Torque pour corriger la rétroalvéolie mandibulaire.";
    }
  }

  // 3. MÉCANIQUE ET CHIRURGIE (Squelettique Vraie)
  const mec: string[] = [];
  
  if (wits > 6 || wits < -5) {
    mec.push("⚠️ DÉCALAGE SQUELETTIQUE SÉVÈRE (Wits hors normes) : Préparation Orthodontique pour Chirurgie Orthognathique fortement recommandée chez l'adulte.");
  }
  
  if (data.panoramique?.resorption_radiculaire) {
    mec.push("⚠️ RÉSORPTION RADICULAIRE DÉTECTÉE : Utilisation impérative de forces très légères (Aligners avec changements lents ou arcs thermiques ultra-souples).");
  }

  if (data.panoramique?.asymetrie_condylienne) {
    mec.push("⚠️ ASYMÉTRIE CONDYLIENNE : Investigation articulaire (CBCT/IRM) requise avant tout traitement de camouflage.");
  }

  if (recouv > 3.5) {
    mec.push("Supraclusie: Mécanique de nivellement courbe de Spee (arcs inverses de Spee ou bite turbos antérieurs).");
  } else if (recouv < 1.0) {
    mec.push("Infraclusie/Béance: Bite blocks postérieurs, éviter les mécaniques extrusives postérieures.");
  }
  
  if (surplomb > 4 && !extrRecommandee) {
    mec.push("Proalvéolie: Contrôle sagittal strict. Utilisation d'élastiques de Classe II ou Distalisation (si DDS avulsées).");
  }

  if (pattern === 'hyperdivergent') {
    mec.push("Contrôle Vertical (Hyperdivergent): Éviter les mécaniques extrusives. Maintien absolu de l'ancrage vertical postérieur (Les Aligners sont très indiqués pour leur effet 'Bite-Block').");
  }

  // 4. RÉDACTION DU RAPPORT MARKDOWN
  const prescriptionBlock = isMixteOrPediatric
    ? `#### 2. Orientation Thérapeutique (Denture Mixte / Patient En Croissance)
⚠️ **Traitement multi-attaches fixe différé.** Compte tenu de l'âge et de la denture mixte, le plan thérapeutique doit être orienté vers une évaluation interceptive et une surveillance de croissance. La prescription d'appareillage fixe type Damon ou de broches haute section est prématurée à ce stade. Une réévaluation à la denture permanente est recommandée.`
    : `#### 2. Prescription Autoligaturante (Type Damon)
* **Maxillaire** : ${torqueMax}
* **Mandibule** : ${torqueMand}
* **Rationnel** : ${raisonTorque}`;

  const md = `
### Synthèse Automatique - Agent ODF
**Profil du Patient** : ${classe}, ${pattern}, Profil ${profil}.
**Incisives** : Surplomb ${surplomb}mm, Recouvrement ${recouv}mm (IMPA: ${impa}°, I/F: ${ifranc}°).
**Analyse d'Espace** : DDM Globale de ${ddmTotale ? ddmTotale.toFixed(1) : '0'}mm.

#### 1. Décision Biomécanique
**Protocole** : ${extrRecommandee ? 'EXTRACTIONNEL' : 'SANS EXTRACTION (BONE ADAPTATION)'}
**Rationnel** : ${extrRaison}
${extrRecommandee ? `**Dents concernées** : ${extrDents}` : ''}

${prescriptionBlock}

#### 3. Mécanique Spécifique
${mec.length > 0 ? mec.map(m => `- ${m}`).join('\n') : '- Nivellement et alignement standard. Arcs CuNiTi.'}
`;

  return {
    extraction: { recommandee: extrRecommandee, raison: extrRaison, dents: extrDents },
    damon: { maxillaire: torqueMax, mandibulaire: torqueMand, raison: raisonTorque },
    mecanique: mec,
    rapportMarkdown: md
  };
}
