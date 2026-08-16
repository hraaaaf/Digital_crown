import React, { useEffect } from 'react';
import { api } from '../../../../services/api';
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

    const responseInterceptor = api.interceptors.response.use(response => {
      const url = response.config?.url || '';
      const archivedCertificate = url.includes('/documents/generate')
        && url.includes('archive=true')
        && !url.includes('preview=true');
      if (archivedCertificate) setCertificateDirty(false);
      return response;
    });

    window.addEventListener('beforeunload', beforeUnload);
    return () => {
      window.removeEventListener('beforeunload', beforeUnload);
      api.interceptors.response.eject(responseInterceptor);
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