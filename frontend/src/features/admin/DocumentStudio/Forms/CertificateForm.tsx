import React, { useEffect } from 'react';
import { CertificateForm as CertificateFormInner } from './CertificateFormInner';
import { isCertificateDirty, setCertificateDirty } from '../CertificateDirtyState';

interface CertificateFormProps {
  patientId: string;
  certifType: string;
  setCertifType: (type: string) => void;
  certifDays: number;
  setCertifDays: (days: number) => void;
  docDate: string;
  certifStartDate: string;
  setCertifStartDate: (date: string) => void;
  certifCustomMotif: string;
  setCertifCustomMotif: (value: string) => void;
}

export const CertificateForm: React.FC<CertificateFormProps> = props => {
  useEffect(() => {
    setCertificateDirty(false);
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (!isCertificateDirty()) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', beforeUnload);
    return () => {
      window.removeEventListener('beforeunload', beforeUnload);
      setCertificateDirty(false);
    };
  }, [props.patientId]);

  return (
    <div
      className="contents"
      onChangeCapture={() => setCertificateDirty(true)}
      onClickCapture={event => {
        if ((event.target as HTMLElement).closest('button')) setCertificateDirty(true);
      }}
    >
      <CertificateFormInner {...props} />
    </div>
  );
};
