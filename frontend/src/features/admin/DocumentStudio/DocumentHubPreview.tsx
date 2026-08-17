import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
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
  const previousPdfUrl = useRef<string | null>(pdfUrl);
  const previousFingerprint = useRef(fingerprint);

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

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      event.preventDefault();
      onClose();
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  const generatePreview = useCallback(() => {
    setStale(true);
    void onGeneratePreview();
  }, [onGeneratePreview]);

  useDocumentPreviewController({
    enabled: open,
    fingerprint,
    onGeneratePreview: generatePreview,
  });

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ x: 600, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 600, opacity: 0 }}
          className="fixed inset-2 z-[11000] drop-shadow-2xl xl:left-auto xl:w-[550px]"
        >
          <LivePreview
            pdfUrl={stale ? null : pdfUrl}
            loading={loading || stale}
            onClose={onClose}
            onRefresh={generatePreview}
            title={title}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
};
