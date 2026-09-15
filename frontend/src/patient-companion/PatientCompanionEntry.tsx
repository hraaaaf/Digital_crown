import { useMemo } from 'react';
import { PatientCompanionPage, patientCompanionDefaultServices } from '../pages/PatientCompanionPage';

/**
 * Product entrypoint for QR activation. The raw invitation token is copied to
 * memory and removed from the visible URL before Patient Companion renders.
 * It is never written to Digital Crown storage.
 */
export const PatientCompanionEntry = () => {
  const initialToken = useMemo(() => {
    if (typeof window === 'undefined') return '';
    const token = new URLSearchParams(window.location.search).get('token')?.trim() || '';
    if (token && window.location.search) {
      window.history.replaceState({}, '', window.location.pathname);
    }
    return token;
  }, []);

  return (
    <PatientCompanionPage
      services={{ ...patientCompanionDefaultServices, initialToken }}
    />
  );
};

export default PatientCompanionEntry;
