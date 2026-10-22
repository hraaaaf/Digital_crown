/**
 * LOT05/J10F — Research-only FDI correction contract, no patient persistence.
 * The selected 32-class model is noncommercial and is NEVER bundled here.
 * All model labels are UNCONFIRMED until independently checked by a dentist.
 */
export const PERMANENT_FDI = Object.freeze(
  [1, 2, 3, 4].flatMap((q) => Array.from({ length: 8 }, (_, i) => String(q * 10 + i + 1))),
);
const allowed = new Set<string>(PERMANENT_FDI);
export const RESEARCH_SCHEMA = 'digital-crown-fdi-review-v1' as const;

export type FdiBox = [number, number, number, number];
export type FdiSuggestion = { fdi: string; bbox: FdiBox; confidence: number };
export type FdiResearchInput = {
  schema: typeof RESEARCH_SCHEMA;
  image_width: number;
  image_height: number;
  proposals: FdiSuggestion[];
};
export type FdiTooth = {
  id: string;
  fdi: string;
  bbox: FdiBox;
  confidence: number | null;
  origin: 'model' | 'manual';
  confirmed: boolean;
  actIds: string[];
};
export type FdiResearchState = {
  schema: typeof RESEARCH_SCHEMA;
  image_width: number;
  image_height: number;
  teeth: FdiTooth[];
  nextId: number;
};
export type ResearchAct = { id: string; specialty: string; label: string };
export const RESEARCH_SPECIALTIES = [
  'Dentisterie conservatrice', 'Endodontie', 'Parodontologie',
  'Chirurgie', 'Prothèse', 'Orthodontie', 'Autres',
] as const;

