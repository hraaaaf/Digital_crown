import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = (file: string) => readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio', file),
  'utf8',
);

const hubContent = source('DocumentHubContent.tsx');

describe('Ordonnance Fidelity V3 U6 coherence', () => {
  it('removes only the redundant local-safety badge from the composed Ordonnance surface', () => {
    expect(hubContent).toContain('data-ordonnance-coherence="u6"');
    expect(hubContent).toContain('title^="Contrôles de sécurité partiellement disponibles"');
    expect(hubContent).toContain('display: none !important');
  });

  it('keeps legal metadata secondary but gives its switch a real 44px touch target', () => {
    expect(hubContent).toContain('data-ordonnance-secondary-meta');
    expect(hubContent).toContain('h-11 w-11');
    expect(hubContent).toContain('role="switch"');
    expect(hubContent).toContain('aria-checked={showLegalAnnotations}');
  });

  it('inherits semantic theme tokens instead of introducing an Ordonnance palette', () => {
    expect(hubContent).toContain('border-border-main');
    expect(hubContent).toContain('bg-glass-bg');
    expect(hubContent).toContain('bg-input-field');
    expect(hubContent).toContain('bg-card');
    expect(hubContent).toContain('text-text-muted');
    expect(hubContent).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(hubContent).not.toContain('data-theme=');
  });
});
