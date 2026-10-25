import { useEffect, useRef, type ReactNode } from 'react';
import { useAuthStore } from '../../stores/useAuthStore';
import { hasUnsavedPatientDocumentDraft, resetPatientDocumentBoundary } from './patientDocumentBoundary';
import { usePatientDraftExitBlocker } from './patientDraftNavigationGate';

/**
 * LOT07 R2: navigation guard must stay ABOVE Cabinet's pathname-keyed animation
 * and the patient route. Data Router only. No patient records in this component.
 * A decline preserves the mounted editor; explicit discard clears dirty state
 * synchronously before React Router navigates to another patient.
 */
export function PatientDraftRouteGuard({ children }: { children: ReactNode }) {
  const { blocker, stayOnPatient, discardAndProceed } = usePatientDraftExitBlocker();
  const user = useAuthStore(state => state.user);
  const authenticated = useAuthStore(state => state.isAuthenticated);
  const scope = authenticated && user
    ? JSON.stringify([user.id, user.employer_id, user.role, user.permissions])
    : null;
  const previousScope = useRef<string | null>(null);
  const stayButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const previous = previousScope.current;
    // Invalidation is not an undoable patient switch. Never retain sensitive
    // in-progress document stores across logout, role change or account switch.
    const identityChanged = Boolean(previous && previous !== scope);
    if (identityChanged || (!scope && hasUnsavedPatientDocumentDraft())) {
      resetPatientDocumentBoundary();
    }
    previousScope.current = scope;
    if (blocker.state === 'blocked') {
      // Invalidation/logout is not a user-approved clinical navigation.
      // Proceed only for an invalidated session; another authenticated
      // principal/role must cancel the stale navigation entirely.
      if (!scope) blocker.proceed();
      else if (identityChanged) blocker.reset();
    }
  }, [scope, blocker.state, blocker]);

  useEffect(() => {
    if (blocker.state === 'blocked') stayButton.current?.focus();
  }, [blocker.state]);

  return (
    <>
      {children}
      {scope && blocker.state === 'blocked' && (
        <div
          className="fixed inset-0 z-[10020] flex items-center justify-center bg-slate-950/70 p-4"
          role="presentation"
        >
          <section
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="patient-draft-exit-heading"
            aria-describedby="patient-draft-exit-description"
            onKeyDown={(event) => {
              if (event.key === 'Escape') {
                event.preventDefault();
                stayOnPatient();
              }
            }}
            className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl"
          >
            <h2 id="patient-draft-exit-heading" className="text-lg font-bold text-slate-900">
              Brouillon non enregistré
            </h2>
            <p id="patient-draft-exit-description" className="mt-2 text-sm text-slate-700">
              Vous avez des modifications non enregistrées dans ce dossier.
              Voulez-vous rester pour les conserver ou quitter sans sauvegarder ?
            </p>
            <div className="mt-6 flex flex-wrap justify-end gap-3">
              <button
                ref={stayButton}
                type="button"
                onClick={stayOnPatient}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-900"
              >
                Rester sur ce dossier
              </button>
              <button
                type="button"
                onClick={discardAndProceed}
                className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
              >
                Quitter sans sauvegarder
              </button>
            </div>
          </section>
        </div>
      )}
    </>
  );
}
