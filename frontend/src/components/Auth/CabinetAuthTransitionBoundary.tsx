import { Fragment, type ReactNode } from 'react';
import { useLocation } from 'react-router-dom';

// CB-01 real first-login: /login remains publicly viewable while the visitor
// is unauthenticated. After a successful form submission, the existing
// ProtectedRoute must NOT reuse its prior anonymous verdict for /dashboard.
//
// Remount the unchanged fail-closed guard only when crossing public-entry <->
// protected-app. Preserve its state (and avoid a re-bootstrap) while moving
// between pages inside the protected application.
const publicEntryPaths = new Set(['/login', '/register', '/terms', '/privacy']);

export function CabinetAuthTransitionBoundary({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const key = publicEntryPaths.has(pathname) ? 'public-entry' : 'protected-app';
  return <Fragment key={key}>{children}</Fragment>;
}
