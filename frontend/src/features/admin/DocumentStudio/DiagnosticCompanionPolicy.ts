export type CompanionTopic = 'PAIN' | 'AESTHETIC' | 'FUNCTION' | 'TRAUMA' | 'CHECKUP' | 'PEDIATRIC';

export interface CompanionOrientation {
  topic: CompanionTopic;
  title: string;
  checklist: string[];
}

export interface PractitionerAct {
  id: string;
  phase: string;
  act: string;
}

const ORIENTATIONS: Record<CompanionTopic, CompanionOrientation> = {
  PAIN: {
    topic: 'PAIN',
    title: 'Douleur / urgence à évaluer',
    checklist: [
      'Compléter l’anamnèse et l’examen clinique ciblé.',
      'Identifier les données cliniques manquantes avant toute conclusion.',
      'Décider des examens complémentaires selon le jugement du praticien.',
      'Documenter le diagnostic retenu par le praticien avant tout plan de traitement.',
    ],
  },
  AESTHETIC: {
    topic: 'AESTHETIC',
    title: 'Demande esthétique à caractériser',
    checklist: [
      'Clarifier la demande et les attentes du patient.',
      'Compléter l’examen clinique avant toute proposition thérapeutique.',
      'Documenter les alternatives réellement discutées avec le patient.',
      'Saisir manuellement les actes uniquement après décision du praticien.',
    ],
  },
  FUNCTION: {
    topic: 'FUNCTION',
    title: 'Situation fonctionnelle / prothétique à évaluer',
    checklist: [
      'Compléter l’examen clinique et le contexte prothétique.',
      'Identifier les données manquantes avant toute conclusion.',
      'Décider des examens complémentaires selon le jugement du praticien.',
      'Saisir manuellement les actes uniquement après décision du praticien.',
    ],
  },
  TRAUMA: {
    topic: 'TRAUMA',
    title: 'Traumatisme à évaluer cliniquement',
    checklist: [
      'Recueillir les circonstances et le délai du traumatisme.',
      'Compléter l’examen clinique avant toute conclusion.',
      'Décider des examens complémentaires selon le jugement du praticien.',
      'Documenter la décision clinique du praticien avant transfert vers un document.',
    ],
  },
  CHECKUP: {
    topic: 'CHECKUP',
    title: 'Contrôle / prévention à structurer',
    checklist: [
      'Compléter l’examen clinique de contrôle.',
      'Identifier les constatations qui nécessitent une documentation spécifique.',
      'Décider des examens complémentaires selon le jugement du praticien.',
      'Saisir manuellement les actes retenus si nécessaire.',
    ],
  },
  PEDIATRIC: {
    topic: 'PEDIATRIC',
    title: 'Contexte pédiatrique à évaluer',
    checklist: [
      'Vérifier les informations patient disponibles avant toute conclusion.',
      'Compléter l’examen clinique adapté au contexte.',
      'Décider des examens complémentaires selon le jugement du praticien.',
      'Saisir manuellement les actes uniquement après décision du praticien.',
    ],
  },
};

export function getCompanionOrientation(topic: CompanionTopic): CompanionOrientation {
  return ORIENTATIONS[topic];
}

export function normalizePractitionerAct(value: string): string {
  return String(value || '').trim().replace(/\s+/g, ' ');
}

export function canTransferPractitionerActs(
  acts: PractitionerAct[],
  practitionerConfirmed: boolean,
): boolean {
  if (!practitionerConfirmed || acts.length === 0) return false;
  return acts.every(item => normalizePractitionerAct(item.act).length > 0);
}

export function buildQuoteTransferPayload(
  acts: PractitionerAct[],
  practitionerConfirmed: boolean,
): Array<{ suggested_act: string; fdi: 'Global'; phase: string }> {
  if (!canTransferPractitionerActs(acts, practitionerConfirmed)) return [];
  return acts.map(item => ({
    suggested_act: normalizePractitionerAct(item.act),
    fdi: 'Global' as const,
    phase: item.phase,
  }));
}
