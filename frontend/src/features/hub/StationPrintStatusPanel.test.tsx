import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { StationPrintStatusPanel } from './StationPrintStatusPanel';

describe('04.8-D Station print status rendering (pure, no dispatch)', () => {
  it('defaults to disabled and under construction with no action', () => {
    const html = renderToStaticMarkup(<StationPrintStatusPanel />);
    expect(html).toContain('data-print-status="disabled"');
    expect(html).toContain('en cours de construction');
    expect(html).not.toMatch(/<button|<a\s|<form|<iframe|<object/);
    expect(html).not.toContain('<embed');
  });

  it.each([
    ['fr', 'Retrait de document', 'dir="ltr"'],
    ['en', 'Document collection', 'dir="ltr"'],
    ['ar', 'استلام الوثيقة', 'dir="rtl"'],
  ] as const)('uses localized heading and reading direction %s', (language, heading, direction) => {
    const html = renderToStaticMarkup(<StationPrintStatusPanel language={language} />);
    expect(html).toContain(heading);
    expect(html).toContain(direction);
    expect(html).toContain('max-w-full');
    expect(html).toContain('break-words');
  });

  it.each(['held', 'uncertain', 'failed'] as const)(
    'shows the safe status %s but never enables print/download/retry',
    status => {
      const html = renderToStaticMarkup(<StationPrintStatusPanel status={status} language="en" />);
      expect(html).toContain(`data-print-status="${status}"`);
      expect(html).not.toMatch(/<button|<a\s|<form|<iframe|<object|window\.print/);
      expect(html).not.toContain('application/pdf');
      expect(html).not.toContain('data:');
    },
  );

  it('refuses to imply automatic retry when the spool status is uncertain', () => {
    const html = renderToStaticMarkup(
      <StationPrintStatusPanel status="uncertain" language="en" />,
    );
    expect(html).toContain('Do not submit the request again');
    expect(html).toContain('aria-live="assertive"');
    expect(html).not.toContain('completed');
  });
});
