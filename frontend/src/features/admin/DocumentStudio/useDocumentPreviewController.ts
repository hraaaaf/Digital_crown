import { useEffect, useRef } from 'react';

interface UseDocumentPreviewControllerParams {
  enabled: boolean;
  fingerprint: string;
  onGeneratePreview: () => void;
  delayMs?: number;
}

export function useDocumentPreviewController({
  enabled,
  fingerprint,
  onGeneratePreview,
  delayMs = 1200,
}: UseDocumentPreviewControllerParams) {
  const lastGeneratedFingerprint = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) return;
    if (lastGeneratedFingerprint.current === fingerprint) return;

    const timer = window.setTimeout(() => {
      lastGeneratedFingerprint.current = fingerprint;
      onGeneratePreview();
    }, delayMs);

    return () => window.clearTimeout(timer);
  }, [delayMs, enabled, fingerprint, onGeneratePreview]);

  useEffect(() => {
    if (!enabled) lastGeneratedFingerprint.current = null;
  }, [enabled]);
}
