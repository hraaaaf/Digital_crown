import { describe, expect, it } from 'vitest';
import { CEPHALO_ACCEPTED_IMAGE_TYPES, isSupportedCephaloImageFile } from './cephaloImageUploadPolicy';

describe('Step1 cephalometric radiograph upload policy', () => {
  it('accepts precisely the JPEG and PNG MIME types advertised by the chooser', () => {
    expect(CEPHALO_ACCEPTED_IMAGE_TYPES).toBe('image/jpeg,image/png');
    for (const type of ['image/jpeg', 'image/png']) {
      expect(isSupportedCephaloImageFile({ type })).toBe(true);
    }
  });

  it('fails closed for SVG, GIF, WebP, DICOM, missing or spoofed MIME strings', () => {
    for (const type of ['image/svg+xml', 'image/gif', 'image/webp', 'application/dicom', '', 'image/JPEG', 'text/html']) {
      expect(isSupportedCephaloImageFile({ type })).toBe(false);
    }
  });
});
