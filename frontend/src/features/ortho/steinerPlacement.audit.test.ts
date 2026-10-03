import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const read=(rel:string)=>fs.readFileSync(path.resolve(process.cwd(),'src','features','ortho',rel),'utf8');

describe('LOT08 Steiner explicit landmark placement audit',()=>{
  it('does not leak unicode escape sequences into visible JSX text',()=>{
    const panel=read('components/CephaloAnalysisWorkbenchPanel.tsx');
    expect(panel).not.toMatch(/>[^<{]*\\u[0-9A-Fa-f]{4}/);
  });
  it('never aliases detector D_point or generic Gn to explicit Steiner identities',()=>{
    const protocol=read('cephaloSteinerProtocol.ts');
    expect(protocol).toContain("id: 'D_Steiner_1959'");
    expect(protocol).toContain("id: 'Gn_anatomic'");
    expect(protocol).not.toContain("{ id: 'D_point'");
    expect(protocol).not.toContain("{ id: 'Gn', label:");
  });
  it('routes image clicks through the audited landmark update path',()=>{
    const step=read('components/Step1CephaloBase.tsx');
    expect(step).toContain('onEmptyAreaClick={activeSteinerPlacement ? handleSteinerExplicitPointPlacement : undefined}');
    expect(step).toContain('updateLandmarksOptimistic([...next, { id: activeSteinerPlacement.id');
    const interaction=read('hooks/useCephaloInteraction.ts');
    expect(interaction).toContain("tagName === 'image'");
  });
  it('re-reads backend scientific authority after each persisted landmark edit',()=>{
    const store=read('stores/useOrthoStore.ts');
    expect(store).toContain('authoritativeRead = await cephaloRepository.getAnalysis(scheduledAnalysisId)');
    expect(store).toContain('anglesData: { ...refreshedAngles');
  });
});


it('reference delta must remain visually neutral in Steiner mode', () => {
  const source = read('components/CephaloAnalysisWorkbenchPanel.tsx');
  expect(source).toContain("analysis === 'steiner' ? P.textMuted : clinicalTone");
});


it('capture harness derives historical references from the packaged source-locked profile', () => {
  const source = fs.readFileSync(path.resolve(process.cwd(),'scripts','capture-ortho-studio-lot08-steiner-after.mjs'),'utf8');
  expect(source).toContain("backend','data','cephalometry','steiner_protocol_profile_v1.json");
  expect(source).not.toContain('const refs=[');
});


it('Steiner delta must come from backend protocol projection, never frontend subtraction', () => {
  const source = read('components/CephaloAnalysisWorkbenchPanel.tsx');
  expect(source).toContain("analysis === 'steiner'");
  expect(source).toContain("typeof metric?.reference_delta === 'number' ? metric.reference_delta : null");
});
