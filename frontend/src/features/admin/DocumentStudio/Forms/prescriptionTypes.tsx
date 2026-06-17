import React from 'react';
import { Pill, Package, Droplets, FlaskConical, Wind, BadgeMinus, Hash } from 'lucide-react';

export interface DrugItem {
  id: number;
  name: string;
  dosage: string;
  forme: string;
  posologie: string;
  type?: 'MEDICAMENT' | 'EXAMEN';
  quantite?: number;
  non_substituable?: boolean;
}

export const FORMES = [
  { l: 'COMPRIMÉS', icon: Pill },
  { l: 'SACHETS', icon: Package },
  { l: 'GÉLULES', icon: Pill },
  { l: 'BAIN DE BOUCHE', icon: Droplets },
  { l: 'AMPOULES', icon: FlaskConical },
  { l: 'SIROP', icon: Droplets },
  { l: 'POMMADE', icon: BadgeMinus },
  { l: 'CRÈME', icon: BadgeMinus },
  { l: 'GOUTTES', icon: Droplets },
  { l: 'SPRAY', icon: Wind },
  { l: 'AUTRE', icon: Hash },
];

export const KIN_PRESET = {
  name: 'KIN',
  dosage: '-',
  forme: 'BAIN DE BOUCHE',
  posologie: '1 rinçage / jour pendant 7 jours',
};

export const DEFAULT_MOROCCO_PRESETS = [
  {
    label: 'Avulsion Simple',
    color: 'blue',
    drugs: [
      { name: 'DOLIPRANE', dosage: '1G', forme: 'COMPRIMÉS', posologie: '1 cp x 3 / jour pendant 4 jours' },
      { name: 'HEXTRIL', dosage: '-', forme: 'BAIN DE BOUCHE', posologie: '2 rincages / jour pendant 7 jours' },
    ],
  },
  {
    label: 'Extraction Sagesse / Chirurgie',
    color: 'rose',
    drugs: [
      { name: 'CLAMOXYL', dosage: '1G', forme: 'GÉLULES', posologie: '1 gél Matin et Soir pendant 6 jours' },
      { name: 'ANTADYS', dosage: '100MG', forme: 'COMPRIMÉS', posologie: '1 cp Matin et Soir pendant 3 jours (au milieu des repas)' },
      { name: 'DOLIPRANE', dosage: '1G', forme: 'COMPRIMÉS', posologie: '1 cp x 3 / jour si douleur' },
      { name: 'HEXTRIL', dosage: '-', forme: 'BAIN DE BOUCHE', posologie: '2 rincages / jour à partir de demain' },
    ],
  },
  {
    label: 'Abcès / Infection',
    color: 'emerald',
    drugs: [
      { name: 'AUGMENTIN', dosage: '1G', forme: 'SACHETS', posologie: '1 sach Matin et Soir pendant 7 jours' },
      { name: 'DOLIPRANE', dosage: '1G', forme: 'COMPRIMÉS', posologie: '1 cp x 3 / jour si douleur' },
    ],
  },
  {
    label: 'Gingivite / Parodontite',
    color: 'teal',
    drugs: [
      { name: 'BI-RODOGYL', dosage: '-', forme: 'COMPRIMÉS', posologie: '1 cp x 3 / jour pendant 6 jours' },
      { name: 'HEXTRIL', dosage: '-', forme: 'BAIN DE BOUCHE', posologie: '2 rincages / jour pendant 10 jours' },
      { name: 'DOLIPRANE', dosage: '1G', forme: 'COMPRIMÉS', posologie: '1 cp x 3 / jour si douleur' },
    ],
  },
  {
    label: 'Pulpite / Douleur Aiguë',
    color: 'amber',
    drugs: [
      { name: 'ALGODONT', dosage: '-', forme: 'COMPRIMÉS', posologie: '1 cp x 3 / jour' },
      { name: 'SOLUPRED', dosage: '20MG', forme: 'COMPRIMÉS', posologie: '3 cp le matin pendant 3 jours' },
    ],
  },
  {
    label: 'Chirurgie Implantaire',
    color: 'indigo',
    drugs: [
      { name: 'AUGMENTIN', dosage: '1G', forme: 'SACHETS', posologie: '1 sach Matin et Soir pendant 7 jours' },
      { name: 'SOLUPRED', dosage: '20MG', forme: 'COMPRIMÉS', posologie: '3 cp le matin pendant 3 jours' },
      { name: 'ANTADYS', dosage: '100MG', forme: 'COMPRIMÉS', posologie: '1 cp Matin et Soir pendant 3 jours' },
      { name: 'HEXTRIL', dosage: '-', forme: 'BAIN DE BOUCHE', posologie: '2 rincages / jour' },
    ],
  },
];

export function getFormeIcon(forme: string): React.ReactElement {
  const match = FORMES.find(f => forme.startsWith(f.l) || forme.toUpperCase().startsWith(f.l));
  const Icon = match?.icon || Pill;
  return <Icon size={13} />;
}

export function fuzzyMatch(input: string, target: string): boolean {
  const a = input.toLowerCase().trim();
  const b = target.toLowerCase();
  if (b.includes(a) || a.includes(b)) return true;
  if (a.length < 3) return false;
  let dist = 0, i = 0, j = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) { i++; j++; } else { dist++; j++; }
  }
  dist += Math.abs((a.length - i) - (b.length - j));
  return dist <= 3;
}
