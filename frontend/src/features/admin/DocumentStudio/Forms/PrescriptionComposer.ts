export type PrescriptionComposerState = {
  amount: string;
  frequency: string;
  constraint: string;
  context: string;
};

type ComposerOption = { value: string; label: string };

export const PRESCRIPTION_AMOUNT_OPTIONS: ComposerOption[] = [
  { value: '½ comprimé', label: '½ comprimé' },
  { value: '1 comprimé', label: '1 comprimé' },
  { value: '2 comprimés', label: '2 comprimés' },
  { value: '3 comprimés', label: '3 comprimés' },
  { value: '1 gélule', label: '1 gélule' },
  { value: '2 gélules', label: '2 gélules' },
  { value: '1 sachet', label: '1 sachet' },
  { value: '2 sachets', label: '2 sachets' },
  { value: '5 ml', label: '5 ml' },
  { value: '10 ml', label: '10 ml' },
  { value: '1 rinçage', label: '1 rinçage' },
  { value: '2 rinçages', label: '2 rinçages' },
];

export const PRESCRIPTION_FREQUENCY_OPTIONS: ComposerOption[] = [
  { value: 'le matin', label: 'Le matin' },
  { value: 'le soir', label: 'Le soir' },
  { value: 'matin et soir', label: 'Matin et soir' },
  { value: '1 fois par jour', label: '1 fois / jour' },
  { value: '2 fois par jour', label: '2 fois / jour' },
  { value: '3 fois par jour', label: '3 fois / jour' },
  { value: '4 fois par jour', label: '4 fois / jour' },
  { value: 'si douleur', label: 'Si douleur' },
];

export const PRESCRIPTION_CONSTRAINT_OPTIONS: ComposerOption[] = [
  { value: '1 jour', label: '1 jour' },
  { value: '3 jours', label: '3 jours' },
  { value: '4 jours', label: '4 jours' },
  { value: '5 jours', label: '5 jours' },
  { value: '6 jours', label: '6 jours' },
  { value: '7 jours', label: '7 jours' },
  { value: '10 jours', label: '10 jours' },
  { value: 'max 3/jour', label: 'Max 3 / jour' },
  { value: 'max 4/jour', label: 'Max 4 / jour' },
];

export const PRESCRIPTION_CONTEXT_OPTIONS: ComposerOption[] = [
  { value: 'après les repas', label: 'Après repas' },
  { value: 'pendant les repas', label: 'Pendant repas' },
  { value: 'avant les repas', label: 'Avant repas' },
  { value: 'à jeun', label: 'À jeun' },
  { value: 'au coucher', label: 'Au coucher' },
  { value: 'si douleur', label: 'Si douleur' },
  { value: '1 jour', label: '1 jour' },
  { value: '3 jours', label: '3 jours' },
  { value: '4 jours', label: '4 jours' },
  { value: '5 jours', label: '5 jours' },
  { value: '6 jours', label: '6 jours' },
  { value: '7 jours', label: '7 jours' },
  { value: '10 jours', label: '10 jours' },
];

const emptyComposer = (): PrescriptionComposerState => ({
  amount: '', frequency: '', constraint: '', context: '',
});

const normalize = (text: string) => text
  .toLowerCase()
  .replace(/[×]/g, 'x')
  .replace(/\s+/g, ' ')
  .trim();

const amountFromText = (text: string): string => {
  const endToken = '(?=\\s|[,.;:)]|$)';
  const rules: Array<[RegExp, (match: RegExpMatchArray) => string]> = [
    [new RegExp(`(?:\\b(?:1\\/2|0[,.]5)|½)\\s*(?:cp|comprim[eé])${endToken}`, 'i'), () => '½ comprimé'],
    [new RegExp(`\\b(\\d+)\\s*(?:cp|comprim[eé]s?)${endToken}`, 'i'), m => `${m[1]} comprimé${Number(m[1]) > 1 ? 's' : ''}`],
    [new RegExp(`\\b(\\d+)\\s*(?:g[eé]l|g[eé]lule?s?)${endToken}`, 'i'), m => `${m[1]} gélule${Number(m[1]) > 1 ? 's' : ''}`],
    [new RegExp(`\\b(\\d+)\\s*(?:sach|sachet?s?)${endToken}`, 'i'), m => `${m[1]} sachet${Number(m[1]) > 1 ? 's' : ''}`],
    [new RegExp(`\\b(\\d+)\\s*(?:rin[cç]age?s?)${endToken}`, 'i'), m => `${m[1]} rinçage${Number(m[1]) > 1 ? 's' : ''}`],
    [new RegExp(`\\b(5|10)\\s*ml${endToken}`, 'i'), m => `${m[1]} ml`],
  ];
  for (const [rule, map] of rules) {
    const match = text.match(rule);
    if (match) {
      const value = map(match);
      if (PRESCRIPTION_AMOUNT_OPTIONS.some(option => option.value === value)) return value;
    }
  }
  return '';
};

