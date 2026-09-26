import type {
  CatalogAct,
  CatalogDentition,
  CatalogSelectionMode,
  CatalogToothType,
  CatalogTreatmentArea,
  Specialty,
} from '../Settings/hooks/useCatalogStore';

export type ApplicabilityLevel = 'SUGGESTED' | 'SEARCH_ONLY' | 'INCOMPATIBLE';

export interface CatalogActContext {
  selectedTeeth: number[];
  selectionMode: CatalogSelectionMode;
  missingTeeth?: number[];
}

export interface EvaluatedCatalogAct {
  act: CatalogAct;
  specialty: string;
  level: ApplicabilityLevel;
  score: number;
  reasons: string[];
}

const unique = <T,>(values: T[]) => Array.from(new Set(values));

export const dentitionForTooth = (tooth: number): CatalogDentition =>
  Math.floor(tooth / 10) >= 5 ? 'PRIMARY' : 'PERMANENT';

export const toothTypeForTooth = (tooth: number): CatalogToothType => {
  const unit = tooth % 10;
  if (unit <= 2) return 'INCISOR';
  if (unit === 3) return 'CANINE';
  if (unit <= 5) return 'PREMOLAR';
  return 'MOLAR';
};

export const treatmentAreaForContext = (context: CatalogActContext): CatalogTreatmentArea => {
  if (context.selectionMode === 'GENERAL') return 'MOUTH';
  if (context.selectionMode === 'GROUP' || context.selectedTeeth.length > 1) return 'TOOTH_RANGE';
  return 'TOOTH';
};

const hasRestriction = <T,>(values: T[] | undefined): values is T[] =>
  Array.isArray(values) && values.length > 0;

export const evaluateCatalogAct = (
  act: CatalogAct,
  specialty: string,
  context: CatalogActContext,
): EvaluatedCatalogAct => {
  if (!act.is_active) {
    return { act, specialty, level: 'INCOMPATIBLE', score: -1, reasons: ['inactive'] };
  }

  const applicability = act.applicability || {};
  const reasons: string[] = [];
  const selected = context.selectedTeeth;
  const selectedDentitions = unique(selected.map(dentitionForTooth));
  const selectedTypes = unique(selected.map(toothTypeForTooth));
  const area = treatmentAreaForContext(context);

  if (hasRestriction(applicability.dentitions) && selectedDentitions.some(d => !applicability.dentitions!.includes(d))) {
    reasons.push('dentition');
  }
  if (hasRestriction(applicability.tooth_types) && selectedTypes.some(t => !applicability.tooth_types!.includes(t))) {
    reasons.push('tooth_type');
  }
  if (hasRestriction(applicability.selection_modes) && !applicability.selection_modes!.includes(context.selectionMode)) {
    reasons.push('selection_mode');
  }
  if (hasRestriction(applicability.treatment_areas) && !applicability.treatment_areas!.includes(area)) {
    reasons.push('treatment_area');
  }

  const min = applicability.min_selected_teeth ?? 0;
  const max = applicability.max_selected_teeth ?? null;
  if (selected.length < min) reasons.push('min_teeth');
  if (max !== null && selected.length > max) reasons.push('max_teeth');

  const missing = new Set(context.missingTeeth || []);
  if (applicability.requires_missing_tooth && !selected.some(t => missing.has(t))) {
    reasons.push('requires_missing_tooth');
  }
  if (applicability.requires_present_tooth && selected.some(t => missing.has(t))) {
    reasons.push('requires_present_tooth');
  }

  if (reasons.length > 0) {
    return { act, specialty, level: 'INCOMPATIBLE', score: -1, reasons };
  }

  const priority = Math.max(0, Math.min(100, applicability.suggestion_priority ?? 0));
  if (priority > 0) {
    return { act, specialty, level: 'SUGGESTED', score: priority, reasons: [] };
  }
  return {
    act,
    specialty,
    level: applicability.searchable_when_not_suggested === false ? 'INCOMPATIBLE' : 'SEARCH_ONLY',
    score: 0,
    reasons: [],
  };
};

export const evaluateCatalog = (
  specialties: Specialty[],
  context: CatalogActContext,
): EvaluatedCatalogAct[] =>
  specialties.flatMap(specialty =>
    specialty.acts.map(act => evaluateCatalogAct(act, specialty.name, context)),
  );

export const suggestedCatalogActs = (
  specialties: Specialty[],
  context: CatalogActContext,
  limit = 6,
): EvaluatedCatalogAct[] =>
  evaluateCatalog(specialties, context)
    .filter(item => item.level === 'SUGGESTED')
    .sort((a, b) => b.score - a.score || a.act.name.localeCompare(b.act.name))
    .slice(0, limit);

export const searchableCatalogActs = (
  specialties: Specialty[],
  context: CatalogActContext,
): EvaluatedCatalogAct[] =>
  evaluateCatalog(specialties, context)
    .filter(item => item.level !== 'INCOMPATIBLE')
    .sort((a, b) => b.score - a.score || a.act.name.localeCompare(b.act.name));
