/** Step 1 file chooser and drag/drop share the same strict browser MIME policy. */
export const CEPHALO_ACCEPTED_IMAGE_TYPES = 'image/jpeg,image/png';

export function isSupportedCephaloImageFile(file: Pick<File, 'type'>): boolean {
  return file.type === 'image/jpeg' || file.type === 'image/png';
}
