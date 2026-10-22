/* LOT05/05.7-J10E, offline research only. No patient DB/network/diagnosis. */
export const FDI_PERMANENT = Object.freeze(
  [1, 2, 3, 4].flatMap(q => Array.from({ length: 8 }, (_, i) => String(q * 10 + i + 1)))
);
export const REVIEW_SCHEMA = 'digital-crown-fdi-review-v1';
const allowedFdi = new Set(FDI_PERMANENT);
const finite = value => typeof value === 'number' && Number.isFinite(value);
const assert = (ok, message) => { if (!ok) throw Error(message); };
const cloneState = state => ({
  ...state,
  teeth: state.teeth.map(tooth => ({ ...tooth, bbox: [...tooth.bbox], acts: [...tooth.acts] }))
});
const mustFdi = fdi => {
  assert(typeof fdi === 'string' && allowedFdi.has(fdi), 'unsupported_permanent_fdi');
  return fdi;
};
const mustBox = bbox => {
  assert(Array.isArray(bbox) && bbox.length === 4 && bbox.every(finite), 'invalid_normalized_box');
  const [x1, y1, x2, y2] = bbox;
  assert(0 <= x1 && x1 < x2 && x2 <= 1 && 0 <= y1 && y1 < y2 && y2 <= 1, 'out_of_frame_box');
  return [...bbox];
};
const getTooth = (state, id) => {
  const tooth = state.teeth.find(t => t.id === id);
  assert(tooth, 'unknown_tooth');
  return tooth;
};
const noConfirmedDuplicate = (state, id, fdi) => {
  assert(!state.teeth.some(t => t.id !== id && t.confirmed && t.fdi === fdi), 'confirmed_fdi_already_exists');
};

export function createReview(data) {
  assert(data && typeof data === 'object' && data.schema === REVIEW_SCHEMA, 'wrong_review_schema');
  assert(Number.isInteger(data.image_width) && 0 < data.image_width && data.image_width <= 10000, 'invalid_image_width');
  assert(Number.isInteger(data.image_height) && 0 < data.image_height && data.image_height <= 10000, 'invalid_image_height');
  assert(Array.isArray(data.proposals) && data.proposals.length <= 300, 'invalid_proposals');
  return {
    schema: REVIEW_SCHEMA, image_width: data.image_width, image_height: data.image_height,
    nextId: data.proposals.length + 1,
    teeth: data.proposals.map((item, i) => {
      assert(item && typeof item === 'object', 'invalid_proposal');
      const fdi = mustFdi(item.fdi), bbox = mustBox(item.bbox);
      assert(finite(item.confidence) && 0 <= item.confidence && item.confidence <= 1, 'invalid_confidence');
      return { id: 't' + (i + 1), fdi, bbox, confidence: item.confidence,
        confirmed: false, origin: 'model', acts: [] };
    })
  };
}
export function setFdi(state, id, fdi) {
  fdi = mustFdi(fdi);
  const next = cloneState(state), tooth = getTooth(next, id);
  if (tooth.confirmed) noConfirmedDuplicate(next, id, fdi);
  tooth.fdi = fdi;
  if (tooth.origin === 'model') tooth.confirmed = false;
  tooth.acts = []; // invalidate previous clinical relation after change
  return next;
}
export function setBox(state, id, bbox) {
  const next = cloneState(state), tooth = getTooth(next, id);
  tooth.bbox = mustBox(bbox);
  tooth.confirmed = false;
  tooth.acts = [];
  return next;
}
export function addTooth(state, fdi, bbox) {
  fdi = mustFdi(fdi);
  const next = cloneState(state), id = 't' + next.nextId++;
  next.teeth.push({ id, fdi, bbox: mustBox(bbox), confidence: null,
    confirmed: false, origin: 'manual', acts: [] });
  return next;
}
export function removeTooth(state, id) {
  getTooth(state, id);
  const next = cloneState(state);
  next.teeth = next.teeth.filter(t => t.id !== id);
  return next;
}
export function confirmTooth(state, id) {
  const next = cloneState(state), tooth = getTooth(next, id);
  noConfirmedDuplicate(next, id, tooth.fdi);
  tooth.confirmed = true;
  return next;
}
export function unconfirmTooth(state, id) {
  const next = cloneState(state), tooth = getTooth(next, id);
  tooth.confirmed = false;
  tooth.acts = [];
  return next;
}
export function duplicateFDIs(state) {
  const counts = new Map();
  state.teeth.forEach(t => counts.set(t.fdi, (counts.get(t.fdi) ?? 0) + 1));
  return [...counts].filter(([, n]) => n > 1).map(([fdi]) => fdi).sort();
}
export const SPECIALTIES = Object.freeze([
  'Dentisterie conservatrice', 'Endodontie', 'Parodontologie', 'Chirurgie',
  'Prothèse', 'Orthodontie', 'Autres'
]);
export function createActDictionary() { return []; }
export function addActToDictionary(dictionary, specialty, label) {
  assert(Array.isArray(dictionary), 'invalid_act_dictionary');
  assert(SPECIALTIES.includes(specialty), 'unknown_specialty');
  assert(typeof label === 'string', 'invalid_act_label');
  label = label.trim();
  assert(label.length >= 2 && label.length <= 100 && !/[<>\u0000-\u001f]/.test(label), 'invalid_act_label');
  assert(!dictionary.some(a => a.specialty === specialty && a.label.toLocaleLowerCase('fr') === label.toLocaleLowerCase('fr')), 'duplicate_act_definition');
  return [...dictionary, { id: 'act-' + (dictionary.reduce((max, a) =>
    Math.max(max, Number(String(a.id).replace(/^act-/, '')) || 0), 0) + 1), specialty, label }];
}
export function assignManualAct(state, id, actId, dictionary) {
  assert(Array.isArray(dictionary) && dictionary.some(a => a.id === actId), 'unknown_dictionary_act');
  const next = cloneState(state), tooth = getTooth(next, id);
  assert(tooth.confirmed, 'unconfirmed_tooth_cannot_receive_act');
  if (!tooth.acts.includes(actId)) tooth.acts.push(actId);
  return next;
}
export function exportReview(state, dictionary) {
  assert(state?.schema === REVIEW_SCHEMA, 'wrong_review_schema');
  assert(Array.isArray(dictionary), 'invalid_act_dictionary');
  const confirmed = state.teeth.filter(t => t.confirmed);
  assert(confirmed.length > 0, 'nothing_confirmed');
  const confirmedFdis = confirmed.map(t => t.fdi);
  assert(new Set(confirmedFdis).size === confirmedFdis.length, 'duplicate_confirmed_fdi');
  return {
    schema: 'digital-crown-fdi-clinician-review-v1', clinical_status: 'RESEARCH_ONLY_NOT_SAVED_TO_PATIENT',
    image_width: state.image_width, image_height: state.image_height,
    reviewed: confirmed.map(t => ({
      fdi: t.fdi, bbox: [...t.bbox], origin: t.origin,
      manually_selected_acts: t.acts.map(act => {
        const definition = dictionary.find(a => a.id === act);
        assert(definition, 'missing_act_definition');
        return { specialty: definition.specialty, label: definition.label };
      })
    })),
    unconfirmed_proposals_excluded: state.teeth.length - confirmed.length,
    diagnosis_inferred: false, model_selected_acts: false
  };
}
