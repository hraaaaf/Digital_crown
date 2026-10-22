import test from 'node:test';
import assert from 'node:assert/strict';
import {
  FDI_PERMANENT, REVIEW_SCHEMA, createReview, setFdi, setBox, addTooth,
  removeTooth, confirmTooth, unconfirmTooth, duplicateFDIs, SPECIALTIES,
  createActDictionary, addActToDictionary, assignManualAct, exportReview
} from './lot05_j10e_fdi_review_state.mjs';

const image = () => ({ schema: REVIEW_SCHEMA, image_width: 2000, image_height: 1000,
  proposals: [{ fdi: '36', bbox: [.12,.20,.22,.64], confidence: .91 },
              { fdi: '37', bbox: [.24,.20,.33,.64], confidence: .75 }] });

test('strict permanent FDI list without temporary teeth', () => {
  assert.equal(FDI_PERMANENT.length, 32);
  assert.equal(new Set(FDI_PERMANENT).size, 32);
  assert.equal(FDI_PERMANENT[0], '11');
  assert.equal(FDI_PERMANENT.at(-1), '48');
  assert.equal(FDI_PERMANENT.includes('55'), false);
});
test('all model regions start UNCONFIRMED, no automatic act', () => {
  const state = createReview(image());
  assert.deepEqual(state.teeth.map(t => t.confirmed), [false,false]);
  assert.deepEqual(state.teeth.map(t => t.acts), [[],[]]);
  assert.throws(() => exportReview(state, []), /nothing_confirmed/);
});
test('a wrong FDI neighboring swap is corrected manually', () => {
  let s = createReview(image());
  s = setFdi(s, 't1', '35');
  assert.equal(s.teeth[0].fdi, '35');
  s = confirmTooth(s, 't1');
  assert.equal(exportReview(s, []).reviewed[0].fdi, '35');
});
test('duplicates may be proposed, but cannot be confirmed twice', () => {
  let s = createReview(image());
  s = setFdi(s, 't2', '36');
  assert.deepEqual(duplicateFDIs(s), ['36']);
  s = confirmTooth(s, 't1');
  assert.throws(() => confirmTooth(s, 't2'), /confirmed_fdi_already_exists/);
});
test('correcting a confirmed tooth resets confirmation and acts', () => {
  let s = confirmTooth(createReview(image()), 't1');
  let dict = addActToDictionary(createActDictionary(), 'Endodontie', 'Acte saisi par le praticien');
  s = assignManualAct(s, 't1', dict[0].id, dict);
  s = setBox(s, 't1', [.13,.20,.23,.64]);
  assert.equal(s.teeth[0].confirmed, false);
  assert.deepEqual(s.teeth[0].acts, []);
  assert.throws(() => assignManualAct(s, 't1', dict[0].id, dict), /unconfirmed_tooth/);
});
test('moving a tooth does not silently change FDI or adjacent proposals', () => {
  const s = setBox(createReview(image()), 't1', [.15,.21,.24,.65]);
  assert.equal(s.teeth[0].fdi, '36');
  assert.equal(s.teeth[1].fdi, '37');
  assert.deepEqual(s.teeth[1].bbox, image().proposals[1].bbox);
});
test('a dentist can add a missed tooth and remove a false proposal', () => {
  let s = createReview(image());
  s = addTooth(s, '38', [.4,.3,.49,.69]);
  assert.equal(s.teeth[2].origin, 'manual');
  s = removeTooth(s, 't2');
  assert.equal(s.teeth.length, 2);
  assert.deepEqual(s.teeth.map(t => t.fdi), ['36','38']);
});
test('temporary tooth, invalid bbox, nonfinite confidence all rejected', () => {
  const wrong = image(); wrong.proposals[0].fdi = '55';
  assert.throws(() => createReview(wrong), /unsupported_permanent_fdi/);
  const inf = image(); inf.proposals[0].bbox = [0,.2,Infinity,.7];
  assert.throws(() => createReview(inf), /invalid_normalized_box/);
  const conf = image(); conf.proposals[0].confidence = NaN;
  assert.throws(() => createReview(conf), /invalid_confidence/);
  assert.throws(() => setBox(createReview(image()),'t1',[-.2,0,.3,.5]),/out_of_frame_box/);
});
test('unconfirmed and unknown tooth cannot receive clinical act', () => {
  const s = createReview(image());
  const d = addActToDictionary([], 'Chirurgie', 'Geste manuel');
  assert.throws(() => assignManualAct(s,'t1','act-1',d),/unconfirmed_tooth/);
  assert.throws(() => assignManualAct(s,'x','act-1',d),/unknown_tooth/);
  assert.throws(() => assignManualAct(s,'t1','act-999',d),/unknown_dictionary_act/);
});
test('only practitioner dictionary definitions; duplicate and HTML rejected', () => {
  assert.equal(SPECIALTIES.length, 7);
  let d = addActToDictionary([], 'Prothèse', 'Acte A');
  assert.throws(() => addActToDictionary(d,'Prothèse',' acte a '),/duplicate_act_definition/);
  assert.throws(() => addActToDictionary(d,'Prothèse','<script>'),/invalid_act_label/);
  assert.throws(() => addActToDictionary(d,'Diagnostic automatique','Acte A'),/unknown_specialty/);
});
test('manual act only appears on confirmed tooth in export, never as model decision', () => {
  const dict = addActToDictionary([], 'Dentisterie conservatrice', 'Libellé métier');
  let s = confirmTooth(createReview(image()), 't1');
  s = assignManualAct(s, 't1', dict[0].id, dict);
  const out = exportReview(s, dict);
  assert.equal(out.reviewed.length, 1);
  assert.equal(out.reviewed[0].manually_selected_acts[0].label, 'Libellé métier');
  assert.equal(out.unconfirmed_proposals_excluded, 1);
  assert.equal(out.clinical_status, 'RESEARCH_ONLY_NOT_SAVED_TO_PATIENT');
  assert.equal(out.model_selected_acts, false);
  assert.equal(out.diagnosis_inferred, false);
  s = unconfirmTooth(s, 't1');
  assert.deepEqual(s.teeth[0].acts, []);
});
test('untrusted model JSON schema or malformed objects fail closed', () => {
  assert.throws(() => createReview({ ...image(),schema:'something-else' }),/wrong_review_schema/);
  assert.throws(() => createReview({ ...image(),image_width:0 }),/invalid_image_width/);
  assert.throws(() => createReview({ ...image(),proposals:[null] }),/invalid_proposal/);
  assert.throws(() => createReview({ ...image(),proposals: Array(301).fill(image().proposals[0]) }),/invalid_proposals/);
});
