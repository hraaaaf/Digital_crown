import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const app = readFileSync(path.join(process.cwd(), 'src', 'App.tsx'), 'utf8');
const header = readFileSync(path.join(process.cwd(), 'src', 'components', 'Header.tsx'), 'utf8');
const hub = readFileSync(path.join(process.cwd(), 'src', 'features', 'hub', 'HubPage.tsx'), 'utf8');
const workstation = readFileSync(path.join(process.cwd(), 'src', 'features', 'hub', 'WorkstationExperiencePage.tsx'), 'utf8');

describe('V1.5-00.2 Hub routing contract', () => {
  it('keeps workstation mode separate from legacy appMode', () => {
    expect(app).toContain('return <Navigate to="/hub" replace />');
    expect(app).toContain('path="/hub"');
    expect(app).toContain('path="/cabinet"');
    expect(app).toContain('path="/station"');
    expect(app).toContain('path="/control-center"');
    expect(app).not.toContain("safeStorage.set('appMode', 'cabinet')");
    expect(app).not.toContain("safeStorage.set('appMode', 'station')");
  });

  it('uses only canonical theme tokens in V1.5 Hub surfaces', () => {
    const source = hub + workstation;
    expect(source).not.toMatch(/(?:rounded|text|tracking|shadow|bg|border)-\[[^\]]+\]/);
    expect(source).not.toMatch(/(?:amber|red|rose|green|emerald|blue|indigo|violet|purple|slate)-\d+/);
    expect(source).not.toContain('shadow-2xl');
    expect(source).toContain('rounded-elite-lg');
    expect(source).toContain('rounded-elite-sm');
    expect(source).toContain('shadow-elite');
    expect(source).toContain('shadow-elite-hover');
    expect(source).toContain('border-border-main');
    expect(source).toContain('text-text-muted');
    expect(source).toContain('bg-card-bg');
    expect(source).toContain('bg-primary/5');
  });

  it('exposes a clean Cabinet return to Hub', () => {
    expect(header).toContain('to="/hub"');
    expect(header).toContain("Changer d'espace");
  });
});
