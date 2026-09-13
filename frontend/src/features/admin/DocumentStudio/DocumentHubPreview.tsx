import React, { useCallback, useEffect, useRef, useState } from 'react';
import { LivePreview } from './LivePreview';
import { useDocumentPreviewController } from './useDocumentPreviewController';

interface DocumentHubPreviewProps {
  open: boolean;
  fingerprint: string;
  pdfUrl: string | null;
  loading: boolean;
  title: string;
  onClose: () => void;
  onGeneratePreview: () => Promise<void> | void;
}

const desktopPreviewQuery = '(min-width: 1280px)';

export const DocumentHubPreview: React.FC<DocumentHubPreviewProps> = ({
  open,
  fingerprint,
  pdfUrl,
  loading,
  title,
  onClose,
  onGeneratePreview,
}) => {
  const [stale, setStale] = useState(false);
  const [desktopInline, setDesktopInline] = useState(() => (
    typeof window !== 'undefined' && window.matchMedia(desktopPreviewQuery).matches
  ));
  const previousPdfUrl = useRef<string | null>(pdfUrl);
  const previousFingerprint = useRef(fingerprint);

  useEffect(() => {
    const media = window.matchMedia(desktopPreviewQuery);
    const update = () => setDesktopInline(media.matches);
    update();
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    if (open && pdfUrl) setStale(true);
  }, [open, pdfUrl]);

  useEffect(() => {
    if (fingerprint !== previousFingerprint.current) {
      previousFingerprint.current = fingerprint;
      if (open) setStale(true);
    }
  }, [fingerprint, open]);

  useEffect(() => {
    if (pdfUrl !== previousPdfUrl.current) {
      previousPdfUrl.current = pdfUrl;
      setStale(false);
    }
  }, [pdfUrl]);

  const generatePreview = useCallback(() => {
    setStale(true);
    void onGeneratePreview();
  }, [onGeneratePreview]);

  useDocumentPreviewController({
    enabled: open,
    fingerprint,
    onGeneratePreview: generatePreview,
  });

  if (!open) return null;

  const preview = (
    <LivePreview
      pdfUrl={stale ? null : pdfUrl}
      loading={loading || stale}
      onClose={onClose}
      onRefresh={generatePreview}
      title={title}
      inline={desktopInline}
    />
  );

  if (desktopInline) {
    return (
      <>
        <style>{`
          @media (min-width: 1280px) {
            .relative:has(> [data-ordonnance-desktop-preview="inline"]) > .custom-scrollbar {
              padding-left: 1.25rem !important;
              padding-right: 27.8125rem !important;
            }
          }
        `}</style>
        <aside
          data-ordonnance-desktop-preview="inline"
          aria-label={`Aperçu document — ${title}`}
          className="absolute inset-y-6 right-5 z-30 hidden w-[400px] min-w-0 xl:block"
        >
          {preview}
        </aside>
      </>
    );
  }

  return preview;
};