const MAX_SOURCE_BYTES = 12 * 1024 * 1024;
const MAX_EDGE = 2560;
const JPEG_QUALITY = 0.92;

export type PreparedEmergencyPhoto = {
  previewUrl: string;
  bytes: Uint8Array<ArrayBuffer>;
  byteSize: number;
  width: number;
  height: number;
  mimeType: 'image/jpeg';
};

const loadImage = (file: File) => new Promise<HTMLImageElement>((resolve, reject) => {
  const url = URL.createObjectURL(file);
  const image = new Image();
  image.onload = () => {
    URL.revokeObjectURL(url);
    resolve(image);
  };
  image.onerror = () => {
    URL.revokeObjectURL(url);
    reject(new Error('Photo illisible.'));
  };
  image.src = url;
});

const canvasBlob = (canvas: HTMLCanvasElement) => new Promise<Blob>((resolve, reject) => {
  canvas.toBlob(
    blob => blob ? resolve(blob) : reject(new Error('Préparation de la photo impossible.')),
    'image/jpeg',
    JPEG_QUALITY,
  );
});

export async function prepareEmergencyPhoto(file: File): Promise<PreparedEmergencyPhoto> {
  if (!/^image\/(jpeg|png|webp)$/i.test(file.type)) {
    throw new Error('Utilisez une photo JPEG, PNG ou WebP.');
  }
  if (file.size <= 0 || file.size > MAX_SOURCE_BYTES) {
    throw new Error('La photo dépasse la limite autorisée.');
  }

  const image = await loadImage(file);
  const scale = Math.min(1, MAX_EDGE / Math.max(image.naturalWidth, image.naturalHeight));
  const width = Math.max(1, Math.round(image.naturalWidth * scale));
  const height = Math.max(1, Math.round(image.naturalHeight * scale));
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  if (!context) throw new Error('Préparation de la photo impossible.');
  context.drawImage(image, 0, 0, width, height);

  const blob = await canvasBlob(canvas);
  if (blob.size <= 0 || blob.size > MAX_SOURCE_BYTES) {
    throw new Error('La photo préparée dépasse la limite autorisée.');
  }
  const bytes = new Uint8Array(await blob.arrayBuffer());
  return {
    previewUrl: URL.createObjectURL(blob),
    bytes,
    byteSize: bytes.byteLength,
    width,
    height,
    mimeType: 'image/jpeg',
  };
}
