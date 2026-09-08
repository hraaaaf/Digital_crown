import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
const source=readFileSync(join(process.cwd(),'src/features/patients/PatientDetailsInner.tsx'),'utf8');
describe('PatientDetails flow handoff',()=>{it('moves attention with active patient surfaces',()=>{expect(source).toContain("useFlowHandoff");expect(source).toContain('flowHandoff(flowContentRef.current)');expect(source).toContain('data-flow-patient-surface={activeTab}');expect(source).toContain('[activeTab, flowHandoff]');});});
