import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const app = readFileSync(path.join(process.cwd(), 'src', 'App.tsx'), 'utf8');
const header = readFileSync(path.join(process.cwd(), 'src', 'components', 'Header.tsx'), 'utf8');

 describe('V1.5-00.2 Hub routing contract', () => {
  it('keeps workstation mode separate from legacy appMode', () => {
    expect(app).toContain("return <Navigate to=\"/hub\" replace />");
    expect(app).toContain('path="/hub"');
    expect(app).toContain('path="/cabinet"');
    expect(app).toContain('path="/station"');
    expect(app).toContain('path="/control-center"');
    expect(app).not.toContain("safeStorage.set('appMode', 'cabinet')");
    expect(app).not.toContain("safeStorage.set('appMode', 'station')");
  });

  it('exposes a clean Cabinet return to Hub', () => {
    expect(header).toContain('to="/hub"');
    expect(header).toContain("Changer d'espace");
  });
});
