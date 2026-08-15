from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'Expected pattern not found in {path}: {old!r}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')

hub = ROOT / 'frontend/src/features/admin/DocumentHub.tsx'
replace_exact(
    hub,
    '"flex-1 h-full flex flex-col px-8 pt-6 pb-32 gap-3 overflow-y-auto bg-transparent dark:bg-slate-900/50 transition-all duration-500 custom-scrollbar",',
    '"flex-1 h-full flex flex-col px-3 sm:px-5 lg:px-8 pt-4 sm:pt-6 pb-32 gap-3 overflow-y-auto bg-transparent dark:bg-slate-900/50 transition-all duration-500 custom-scrollbar",',
)
replace_exact(
    hub,
    'sideStudioType === \'PREVIEW\' ? "pr-[570px]" : ""',
    'sideStudioType === \'PREVIEW\' ? "xl:pr-[570px]" : ""',
)
replace_exact(
    hub,
    'className="fixed right-2 top-2 bottom-2 w-[550px] z-[11000] drop-shadow-2xl"',
    'className="pointer-events-none"',
)

form = ROOT / 'frontend/src/features/admin/DocumentStudio/Forms/CertificateForm.tsx'
replace_exact(
    form,
    'className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-4xl w-full mx-auto py-8"',
    'className="space-y-6 sm:space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-4xl w-full mx-auto py-4 sm:py-6 lg:py-8"',
)
replace_exact(
    form,
    'className="bg-white/40 backdrop-blur-xl rounded-[3rem] border border-white/60 p-10 shadow-sm relative overflow-hidden"',
    'className="bg-white/40 backdrop-blur-xl rounded-[2rem] sm:rounded-[3rem] border border-white/60 p-4 sm:p-6 lg:p-10 shadow-sm relative overflow-hidden"',
)
replace_exact(
    form,
    'className="flex items-center justify-between mb-4 gap-4"',
    'className="flex flex-col items-stretch justify-between gap-3 mb-4 sm:flex-row sm:items-center sm:gap-4"',
)
replace_exact(
    form,
    'className="flex flex-wrap justify-center gap-4"',
    'className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-4"',
)
replace_exact(
    form,
    '"flex items-center justify-center gap-3 px-6 py-4 rounded-[1.5rem] text-[10px] font-black uppercase tracking-widest transition-all border shadow-sm min-w-[180px]",',
    '"flex w-full min-w-0 items-center justify-center gap-3 px-4 sm:px-6 py-4 rounded-[1.5rem] text-[10px] font-black uppercase tracking-widest transition-all border shadow-sm sm:min-w-[180px]",',
)

contract = ROOT / 'frontend/src/features/admin/DocumentStudio/CertificateResponsiveLayout.test.ts'
contract.write_text("""import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const frontendRoot = fileURLToPath(new URL('../../../../', import.meta.url));
const hub = readFileSync(`${frontendRoot}src/features/admin/DocumentHub.tsx`, 'utf8');
const form = readFileSync(`${frontendRoot}src/features/admin/DocumentStudio/Forms/CertificateForm.tsx`, 'utf8');

describe('P3 Certificat responsive layout contract', () => {
  it('ne réserve la colonne aperçu de 570px que sur grand écran', () => {
    expect(hub).toContain('xl:pr-[570px]');
    expect(hub).not.toContain('? \"pr-[570px]\" : \"\"');
  });

  it('ne conserve pas un wrapper fixe fantôme de 550px autour du portail aperçu', () => {
    expect(hub).toContain('className=\"pointer-events-none\"');
    expect(hub).not.toContain('fixed right-2 top-2 bottom-2 w-[550px] z-[11000]');
  });

  it('rend la carte et les choix Certificat adaptatifs aux petites largeurs', () => {
    expect(form).toContain('p-4 sm:p-6 lg:p-10');
    expect(form).toContain('grid grid-cols-1 gap-3 sm:grid-cols-3');
    expect(form).toContain('w-full min-w-0');
  });
});
""", encoding='utf-8')

print('P3 certificate responsive patch applied')
