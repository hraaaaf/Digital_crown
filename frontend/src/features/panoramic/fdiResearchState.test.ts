import { describe, expect, it } from 'vitest';
import {
  RESEARCH_SCHEMA, PERMANENT_FDI, isDeliberateFdiDrag, createResearchState, parseResearchInput,
  addResearchTooth, duplicateFdi, confirmResearchTooth, editResearchTooth,
  undoResearchConfirmation, addResearchAct, attachResearchAct, researchExport,
} from './fdiResearchState';

const source = () => ({
  schema: RESEARCH_SCHEMA, image_width: 1200, image_height: 600,
  proposals: [
    { fdi: '36', bbox: [0.2, 0.3, 0.3, 0.6] as [number,number,number,number], confidence: .8 },
    { fdi: '37', bbox: [0.4, 0.3, 0.5, 0.6] as [number,number,number,number], confidence: .75 },
  ],
});

describe('LOT05/J10F FDI research state (never a clinical patient record)', () => {
  it('has only 32 adult permanent FDI codes', () => {
    expect(PERMANENT_FDI).toHaveLength(32);
    expect(new Set(PERMANENT_FDI).size).toBe(32);
    expect(PERMANENT_FDI).not.toContain('51');
  });
  it('does not silently accept unknown JSON, primary FDI, nonfinite geometry, or bad image size', () => {
    expect(() => parseResearchInput({...source(), schema: 'unknown'})).toThrow();
    expect(() => parseResearchInput({...source(), image_width: -1})).toThrow();
    expect(() => parseResearchInput({...source(),proposals:[{...source().proposals[0], fdi:'55'}]})).toThrow();
    expect(() => parseResearchInput({...source(),proposals:[{...source().proposals[0], bbox:[.2,.1,Infinity,.9]}]})).toThrow();
  });
  it('does not treat a click or pointer jitter as an anatomy edit', () => {
    expect(isDeliberateFdiDrag(0, 0)).toBe(false);
    expect(isDeliberateFdiDrag(0.002, 0.001)).toBe(false);
    expect(isDeliberateFdiDrag(NaN, 0)).toBe(false);
    expect(isDeliberateFdiDrag(0.02, 0.01)).toBe(true);
  });
  it('never starts with any automatic confirmation or selected clinical act', () => {
    const state=createResearchState(source());
    expect(state.teeth.map(x=>x.confirmed)).toEqual([false,false]);
    expect(state.teeth.every(x=>x.actIds.length===0)).toBe(true);
    expect(()=>researchExport(state,[])).toThrow(/Aucune dent confirmée/);
  });
  it('permits correcting neighboring FDI, but invalidates stale manual acceptance', () => {
    let state=createResearchState(source());
    state=confirmResearchTooth(state,'t1');
    state=editResearchTooth(state,'t1',{fdi:'35'});
    expect(state.teeth[0].fdi).toBe('35');
    expect(state.teeth[0].confirmed).toBe(false);
  });
  it('blocks a second confirmed tooth with the same FDI, never shifts all tooth labels', () => {
    let state=createResearchState(source());
    state=editResearchTooth(state,'t2',{fdi:'36'});
    expect(duplicateFdi(state)).toEqual(['36']);
    state=confirmResearchTooth(state,'t1');
    expect(()=>confirmResearchTooth(state,'t2')).toThrow(/déjà confirmé/);
  });
  it('supports a missed tooth manually added, and requires manual confirmation', () => {
    let state=addResearchTooth(createResearchState(source()),'38',[.6,.25,.67,.65]);
    expect(state.teeth[2].origin).toBe('manual');
    expect(state.teeth[2].confirmed).toBe(false);
    state=confirmResearchTooth(state,'t3');
    state=editResearchTooth(state,'t3',{bbox:[.61,.25,.68,.65]});
    expect(state.teeth[2].confirmed).toBe(false);
  });
  it('never links an act to an unconfirmed tooth; act catalog written by user only', () => {
    const dictionary=addResearchAct([],'Endodontie','Acte saisi manuellement');
    const state=createResearchState(source());
    expect(()=>attachResearchAct(state,'t1',dictionary[0].id,dictionary)).toThrow(/Confirmer/);
    let next=confirmResearchTooth(state,'t1');
    next=attachResearchAct(next,'t1',dictionary[0].id,dictionary);
    const out=researchExport(next,dictionary);
    expect(out.reviewed).toHaveLength(1);
    expect(out.reviewed[0].manually_selected_acts[0].label).toBe('Acte saisi manuellement');
    expect(out.clinical_status).toBe('RESEARCH_ONLY_NOT_SAVED_TO_PATIENT');
    expect(out.model_selected_acts).toBe(false);
    expect(out.diagnosis_inferred).toBe(false);
    next=undoResearchConfirmation(next,'t1');
    expect(next.teeth[0].actIds).toEqual([]);
  });
});
