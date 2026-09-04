export const IS_DC_PREVIEW_DEMO_BUILD = import.meta.env.VITE_DC_PREVIEW_DEMO === '1';

export function isDcPreviewHost(): boolean {
  const host = window.location.hostname;
  const isTrustedVercelPreview = host.startsWith('digital-crown-p2-runtime-')
    && host.endsWith('-achraf-benmoussa-s-projects.vercel.app');
  const isLocalEvidenceHost = import.meta.env.DEV
    && (host === 'localhost' || host === '127.0.0.1');

  return isTrustedVercelPreview || isLocalEvidenceHost;
}

export function isDcPreviewDemoRequested(): boolean {
  return IS_DC_PREVIEW_DEMO_BUILD
    && isDcPreviewHost()
    && new URLSearchParams(window.location.search).get('demo') === '1';
}
