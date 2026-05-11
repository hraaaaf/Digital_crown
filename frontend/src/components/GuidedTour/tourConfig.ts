// ============================================================
// DIGITAL CROWN - GUIDED TOUR CONFIGURATION v1.0
// Architecture : Tour Contextuel par Page + Beacon Spotlights
// ============================================================

export type TourStepPlacement = 'top' | 'bottom' | 'left' | 'right' | 'center';

export interface TourStep {
  id: string;
  page: string;          // Route à activer pour cette étape
  targetSelector?: string; // Sélecteur CSS de l'élément à mettre en valeur
  placement: TourStepPlacement;
  category: string;      // Ex: 'Dashboard', 'Patients', 'Documents'
  icon: string;          // Emoji / icône symbolique
  title: string;
  subtitle: string;
  description: string;
  features?: string[];   // Liste de bullet points de fonctionnalités
  badge?: string;        // Badge Premium, IA, Nouveau...
  isPageIntro?: boolean; // Si true, affiche le spotlight sur toute la page
}

export const TOUR_STEPS: TourStep[] = [
  // ─── INTRO ───────────────────────────────────────────────────────
  {
    id: 'welcome',
    page: '/dashboard',
    placement: 'center',
    category: 'Bienvenue',
    icon: '👑',
    title: 'Bienvenue dans Digital Crown',
    subtitle: 'Votre cabinet dentaire intelligent',
    description: 'Ce guide interactif vous présente toutes les fonctionnalités de votre plateforme en 2 minutes. Chaque module a été conçu pour maximiser votre efficacité clinique et administrative.',
    features: [
      'Interface Ghost Elite — Design premium inspiré des meilleurs SaaS médicaux',
      'IA intégrée — Analyse céphalométrique, diagnostic assisté, prescriptions intelligentes',
      'Zéro paper — Génération de tous vos documents médicaux en PDF en 1 clic',
      'Apprentissage continu — Le système apprend vos habitudes de prescription'
    ],
    isPageIntro: true,
  },

  // ─── DASHBOARD ───────────────────────────────────────────────────
  {
    id: 'dashboard-kpis',
    page: '/dashboard',
    targetSelector: '[data-tour="dashboard-stats"]',
    placement: 'bottom',
    category: 'Tableau de bord',
    icon: '📊',
    title: 'Statistiques Temps Réel',
    subtitle: "Vue d'ensemble instantanée",
    description: "Vos KPIs cliniques et financiers sont calculés en temps réel. Nombre de patients actifs, chiffre d'affaires du mois, analyses réalisées — tout est centralisé ici.",
    badge: 'Temps Réel',
  },
  {
    id: 'dashboard-agenda',
    page: '/dashboard',
    targetSelector: '[data-tour="dashboard-agenda"]',
    placement: 'top',
    category: 'Tableau de bord',
    icon: '📅',
    title: 'Agenda du Jour',
    subtitle: 'Vos rendez-vous à portée de main',
    description: "Visualisez vos prochains rendez-vous directement depuis le tableau de bord. Accédez au dossier d'un patient en un clic depuis cette vue.",
  },

  // ─── AGENDA ──────────────────────────────────────────────────────
  {
    id: 'agenda-intro',
    page: '/agenda',
    placement: 'center',
    category: 'Studio Agenda',
    icon: '🗓️',
    title: 'Studio Agenda',
    subtitle: 'Gestion intelligente de votre planning',
    description: 'Un agenda médical complet avec gestion des créneaux, des motifs de consultation et une vue hebdomadaire interactive. Chaque rendez-vous est lié au dossier patient.',
    features: [
      'Vue Jour / Semaine / Mois',
      'Détection automatique des conflits de créneaux',
      'Lien direct vers le dossier patient depuis le RDV',
      'Motifs de consultation paramétrables'
    ],
    badge: 'Nouveau',
    isPageIntro: true,
  },

  // ─── PATIENTS ─────────────────────────────────────────────────────
  {
    id: 'patients-list',
    page: '/patients',
    placement: 'center',
    category: 'Dossiers Patients',
    icon: '🏥',
    title: 'Gestion des Dossiers Patients',
    subtitle: 'Chaque patient, un dossier complet',
    description: "Recherchez, filtrez et gérez l'ensemble de vos dossiers patients depuis cette interface. Le système anti-doublons assure l'intégrité de votre base de données.",
    features: [
      'Recherche instantanée par nom, prénom ou numéro de dossier',
      'Tri par date de création ou numéro de dossier',
      'Détection automatique des doublons (Nom + Prénom + Date de naissance)',
      'Accès direct au dossier complet en 1 clic'
    ],
    isPageIntro: true,
  },
  {
    id: 'patient-dossier',
    page: '/patients',
    placement: 'center',
    category: 'Dossiers Patients',
    icon: '📋',
    title: 'Dossier Patient Complet',
    subtitle: 'Tout l\'historique clinique en un seul endroit',
    description: "Chaque dossier patient est organisé en onglets. Informations générales, analyses céphalométriques, hub documentaire et archives — tout est accessible et structuré.",
    features: [
      'Onglet Admin — Informations personnelles et médicales',
      'Onglet Analyse — Studio Céphalométrique IA',
      'Onglet Documents — Génération d\'ordonnances, certificats et devis',
      'Onglet Archives — Historique de tous les documents générés'
    ],
  },

  // ─── ANALYSE CÉPHALOMÉTRIQUE ─────────────────────────────────────
  {
    id: 'cephalo-studio',
    page: '/patients',
    placement: 'center',
    category: 'IA Céphalométrique',
    icon: '🧠',
    title: 'Studio Céphalométrique IA',
    subtitle: 'Analyse radiologique assistée par intelligence artificielle',
    description: "Uploadez une radiographie céphalométrique et laissez l'IA détecter automatiquement les 19 points anatomiques. Le moteur COM calcule tous les angles cliniques en quelques secondes.",
    features: [
      'Détection IA de 19 landmarks anatomiques (PyTorch / U-Net CephLD-CCA)',
      'Calcul automatique de 15+ angles céphalométriques (Tweed, ANB, SNA, SNB...)',
      "Normes COM (Centre d'Orthodontie Moderne) intégrées par âge",
      'Génération du rapport PDF complet en 1 clic',
      'Calibration mm/pixel pour une précision maximale'
    ],
    badge: 'IA Embarquée',
  },

  // ─── HUB DOCUMENTAIRE ────────────────────────────────────────────
  {
    id: 'hub-docs',
    page: '/patients',
    placement: 'center',
    category: 'Hub Documentaire',
    icon: '📄',
    title: 'Hub Documentaire',
    subtitle: 'Tous vos documents médicaux en 30 secondes',
    description: "Générez des ordonnances, certificats, devis et notes d'honoraires en un clic. Le système de prescriptions intelligentes apprend vos habitudes pour suggérer automatiquement le bon protocole.",
    features: [
      '💊 Ordonnances — Avec autocomplete médicaments et suggestions IA',
      '📜 Certificats — Médical, repos, aptitude sportive',
      "💰 Devis & Notes d'honoraires — Avec odontogramme interactif intégré",
      '📊 Bilan Céphalométrique — Rapport complet avec tous les angles',
      '📝 Document Libre — Modèle personnalisable pour tout usage'
    ],
    badge: 'Productivité x5',
  },
  {
    id: 'prescription-ai',
    page: '/patients',
    placement: 'center',
    category: 'Hub Documentaire',
    icon: '⚡',
    title: 'Prescriptions Intelligentes',
    subtitle: "L'IA qui apprend vos habitudes",
    description: "Le moteur de prescription analyse le contexte clinique du patient (actes prévus, antécédents) pour suggérer le protocole médicamenteux optimal. Plus vous l'utilisez, plus il devient précis.",
    features: [
      'Agent Chercheur — Analyse le dossier et les RDV du jour',
      'Autocomplete médicaments — Base de 68+ médicaments dentaires',
      'Détection des interactions — Alertes en temps réel',
      "Habitudes personnalisées — Le système apprend vos protocoles favoris",
      'Saisie rapide — Tapez un médicament, le reste se complète automatiquement'
    ],
    badge: 'IA Auto-Learning',
  },

  // ─── ODONTOGRAMME ────────────────────────────────────────────────
  {
    id: 'odontogram',
    page: '/patients',
    placement: 'center',
    category: 'Odontogramme',
    icon: '🦷',
    title: 'Odontogramme Interactif',
    subtitle: 'Plan de traitement visuel en FDI',
    description: "Cliquez sur chaque dent pour saisir les soins réalisés ou planifiés. Le système FDI (ISO 3950) couvre les 32 dents avec 40+ types de traitements. Les devis sont générés directement depuis l'odontogramme.",
    features: [
      '32 dents représentées avec couronnes et racines anatomiques',
      '40+ traitements : Carie, Endo, Extraction, Implant, Couronne, Prothèse...',
      'Sélection de surfaces (M, O, D, MOD...)',
      "Intégration directe dans les Devis et Notes d'honoraires"
    ],
    badge: 'SVG Interactif',
  },

  // ─── COMPTABILITÉ ────────────────────────────────────────────────
  {
    id: 'accounting',
    page: '/accounting',
    placement: 'center',
    category: 'Comptabilité',
    icon: '💳',
    title: 'Module Comptabilité',
    subtitle: 'Suivi financier de votre cabinet',
    description: "Gérez vos paiements, suivez vos impayés et exportez vos données financières. Chaque note d'honoraires générée est automatiquement enregistrée dans le registre comptable.",
    features: [
      "Vue globale du chiffre d'affaires par période",
      'Suivi des règlements par patient',
      'Export des données pour votre comptable',
      'Historique complet des transactions'
    ],
    isPageIntro: true,
  },

  // ─── ARCHIVES ────────────────────────────────────────────────────
  {
    id: 'archives',
    page: '/patients',
    placement: 'center',
    category: 'Archives',
    icon: '🗂️',
    title: 'Archives & Historique',
    subtitle: 'Traçabilité complète de tous les documents',
    description: "Tous les documents générés sont archivés automatiquement avec versioning. Retrouvez n'importe quelle ordonnance ou note d'honoraires en quelques secondes.",
    features: [
      'Versioning — Chaque mise à jour crée une nouvelle version',
      'Corbeille — Restauration possible pendant 1 an',
      'Détection de doublons — Alertes si un document identique existe',
      'Recherche rapide — Filtre par type, date ou patient'
    ],
  },

  // ─── BIBLIOTHÈQUE ────────────────────────────────────────────────
  {
    id: 'bibliotheque',
    page: '/bibliotheque',
    placement: 'center',
    category: 'Bibliothèque Élite',
    icon: '📚',
    title: 'Bibliothèque Clinique Élite',
    subtitle: 'Références médicales à portée de main',
    description: "Accédez à la base de référence clinique intégrée. Protocoles, normes céphalométriques, guide pharmacologique dental — tout est disponible hors ligne.",
    isPageIntro: true,
  },

  // ─── SETTINGS ────────────────────────────────────────────────────
  {
    id: 'settings-branding',
    page: '/settings',
    placement: 'center',
    category: 'Paramètres',
    icon: '🎨',
    title: 'Personnalisation du Cabinet',
    subtitle: 'Votre identité visuelle sur chaque document',
    description: "Configurez les informations de votre cabinet, votre logo, vos couleurs de marque et vos spécialités. Ces éléments sont automatiquement appliqués sur tous vos documents PDF générés.",
    features: [
      'Logo du cabinet — Affiché sur tous les en-têtes PDF',
      "Couleurs de marque — Synchronisées avec l'interface et les PDF",
      'Informations de contact — Adresse, téléphone, email sur chaque document',
      'QR Code dynamique — vCard, paiement ou lien de prise de RDV',
      'Support bilingue — Nom et spécialités en français et en arabe'
    ],
    isPageIntro: true,
    badge: 'Personnalisation',
  },

  // ─── PANORAMIQUE IA ──────────────────────────────────────────────
  {
    id: 'panoramic-ai',
    page: '/patients',
    placement: 'center',
    category: 'IA Panoramique',
    icon: '🔬',
    title: 'Analyse Panoramique IA',
    subtitle: 'Bilan radiologique automatisé — 31 pathologies détectables',
    description: "Uploadez une radio panoramique (OPG). Le moteur de vision IA détecte jusqu'à 31 types de pathologies et génère un compte-rendu radiologique structuré en quelques secondes. Zéro LLM, 100% local et instantané.",
    features: [
      'Caries, Lésions périapicales, Kystes',
      'Perte osseuse, Dents manquantes, Inclusions',
      'Traitements existants : Couronnes, Endos, Implants',
      'Matériel orthodontique : Brackets, Fils, TADs',
      'Rapport médical structuré en 4 sections cliniques'
    ],
    badge: 'IA Vision 31 Classes',
  },

  // ─── FIN ─────────────────────────────────────────────────────────
  {
    id: 'finish',
    page: '/dashboard',
    placement: 'center',
    category: 'Fin du Tour',
    icon: '🚀',
    title: 'Vous êtes prêt !',
    subtitle: 'Digital Crown est à votre service',
    description: "Vous maîtrisez maintenant toutes les fonctionnalités de Digital Crown. Commencez par créer votre premier dossier patient ou configurez votre cabinet dans les Paramètres.",
    features: [
      '→ Créer un premier patient',
      '→ Configurer le cabinet dans Paramètres',
      '→ Lancer votre première analyse céphalométrique',
      '→ Générer votre première ordonnance'
    ],
    isPageIntro: true,
  },
];

export const TOUR_STORAGE_KEY = 'digitalcrown_tour_completed';
export const TOUR_VERSION = '1.0';
