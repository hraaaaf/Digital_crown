import { useBlocker } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { hasUnsavedPatientDocumentDraft, resetPatientDocumentBoundary } from './patientDocumentBoundary';

/**
 * LOT07 R2: pure policy for patient-dossier draft transitions.
 *
 * A document tab switch CAN unmount DocumentHub and lose a draft without
 * changing pathname. Allow only search changes retaining the current tab.
 * An explicit account revocation/unmount is not an "undoable" navigation:
 * the caller must clear sensitive state independently on logout.
 */
export function shouldBlockPatientDraftExit(
  currentPathname: string,
  nextPathname: string,
  dirty: boolean,
  currentSearch = '',
  nextSearch = '',
): boolean {
  if (!dirty || !/^\/patients\/\d+\/?$/.test(currentPathname)) return false;
  if (currentPathname !== nextPathname) return true;
  // A query-only switch away from DocumentHub destroys its editor in
  // PatientDetailsInner even though the /patients/:id pathname is unchanged.
  const currentTab = new URLSearchParams(currentSearch).get('tab') || 'tracking';
  const nextTab = new URLSearchParams(nextSearch).get('tab') || 'tracking';
  return currentTab !== nextTab;
}

/**
 * Requires a React Router DATA router; do not mount under current BrowserRouter.
 *
 * Mounted only by the isolated R2 Data Router candidate. The
 * blocker must be installed ABOVE any keyed/animated patient subtree so that
 * a cancelled A->B navigation preserves its real editor, focused input, draft
 * and media tree. Mounting it only after the route has switched is TOO LATE.
 */
export function usePatientDraftExitBlocker() {
  const blocker = useBlocker(({ currentLocation, nextLocation }) => {
    // Session invalidation and logout must not be stopped by a stale dirty bit.
    // The root navigation guard separately clears document state on revocation.
    const auth = useAuthStore.getState();
    if (!auth.isAuthenticated || !auth.user) return false;
    return shouldBlockPatientDraftExit(
      currentLocation.pathname,
      nextLocation.pathname,
      hasUnsavedPatientDocumentDraft(),
      currentLocation.search,
      nextLocation.search,
    );
  });

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
