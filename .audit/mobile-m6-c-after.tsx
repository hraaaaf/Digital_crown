import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import './styles/mobileGlassSystem.css';
import { ApptCard } from './features/mobile/Dashboard/components/ApptCard';
import { SignatureModal } from './features/mobile/Dashboard/components/SignatureModal';
import type { Appointment } from './features/mobile/Dashboard/types';

declare global {
  interface Window {
    __M6C_SAVE_COUNT__?: number;
    __M6C_LAST_SIGNATURE__?: string;
  }
}

const appointment: Appointment = {
  id: 77,
  patient_id: 12,
  patient_name: 'BENNANI Sara',
  phone: '0612345678',
  date: '2026-08-25',
  time: '10:30',
  duration_minutes: 60,
  motif: 'Contrôle implant 36',
  status: 'PLANIFIE',
};

const docs = [
  { id: 66, filename: 'Devis_Implant_36.pdf', document_type: 'DEVIS', created_at: '25/08/2026', signed: false },
];

function AuditApp() {
  const [open, setOpen] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(66);

  const save = (dataUrl: string) => {
    window.__M6C_SAVE_COUNT__ = (window.__M6C_SAVE_COUNT__ || 0) + 1;
    window.__M6C_LAST_SIGNATURE__ = dataUrl;
  };

  return (
    <div className="min-h-[100dvh] bg-background text-text-main font-outfit px-5 py-6" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
      <div className="document-watermark fixed inset-0 pointer-events-none opacity-50" />
      <main className="relative z-10 max-w-md mx-auto space-y-4">
        <div className="px-1">
          <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">Agenda mobile</p>
          <h1 className="text-xl font-black text-text-main mt-1">Signature au fauteuil</h1>
          <p className="text-xs text-text-muted mt-1">AFTER exact produit · BENNANI Sara</p>
        </div>
        <ApptCard apt={appointment} onStatusChange={() => {}} onWhatsApp={() => {}} onDelete={() => {}} onSign={() => setOpen(true)} />
      </main>

      {open && (
        <SignatureModal
          sigPatientName="BENNANI Sara"
          isLoadingDocs={false}
          sigDocs={docs}
          selectedDocId={selectedDocId}
          setSelectedDocId={setSelectedDocId}
          isSigning={false}
          onSaveSignature={save}
          onCancel={() => setOpen(false)}
        />
      )}
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<AuditApp />);
