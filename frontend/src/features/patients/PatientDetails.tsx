import { useEffect, useLayoutEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { DigitalCrownLoader } from '../../components/DigitalCrownLoader';
import { PatientDetails as PatientDetailsInner } from './PatientDetailsInner';
import {
  clearPatientDocumentDraftBoundary,
  hasUnsavedPatientDocumentDraft,
  resetPatientDocumentBoundary,
} from './patientDocumentBoundary';
import { isSamePatientDocumentTabNavigation } from './patientDocumentHistoryGuard';

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

  useEffect(() => {
    if (!id) return;

    const originalPushState = window.history.pushState.bind(window.history);
    const originalReplaceState = window.history.replaceState.bind(window.history);

    const shouldProceed = (url?: string | URL | null) => {
      if (!isSamePatientDocumentTabNavigation(window.location.href, url, id)) return true;
      if (!hasUnsavedPatientDocumentDraft()) return true;

      const confirmed = window.confirm(
        'Des modifications non enregistrées sont présentes dans le Studio documentaire. Changer de document et les abandonner ?',
      );
      if (!confirmed) return false;

      clearPatientDocumentDraftBoundary();
      return true;
    };

    window.history.pushState = ((data: unknown, unused: string, url?: string | URL | null) => {
      if (!shouldProceed(url)) return;
      originalPushState(data, unused, url);
    }) as History['pushState'];

    window.history.replaceState = ((data: unknown, unused: string, url?: string | URL | null) => {
      if (!shouldProceed(url)) return;
      originalReplaceState(data, unused, url);
    }) as History['replaceState'];

    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (!hasUnsavedPatientDocumentDraft()) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', beforeUnload);

    return () => {
      window.history.pushState = originalPushState;
      window.history.replaceState = originalReplaceState;
      window.removeEventListener('beforeunload', beforeUnload);
    };
  }, [id]);

  if (!id || readyPatientId !== id) {
    return <DigitalCrownLoader text="Sécurisation du dossier patient..." />;
  }

  return <PatientDetailsInner key={id} />;
};