import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();

describe('Ortho F5 UI safety contract', () => {
  it('keeps the F5 viewer explicitly non-interpretative', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/ortho/OrthoSuperimpositionViewer.tsx'), 'utf8').toLowerCase();
    expect(file).toContain('estimation géométrique uniquement');
    expect(file).toContain('interprétation clinique par le praticien');
    expect(file).toContain('engine_estimate_only');
    expect(file).toContain('validation clinique non établie');
    for (const forbidden of ['amélioration automatique', 'aggravation automatique', 'succès thérapeutique', 'échec thérapeutique', 'score de progression']) {
      expect(file).not.toContain(forbidden);
    }
  });

  it('requires practitioner-selected stable regions before estimation', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/ortho/OrthoSuperimpositionViewer.tsx'), 'utf8');
    expect(file).toContain('data-f5-roi={dataKey}');
    expect(file).toContain('!referenceRoi || !movingRoi || estimating');
    expect(file).toContain('Aucune zone n’est inventée automatiquement');
  });

  it('uses a dedicated modal work surface and canvas overlay', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/ortho/OrthoSuperimpositionViewer.tsx'), 'utf8');
    expect(file).toContain('role="dialog"');
    expect(file).toContain('aria-modal="true"');
    expect(file).toContain('data-f5-overlay-canvas');
    expect(file).toContain("ctx.setTransform(m00, m10, m01, m11, m02, m12)");
  });
});


describe('Ortho F5 source privacy boundary', () => {
  it('does not allow arbitrary external image URLs in the viewer', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/ortho/OrthoSuperimpositionViewer.tsx'), 'utf8');
    expect(file).toContain("startsWith('api/static/uploads/radios/')");
    expect(file).not.toContain("if (/^https?:\\/\\//i.test(imagePath)) return imagePath");
  });
});


describe('Ortho F5 modal keyboard contract', () => {
  it('traps focus, focuses close initially, restores focus, and supports Escape', () => {
    const file = fs.readFileSync(path.join(root, 'src/features/ortho/OrthoSuperimpositionViewer.tsx'), 'utf8');
    expect(file).toContain('closeButtonRef.current?.focus()');
    expect(file).toContain("event.key !== 'Tab'");
    expect(file).toContain('previousFocused?.focus()');
    expect(file).toContain("event.key === 'Escape'");
    expect(file).toContain('tabIndex={-1}');
  });
});