const frequencyFromText = (text: string): string => {
  if (/matin\s+et\s+soir/i.test(text)) return 'matin et soir';
  if (/\ble\s+matin\b/i.test(text)) return 'le matin';
  if (/\ble\s+soir\b/i.test(text)) return 'le soir';
  const painWithMaximum = /\bsi\s+douleur\b/i.test(text)
    && /(?:max(?:imum)?|sans\s+d[eé]passer)/i.test(text);
  if (painWithMaximum) return 'si douleur';
  const perDay = text.match(/(?:x\s*|\b)([1-4])\s*(?:x|fois)?\s*\/?\s*(?:par\s+)?jour/i);
  if (perDay) return `${perDay[1]} fois par jour`;
  if (/\bsi\s+douleur\b/i.test(text)) return 'si douleur';
  return '';
};

const durationFromText = (text: string): string => {
  const match = text.match(/(?:pendant\s+)?(1|3|4|5|6|7|10)\s+jours?\b/i);
  if (!match) return '';
  return `${match[1]} jour${match[1] === '1' ? '' : 's'}`;
};

const maxFromText = (text: string): string => {
  const match = text.match(/(?:max(?:imum)?\s*|sans\s+d[eé]passer\s+)([34])\s*(?:fois)?\s*\/?\s*(?:par\s+)?jour/i);
  return match ? `max ${match[1]}/jour` : '';
};

const contextFromText = (text: string): string => {
  if (/apr[eè]s\s+(?:les\s+)?repas/i.test(text)) return 'après les repas';
  if (/(?:pendant|au\s+milieu\s+des)\s+(?:les\s+)?repas/i.test(text)) return 'pendant les repas';
  if (/avant\s+(?:les\s+)?repas/i.test(text)) return 'avant les repas';
  if (/\b[àa]\s+jeun\b/i.test(text)) return 'à jeun';
  if (/au\s+coucher/i.test(text)) return 'au coucher';
  if (/\bsi\s+douleur\b/i.test(text)) return 'si douleur';
  return '';
};

export function parsePrescriptionPosology(posology: string): PrescriptionComposerState {
  if (!posology.trim()) return emptyComposer();
  const text = normalize(posology);
  const duration = durationFromText(text);
  const maximum = maxFromText(text);
  return {
    amount: amountFromText(text),
    frequency: frequencyFromText(text),
    constraint: maximum || duration,
    context: maximum && duration ? duration : contextFromText(text),
  };
}

const isDuration = (value: string) => /^\d+\s+jours?$/.test(value);
const isMaximum = (value: string) => /^max\s+[34]\/jour$/.test(value);

export function composePrescriptionPosology(state: PrescriptionComposerState): string {
  const chunks: string[] = [];
  if (state.amount) chunks.push(state.amount);
  if (state.frequency) chunks.push(state.frequency);

  let sentence = chunks.join(', ');

  if (isMaximum(state.constraint)) {
    const max = state.constraint.match(/[34]/)?.[0];
    sentence += `${sentence ? ', ' : ''}sans dépasser ${max} fois par jour`;
  } else if (isDuration(state.constraint)) {
    sentence += `${sentence ? ' pendant ' : 'Pendant '}${state.constraint}`;
  }

  if (isDuration(state.context)) {
    sentence += `${sentence ? ' pendant ' : 'Pendant '}${state.context}`;
  } else if (state.context) {
    sentence += `${sentence ? ', ' : ''}${state.context}`;
  }

  if (!sentence) return '';
  return `${sentence.charAt(0).toUpperCase()}${sentence.slice(1)}.`;
}

export function composerRecognitionCount(state: PrescriptionComposerState): number {
  return Object.values(state).filter(Boolean).length;
}
