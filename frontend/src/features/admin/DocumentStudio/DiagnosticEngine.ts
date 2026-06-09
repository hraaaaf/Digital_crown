export interface DiagnosticRule {
  motif: string;
  vitality?: string;
  percussion?: string;
  palpation?: string;
  radiology?: string;
  lesionDuration?: string;
  result: {
    title: string;
    description: string;
    protocol: string[];
    treatmentPlan: { phase: string; act: string; price: number }[];
    warnings: string[];
  };
}

export const diagnosticRules: DiagnosticRule[] = [
  // DOULEUR
  {
    motif: 'DOULEUR',
    vitality: 'POSITIVE_PERSISTANTE',
    result: {
      title: "🦷 Pulpite Irréversible Aiguë",
      description: "Inflammation sévère et irréversible de la pulpe. Douleur spontanée lancinante, accrue en position couchée.",
      protocol: ["PARACETAMOL 1g x3/jour", "⚠️ AINS contre-indiqués sans couverture antibiotique"],
      treatmentPlan: [
        { phase: "ENDO", act: "Traitement Canalaire (Pulpectomie)", price: 1200 },
        { phase: "PROTHESE", act: "Reconstruction Corono-Radiculaire (Inlay-Core) + Couronne", price: 3500 }
      ],
      warnings: ["⚠️ Risque de nécrose pulpaire rapide en l'absence de traitement étiologique direct sous digue."]
    }
  },
  {
    motif: 'DOULEUR',
    vitality: 'POSITIVE_TRANSITOIRE',
    result: {
      title: "🦷 Pulpite Réversible / Hyperémie Pulpaire",
      description: "Réaction inflammatoire pulpaire modérée liée à une carie active ou une agression mécanique.",
      protocol: ["PARACETAMOL 500mg si besoin"],
      treatmentPlan: [
        { phase: "CONSERVATRICE", act: "Restauration Composite / Cavotech", price: 400 }
      ],
      warnings: []
    }
  },
  {
    motif: 'DOULEUR',
    vitality: 'NEGATIVE',
    percussion: 'POSITIVE_AXIALE',
    result: {
      title: "🌋 Parodontite Apicale Aiguë",
      description: "Nécrose pulpaire compliquée d'une infection du ligament parodontal apical. Dent extrudée et très douloureuse à la mastication.",
      protocol: ["AMOXICILLINE 1g x2/jour (dalacine si allergie)", "PARACETAMOL 1g x3/jour", "🛡️ Saccharomyces Boulardii 250mg"],
      treatmentPlan: [
        { phase: "ENDO", act: "Ouverture de chambre & Désinfection canalaire", price: 800 },
        { phase: "ENDO", act: "Obturation Canalaire Définitive (Gutta)", price: 1200 }
      ],
      warnings: ["🔴 Contre-indication formelle d'AINS seul : Risque majeur de cellulite cervico-faciale agressive."]
    }
  },
  {
    motif: 'DOULEUR',
    vitality: 'NEGATIVE',
    percussion: 'NEGATIVE',
    result: {
      title: "💀 Nécrose Pulpaire Asymptomatique",
      description: "Mortification complète de la pulpe dentaire suite à un traumatisme ou une carie profonde non traitée.",
      protocol: [],
      treatmentPlan: [
        { phase: "ENDO", act: "Traitement endodontique complet", price: 1200 }
      ],
      warnings: []
    }
  },
  {
    motif: 'DOULEUR',
    vitality: 'NEGATIVE',
    percussion: 'POSITIVE_TRANSVERSALE',
    result: {
      title: "💀 Nécrose Pulpaire avec Parodontite Latérale",
      description: "Mortification complète de la pulpe dentaire avec atteinte parodontale latérale.",
      protocol: [],
      treatmentPlan: [
        { phase: "ENDO", act: "Traitement endodontique complet", price: 1200 }
      ],
      warnings: []
    }
  },
  // GONFLEMENT
  {
    motif: 'GONFLEMENT',
    palpation: 'FLUCTUANTE',
    result: {
      title: "🌋 Abcès Périapical Aigu",
      description: "Collection purulente localisée au niveau de l'apex radiculaire d'origine pulpaire.",
      protocol: ["AMOXICILLINE 1g x2/jour (ou Clindamycine 600mg)", "PARACETAMOL 1g x3/jour", "🛡️ Saccharomyces Boulardii 250mg"],
      treatmentPlan: [
        { phase: "ENDO", act: "Ouverture & Drainage canalaire d'urgence", price: 800 },
        { phase: "CHIRURGIE", act: "Extraction chirurgicale si dent non conservable", price: 900 }
      ],
      warnings: ["🔴 Urgence Médicale : Prescription immédiate d'Amoxicilline. Proscription absolue des AINS (risque de diffusion bactérienne cervico-faciale)."]
    }
  },
  {
    motif: 'GONFLEMENT',
    percussion: 'POSITIVE_AXIALE',
    result: {
      title: "🌋 Abcès Périapical Aigu",
      description: "Collection purulente localisée au niveau de l'apex radiculaire d'origine pulpaire.",
      protocol: ["AMOXICILLINE 1g x2/jour (ou Clindamycine 600mg)", "PARACETAMOL 1g x3/jour", "🛡️ Saccharomyces Boulardii 250mg"],
      treatmentPlan: [
        { phase: "ENDO", act: "Ouverture & Drainage canalaire d'urgence", price: 800 },
        { phase: "CHIRURGIE", act: "Extraction chirurgicale si dent non conservable", price: 900 }
      ],
      warnings: ["🔴 Urgence Médicale : Prescription immédiate d'Amoxicilline. Proscription absolue des AINS (risque de diffusion bactérienne cervico-faciale)."]
    }
  },
  {
    motif: 'GONFLEMENT',
    palpation: 'SENSITIVE',
    result: {
      title: "🌋 Abcès Parodontal Aigu",
      description: "Infection purulente localisée dans les tissus parodontaux de soutien.",
      protocol: ["SPIRAMYCINE_METRONIDAZOLE 1.5MUI/250mg (Bi-Rodogyl)", "Chlorhexidine 0.12% (Bain de bouche)"],
      treatmentPlan: [
        { phase: "PARO", act: "Drainage de la poche & Irrigation sous-gingivale", price: 500 },
        { phase: "PARO", act: "Surfaçage Radiculaire (SRP) après phase aiguë", price: 1500 }
      ],
      warnings: []
    }
  },
  {
    motif: 'GONFLEMENT',
    palpation: 'NEGATIVE',
    result: {
      title: "🌋 Abcès Parodontal Aigu",
      description: "Infection purulente localisée dans les tissus parodontaux de soutien.",
      protocol: ["SPIRAMYCINE_METRONIDAZOLE 1.5MUI/250mg (Bi-Rodogyl)", "Chlorhexidine 0.12% (Bain de bouche)"],
      treatmentPlan: [
        { phase: "PARO", act: "Drainage de la poche & Irrigation sous-gingivale", price: 500 },
        { phase: "PARO", act: "Surfaçage Radiculaire (SRP) après phase aiguë", price: 1500 }
      ],
      warnings: []
    }
  },
  // PARO
  {
    motif: 'PARO',
    radiology: 'PERTE_OSSEUSE',
    result: {
      title: "🦷 Parodontite Chronique Active (EFP/AAP 2017)",
      description: "Destruction progressive de l'os alvéolaire et du ligament parodontal d'origine bactérienne.",
      protocol: ["AMOXICILLINE 500mg + METRONIDAZOLE 500mg x3/jour (Adjuvant)", "Bain de bouche Chlorhexidine"],
      treatmentPlan: [
        { phase: "PARO", act: "Bilan Parodontal & Sondage systématique", price: 600 },
        { phase: "PARO", act: "Détartrage & Surfaçage Radiculaire (SRP) complet", price: 3000 }
      ],
      warnings: ["⚠️ Risque de mobilités dentaires accrues et pertes dentaires multiples sans traitement de soutien."]
    }
  },
  {
    motif: 'PARO',
    radiology: 'RADIOCLAIRE',
    result: {
      title: "🩸 Gingivite Chronique Induite par la Plaque",
      description: "Inflammation superficielle et réversible de la gencive marginale sans perte d'attache.",
      protocol: ["Bain de bouche Chlorhexidine 0.12%"],
      treatmentPlan: [
        { phase: "CONSERVATRICE", act: "Détartrage supra-gingival complet & Aéropolissage", price: 500 }
      ],
      warnings: []
    }
  },
  {
    motif: 'PARO',
    radiology: 'PROXIMITE_NERF',
    result: {
      title: "🩸 Gingivite Chronique Induite par la Plaque",
      description: "Inflammation superficielle et réversible de la gencive marginale sans perte d'attache.",
      protocol: ["Bain de bouche Chlorhexidine 0.12%"],
      treatmentPlan: [
        { phase: "CONSERVATRICE", act: "Détartrage supra-gingival complet & Aéropolissage", price: 500 }
      ],
      warnings: []
    }
  },
  {
    motif: 'PARO',
    radiology: 'AUCUNE',
    result: {
      title: "🩸 Gingivite Chronique Induite par la Plaque",
      description: "Inflammation superficielle et réversible de la gencive marginale sans perte d'attache.",
      protocol: ["Bain de bouche Chlorhexidine 0.12%"],
      treatmentPlan: [
        { phase: "CONSERVATRICE", act: "Détartrage supra-gingival complet & Aéropolissage", price: 500 }
      ],
      warnings: []
    }
  },
  // LESION
  {
    motif: 'LESION',
    lesionDuration: 'PLUS_14',
    result: {
      title: "🚨 Lésion Suspecte de la Muqueuse (> 14 jours)",
      description: "Lésion ulcérée, érythroplasique ou leucoplasique persistante au-delà de la période normale de cicatrisation de 14 jours.",
      protocol: ["⚠️ Référer en Service Spécialisé de Stomatologie"],
      treatmentPlan: [
        { phase: "CHIRURGIE", act: "Biopsie anatomopathologique sous anesthésie locale", price: 1500 }
      ],
      warnings: ["🔴 ALERTE CARCINOME : Toute lésion muqueuse ne présentant aucune tendance à la guérison après 14 jours doit impérativement faire l'objet d'une biopsie pour dépistage précoce du cancer buccal."]
    }
  },
  {
    motif: 'LESION',
    lesionDuration: 'MOINS_14',
    result: {
      title: "👅 Lésion Traumatique Muqueuse Récente",
      description: "Ulcération muqueuse superficielle probablement d'origine traumatique ou aphteuse.",
      protocol: ["Gel buccal antiseptique / antalgique local"],
      treatmentPlan: [
        { phase: "CONSERVATRICE", act: "Élimination des facteurs irritants (dent cassée, crochet)", price: 300 }
      ],
      warnings: ["🕒 Règle de sécurité : À réévaluer dans 14 jours. Si la lésion persiste, planifier d'office une biopsie."]
    }
  }
];