export function assertResearchFdi(fdi: unknown): asserts fdi is string {
  if (typeof fdi !== 'string' || !allowed.has(fdi)) throw new Error('FDI permanent invalide (11–48).');
}
export function validateBox(box: unknown): FdiBox {
  if (!Array.isArray(box) || box.length !== 4 || box.some((x) => typeof x !== 'number' || !Number.isFinite(x))) {
    throw new Error('Rectangle dentaire invalide.');
  }
  const [x1, y1, x2, y2] = box;
  if (!(0 <= x1 && x1 < x2 && x2 <= 1 && 0 <= y1 && y1 < y2 && y2 <= 1)) {
    throw new Error('Rectangle hors image.');
  }
  return [x1, y1, x2, y2];
}
export function parseResearchInput(raw: unknown): FdiResearchInput {
  if (raw === null || typeof raw !== 'object') throw new Error('JSON FDI invalide.');
  const data = raw as Partial<FdiResearchInput>;
  if (data.schema !== RESEARCH_SCHEMA) throw new Error('Version du JSON FDI incorrecte.');
  if (!Number.isInteger(data.image_width) || !(data.image_width! > 0 && data.image_width! <= 10000)
      || !Number.isInteger(data.image_height) || !(data.image_height! > 0 && data.image_height! <= 10000)) {
    throw new Error('Dimensions de l’image invalides.');
  }
  if (!Array.isArray(data.proposals) || data.proposals.length > 300) {
    throw new Error('Nombre de dents proposées invalide.');
  }
  const proposals = data.proposals.map((item) => {
    if (!item || typeof item !== 'object') throw new Error('Proposition invalide.');
    assertResearchFdi(item.fdi);
    const bbox = validateBox(item.bbox);
    if (typeof item.confidence !== 'number' || !Number.isFinite(item.confidence)
        || item.confidence < 0 || item.confidence > 1) throw new Error('Confiance du modèle invalide.');
    return { fdi: item.fdi, bbox, confidence: item.confidence };
  });
  return {
    schema: RESEARCH_SCHEMA, image_width: data.image_width!,
    image_height: data.image_height!, proposals,
  };
}
export function createResearchState(data: FdiResearchInput): FdiResearchState {
  const parsed = parseResearchInput(data);
  return {
    schema: RESEARCH_SCHEMA, image_width: parsed.image_width,
    image_height: parsed.image_height, nextId: parsed.proposals.length + 1,
    teeth: parsed.proposals.map((p, idx) => ({
      id: `t${idx + 1}`, fdi: p.fdi, bbox: [...p.bbox] as FdiBox,
      confidence: p.confidence, origin: 'model' as const,
      confirmed: false, actIds: [],
    })),
  };
}
const copy = (state: FdiResearchState): FdiResearchState => ({
  ...state, teeth: state.teeth.map((t) => ({ ...t, bbox: [...t.bbox] as FdiBox, actIds: [...t.actIds] })),
});
const requireTooth = (state: FdiResearchState, id: string): FdiTooth => {
  const found = state.teeth.find((t) => t.id === id);
  if (!found) throw new Error('Dent introuvable.');
  return found;
};
export function duplicateFdi(state: FdiResearchState): string[] {
  const count = new Map<string, number>();
  for (const tooth of state.teeth) count.set(tooth.fdi, (count.get(tooth.fdi) || 0) + 1);
  return [...count].filter(([, value]) => value > 1).map(([fdi]) => fdi).sort();
}
export function editResearchTooth(
  state: FdiResearchState, id: string, change: { fdi?: string; bbox?: FdiBox },
): FdiResearchState {
  const next = copy(state);
  const tooth = requireTooth(next, id);
  if (change.fdi !== undefined) {
    assertResearchFdi(change.fdi);
    tooth.fdi = change.fdi;
  }
  if (change.bbox !== undefined) tooth.bbox = validateBox(change.bbox);
  tooth.confirmed = false;
  tooth.actIds = [];
  return next;
}
export function addResearchTooth(state: FdiResearchState, fdi: string, box: FdiBox): FdiResearchState {
  assertResearchFdi(fdi);
  const next = copy(state), id = `t${next.nextId++}`;
  next.teeth.push({ id, fdi, bbox: validateBox(box), confidence: null, origin: 'manual', confirmed: false, actIds: [] });
  return next;
}
export function discardResearchTooth(state: FdiResearchState, id: string): FdiResearchState {
  requireTooth(state, id);
  return { ...copy(state), teeth: state.teeth.filter((t) => t.id !== id).map((t) => ({ ...t, bbox: [...t.bbox] as FdiBox, actIds: [...t.actIds] })) };
}
export function confirmResearchTooth(state: FdiResearchState, id: string): FdiResearchState {
  const next = copy(state), tooth = requireTooth(next, id);
  if (next.teeth.some((t) => t.id !== id && t.confirmed && t.fdi === tooth.fdi)) {
    throw new Error('Ce numéro FDI est déjà confirmé sur une autre dent.');
  }
  tooth.confirmed = true;
  return next;
}
export function undoResearchConfirmation(state: FdiResearchState, id: string): FdiResearchState {
  const next = copy(state), tooth = requireTooth(next, id);
  tooth.confirmed = false;
  tooth.actIds = [];
  return next;
}
export function addResearchAct(dictionary: ResearchAct[], specialty: string, label: string): ResearchAct[] {
  if (!(RESEARCH_SPECIALTIES as readonly string[]).includes(specialty)) throw new Error('Spécialité invalide.');
  const name = label.trim();
  if (name.length < 2 || name.length > 100 || /[<>\u0000-\u001f]/.test(name)) throw new Error('Libellé d’acte invalide.');
  if (dictionary.some((a) => a.specialty === specialty && a.label.toLocaleLowerCase('fr') === name.toLocaleLowerCase('fr'))) {
    throw new Error('Acte déjà dans le dictionnaire.');
  }
  return [...dictionary, { id: `act-${dictionary.length + 1}`, specialty, label: name }];
}
export function attachResearchAct(state: FdiResearchState, id: string, actId: string, dict: ResearchAct[]): FdiResearchState {
  if (!dict.some((a) => a.id === actId)) throw new Error('Acte inconnu.');
  const next = copy(state), tooth = requireTooth(next, id);
  if (!tooth.confirmed) throw new Error('Confirmer la dent avant tout acte.');
  if (!tooth.actIds.includes(actId)) tooth.actIds.push(actId);
  return next;
}
export function researchExport(state: FdiResearchState, dict: ResearchAct[]) {
  const checked = state.teeth.filter((t) => t.confirmed);
  if (!checked.length) throw new Error('Aucune dent confirmée.');
  if (new Set(checked.map((t) => t.fdi)).size !== checked.length) throw new Error('FDI confirmé en doublon.');
  return {
    schema: 'digital-crown-fdi-clinician-review-v1',
    clinical_status: 'RESEARCH_ONLY_NOT_SAVED_TO_PATIENT',
    image_width: state.image_width,
    image_height: state.image_height,
    reviewed: checked.map((t) => ({
      fdi: t.fdi, bbox: [...t.bbox], origin: t.origin,
      manually_selected_acts: t.actIds.map((a) => {
        const act = dict.find((d) => d.id === a);
        if (!act) throw new Error('Acte disparu.');
        return { specialty: act.specialty, label: act.label };
      }),
    })),
    unconfirmed_proposals_excluded: state.teeth.length - checked.length,
    diagnosis_inferred: false,
    model_selected_acts: false,
  };
}
