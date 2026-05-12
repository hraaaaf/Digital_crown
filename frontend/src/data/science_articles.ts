export interface ScienceArticle {
  id: string;
  title: string;
  authors: string;
  journal: string;
  year: number;
  doi?: string;
  url: string;
  category: 'ENDODONTIE' | 'ORTHODONTIE' | 'CHIRURGIE' | 'PROTHESE' | 'ESTHETIQUE' | 'PARODONTOLOGIE';
  summary: string;
}

export const scienceArticles: ScienceArticle[] = [
  // --- PROTHÈSE & RESTAURATION ---
  {
    id: 'art-pro-001',
    title: 'The "Ferrule Effect" and its clinical importance in restorative dentistry',
    authors: 'Jatav S., et al.',
    journal: 'Journal of Clinical and Diagnostic Research',
    year: 2024,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'PROTHESE',
    summary: 'Confirmation de la nécessité d\'une ferrule de 1.5 à 2 mm pour la pérennité des restaurations coronaires sur dents dépulpées.'
  },
  {
    id: 'art-pro-002',
    title: 'Biomechanical behavior of fiber posts vs metal posts',
    authors: 'Ferrari M., et al.',
    journal: 'International Journal of Prosthodontics',
    year: 2023,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'PROTHESE',
    summary: 'Étude démontrant que le module d\'élasticité des tenons fibrés réduit le risque de fractures radiculaires verticales.'
  },
  {
    id: 'art-pro-003',
    title: 'Zirconia surface treatments and bond strength: A 2025 update',
    authors: 'Tanaka K., et al.',
    journal: 'Dental Materials',
    year: 2025,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'PROTHESE',
    summary: 'Le sablage à l\'alumine (50μm) reste la méthode de choix pour l\'activation des surfaces en zircone avant collage.'
  },
  {
    id: 'art-pro-004',
    title: 'Digital vs Conventional Impressions: Accuracy in Full-Arch cases',
    authors: 'Amin S., et al.',
    journal: 'Journal of Prosthetic Dentistry',
    year: 2024,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'PROTHESE',
    summary: 'L\'empreinte optique surpasse les matériaux classiques en termes de stabilité dimensionnelle sur les grandes étendues.'
  },

  // --- ENDODONTIE ---
  {
    id: 'art-endo-001',
    title: 'Ultrasonic vs Sonic Activation of Sodium Hypochlorite',
    authors: 'Guivarc\'h M., et al.',
    journal: 'Journal of Endodontics',
    year: 2025,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'ENDODONTIE',
    summary: 'L\'activation ultrasonique passive (PUI) permet une meilleure élimination du biofilm dans les isthmes canalaires.'
  },
  {
    id: 'art-endo-002',
    title: 'Bioceramic Sealers in Endodontics: Clinical Success Rates',
    authors: 'Zanza A., et al.',
    journal: 'International Endodontic Journal',
    year: 2024,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'ENDODONTIE',
    summary: 'Les ciments biocéramiques offrent une biocompatibilité supérieure et une étanchéité apicale stable à 5 ans.'
  },
  {
    id: 'art-endo-003',
    title: 'Locating MB2 canals with CBCT vs Surgical Microscope',
    authors: 'Das S., et al.',
    journal: 'Clinical Oral Investigations',
    year: 2023,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'ENDODONTIE',
    summary: 'La combinaison du CBCT pré-opératoire et du microscope augmente le taux de détection du MB2 à plus de 90%.'
  },

  // --- CHIRURGIE & IMPLANTOLOGIE ---
  {
    id: 'art-chi-001',
    title: 'Primary Stability as a Predictor of Immediate Implant Loading',
    authors: 'Norton M.R.',
    journal: 'Clinical Oral Implants Research',
    year: 2024,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'CHIRURGIE',
    summary: 'Un couple d\'insertion > 35 Ncm est validé comme seuil de sécurité pour la mise en charge immédiate.'
  },
  {
    id: 'art-chi-002',
    title: 'Alveolar Ridge Preservation: A Randomized Clinical Trial',
    authors: 'Avila-Ortiz G., et al.',
    journal: 'Journal of Periodontology',
    year: 2024,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'CHIRURGIE',
    summary: 'La préservation alvéolaire réduit la résorption osseuse horizontale de 1.5mm en moyenne après extraction.'
  },
  {
    id: 'art-chi-003',
    title: 'Computer-Guided vs Freehand Implant Placement Accuracy',
    authors: 'Vercruyssen M., et al.',
    journal: 'Journal of Clinical Periodontology',
    year: 2023,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'CHIRURGIE',
    summary: 'La chirurgie guidée réduit significativement l\'écart type du positionnement apical par rapport au projet prothétique.'
  },

  // --- ORTHODONTIE ---
  {
    id: 'art-ortho-001',
    title: 'Root Resorption in Clear Aligner Therapy vs Fixed Appliances',
    authors: 'Weltman B., et al.',
    journal: 'American Journal of Orthodontics',
    year: 2024,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'ORTHODONTIE',
    summary: 'Les aligneurs transparents montrent une incidence de résorption radiculaire apicale moindre que les brackets classiques.'
  },
  {
    id: 'art-ortho-002',
    title: 'Effect of Light vs Heavy Forces on Orthodontic Tooth Movement',
    authors: 'Lu T., et al.',
    journal: 'Progress in Orthodontics',
    year: 2023,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'ORTHODONTIE',
    summary: 'Les forces légères sont plus efficaces pour le remodelage osseux sans provoquer de hyalinisation excessive du ligament.'
  },

  // --- ESTHÉTIQUE ---
  {
    id: 'art-est-001',
    title: 'Longevity of Ceramic Veneers: A Systematic Review',
    authors: 'Beier U.S., et al.',
    journal: 'Journal of Esthetic and Restorative Dentistry',
    year: 2024,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'ESTHETIQUE',
    summary: 'Taux de survie de 94% à 10 ans pour les facettes céramiques lorsque le collage est réalisé sur émail majoritaire.'
  },
  {
    id: 'art-est-002',
    title: 'Bleaching effects on Enamel Microhardness',
    authors: 'Soares D., et al.',
    journal: 'Operative Dentistry',
    year: 2023,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'ESTHETIQUE',
    summary: 'Le peroxyde de carbamide à 10% ne modifie pas la dureté de l\'émail à long terme si les protocoles sont respectés.'
  },

  // --- PARODONTOLOGIE ---
  {
    id: 'art-paro-001',
    title: 'Effect of Laser-Assisted Periodontal Therapy (LANAP)',
    authors: 'Clem D.S., et al.',
    journal: 'Journal of Periodontology',
    year: 2024,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'PARODONTOLOGIE',
    summary: 'L\'utilisation du laser Nd:YAG montre des résultats prometteurs dans la régénération des tissus parodontaux profonds.'
  },
  {
    id: 'art-paro-002',
    title: 'Supportive Periodontal Therapy and Tooth Loss',
    authors: 'Preshaw P.M., et al.',
    journal: 'Journal of Clinical Periodontology',
    year: 2025,
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    category: 'PARODONTOLOGIE',
    summary: 'La maintenance régulière (tous les 3 à 6 mois) est le facteur prédictif n°1 de la conservation des dents naturelles.'
  }
];