export const evaluateDiagnosis = (params: { motif: string, vitality: string, percussion: string, palpation: string, radiology: string, lesionDuration: string, medicalHistory: string }) => {
  const matchedRule = diagnosticRules.find(r => {
    if (r.motif !== params.motif) return false;
    if (r.vitality && r.vitality !== params.vitality) return false;
    if (r.percussion && r.percussion !== params.percussion) return false;
    if (r.palpation && r.palpation !== params.palpation) return false;
    if (r.radiology && r.radiology !== params.radiology) return false;
    if (r.lesionDuration && r.lesionDuration !== params.lesionDuration) return false;
    return true;
  });

  const result = matchedRule ? JSON.parse(JSON.stringify(matchedRule.result)) : {
    title: "Consultation Standard",
    description: "Examen clinique normal. Aucun traitement urgent requis.",
    protocol: ["PARACETAMOL 1g si douleur"],
    treatmentPlan: [{ phase: "CONSERVATRICE", act: "Détartrage & Polissage", price: 400 }],
    warnings: []
  };

  // APPLY PHARMACOVIGILANCE
  const atcd = params.medicalHistory.toLowerCase();
  const hasPenicillinAllergy = atcd.includes('pénicilline') || atcd.includes('penicilline') || atcd.includes('clamoxyl') || atcd.includes('amoxicilline');
  const hasAinsAllergy = atcd.includes('ains') || atcd.includes('ibuprofène') || atcd.includes('ibuprofene') || atcd.includes('anti-inflammatoire');

  result.protocol = result.protocol.map((p: string) => {
    let modifiedP = p;
    if (hasPenicillinAllergy && modifiedP.toLowerCase().includes('amoxicilline')) {
      modifiedP = modifiedP.replace('AMOXICILLINE', 'CLINDAMYCINE/MACROLIDE (⚠️ Substitution cause Allergie Pénicilline)');
      result.warnings.push("⚠️ Allergie à la Pénicilline détectée. Antibiothérapie modifiée automatiquement vers une classe alternative.");
    }
    if (hasAinsAllergy && modifiedP.toLowerCase().includes('ains')) {
      modifiedP = modifiedP.replace('AINS', 'CORTICOSTÉROÏDES (⚠️ Substitution cause Allergie AINS)');
      result.warnings.push("⚠️ Allergie aux AINS détectée. Modification du protocole anti-inflammatoire suggérée.");
    }
    return modifiedP;
  });

  return result;
};
