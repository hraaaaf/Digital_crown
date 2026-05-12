// ============================================================
// DIGITAL CROWN - GUIDED TOUR CONFIGURATION v2.0
// Architecture : Tour Contextuel + PreActions + DOM Detection
// ============================================================

export type TourStepPlacement = 'top' | 'bottom' | 'left' | 'right' | 'center';

export interface TourStep {
  id: string;
  page: string;                 // Route à activer pour cette étape
  pageDynamic?: boolean;        // Si true, la page sera résolue dynamiquement
  targetSelector?: string;      // Sélecteur CSS de l'élément à mettre en valeur
  placement: TourStepPlacement;
  category: string;
  icon: string;
  title: string;
  subtitle: string;
  description: string;
  features?: string[];
  badge?: string;
  isPageIntro?: boolean;        // Spotlight sur toute la page (overlay blur)
  preAction?: string;           // Identifiant d'une action à exécuter AVANT la résolution du target
}

// Catégories ordonnées (pour la barre segmentée)
export const TOUR_CATEGORIES = [
  'Bienvenue',
  'Dashboard',
  'Agenda',
  'Dossier Patient',
  'Documents',
  'Bibliothèque',
  'Configuration',
  'Tour Terminé',
] as const;

export const TOUR_STEPS: TourStep[] = [
  // ─── INTRO ───────────────────────────────────────────────────────
  {
    id: 'welcome',
    page: '/dashboard',
    placement: 'center',
    category: 'Bienvenue',
    icon: '👑',
    title: 'Bienvenue dans Digital Crown',
    subtitle: 'Votre cabinet, réinventé.',
    description: 'Découvrez en 2 minutes comment Digital Crown va transformer votre quotidien clinique et administratif.',
    features: [
      'Génération instantanée de tous vos documents',
      'Analyse IA de vos radiographies',
      'Prescriptions qui apprennent vos habitudes',
    ],
    isPageIntro: true,
  },

  // ─── DASHBOARD ───────────────────────────────────────────────────
  {
    id: 'dashboard-stats',
    page: '/dashboard',
    targetSelector: '[data-tour="dashboard-stats"]',
    placement: 'top',
    category: 'Dashboard',
    icon: '📊',
    title: 'Pilotage en Temps Réel',
    subtitle: 'Vos indicateurs clés',
    description: "Patients actifs, analyses IA réalisées, activité hebdomadaire — tout est calculé automatiquement et affiché ici.",
    badge: 'Live',
  },
  {
    id: 'quick-action',
    page: '/dashboard',
    targetSelector: '[data-tour="quick-action-new-patient"]',
    placement: 'right',
    category: 'Dashboard',
    icon: '⚡',
    title: 'Créer un Dossier Patient',
    subtitle: 'En un clic',
    description: "Ajoutez un nouveau patient en quelques secondes. Le moteur anti-doublon vérifie automatiquement les similarités (nom + prénom + date de naissance) pour protéger votre base.",
  },

  // ─── AGENDA ──────────────────────────────────────────────────────
  {
    id: 'agenda-studio',
    page: '/agenda',
    targetSelector: '[data-tour="agenda-header"]',
    placement: 'bottom',
    category: 'Agenda',
    icon: '📅',
    title: 'Studio Agenda',
    subtitle: 'Votre planning intelligent',
    description: "Gérez vos rendez-vous avec une vue Jour / Semaine / Mois. Chaque créneau est lié au dossier du patient.",
    features: [
      'Détection des conflits de créneaux',
      'Accès direct au dossier depuis le RDV',
      'Motifs de consultation paramétrables',
    ],
  },

  // ─── DOSSIER PATIENT ─────────────────────────────────────────────
  {
    id: 'patient-list',
    page: '/patients',
    placement: 'center',
    category: 'Dossier Patient',
    icon: '🏥',
    title: 'Vos Dossiers Patients',
    subtitle: 'Recherche et navigation',
    description: "Recherchez par nom, prénom ou numéro de dossier. Cliquez sur un patient pour accéder à son dossier complet avec tous les onglets cliniques.",
    features: [
      'Tri par date de création ou N° dossier',
      'Détection automatique des doublons',
      'Accès direct au dossier en 1 clic',
    ],
    isPageIntro: true,
  },
  {
    id: 'patient-tabs',
    page: '/patients',
    pageDynamic: true,  // Sera résolu vers /patients/:firstId
    targetSelector: '[data-tour="patient-tabs"]',
    placement: 'bottom',
    category: 'Dossier Patient',
    icon: '📋',
    title: 'Onglets du Dossier',
    subtitle: 'Radiologie · Documents · Archives',
    description: "Chaque dossier est organisé en onglets. L'IA céphalométrique, la génération de documents et l'historique sont à portée de clic.",
  },

  // ─── DOCUMENTS ───────────────────────────────────────────────────
  {
    id: 'document-hub',
    page: '/patients',
    pageDynamic: true,
    targetSelector: '[data-tour="document-tabs"]',
    placement: 'bottom',
    category: 'Documents',
    icon: '📄',
    title: 'Hub Documentaire',
    subtitle: 'Ordonnances · Devis · Certificats',
    description: "Générez n'importe quel document médical en quelques secondes. Les prescriptions sont enrichies par l'IA qui apprend vos habitudes.",
    features: [
      '💊 Ordonnances avec autocomplete médicaments',
      '💰 Devis \u0026 Notes d\'honoraires avec odontogramme FDI',
      '📜 Certificats médicaux et documents libres',
    ],
    badge: 'IA',
    preAction: 'switch-to-admin-tab',
  },

  // ─── BIBLIOTHÈQUE ────────────────────────────────────────────────
  {
    id: 'library-expert',
    page: '/bibliotheque',
    targetSelector: '[data-tour="library-search"]',
    placement: 'bottom',
    category: 'Bibliothèque',
    icon: '📚',
    title: 'Bibliothèque Clinique',
    subtitle: 'Protocoles et références',
    description: "Accédez à votre base de protocoles cliniques et fiches médicaments. Recherchez par catégorie, nom ou indication.",
  },

  // ─── SETTINGS ────────────────────────────────────────────────────
  {
    id: 'settings-nav',
    page: '/settings',
    targetSelector: '[data-tour="settings-navigation"]',
    placement: 'right',
    category: 'Configuration',
    icon: '⚙️',
    title: 'Paramètres du Cabinet',
    subtitle: 'Profil · Branding · Équipe',
    description: "Configurez les informations de votre cabinet, votre logo, vos couleurs de marque et vos spécialités. Tout est automatiquement appliqué sur vos documents PDF.",
    features: [
      'Logo et couleurs synchronisés sur les PDF',
      'Informations de contact et QR Code',
      'Support bilingue (français / arabe)',
    ],
    badge: 'Branding',
  },

  // ─── CONCLUSION ──────────────────────────────────────────────────
  {
    id: 'finish',
    page: '/dashboard',
    placement: 'center',
    category: 'Tour Terminé',
    icon: '🚀',
    title: 'Vous êtes prêt !',
    subtitle: 'Digital Crown est à votre service.',
    description: "Vous maîtrisez maintenant les fondamentaux. Commencez par créer votre premier patient ou configurez votre cabinet.",
    features: [
      '→ Créer un premier patient',
      '→ Configurer le cabinet dans Paramètres',
      '→ Lancer votre première analyse IA',
    ],
    isPageIntro: true,
  },
];

export const TOUR_STORAGE_KEY = 'digitalcrown_tour_completed';
export const TOUR_VERSION = '2.0';
