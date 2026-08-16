import { useLayoutEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { DigitalCrownLoader } from '../../components/DigitalCrownLoader';
import { PatientDetails as PatientDetailsInner } from './PatientDetailsInner';
import { resetPatientDocumentBoundary } from './patientDocumentBoundary';

/**
 * Route-level patient isolation boundary.
 *
 * React Router can reuse the same route component when only /patients/:id changes.
 * We therefore block rendering until all patient-scoped shared document state has
 * been reset, then mount a fresh patient tree keyed by the current id.
 */
export const PatientDetails = () => {
  const { id } = useParams();
  const [readyPatientId, setReadyPatientId] = useState<string | null>(null);

  useLayoutEffect(() => {
    resetPatientDocumentBoundary();
    setReadyPatientId(id ?? null);

    return () => {
      resetPatientDocumentBoundary();
    };
  }, [id]);

  if (!id || readyPatientId !== id) {
    return <DigitalCrownLoader text="Sécurisation du dossier patient..." />;
  }

  return <PatientDetailsInner key={id} />;
};
