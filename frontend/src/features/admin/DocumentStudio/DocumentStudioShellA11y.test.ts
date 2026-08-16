import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (relativePath: string) => readFileSync(new URL(relativePath, import.meta.url), 'utf8');

const headerSource = read('./StudioHeader.tsx');
const tabsSource = read('./StudioTabs.tsx');
const footerSource = read('./StudioFooter.tsx');
const previewSource = read('./LivePreview.tsx');

describe('Document Studio shell accessibility boundary', () => {
  it('exposes the document date label and pressed states', () => {
    expect(headerSource).toContain('htmlFor="document-studio-date"');
    expect(headerSource).toContain('id="document-studio-date"');
    expect(headerSource).toContain('aria-pressed={showOdontoPanoramique}');
    expect(tabsSource).toContain('aria-pressed={active}');
    expect(footerSource).toContain("aria-pressed={sideStudioType === 'PREVIEW'}");
  });

  it('declares modal surfaces and keyboard escape behavior', () => {
    expect(footerSource).toContain('role="dialog"');
    expect(footerSource).toContain('aria-modal="true"');
    expect(previewSource).toContain('role="dialog"');
    expect(previewSource).toContain("event.key === 'Escape'");
    expect(previewSource).toContain('title={`Aperçu PDF — ${title}`}');
  });

  it('keeps primary shell controls at touch-friendly heights', () => {
    expect(headerSource).toContain('min-h-11');
    expect(tabsSource).toContain('min-h-11');
    expect(footerSource).toContain('min-h-11');
    expect(previewSource).toContain('min-h-11');
  });
});
