const MAX_SOURCE_BYTES = 12 * 1024 * 1024;

export type PreparedEmergencyPhoto = {
  previewUrl: string;
  candidates: Array<{
    imageB64: string;
    byteSize: number;
    width: number;
    height: number;
  }>;
};

const readDataUrl = (blob: Blob) => new Promise<string>((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(String(reader.result || ''));
  reader.onerror = () => reject(reader.error || new Error('Lecture de la photo impossible.'));
  reader.readAsDataURL(blob);
});

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

const canvasBlob = (canvas: HTMLCanvasElement, quality: number) => new Promise<Blob>((resolve, reject) => {
  canvas.toBlob(
    blob => blob ? resolve(blob) : reject(new Error('Compression de la photo impossible.')),
    'image/jpeg',
    quality,
  );
});

const base64Body = async (blob: Blob) => {
  const dataUrl = await readDataUrl(blob);
  const marker = 'base64,';
  const index = dataUrl.indexOf(marker);
  if (index < 0) throw new Error('Encodage photo impossible.');
  return dataUrl.slice(index + marker.length);
};

export async function prepareEmergencyPhoto(file: File): Promise<PreparedEmergencyPhoto> {
  if (!/^image\/(jpeg|png|webp)$/i.test(file.type)) {
    throw new Error('Utilisez une photo JPEG, PNG ou WebP.');
  }
  if (file.size <= 0 || file.size > MAX_SOURCE_BYTES) {
    throw new Error('La photo dépasse la limite autorisée.');
  }

  const image = await loadImage(file);
  const plans = [
    { maxEdge: 1280, quality: 0.82 },
    { maxEdge: 1280, quality: 0.70 },
    { maxEdge: 1024, quality: 0.68 },
    { maxEdge: 1024, quality: 0.56 },
    { maxEdge: 800, quality: 0.54 },
  ];
  const candidates: PreparedEmergencyPhoto['candidates'] = [];

  for (const plan of plans) {
    const scale = Math.min(1, plan.maxEdge / Math.max(image.naturalWidth, image.naturalHeight));
    const width = Math.max(1, Math.round(image.naturalWidth * scale));
    const height = Math.max(1, Math.round(image.naturalHeight * scale));
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Préparation de la photo impossible.');
    context.drawImage(image, 0, 0, width, height);
    const blob = await canvasBlob(canvas, plan.quality);
    candidates.push({
      imageB64: await base64Body(blob),
      byteSize: blob.size,
      width,
      height,
    });
  }

  if (!candidates.length) throw new Error('Préparation de la photo impossible.');
  return {
    previewUrl: URL.createObjectURL(file),
    candidates,
  };
}
