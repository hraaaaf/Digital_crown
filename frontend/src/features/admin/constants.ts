import { 
  Stethoscope, 
  Activity, 
  LayoutGrid, 
  Component, 
  Scissors, 
  Anchor, 
  Sparkles, 
  Building2, 
  Moon,
  Phone,
  Palette,
  CheckCircle2,
  Image as ImageIcon,
  Wand2,
  HeartPulse,
  Leaf,
  Layers,
  QrCode
} from 'lucide-react';

export const SPECIALTIES_DICT = [
  { id: 'soins', fr: 'Soins', ar: 'علاج', icon: HeartPulse },
  { id: 'endo', fr: 'Endodontie', ar: 'علاج العصب', icon: Activity },
  { id: 'paro', fr: 'Parodontologie', ar: 'أمراض اللثة', icon: Leaf },
  { id: 'ortho', fr: 'Orthodontie', ar: 'تقويم الأسنان', icon: LayoutGrid },
  { id: 'prothese', fr: 'Prothèse', ar: 'تعويض الأسنان', icon: Component },
  { id: 'chirurgie', fr: 'Chirurgie', ar: 'جراحة', icon: Scissors },
  { id: 'implant', fr: 'Implantologie', ar: 'زراعة الأسنان', icon: Anchor },
  { id: 'blanchiment', fr: 'Blanchiment', ar: 'تبييض الأسنان', icon: Sparkles },
  { id: 'esthetique', fr: 'Esthétique', ar: 'تجميل الأسنان', icon: Wand2 }
];

export const STEPS = [
  { id: 1, title: "Identité", icon: Building2 },
  { id: 2, title: "Domaines", icon: Stethoscope },
  { id: 3, title: "Contacts", icon: Phone },
  { id: 4, title: "Signature", icon: QrCode },
  { id: 5, title: "Design", icon: ImageIcon },
  { id: 6, title: "Ambiance", icon: Palette },
  { id: 7, title: "Lancement", icon: CheckCircle2 }
];

// Wait, I should use the correct icons. Let's re-import them or use string names/component references if needed.
// Actually, I'll just copy the constants from SetupWizard and fix imports.

export const CROWN_MESSAGES: Record<number, string> = {
  1: "Bienvenue Docteur. Commençons par définir l'identité de votre cabinet pour personnaliser vos documents.",
  2: "Sélectionnez vos expertises. Je vais les formater automatiquement en Français et en Arabe.",
  3: "Comment vos patients peuvent-ils vous joindre ? Ces infos figureront discrètement en pied de page.",
  4: "Donnez une dimension numérique à vos documents. Que doivent voir vos patients en scannant votre QR Code ?",
  5: "C'est ici que la magie opère. Choisissez un style qui vous ressemble. L'aperçu à droite est vivant !",
  6: "Dernière touche : l'ambiance de votre logiciel. Ghost Elite est mon préféré pour son élégance.",
  7: "Tout est prêt. Vérifiez une dernière fois. Je m'occupe de configurer tout votre univers Digital Crown."
};

export const PREMIUM_FONTS = [
  { id: 'inter', name: 'Inter Tight', desc: 'Clarté clinique absolue, lecture rapide.', class: 'font-sans' },
  { id: 'outfit', name: 'Outfit', desc: 'Design premium, élégance moderne.', class: 'font-outfit' },
  { id: 'playfair', name: 'Playfair Display', desc: 'Prestige traditionnel, haute spécialité.', class: 'font-playfair' },
  { id: 'mono', name: 'JetBrains Mono', desc: 'Sécurité maximale des dosages (Monospace).', class: 'font-mono' },
  { id: 'serif', name: 'Lora', desc: 'Sérif humaniste, lisibilité optimale sur papier.', class: 'font-serif' }
];

export const DESIGN_VARIANTS = [
  { id: 'swiss', name: 'Swiss Clinic (Asymétrique)', icon: LayoutGrid },
  { id: 'royal', name: 'Royal Elite (Classique)', icon: Building2 }
];

