import { describe, expect, it, vi } from 'vitest';
import {
  buildDocumentShareData,
  buildDocumentShareFile,
  canNativeShareDocument,
  isShareAbortError,
} from '../features/mobile/Context/mobileDocumentShare';

describe('M6-F contextual document share', () => {
  it('builds a generic PDF filename without patient or source filename metadata', () => {
    const blob = new Blob(['pdf'], { type: 'application/pdf' });
    const file = buildDocumentShareFile(blob, 'application/pdf');
    expect(file.name).toBe('document-digital-crown.pdf');
    expect(file.type).toBe('application/pdf');
    expect(file.name).not.toMatch(/BENNANI|Ordonnance/i);
  });

  it('builds a file-only ShareData payload', () => {
    const data = buildDocumentShareData(new Blob(['pdf'], { type: 'application/pdf' }));
    expect(Object.keys(data)).toEqual(['files']);
    expect(data.url).toBeUndefined();
    expect(data.text).toBeUndefined();
    expect(data.title).toBeUndefined();
    expect(data.files).toHaveLength(1);
  });

  it('fails closed when native file sharing is unavailable or rejected by canShare', () => {
    const data = buildDocumentShareData(new Blob(['pdf'], { type: 'application/pdf' }));
    expect(canNativeShareDocument({}, data)).toBe(false);
    expect(canNativeShareDocument({ share: vi.fn(), canShare: () => false }, data)).toBe(false);
    expect(canNativeShareDocument({ share: vi.fn(), canShare: () => { throw new Error('blocked'); } }, data)).toBe(false);
  });

  it('accepts only an explicit positive file capability check', () => {
    const data = buildDocumentShareData(new Blob(['pdf'], { type: 'application/pdf' }));
    const canShare = vi.fn((candidate?: ShareData) => Object.keys(candidate || {}).length === 1 && !!candidate?.files?.length);
    expect(canNativeShareDocument({ share: vi.fn(), canShare }, data)).toBe(true);
    expect(canShare).toHaveBeenCalledWith({ files: data.files });
  });

  it('classifies native cancellation without treating other errors as cancellation', () => {
    expect(isShareAbortError({ name: 'AbortError' })).toBe(true);
    expect(isShareAbortError({ name: 'NotAllowedError' })).toBe(false);
    expect(isShareAbortError(new Error('share failed'))).toBe(false);
  });
});
