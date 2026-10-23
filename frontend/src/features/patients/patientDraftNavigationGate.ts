import { useBlocker } from 'react-router-dom';
import { hasUnsavedPatientDocumentDraft, resetPatientDocumentBoundary } from './patientDocumentBoundary';

/**
 * LOT07 R2: pure policy for patient-dossier draft transitions.
 *
 * A change of search params (document tab) is not a dossier exit. Only the
 * departure from a patient dossier pathname can discard a clinical draft.
 * An explicit account revocation/unmount is not an "undoable" navigation:
 * the caller must clear sensitive state independently on logout.
 */
export function shouldBlockPatientDraftExit(
  currentPathname: string,
  nextPathname: string,
  dirty: boolean,
): boolean {
  return dirty &&
    /^\/patients\/\d+\/?$/.test(currentPathname) &&
    currentPathname !== nextPathname;
}

/**
 * Requires a React Router DATA router; do not mount under current BrowserRouter.
 *
 * Deliberately dormant while the global routing migration is tested. The
 * blocker must be installed ABOVE any keyed/animated patient subtree so that
 * a cancelled A->B navigation preserves its real editor, focused input, draft
 * and media tree. Mounting it only after the route has switched is TOO LATE.
 */
export function usePatientDraftExitBlocker() {
  const blocker = useBlocker(({ currentLocation, nextLocation }) =>
    shouldBlockPatientDraftExit(
      currentLocation.pathname,
      nextLocation.pathname,
      hasUnsavedPatientDocumentDraft(),
    ),
  );

  const discardAndProceed = () => {
    if (blocker.state !== 'blocked') return;
    // Explicit user choice only. Clear before B is allowed to mount.
    resetPatientDocumentBoundary();
    blocker.proceed();
  };

  const stayOnPatient = () => {
    if (blocker.state === 'blocked') blocker.reset();
  };

  return { blocker, discardAndProceed, stayOnPatient };
}
