import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
const read=(p:string)=>readFileSync(new URL(p,import.meta.url),'utf8');
describe('UX continuity contract',()=>{
  it('portals dialogs',()=>{const s=read('./components/CrownDialog.tsx');expect(s).toContain('createPortal');expect(s).toContain('document.body');expect(s).toContain("document.body.style.overflow = 'hidden'");expect(s).toContain("event.key === 'Tab'");expect(s).toContain("event.key === 'Escape'");expect(s).toContain('100dvh');});
  it('uses CrownDialog',()=>{const s=read('./features/patients/PatientList.tsx');expect(s).toContain('<CrownDialog');expect(s).toContain('data-dialog-autofocus');expect(s).not.toContain('h-screen w-screen');});
  it('hands wizard steps into view',()=>{const s=read('./features/admin/SetupWizard/SetupWizard.tsx');expect(s).toContain('useFlowHandoff');expect(s).toContain('flowHandoff(flowTargetRef.current)');expect(s).toContain('data-flow-step={currentStep}');});
});