export const BRAND_IDENTITIES = [
  {
    id: 'elite-royal',
    name: 'Élite Royal',
    desc: 'Autorité & Confiance',
    primary: '#003380', secondary: '#1e40af', accent: '#60a5fa',
    vibe: 'Professionnel Classique'
  },
  {
    id: 'rose-prestige',
    name: 'Rose Prestige',
    desc: 'Luxe & Douceur',
    primary: '#db2777', secondary: '#9d174d', accent: '#fbcfe8',
    vibe: 'Féminin & Esthétique'
  },
  {
    id: 'emerald-zen',
    name: 'Émeraude Zen',
    desc: 'Santé & Sérénité',
    primary: '#065f46', secondary: '#047857', accent: '#a7f3d0',
    vibe: 'Naturel & Serein'
  },
  {
    id: 'indigo-night',
    name: 'Indigo Night',
    desc: 'Innovation & Tech',
    primary: '#312e81', secondary: '#4338ca', accent: '#c7d2fe',
    vibe: 'Moderne & Futuriste'
  },
  {
    id: 'noir-elite',
    name: 'Graphite Élite',
    desc: 'Minimalisme & Pureté',
    primary: '#0f172a', secondary: '#334155', accent: '#94a3b8',
    vibe: 'Épuré & Intemporel'
  },
  {
    id: 'gold-heritage',
    name: 'Or Héritage',
    desc: 'Excellence & Tradition',
    primary: '#854d0e', secondary: '#a16207', accent: '#fef9c3',
    vibe: 'Prestigieux & Ancien'
  },
  {
    id: 'mono-black',
    name: 'Monochrome Absolu',
    desc: 'Noir & Blanc Pur',
    primary: '#000000', secondary: '#475569', accent: '#94a3b8',
    vibe: 'Impression Économique & Nette'
  },
  {
    id: 'pediatric-soft',
    name: 'Pédiatrie Douce',
    desc: 'Chaleur & Bienveillance',
    primary: '#f97316', secondary: '#fb923c', accent: '#7dd3fc',
    vibe: 'Enfance & Sérénité'
  }
];

export const APP_THEMES = [
  {
    id: 'elite',
    dataTheme: '',
    name: 'Ghost Elite',
    desc: 'Clarté Premium',
    defaultAccent: '#003380',
    preview: { bg: '#f8fafc', card: '#ffffff', border: '#e2e8f0', text: '#0f172a', accent: '#003380' }
  },
  {
    id: 'prestige',
    dataTheme: 'prestige',
    name: 'Nuit Elite',
    desc: 'Sombre & Luxueux',
    defaultAccent: '#3b82f6',
    preview: { bg: '#020617', card: '#0f172a', border: '#1e293b', text: '#f8fafc', accent: '#3b82f6' }
  },
  {
    id: 'emerald',
    dataTheme: 'emerald',
    name: 'Zen Émeraude',
    desc: 'Serein & Médical',
    defaultAccent: '#059669',
    preview: { bg: '#f0fdf4', card: '#fcfdfd', border: '#d1fae5', text: '#064e3b', accent: '#059669' }
  },
  {
    id: 'rose',
    dataTheme: 'rose',
    name: 'Rose Prestige',
    desc: 'Douceur & Luxe',
    defaultAccent: '#db2777',
    preview: { bg: '#fff1f2', card: '#fffbfb', border: '#fecdd3', text: '#831843', accent: '#db2777' }
  },
  {
    id: 'ocean',
    dataTheme: 'ocean',
    name: 'Océan Profond',
    desc: 'Confiance & Clarté',
    defaultAccent: '#0284c7',
    preview: { bg: '#f0f9ff', card: '#ffffff', border: '#bae6fd', text: '#0c4a6e', accent: '#0284c7' }
  },
  {
    id: 'graphite',
    dataTheme: 'graphite',
    name: 'Graphite Zen',
    desc: 'Minimalisme Total',
    defaultAccent: '#475569',
    preview: { bg: '#f1f5f9', card: '#ffffff', border: '#e2e8f0', text: '#0f172a', accent: '#475569' }
  },
  {
    id: 'high-contrast',
    dataTheme: 'high-contrast',
    name: 'Haut Contraste',
    desc: 'Lisibilité Clinique',
    defaultAccent: '#000000',
    preview: { bg: '#ffffff', card: '#ffffff', border: '#000000', text: '#000000', accent: '#000000' }
  }
] as const;
