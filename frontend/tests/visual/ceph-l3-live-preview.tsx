import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import '../../src/index.css';
import { LivePreview } from '../../src/features/admin/DocumentStudio/LivePreview';

function Review(): React.ReactElement {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    let blobUrl: string | null = null;
    fetch('/ceph-l3-preview-fixture.pdf')
      .then(response => {
        if (!response.ok) throw new Error('PDF fixture fetch failed');
        return response.blob();
      })
      .then(blob => {
        if (!active) return;
        blobUrl = URL.createObjectURL(blob);
        setPdfUrl(blobUrl);
      });
    return () => {
      active = false;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, []);
  return <LivePreview pdfUrl={pdfUrl} loading={!pdfUrl}
    title="Bilan orthodontique — démonstration"
    onClose={() => {}} />;
}

createRoot(document.getElementById('root')!).render(<Review />);
