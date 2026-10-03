import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const read=(rel:string)=>fs.readFileSync(path.resolve(process.cwd(),'src','features','ortho',rel),'utf8');

describe('LOT08 Steiner explicit landmark placement audit',()=>{
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
