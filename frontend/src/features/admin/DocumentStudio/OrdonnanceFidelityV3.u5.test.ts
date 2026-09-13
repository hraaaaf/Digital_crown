import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = (file: string) => readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio', file),
  'utf8',
);

const preview = source('DocumentHubPreview.tsx');
const livePreview = source('LivePreview.tsx');

describe('Ordonnance Fidelity V3 U5 desktop composition', () => {
  it('uses a balanced inline split at desktop width without collapsing the editor', () => {
    expect(preview).toContain("const desktopPreviewQuery = '(min-width: 1280px)'");
    expect(preview).toContain('data-ordonnance-desktop-preview="inline"');
    expect(preview).toContain('w-[300px]');
    expect(preview).toContain('padding-right: 21.25rem !important');
    expect(preview).toContain('padding-left: 1rem !important');
  });

  it('keeps the mobile and tablet preview modal behavior', () => {
    expect(preview).toContain('inline={desktopInline}');
    expect(preview).toContain('if (desktopInline)');
    expect(livePreview).toContain('if (inline)');
    expect(livePreview).toContain('createPortal(');
  });

  it('does not introduce a local Ordonnance theme or hard-coded palette', () => {
    expect(preview).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(preview).not.toContain('data-theme=');
  });
});